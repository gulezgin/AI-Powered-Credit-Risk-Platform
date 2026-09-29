import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { en, translations } from "./translations";
import type { Locale } from "./translations";

const STORAGE_KEY = "bankai.locale";
const LOCALE_TAG: Record<Locale, string> = { en: "en-US", tr: "tr-TR" };

interface I18nValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  /** Dot-path lookup with {placeholder} interpolation; falls back to English. */
  t: (path: string, vars?: Record<string, string | number>) => string;
  localeTag: string;
}

const I18nContext = createContext<I18nValue | null>(null);

function lookup(source: unknown, path: string): string | undefined {
  const value = path.split(".").reduce<unknown>(
    (acc, key) => (acc && typeof acc === "object" ? (acc as Record<string, unknown>)[key] : undefined),
    source,
  );
  return typeof value === "string" ? value : undefined;
}

function detectInitialLocale(): Locale {
  if (typeof window === "undefined") return "en";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "tr") return stored;
  return window.navigator.language?.toLowerCase().startsWith("tr") ? "tr" : "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(detectInitialLocale);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, locale);
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((next: Locale) => setLocaleState(next), []);

  const t = useCallback(
    (path: string, vars?: Record<string, string | number>) => {
      const raw = lookup(translations[locale], path) ?? lookup(en, path) ?? path;
      if (!vars) return raw;
      return Object.entries(vars).reduce(
        (acc, [key, value]) => acc.replaceAll(`{${key}}`, String(value)),
        raw,
      );
    },
    [locale],
  );

  const value = useMemo<I18nValue>(
    () => ({ locale, setLocale, t, localeTag: LOCALE_TAG[locale] }),
    [locale, setLocale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside <I18nProvider>");
  return ctx;
}

export type { Locale };
