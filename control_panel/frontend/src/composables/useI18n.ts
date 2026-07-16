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

// 避免初始從後端載入語言時又立刻寫回後端造成無謂請求
let suppressBackendSync = false

watch(currentLocale, (newLocale) => {
  if ('localStorage' in window) {
    localStorage.setItem('user-locale', newLocale)
  }
  if (!suppressBackendSync) {
    void persistLocaleToBackend(newLocale)
  }
})

// 從後端 config.yaml 讀取語言（開機時呼叫一次，config.yaml 為單一真實來源）
async function loadLocaleFromBackend(): Promise<void> {
  try {
    const res = await fetch(buildApiUrl('/api/config/language'))
    if (!res.ok) return
    const data = await res.json()
    if (isLocale(data?.language)) {
      suppressBackendSync = true
      currentLocale.value = data.language
      suppressBackendSync = false
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
