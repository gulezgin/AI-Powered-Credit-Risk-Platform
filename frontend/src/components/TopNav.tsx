import { NavLink } from "react-router-dom";
import { useI18n } from "../i18n";
import type { Locale } from "../i18n";

const NAV = [
  { to: "/", key: "nav.book", end: true },
  { to: "/customer", key: "nav.account" },
  { to: "/alerts", key: "nav.watchlist" },
  { to: "/monitoring", key: "nav.model" },
  { to: "/simulator", key: "nav.score" },
  { to: "/stress-test", key: "nav.scenario" },
  { to: "/real-dataset", key: "nav.realBook" },
];

const LOCALES: { code: Locale; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "tr", label: "TR" },
];

function LanguageToggle() {
  const { locale, setLocale } = useI18n();
  return (
    <div className="flex items-center divide-x divide-rule border border-rule">
      {LOCALES.map(({ code, label }) => (
        <button
          key={code}
          onClick={() => setLocale(code)}
          aria-pressed={locale === code}
          className={`px-2.5 py-1 text-[0.72rem] font-medium transition-colors ${
            locale === code ? "bg-ink text-paper" : "text-ink-3 hover:text-ink"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

/* Sections are positions along a measured rule; the active one carries a tick
   rather than a filled pill. */
export default function TopNav() {
  const { t } = useI18n();

  return (
    <header className="sticky top-0 z-30 border-b border-ink bg-ground/95 backdrop-blur-[2px]">
      <div className="mx-auto flex max-w-[1240px] items-center gap-8 px-6">
        <NavLink to="/" className="flex shrink-0 items-baseline gap-2 py-4">
          <span className="text-[1.0625rem] font-semibold tracking-[-0.03em] text-ink">
            {t("brand.name")}
          </span>
          <span className="t-micro hidden text-ink-3 sm:inline">{t("brand.tagline")}</span>
        </NavLink>

        <nav className="-mb-px flex flex-1 items-stretch gap-6 overflow-x-auto">
          {NAV.map(({ to, key, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `shrink-0 border-b-2 pt-5 pb-[18px] text-[0.84rem] font-medium transition-colors ${
                  isActive
                    ? "border-ink text-ink"
                    : "border-transparent text-ink-3 hover:text-ink-2"
                }`
              }
            >
              {t(key)}
            </NavLink>
          ))}
        </nav>

        <LanguageToggle />
      </div>
    </header>
  );
}
