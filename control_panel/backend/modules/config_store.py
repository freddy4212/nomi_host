"""
config_store.py - 讀寫 nomi_host/config.yaml 的共用工具

目前用於前端語言選項的持久化：
- 語言選項存於 config.yaml 的頂層 `language` 欄位
- 若 config.yaml 不存在或未設定 language，預設為英文 ("en")
- 寫入時保留其他區塊（例如 llm.api_key），只更新 language
"""

import os
import threading
from typing import Any, Dict

import yaml

# 支援的語言代碼；預設英文
SUPPORTED_LANGUAGES = ("en", "zh", "ja")
DEFAULT_LANGUAGE = "en"

# config.yaml 位於 nomi_host 專案根目錄（本檔在 control_panel/backend/modules/ 下，往上 4 層）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_NOMI_HOST_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_DIR)))
CONFIG_PATH = os.path.join(_NOMI_HOST_DIR, "config.yaml")

# 讀寫 config.yaml 時序列化，避免多執行緒同時讀寫造成檔案損毀
_lock = threading.Lock()


def _load_raw() -> Dict[str, Any]:
    """讀取整份 config.yaml；檔案不存在或格式錯誤時回傳空 dict"""
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[ConfigStore] Failed to read {CONFIG_PATH}: {e}")
        return {}


def get_language() -> str:
    """取得目前語言設定；未設定或不合法時回傳預設英文"""
    with _lock:
        data = _load_raw()
    lang = data.get("language")
    if isinstance(lang, str) and lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def set_language(language: str) -> str:
    """
    更新 config.yaml 的 language 欄位並回寫；保留其他區塊不變。

    Returns:
        實際寫入的語言代碼

    Raises:
        ValueError: 語言代碼不在支援清單內
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )

    with _lock:
        data = _load_raw()
        data["language"] = language
        tmp_path = CONFIG_PATH + ".tmp"
        try:
            # 先寫暫存檔再原子替換，避免寫入中途損毀既有設定
            with open(tmp_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
            os.replace(tmp_path, CONFIG_PATH)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    return language
