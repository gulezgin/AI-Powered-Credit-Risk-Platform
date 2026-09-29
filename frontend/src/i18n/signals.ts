import type { Signal } from "../api/types";
import type { Locale } from "./translations";

/* The API reports a detected change as a code and its numbers. The sentence is
   written here, where the reader's language is known. */

type Writer = (p: Record<string, number>, n: (v: number) => string) => string;

const EN: Record<string, Writer> = {
  utilization_up: (p, n) => `Utilisation up ${n(p.pct)} points over two months`,
  balance_down: (p, n) => `Balance down ${n(p.pct)}%`,
  new_late_payments: (p, n) =>
    p.count === 1 ? "One new missed payment" : `${n(p.count)} new missed payments`,
  withdrawals_up: (p, n) => `Cash withdrawals up ${n(p.pct)}%`,
  late_payments_90d: (p, n) =>
    p.count === 1 ? "One missed payment in the last 90 days" : `${n(p.count)} missed payments in the last 90 days`,
  delinquency_worse: (p, n) =>
    p.months === 1 ? "Arrears deepened by one month" : `Arrears deepened by ${n(p.months)} months`,
  payment_down: (p, n) => `Monthly payment down ${n(p.pct)}%`,
  no_dominant_driver: () => "Estimate rose without a single dominant driver",
};

const TR: Record<string, Writer> = {
  utilization_up: (p, n) => `Kullanım oranı iki ayda ${n(p.pct)} puan arttı`,
  balance_down: (p, n) => `Bakiye %${n(p.pct)} azaldı`,
  new_late_payments: (p, n) => `${n(p.count)} yeni geciken ödeme`,
  withdrawals_up: (p, n) => `Nakit çekim %${n(p.pct)} arttı`,
  late_payments_90d: (p, n) => `Son 90 günde ${n(p.count)} geciken ödeme`,
  delinquency_worse: (p, n) => `Gecikme ${n(p.months)} ay derinleşti`,
  payment_down: (p, n) => `Aylık ödeme %${n(p.pct)} azaldı`,
  no_dominant_driver: () => "Tek bir baskın etken olmadan tahmin yükseldi",
};

export function writeSignal(
  signal: Signal,
  locale: Locale,
  formatNumber: (v: number) => string,
): string {
  const table = locale === "tr" ? TR : EN;
  const write = table[signal.code] ?? EN[signal.code];
  return write ? write(signal.params ?? {}, formatNumber) : signal.code;
}
