"""
config_store.py - 讀寫 nomi_host/config.yaml 的共用工具

目前用於前端語言選項的持久化：
- 語言選項存於 config.yaml 的頂層 `language` 欄位
- 若 config.yaml 不存在或未設定 language，預設為英文 ("en")
- 寫入時保留其他區塊（例如 llm.api_key）與（若安裝 ruamel）註解、格式

安全原則（重要）：
- 若 config.yaml 已存在且有內容、卻無法被解析成 dict，set_language 會直接中止
  並拋出例外，「絕不」用只含 language 的內容覆寫檔案。這可避免因暫時性讀取/解析
  失敗而抹除使用者的 llm 設定（api_key 等）。
"""

import os
import threading
from typing import Any, Dict, Optional, Tuple

import yaml

# 選用：ruamel.yaml 可在往返讀寫時保留註解與格式（未安裝時自動退回 PyYAML）
try:
    from ruamel.yaml import YAML as _RuamelYAML

    _ruamel: Optional["_RuamelYAML"] = _RuamelYAML()
    _ruamel.preserve_quotes = True
    _ruamel.indent(mapping=2, sequence=4, offset=2)
except Exception:  # pragma: no cover - ruamel 未安裝
    _ruamel = None

# 支援的語言代碼；預設英文
SUPPORTED_LANGUAGES = ("en", "zh", "ja")
DEFAULT_LANGUAGE = "en"

# config.yaml 位於 nomi_host 專案根目錄（本檔在 control_panel/backend/modules/ 下，往上 4 層）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_NOMI_HOST_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_DIR)))
CONFIG_PATH = os.path.join(_NOMI_HOST_DIR, "config.yaml")

# 讀寫 config.yaml 時序列化，避免多執行緒同時讀寫造成檔案損毀
_lock = threading.Lock()


class ConfigReadError(Exception):
    """config.yaml 存在且有內容但無法解析；為避免覆寫遺失資料而中止寫入。"""


def _read_existing() -> Tuple[Dict[str, Any], Any]:
    """
    讀取現有 config.yaml。

    Returns:
        (data, doc)
        - data: 解析後的一般 dict（供讀取值使用）
        - doc:  供 ruamel 原地回寫、保留註解的文件物件；PyYAML 模式下為 None
        檔案不存在或內容為空 -> ({}, None)（可安全新建）

    Raises:
        ConfigReadError: 檔案存在且有內容，但無法解析為 dict（此時「絕不」覆寫）
    """
    if not os.path.exists(CONFIG_PATH):
        return {}, None

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        raise ConfigReadError(f"cannot read {CONFIG_PATH}: {e}")

    if raw.strip() == "":
        return {}, None

    if _ruamel is not None:
        try:
            doc = _ruamel.load(raw)
        except Exception as e:
            raise ConfigReadError(f"cannot parse {CONFIG_PATH}: {e}")
        if doc is None:
            return {}, None
        if not isinstance(doc, dict):
            raise ConfigReadError(f"{CONFIG_PATH} top-level is not a mapping")
        return dict(doc), doc

    try:
        data = yaml.safe_load(raw)
    except Exception as e:
        raise ConfigReadError(f"cannot parse {CONFIG_PATH}: {e}")
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        raise ConfigReadError(f"{CONFIG_PATH} top-level is not a mapping")
    return data, None


def _write_atomic(payload: Any, use_ruamel: bool) -> None:
    """先寫暫存檔再原子替換，避免寫入中途損毀既有設定"""
    tmp_path = CONFIG_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            if use_ruamel and _ruamel is not None:
                _ruamel.dump(payload, f)
            else:
                yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def get_language() -> str:
    """取得目前語言設定；未設定、不合法或讀取失敗時回傳預設英文（讀取永不具破壞性）"""
    with _lock:
        try:
            data, _doc = _read_existing()
        except ConfigReadError:
            return DEFAULT_LANGUAGE
    lang = data.get("language")
    if isinstance(lang, str) and lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def set_language(language: str) -> str:
    """
    更新 config.yaml 的 language 欄位並回寫；保留其他區塊（如 llm）不變。

    Returns:
        實際寫入的語言代碼

    Raises:
        ValueError: 語言代碼不在支援清單內
        ConfigReadError: 既有 config.yaml 無法解析（為保護 llm 等設定而中止，不覆寫）
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )

    with _lock:
        # 讀不到既有內容就中止（不覆寫），避免抹除使用者的 llm 設定
        data, doc = _read_existing()

        if doc is not None:
            # ruamel 往返模式：原地更新，保留註解與其他區塊
            doc["language"] = language
            _write_atomic(doc, use_ruamel=True)
        else:
            # PyYAML 模式，或原本沒有 config.yaml（此時沒有 llm 可保留）
            data = dict(data)
            data["language"] = language
            _write_atomic(data, use_ruamel=False)

    return language
