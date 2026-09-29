import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageHeader from "../components/PageHeader";
import { ErrorState, LoadingState } from "../components/StateViews";
import {
  BandMeasure,
  Cell,
  DataTable,
  MiniMeasure,
  Note,
  Panel,
  Readout,
  Row,
} from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { getExpectedLoss, getFairness, getModelMetrics, getModelMonitoring } from "../api/client";
import { useI18n } from "../i18n";
import { BAND_HEX, INK_3, RULE, RISK_ORDER, SIGNAL, useFormat } from "../lib/format";

const DRIFT_COLOR = { LOW: BAND_HEX.LOW, MEDIUM: BAND_HEX.MEDIUM, HIGH: BAND_HEX.CRITICAL };

export default function ModelMonitoring() {
  const { t } = useI18n();
  const { fmtInt, fmtDec, fmtPct, fmtCompact, fmtDateTime } = useFormat();

  const metrics = useFetch(getModelMetrics, []);
  const monitoring = useFetch(getModelMonitoring, []);
  const expectedLoss = useFetch(getExpectedLoss, []);
  const fairness = useFetch(getFairness, []);

  if (metrics.loading || monitoring.loading || expectedLoss.loading) return <LoadingState />;
  if (metrics.error || !metrics.data) return <ErrorState message={metrics.error ?? "no reading"} />;
  if (monitoring.error || !monitoring.data) return <ErrorState message={monitoring.error ?? "no reading"} />;
  if (expectedLoss.error || !expectedLoss.data) return <ErrorState message={expectedLoss.error ?? "no reading"} />;

  const m = metrics.data;
  const mon = monitoring.data;
  const el = expectedLoss.data;
  const champ = m.comparison[`${m.champion_model}_calibrated`] ?? m.comparison[m.champion_model];

  const candidates = Object.entries(m.comparison).sort((a, b) => b[1].roc_auc - a[1].roc_auc);
  const calibration = champ.calibration_curve.mean_predicted.map((x, i) => ({
    stated: x,
    actual: champ.calibration_curve.fraction_positive[i],
  }));
  const bands = RISK_ORDER.map((k) => ({
    key: k,
    label: t(`risk.${k}`),
    value: mon.risk_level_distribution[k] ?? 0,
    color: BAND_HEX[k],
  }));
  const drift = Object.entries(mon.feature_drift).sort((a, b) => b[1].psi - a[1].psi);
  const maxPsi = Math.max(...drift.map(([, v]) => v.psi), 0.3);

  return (
    <>
      <PageHeader
        title={t("model.title")}
        lede={t("model.lede")}
        aside={
          <div className="text-right">
            <div className="t-small text-ink-3">{t("model.champion")}</div>
            <div className="fig mt-1 text-sm font-medium text-ink">{m.champion_model}</div>
            <div className="t-micro mt-1 text-ink-4">
              {m.model_version} · {t("model.trained")} {m.trained_at ? fmtDateTime(m.trained_at) : "—"}
            </div>
          </div>
        }
      />

      <div className="grid gap-px border border-rule bg-rule sm:grid-cols-3 lg:grid-cols-6">
        {[
          ["ROC-AUC", fmtDec(champ.roc_auc)],
          ["Gini", fmtDec(champ.gini)],
          ["KS", fmtDec(champ.ks_statistic)],
          ["Brier", fmtDec(champ.brier_score)],
          [t("model.psi"), fmtDec(mon.population_psi)],
        ].map(([label, value]) => (
          <div key={label} className="bg-paper px-5 py-5">
            <Readout label={label} value={value} scale="inline" />
          </div>
        ))}
        <div className="bg-paper px-5 py-5">
          <Readout
            label={t("model.expectedLoss")}
            value={fmtCompact(el.total_expected_loss)}
            sub={t("model.expectedLossNote", {
              ratio: fmtPct(el.expected_loss_ratio),
              lgd: fmtPct(el.lgd_assumption, 0),
            })}
            scale="inline"
          />
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Panel title={t("model.comparisonTitle")} note={t("model.comparisonNote")}>
          <DataTable
            minWidth="min-w-[480px]"
            columns={[
              { key: "model", label: t("common.model") },
              { key: "auc", label: "ROC-AUC", numeric: true },
              { key: "pr", label: "PR-AUC", numeric: true },
              { key: "gini", label: "Gini", numeric: true },
              { key: "ks", label: "KS", numeric: true },
              { key: "brier", label: "Brier", numeric: true },
            ]}
          >
            {candidates.map(([name, v]) => (
              <Row key={name}>
                <Cell strong className="fig">
                  {name}
                </Cell>
                <Cell numeric>{fmtDec(v.roc_auc)}</Cell>
                <Cell numeric>{fmtDec(v.pr_auc)}</Cell>
                <Cell numeric>{fmtDec(v.gini)}</Cell>
                <Cell numeric>{fmtDec(v.ks_statistic)}</Cell>
                <Cell numeric>{fmtDec(v.brier_score)}</Cell>
              </Row>
            ))}
          </DataTable>

          <h3 className="t-h3 mt-8 text-ink">{t("model.calibrationTitle")}</h3>
          <p className="t-small mt-1 mb-4 text-ink-2">{t("model.calibrationNote")}</p>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={calibration} margin={{ top: 8, left: 0, right: 12, bottom: 0 }}>
              <XAxis
                dataKey="stated"
                type="number"
                domain={[0, 1]}
                stroke={RULE}
                tick={{ fontSize: 12, fill: INK_3, fontFamily: "IBM Plex Mono" }}
                tickFormatter={(v) => fmtDec(v, 1)}
              />
              <YAxis
                type="number"
                domain={[0, 1]}
                stroke={RULE}
                tick={{ fontSize: 12, fill: INK_3, fontFamily: "IBM Plex Mono" }}
                tickFormatter={(v) => fmtDec(v, 1)}
              />
              <ReferenceLine
                segment={[
                  { x: 0, y: 0 },
                  { x: 1, y: 1 },
                ]}
                stroke={INK_3}
                strokeDasharray="3 3"
              />
              <Tooltip
                cursor={{ stroke: RULE }}
                formatter={(v) => fmtDec(Number(v), 3)}
                contentStyle={{
                  borderRadius: 2,
                  border: "1px solid #12262b",
                  background: "#f4f6f3",
                  fontSize: 13,
                }}
              />
              <Line
                type="linear"
                dataKey="actual"
                name={t("model.observed")}
                stroke={SIGNAL}
                strokeWidth={1.75}
                dot={{ r: 2.5, fill: SIGNAL, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Panel>

        <div className="space-y-6">
          <Panel title={t("model.distributionTitle")}>
            <BandMeasure bands={bands} formatValue={fmtInt} formatShare={(f) => fmtPct(f, 1)} height="h-9" />
          </Panel>

          <Panel title={t("model.driftTitle")} note={t("model.driftNote")}>
            <ul className="max-h-[22rem] space-y-2.5 overflow-y-auto pr-1">
              {drift.map(([feature, v]) => (
                <li key={feature}>
                  <div className="flex items-baseline justify-between gap-4">
                    <span className="t-small text-ink-2">{feature}</span>
                    <span className="fig t-small" style={{ color: DRIFT_COLOR[v.severity] }}>
                      {fmtDec(v.psi)}
                    </span>
                  </div>
                  <div className="mt-1">
                    <MiniMeasure value={v.psi} max={maxPsi} color={DRIFT_COLOR[v.severity]} />
                  </div>
                </li>
              ))}
            </ul>
            <p className="t-micro mt-4 text-ink-3">{t("model.driftLegend")}</p>
          </Panel>
        </div>
      </div>

      <div className="mt-6">
        <Panel title={t("model.fairTitle")} note={t("model.fairNote")}>
          {fairness.loading && <LoadingState />}
          {fairness.data && (
            <>
              <DataTable
                columns={[
                  { key: "group", label: t("common.group") },
                  { key: "n", label: "n", numeric: true },
                  { key: "pd", label: t("model.avgPd"), numeric: true },
                  { key: "rate", label: t("model.approvalRate"), numeric: true },
                  { key: "ratio", label: t("model.ratio"), numeric: true },
                  { key: "status", label: t("common.status"), numeric: true },
                ]}
              >
                {fairness.data.map((r) => (
                  <Row key={r.occupation}>
                    <Cell strong>{r.occupation}</Cell>
                    <Cell numeric>{fmtInt(r.n)}</Cell>
                    <Cell numeric>{fmtPct(r.avg_pd)}</Cell>
                    <Cell numeric>{fmtPct(r.approval_rate)}</Cell>
                    <Cell numeric>{fmtDec(r.adverse_impact_ratio)}</Cell>
                    <Cell numeric>
                      <span className={r.flagged ? "font-medium text-signal" : "text-band-low"}>
                        {r.flagged ? t("common.flagged") : t("common.pass")}
                      </span>
                    </Cell>
                  </Row>
                ))}
              </DataTable>
              <div className="mt-5">
                {fairness.data.some((r) => r.flagged) ? (
                  <Note tone="caution">{t("model.someFlagged")}</Note>
                ) : (
                  <Note tone="verify">{t("model.allClear")}</Note>
                )}
              </div>
            </>
          )}
        </Panel>
      </div>
    </>
  );
}
