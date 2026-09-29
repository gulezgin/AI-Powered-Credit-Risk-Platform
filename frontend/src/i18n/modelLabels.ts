import type { Locale } from "./translations";

/* The API states model features, adverse action grounds and recommended
   actions as codes. The wording lives here, where the reader's language is
   known. An unmapped code falls through as itself rather than disappearing,
   so a new code from the API is visible instead of silent. */

type Table = Record<string, string>;

const FEATURE_EN: Table = {
  debt_to_income: "Debt to income",
  payment_to_income: "Payment to income",
  credit_utilization: "Credit utilisation",
  num_late_payments: "Missed payments",
  employment_years: "Time in employment",
  credit_history_years: "Length of credit history",
  num_existing_loans: "Open loans",
  num_credit_inquiries_6m: "Recent credit searches",
  account_balance: "Account balance",
  income: "Monthly income",
  total_debt: "Total debt",
  monthly_payment: "Monthly payment",
  transaction_intensity: "Transaction activity",
  age: "Age",
  occupation: "Occupation",
  utilization_change_30d: "Utilisation change, 30 days",
  utilization_change_60d: "Utilisation change, 60 days",
  utilization_change_90d: "Utilisation change, 90 days",
  balance_change_30d: "Balance change, 30 days",
  balance_change_90d: "Balance change, 90 days",
  withdrawal_change_30d: "Cash withdrawal change, 30 days",
  late_payments_last_90d: "Missed payments, last 90 days",
};

const FEATURE_TR: Table = {
  debt_to_income: "Borç / gelir",
  payment_to_income: "Ödeme / gelir",
  credit_utilization: "Kredi kullanım oranı",
  num_late_payments: "Geciken ödemeler",
  employment_years: "Çalışma süresi",
  credit_history_years: "Kredi geçmişi uzunluğu",
  num_existing_loans: "Açık krediler",
  num_credit_inquiries_6m: "Yakın tarihli kredi sorguları",
  account_balance: "Hesap bakiyesi",
  income: "Aylık gelir",
  total_debt: "Toplam borç",
  monthly_payment: "Aylık ödeme",
  transaction_intensity: "İşlem yoğunluğu",
  age: "Yaş",
  occupation: "Meslek",
  utilization_change_30d: "Kullanım oranı değişimi, 30 gün",
  utilization_change_60d: "Kullanım oranı değişimi, 60 gün",
  utilization_change_90d: "Kullanım oranı değişimi, 90 gün",
  balance_change_30d: "Bakiye değişimi, 30 gün",
  balance_change_90d: "Bakiye değişimi, 90 gün",
  withdrawal_change_30d: "Nakit çekim değişimi, 30 gün",
  late_payments_last_90d: "Geciken ödemeler, son 90 gün",
};

/* Adverse action grounds. The wording is what the applicant reads, so it stays
   plain and states the ground rather than blaming the applicant. */
const GROUND_EN: Table = {
  dti_too_high: "Debt is too high relative to income",
  payment_burden_too_high: "Monthly payments are too high relative to income",
  revolving_utilisation_too_high: "Too much of the available credit limit is in use",
  delinquent_obligations: "Payments missed on a current or past credit obligation",
  recent_delinquency: "A payment was missed recently",
  too_many_recent_inquiries: "Too many recent applications for credit",
  credit_history_too_short: "Credit history is too short to assess",
  employment_too_short: "Time in current employment is too short",
  too_many_obligations: "Too many open credit obligations",
  insufficient_reserves: "Account balance is low relative to obligations",
  income_insufficient_for_amount: "Income does not support the amount requested",
  amount_owed_too_high: "The total amount owed is too high",
  monthly_obligations_too_high: "Existing monthly commitments are too high",
  insufficient_account_activity: "Too little account activity to assess usage",
  utilisation_rising: "Credit use has risen sharply in recent months",
  balance_falling: "Account balance has fallen in recent months",
  cash_withdrawals_rising: "Cash withdrawals have risen unusually",
};

const GROUND_TR: Table = {
  dti_too_high: "Borç, gelire göre fazla yüksek",
  payment_burden_too_high: "Aylık ödemeler gelire göre fazla yüksek",
  revolving_utilisation_too_high: "Kullanılabilir kredi limitinin fazlası kullanımda",
  delinquent_obligations: "Mevcut veya geçmiş bir kredi borcunda ödeme aksaması var",
  recent_delinquency: "Yakın zamanda bir ödeme aksadı",
  too_many_recent_inquiries: "Yakın dönemde çok fazla kredi başvurusu var",
  credit_history_too_short: "Kredi geçmişi değerlendirme için fazla kısa",
  employment_too_short: "Mevcut işteki çalışma süresi fazla kısa",
  too_many_obligations: "Açık kredi borcu sayısı fazla",
  insufficient_reserves: "Hesap bakiyesi yükümlülüklere göre düşük",
  income_insufficient_for_amount: "Gelir, talep edilen tutarı karşılamıyor",
  amount_owed_too_high: "Toplam borç tutarı fazla yüksek",
  monthly_obligations_too_high: "Mevcut aylık yükümlülükler fazla yüksek",
  insufficient_account_activity: "Kullanımı değerlendirmek için hesap hareketi az",
  utilisation_rising: "Kredi kullanımı son aylarda hızla arttı",
  balance_falling: "Hesap bakiyesi son aylarda düştü",
  cash_withdrawals_rising: "Nakit çekimler olağandışı şekilde arttı",
};

const ACTION_EN: Table = {
  immediate_review: "Review now",
  monitor_next_cycle: "Watch next cycle",
};

const ACTION_TR: Table = {
  immediate_review: "Hemen incele",
  monitor_next_cycle: "Gelecek dönem izle",
};

const pick = (en: Table, tr: Table, code: string, locale: Locale) =>
  (locale === "tr" ? tr[code] : en[code]) ?? en[code] ?? code;

export const featureLabel = (code: string, locale: Locale) =>
  pick(FEATURE_EN, FEATURE_TR, code, locale);

export const adverseActionGround = (code: string, locale: Locale) =>
  pick(GROUND_EN, GROUND_TR, code, locale);

export const recommendedAction = (code: string, locale: Locale) =>
  pick(ACTION_EN, ACTION_TR, code, locale);
