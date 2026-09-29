import PageHeader from "../components/PageHeader";
import { ErrorState, LoadingState } from "../components/StateViews";
import { BandMeasure, Cell, DataTable, Note, Panel, Readout, Row } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { getRealFairness, getRealMetrics, getRealProvenance, getRealSummary } from "../api/client";
import type { ModelMetricEntry } from "../api/types";
import { useI18n } from "../i18n";
import { BAND_HEX, RISK_ORDER, useFormat } from "../lib/format";

const CURRENCY = "NT$";

export default function RealDataset() {
  const { t } = useI18n();
  const { fmtInt, fmtDec, fmtPct, fmtCompact } = useFormat();

  const provenance = useFetch(getRealProvenance, []);
  const summary = useFetch(getRealSummary, []);
  const metrics = useFetch(getRealMetrics, []);
  const fairness = useFetch(getRealFairness, []);

  if (provenance.loading || summary.loading || metrics.loading) return <LoadingState />;
  if (provenance.error || summary.error || metrics.error)
    return <ErrorState message={t("realBook.notReady")} />;

  const p = provenance.data!;
  const s = summary.data!;
  const real = metrics.data!.real;
  const synthetic = metrics.data!.synthetic;

  const champ = (m: { champion_model: string; comparison: Record<string, ModelMetricEntry> } | undefined) =>
    m ? (m.comparison[`${m.champion_model}_calibrated`] ?? m.comparison[m.champion_model]) : undefined;
  const realChamp = champ(real);
  const synthChamp = champ(synthetic);

  const bands = RISK_ORDER.map((k) => ({
    key: k,
    label: t(`risk.${k}`),
    value: s.risk_level_distribution[k] ?? 0,
    color: BAND_HEX[k],
  }));

  const comparison: [string, string, string][] = [
    [t("realBook.champion"), synthetic?.champion_model ?? "—", real.champion_model],
    ["ROC-AUC", synthChamp ? fmtDec(synthChamp.roc_auc) : "—", realChamp ? fmtDec(realChamp.roc_auc) : "—"],
    ["Gini", synthChamp ? fmtDec(synthChamp.gini) : "—", realChamp ? fmtDec(realChamp.gini) : "—"],
    ["KS", synthChamp ? fmtDec(synthChamp.ks_statistic) : "—", realChamp ? fmtDec(realChamp.ks_statistic) : "—"],
    ["Brier", synthChamp ? fmtDec(synthChamp.brier_score) : "—", realChamp ? fmtDec(realChamp.brier_score) : "—"],
    [
      t("realBook.baseRate"),
      synthetic?.base_default_rate != null ? fmtPct(synthetic.base_default_rate) : "—",
      fmtPct(real.base_default_rate),
    ],
  ];

  return (
    <>
      <PageHeader
        title={t("realBook.title")}
        lede={t("realBook.lede")}
        aside={
          <div className="text-right">
            <div className="fig text-2xl font-medium text-ink">{fmtInt(p.n_customers)}</div>
            <div className="t-small text-ink-3">{t("common.accounts")}</div>
          </div>
        }
      />

      <Panel title={p.name} note={p.origin}>
        <dl className="grid gap-x-10 sm:grid-cols-2">
          {[
            [
              t("realBook.source"),
              <a key="src" href={p.url} target="_blank" rel="noreferrer" className="underline decoration-rule underline-offset-4 hover:decoration-ink">
                {p.source}
              </a>,
            ],
            [t("realBook.accounts"), <span key="n" className="fig">{fmtInt(p.n_customers)}</span>],
            [t("realBook.history"), t("realBook.historyValue", { n: p.history_months })],
            [t("realBook.target"), p.target],
          ].map(([label, value], i) => (
            <div
              key={i}
              className="flex items-baseline justify-between gap-6 border-b border-rule-soft py-2.5"
            >
              <dt className="t-small text-ink-2">{label}</dt>
              <dd className="t-small text-right font-medium text-ink">{value}</dd>
            </div>
          ))}
        </dl>
        <p className="t-micro mt-4 text-ink-3">{p.citation}</p>

        <div className="mt-5">
          <Note tone="caution">
            <span className="font-medium">
              {t("realBook.excluded")}:{" "}
              {p.excluded_from_model.map((a) => t(`realBook.attributes.${a}`)).join(", ")}.
            </span>{" "}
            {t("realBook.excludedNote")}
          </Note>
        </div>
      </Panel>

      <div className="mt-6 grid gap-px border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-5">
        <div className="bg-paper px-5 py-5">
          <Readout label={t("realBook.scored")} value={fmtInt(s.total_customers)} scale="inline" />
        </div>
        <div className="bg-paper px-5 py-5">
          <Readout label={t("realBook.actualRate")} value={fmtPct(s.actual_default_rate)} scale="inline" />
        </div>
        <div className="bg-paper px-5 py-5">
          <Readout
            label={t("realBook.modelPd")}
            value={fmtPct(s.avg_probability_of_default)}
            sub={t("realBook.modelPdNote")}
            scale="inline"
          />
        </div>
        <div className="bg-paper px-5 py-5">
          <Readout
            label={t("realBook.expectedLoss")}
            value={fmtCompact(s.expected_loss.total_expected_loss, CURRENCY)}
            scale="inline"
          />
        </div>
        <div className="bg-paper px-5 py-5">
          <Readout
            label={t("realBook.escalations")}
            value={fmtInt(s.alert_count)}
            tone="signal"
            scale="inline"
          />
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel title={t("realBook.comparisonTitle")} note={t("realBook.comparisonNote")}>
          <DataTable
            minWidth="min-w-[420px]"
            columns={[
              { key: "metric", label: t("common.metric") },
              { key: "syn", label: t("realBook.synthetic"), numeric: true },
              { key: "real", label: t("realBook.real"), numeric: true },
            ]}
          >
            {comparison.map(([label, a, b]) => (
              <Row key={label}>
                <Cell strong>{label}</Cell>
                <Cell numeric className="text-ink-3">
                  {a}
                </Cell>
                <Cell numeric className="font-medium text-ink">
                  {b}
                </Cell>
              </Row>
            ))}
          </DataTable>
          <div className="mt-5">
            <Note>{t("realBook.comparisonRead")}</Note>
          </div>
        </Panel>

        <Panel
          title={t("realBook.distributionTitle")}
          note={`${t("realBook.decisions")}: ${Object.entries(s.decision_distribution)
            .map(([k, v]) => `${t(`decision.${k}`)} ${fmtInt(v)}`)
            .join(", ")}`}
        >
          <BandMeasure bands={bands} formatValue={fmtInt} formatShare={(f) => fmtPct(f, 1)} />
          <p className="t-small mt-6 text-ink-2">
            {t("realBook.exposureNote", {
              ratio: fmtPct(s.expected_loss.expected_loss_ratio),
              exposure: fmtCompact(s.expected_loss.total_exposure, CURRENCY),
              lgd: fmtPct(s.expected_loss.lgd_assumption, 0),
            })}
          </p>
        </Panel>
      </div>

      <div className="mt-6">
        <Panel title={t("realBook.fairTitle")} note={t("realBook.fairNote")}>
          {fairness.loading && <LoadingState />}
          {fairness.data &&
            Object.entries(fairness.data).map(([attribute, rows]) => (
              <div key={attribute} className="mb-8 last:mb-0">
                <h3 className="t-h3 mb-3 text-ink">{t(`realBook.attributes.${attribute}`)}</h3>
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
                  {rows.map((r) => (
                    <Row key={String(r[attribute])}>
                      <Cell strong>{String(r[attribute])}</Cell>
                      <Cell numeric>{fmtInt(r.n)}</Cell>
                      <Cell numeric>{fmtPct(r.avg_pd)}</Cell>
                      <Cell numeric>{fmtPct(r.approval_rate)}</Cell>
                      <Cell numeric>{fmtDec(r.adverse_impact_ratio)}</Cell>
                      <Cell numeric>
                        {r.flagged ? (
                          <span className="font-medium text-signal">{t("common.flagged")}</span>
                        ) : r.insufficient_sample ? (
                          <span className="text-ink-4">{t("common.sampleTooSmall")}</span>
                        ) : (
                          <span className="text-band-low">{t("common.pass")}</span>
                        )}
                      </Cell>
                    </Row>
                  ))}
                </DataTable>
              </div>
            ))}
          <div className="mt-6">
            <Note>{t("realBook.fourFifths")}</Note>
          </div>
        </Panel>
      </div>
    </>
  );
}
