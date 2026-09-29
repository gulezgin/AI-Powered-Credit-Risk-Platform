import { useMemo } from "react";
import { useI18n } from "../i18n";

export const RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;

/* Printed-ink RAG: the banding a bank's own risk report uses, kept muted so a
   full table of it stays readable. */
export const BAND_HEX: Record<string, string> = {
  LOW: "#2e6f63",
  MEDIUM: "#9c7420",
  HIGH: "#b3561f",
  CRITICAL: "#8c2a22",
};

export const INK = "#12262b";
export const INK_3 = "#74878b";
export const RULE = "#c3ccc7";
export const SIGNAL = "#b3382c";

export function useFormat() {
  const { localeTag } = useI18n();

  return useMemo(() => {
    const int = new Intl.NumberFormat(localeTag, { maximumFractionDigits: 0 });
    const dec = (digits: number) =>
      new Intl.NumberFormat(localeTag, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });

    /* Percent goes through Intl rather than a trailing "%" so the symbol lands
       where the locale puts it — Turkish writes %7,05, English 7.05%. */
    const pct = (digits: number) =>
      new Intl.NumberFormat(localeTag, {
        style: "percent",
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });

    const fmtInt = (n: number) => int.format(n);
    const fmtDec = (n: number, digits = 3) => dec(digits).format(n);
    const fmtPct = (n: number, digits = 2) => pct(digits).format(n);
    const fmtMoney = (n: number, currency = "TL") => `${int.format(n)} ${currency}`;
    const fmtCompact = (n: number, currency = "TL") => {
      const abs = Math.abs(n);
      if (abs >= 1_000_000_000) return `${dec(1).format(n / 1_000_000_000)}B ${currency}`;
      if (abs >= 1_000_000) return `${dec(1).format(n / 1_000_000)}M ${currency}`;
      if (abs >= 1_000) return `${dec(1).format(n / 1_000)}K ${currency}`;
      return `${int.format(n)} ${currency}`;
    };
    const fmtDateTime = (iso: string) =>
      new Intl.DateTimeFormat(localeTag, { dateStyle: "medium", timeStyle: "short" }).format(
        new Date(iso),
      );

    return { fmtInt, fmtDec, fmtPct, fmtMoney, fmtCompact, fmtDateTime };
  }, [localeTag]);
}
