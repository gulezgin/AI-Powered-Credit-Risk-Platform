import { useState } from "react";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import DecisionBadge from "../components/DecisionBadge";
import ShapDriverChart from "../components/ShapDriverChart";
import { ErrorState } from "../components/StateViews";
import { Button, Field, Note, Panel, Readout, Select, Slider, TextInput } from "../components/ui";
import { postPredictRisk } from "../api/client";
import type { DecisionResult, PredictRiskRequest } from "../api/types";
import { useI18n } from "../i18n";
import { adverseActionGround } from "../i18n/modelLabels";
import { useFormat } from "../lib/format";

const OCCUPATIONS = [
  "Engineer", "Teacher", "Civil Servant", "Business Owner", "Healthcare Worker",
  "Retail Worker", "Driver", "Accountant", "IT Specialist", "Retired",
];

const DEFAULTS: PredictRiskRequest = {
  age: 34, occupation: "Engineer", income: 85000,
  employment_years: 3, credit_history_years: 6,
  num_existing_loans: 2, num_credit_inquiries_6m: 3,
  total_debt: 310000, monthly_payment: 9800,
  credit_utilization: 0.72, num_late_payments: 2,
  account_balance: 42000, transaction_intensity: 35,
  loan_amount: 250000,
};

export default function LiveRiskSimulator() {
  const { t, locale } = useI18n();
  const { fmtInt, fmtMoney, fmtPct } = useFormat();

  const [form, setForm] = useState<PredictRiskRequest>(DEFAULTS);
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof PredictRiskRequest>(key: K, value: PredictRiskRequest[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const numberField = (key: keyof PredictRiskRequest, label: string, step?: string) => (
    <Field label={label}>
      <TextInput
        type="number"
        step={step}
        value={form[key] as number}
        onChange={(e) => set(key, Number(e.target.value) as never)}
      />
    </Field>
  );

  async function submit() {
    setWorking(true);
    setError(null);
    try {
      setResult(await postPredictRisk(form));
    } catch (e: any) {
      setError(e?.response?.data?.detail ? JSON.stringify(e.response.data.detail) : e.message);
    } finally {
      setWorking(false);
    }
  }

  const verdictLine = () => {
    if (!result) return null;
    const amount = fmtMoney(result.approved_amount ?? 0);
    const rate = result.suggested_interest_rate != null ? fmtPct(result.suggested_interest_rate) : "—";
    if (result.decision === "APPROVE")
      return <Note tone="verify">{t("score.approvedLine", { amount, rate })}</Note>;
    if (result.decision === "MANUAL_REVIEW")
      return <Note tone="caution">{t("score.reviewLine", { amount })}</Note>;
    return <Note tone="signal">{t("score.declinedLine")}</Note>;
  };

  return (
    <>
      <PageHeader title={t("score.title")} lede={t("score.lede")} />

      <Panel>
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {numberField("age", t("score.age"))}
          <Field label={t("score.occupation")}>
            <Select value={form.occupation} onChange={(e) => set("occupation", e.target.value)}>
              {OCCUPATIONS.map((o) => (
                <option key={o}>{o}</option>
              ))}
            </Select>
          </Field>
          {numberField("income", t("score.income"))}
          {numberField("employment_years", t("score.employmentYears"), "0.5")}
          {numberField("credit_history_years", t("score.historyYears"), "0.5")}
          {numberField("num_existing_loans", t("score.loans"))}
          {numberField("num_credit_inquiries_6m", t("score.inquiries"))}
          {numberField("total_debt", t("score.debt"))}
          {numberField("monthly_payment", t("score.payment"))}
          <Field label={`${t("score.utilization")} — ${fmtPct(form.credit_utilization, 0)}`}>
            <Slider
              min={0}
              max={1}
              step={0.01}
              value={form.credit_utilization}
              onChange={(e) => set("credit_utilization", Number(e.target.value))}
            />
          </Field>
          {numberField("num_late_payments", t("score.latePayments"))}
          {numberField("account_balance", t("score.balance"))}
          {numberField("transaction_intensity", t("score.activity"))}
          {numberField("loan_amount", t("score.amount"))}
        </div>

        <div className="mt-7">
          <Button onClick={submit} disabled={working}>
            {working ? t("score.working") : t("score.submit")}
          </Button>
        </div>
      </Panel>

      {error && (
        <div className="mt-6">
          <ErrorState message={error} />
        </div>
      )}

      {result && (
        <>
          <div className="mt-8 grid gap-px border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-paper px-6 py-6">
              <Readout label={t("common.score")} value={fmtInt(result.risk_score)} scale="hero" />
            </div>
            <div className="bg-paper px-6 py-6">
              <Readout
                label={t("common.pd")}
                value={fmtPct(result.probability_of_default, 1)}
                scale="panel"
              />
            </div>
            <div className="flex flex-col justify-center bg-paper px-6 py-6">
              <div className="t-small text-ink-2">{t("common.riskBand")}</div>
              <div className="mt-2">
                <RiskBadge level={result.risk_level} />
              </div>
            </div>
            <div className="flex flex-col justify-center bg-paper px-6 py-6">
              <div className="t-small text-ink-2">{t("common.decision")}</div>
              <div className="mt-2">
                <DecisionBadge decision={result.decision} />
              </div>
            </div>
          </div>

          <div className="mt-6">{verdictLine()}</div>

          {result.reason_codes.length > 0 && (
            <div className="mt-6">
              <Panel title={t("account.reasonsTitle")} note={t("account.reasonsNote")}>
                <ol className="space-y-2">
                  {result.reason_codes.map((r, i) => (
                    <li key={r} className="t-body flex gap-3 text-ink">
                      <span className="fig t-small pt-1 text-signal">{i + 1}</span>
                      {adverseActionGround(r, locale)}
                    </li>
                  ))}
                </ol>
              </Panel>
            </div>
          )}

          <div className="mt-6">
            <Panel title={t("score.driversTitle")} note={t("account.driversNote")}>
              <ShapDriverChart drivers={result.key_risk_drivers} />
            </Panel>
          </div>
        </>
      )}
    </>
  );
}
