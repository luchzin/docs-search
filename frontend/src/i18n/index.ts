import { createI18n } from "vue-i18n"
import en from "./locales/en"
import km from "./locales/km"

export type SupportedLocale = "en" | "km"

const SAVED_LOCALE_KEY = "app_locale"

function getInitialLocale(): SupportedLocale {
  const saved = localStorage.getItem(SAVED_LOCALE_KEY)
  if (saved === "en" || saved === "km") {
    return saved
  }
  return "en"
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: "en",
  messages: {
    en,
    km,
  },
})

export function setLanguage(locale: SupportedLocale) {
  i18n.global.locale.value = locale
  localStorage.setItem(SAVED_LOCALE_KEY, locale)
  document.documentElement.setAttribute("lang", locale)
}

// Set HTML lang attribute on init
if (typeof document !== "undefined") {
  document.documentElement.setAttribute("lang", getInitialLocale())
}
