import { ref, watch } from 'vue'
import messages from '../locales'
import { buildApiUrl } from '../utils/backend'

export type Locale = 'zh' | 'en' | 'ja'

export const SUPPORTED_LOCALES: Locale[] = ['en', 'zh', 'ja']

// 各語言的顯示名稱（用於語言選擇器）
export const LOCALE_LABELS: Record<Locale, string> = {
  en: 'English',
  zh: '繁體中文',
  ja: '日本語'
}

// config.yaml 未設定語言時的預設值（英文）
const DEFAULT_LOCALE: Locale = 'en'

function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (SUPPORTED_LOCALES as string[]).includes(value)
}

// 初始值：優先用 localStorage 快取（避免重新整理時閃爍），最終以 config.yaml 為準（見 loadLocaleFromBackend）
const cached = 'localStorage' in window ? localStorage.getItem('user-locale') : null
const currentLocale = ref<Locale>(isLocale(cached) ? cached : DEFAULT_LOCALE)

// 記錄「後端 config.yaml 目前已知的語言」。用來避免開機從後端載入語言時，
// 又把同一個值寫回後端造成無謂（且潛在具風險）的寫入。
// 用值比對而非旗標，可避免 Vue watch 為非同步（下一個 tick 才觸發）導致旗標失效的時序問題。
let knownBackendLocale: Locale | null = null

watch(currentLocale, (newLocale) => {
  if ('localStorage' in window) {
    localStorage.setItem('user-locale', newLocale)
  }
  // 與後端已知值相同代表這次變更來自「從後端載入」，不需再寫回
  if (newLocale === knownBackendLocale) return
  knownBackendLocale = newLocale
  void persistLocaleToBackend(newLocale)
})

// 從後端 config.yaml 讀取語言（開機時呼叫一次，config.yaml 為單一真實來源）
async function loadLocaleFromBackend(): Promise<void> {
  try {
    const res = await fetch(buildApiUrl('/api/config/language'))
    if (!res.ok) return
    const data = await res.json()
    if (isLocale(data?.language)) {
      // 先標記為後端已知值，稍後 watch 觸發時會因值相同而略過寫回
      knownBackendLocale = data.language
      currentLocale.value = data.language
    }
  } catch {
    // 後端未就緒時沿用 localStorage / 預設值
  }
}

// 將語言變更寫回後端 config.yaml
async function persistLocaleToBackend(locale: Locale): Promise<void> {
  try {
    await fetch(buildApiUrl('/api/config/language'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: locale })
    })
  } catch {
    // 寫回失敗不影響前端顯示，下次變更會再嘗試
  }
}

export function useI18n() {

  // 三語循環切換：en -> zh -> ja -> en
  const toggleLocale = () => {
    const idx = SUPPORTED_LOCALES.indexOf(currentLocale.value)
    currentLocale.value = SUPPORTED_LOCALES[(idx + 1) % SUPPORTED_LOCALES.length]
  }

  const setLocale = (locale: Locale) => {
    if (isLocale(locale)) {
      currentLocale.value = locale
    }
  }

  // Simple getter for nested keys e.g. 'nav.perception'
  const t = (key: string): string => {
    const keys = key.split('.')
    let result: any = messages[currentLocale.value]

    for (const k of keys) {
      if (result && typeof result === 'object' && k in result) {
        result = result[k]
      } else {
        return key // Fallback to key if not found
      }
    }

    return result as string
  }

  // Handle dynamic text received from backend
  const tDynamic = (text: string | null | undefined): string => {
    if (!text) return text || ''

    const dict = messages[currentLocale.value]?.dynamic
    if (!dict) return text

    let result = text
    // Sort keys by length so "可能坐著" is replaced before "坐著"
    const keys = Object.keys(dict).sort((a, b) => b.length - a.length)

    for (const key of keys) {
      if (result.includes(key)) {
        result = result.replace(new RegExp(key, 'g'), (dict as Record<string, string>)[key])
      }
    }

    return result
  }

  return {
    locale: currentLocale,
    supportedLocales: SUPPORTED_LOCALES,
    localeLabels: LOCALE_LABELS,
    toggleLocale,
    setLocale,
    loadLocaleFromBackend,
    t,
    tDynamic
  }
}
