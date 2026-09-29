import { useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import DecisionBadge from "../components/DecisionBadge";
import ShapDriverChart from "../components/ShapDriverChart";
import { ErrorState, LoadingState } from "../components/StateViews";
import { Button, Panel, Readout, TextInput } from "../components/ui";
import { getCustomer, getCustomerHistory, postCreditDecision } from "../api/client";
import type { CreditDecisionResult, Customer, RiskHistoryPoint } from "../api/types";
import { useI18n } from "../i18n";
import { adverseActionGround } from "../i18n/modelLabels";
import { INK_3, RULE, SIGNAL, useFormat } from "../lib/format";

export default function Customer360() {
  const { t, locale } = useI18n();
  const { fmtInt, fmtMoney, fmtPct } = useFormat();

  const [accountId, setAccountId] = useState("10001");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [decision, setDecision] = useState<CreditDecisionResult | null>(null);
  const [history, setHistory] = useState<RiskHistoryPoint[] | null>(null);

  async function openAccount() {
    const id = Number(accountId);
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const c = await getCustomer(id);
      const [h, d] = await Promise.all([getCustomerHistory(id), postCreditDecision(id, c.total_debt)]);
      setCustomer(c);
      setHistory(h);
      setDecision(d);
    } catch (e: any) {
      setError(e?.response?.status === 404 ? t("account.notFound") : (e?.message ?? t("account.notFound")));
      setCustomer(null);
    } finally {
      setLoading(false);
    }
  }

  const standing =
    customer && decision
      ? [
          [t("account.occupation"), customer.occupation, false],
          [t("account.age"), String(customer.age), true],
          [t("account.income"), fmtMoney(customer.income), true],
          [t("account.debt"), fmtMoney(customer.total_debt), true],
          [t("account.utilization"), fmtPct(customer.credit_utilization, 0), true],
          [t("account.balance"), fmtMoney(customer.account_balance), true],
          [t("account.employment"), `${customer.employment_years} ${t("common.years")}`, true],
          ...(decision.suggested_interest_rate != null
            ? [[t("account.rate"), fmtPct(decision.suggested_interest_rate), true] as const]
            : []),
          [t("account.approved"), fmtMoney(decision.approved_amount ?? 0), true],
        ]
      : [];

  return (
    <>
      <PageHeader title={t("account.title")} lede={t("account.lede")} />

      <Panel>
        <div className="flex flex-wrap items-end gap-4">
          <label className="block">
            <span className="t-small block text-ink-2">{t("account.idLabel")}</span>
            <TextInput
              type="number"
              className="mt-1.5 w-48"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && openAccount()}
              placeholder="18472"
            />
          </label>
          <Button onClick={openAccount} disabled={loading}>
            {loading ? t("common.loading") : t("account.open")}
          </Button>
        </div>
      </Panel>

      {error && (
        <div className="mt-6">
          <ErrorState message={error} />
        </div>
      )}
      {loading && !customer && <LoadingState label={t("account.reading")} />}

      {customer && decision && (
        <>
          {/* The decision record: score, estimate, band and verdict on one line,
              the way a credit memo states them. */}
          <div className="mt-8 grid gap-px border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-paper px-6 py-6">
              <Readout label={t("common.score")} value={fmtInt(decision.risk_score)} scale="hero" />
            </div>
            <div className="bg-paper px-6 py-6">
              <Readout
                label={t("common.pd")}
                value={fmtPct(decision.probability_of_default, 1)}
                scale="panel"
              />
            </div>
            <div className="flex flex-col justify-center bg-paper px-6 py-6">
              <div className="t-small text-ink-2">{t("common.riskBand")}</div>
              <div className="mt-2">
                <RiskBadge level={decision.risk_level} />
              </div>
            </div>
            <div className="flex flex-col justify-center bg-paper px-6 py-6">
              <div className="t-small text-ink-2">{t("common.decision")}</div>
              <div className="mt-2">
                <DecisionBadge decision={decision.decision} />
              </div>
            </div>
          </div>

          {decision.reason_codes.length > 0 && (
            <div className="mt-6">
              <Panel title={t("account.reasonsTitle")} note={t("account.reasonsNote")}>
                <ol className="space-y-2">
                  {decision.reason_codes.map((r, i) => (
                    <li key={r} className="t-body flex gap-3 text-ink">
                      <span className="fig t-small pt-1 text-signal">{i + 1}</span>
                      {adverseActionGround(r, locale)}
                    </li>
                  ))}
                </ol>
              </Panel>
            </div>
          )}

          <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
            <Panel title={t("account.profile")}>
              <dl>
                {standing.map(([label, value, numeric]) => (
                  <div
                    key={String(label)}
                    className="flex items-baseline justify-between gap-6 border-b border-rule-soft py-2.5 last:border-0"
                  >
                    <dt className="t-small text-ink-2">{label}</dt>
                    <dd className={`t-small font-medium text-ink ${numeric ? "fig" : ""}`}>{value}</dd>
                  </div>
                ))}
              </dl>
            </Panel>

            <Panel title={t("account.driversTitle")} note={t("account.driversNote")}>
              <ShapDriverChart drivers={decision.key_risk_drivers} />
            </Panel>
          </div>

          {history && (
            <div className="mt-6">
              <Panel title={t("account.trendTitle")} note={t("account.trendNote")}>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={history} margin={{ top: 8, left: 0, right: 8, bottom: 0 }}>
                    <XAxis
                      dataKey="month_index"
                      stroke={RULE}
                      tick={{ fontSize: 12, fill: INK_3, fontFamily: "IBM Plex Mono" }}
                      tickLine={{ stroke: RULE }}
                    />
                    <YAxis
                      yAxisId="left"
                      stroke={RULE}
                      tick={{ fontSize: 12, fill: INK_3, fontFamily: "IBM Plex Mono" }}
                      tickLine={{ stroke: RULE }}
                      tickFormatter={(v) => fmtPct(v, 0)}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      stroke={RULE}
                      tick={{ fontSize: 12, fill: INK_3, fontFamily: "IBM Plex Mono" }}
                      tickLine={{ stroke: RULE }}
                      tickFormatter={(v) => fmtInt(v)}
                    />
                    <Tooltip
                      cursor={{ stroke: RULE }}
                      formatter={(v, name) =>
                        name === t("account.utilizationSeries")
                          ? [fmtPct(Number(v), 1), String(name)]
                          : [fmtMoney(Number(v)), String(name)]
                      }
                      labelFormatter={(m) => `${t("account.month")} ${m}`}
                      contentStyle={{
                        borderRadius: 2,
                        border: "1px solid #12262b",
                        background: "#f4f6f3",
                        fontSize: 13,
                      }}
                    />
                    <Line
                      yAxisId="left"
                      type="linear"
                      dataKey="credit_utilization"
                      name={t("account.utilizationSeries")}
                      stroke={SIGNAL}
                      strokeWidth={1.75}
                      dot={false}
                    />
                    <Line
                      yAxisId="right"
                      type="linear"
                      dataKey="account_balance"
                      name={t("account.balanceSeries")}
                      stroke="#12262b"
                      strokeWidth={1.75}
                      strokeDasharray="3 3"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <div className="mt-3 flex gap-6">
                  <span className="t-small flex items-center gap-2 text-ink-2">
                    <span className="inline-block h-0.5 w-6" style={{ background: SIGNAL }} />
                    {t("account.utilizationSeries")}
                  </span>
                  <span className="t-small flex items-center gap-2 text-ink-2">
                    <span
                      className="inline-block h-0.5 w-6"
                      style={{ backgroundImage: "repeating-linear-gradient(to right,#12262b 0 3px,transparent 3px 6px)" }}
                    />
                    {t("account.balanceSeries")}
                  </span>
                </div>
              </Panel>
            </div>
          )}
        </>
      )}
    </>
  );
}
