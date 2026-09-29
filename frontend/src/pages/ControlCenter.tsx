import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import { ErrorState, LoadingState } from "../components/StateViews";
import { BandMeasure, Cell, DataTable, Panel, Readout, Row } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { getAlerts, getPortfolioSummary } from "../api/client";
import { useI18n } from "../i18n";
import { recommendedAction } from "../i18n/modelLabels";
import { BAND_HEX, RISK_ORDER, useFormat } from "../lib/format";

export default function ControlCenter() {
  const { t, locale } = useI18n();
  const { fmtInt, fmtPct } = useFormat();
  const summary = useFetch(getPortfolioSummary, []);
  const alerts = useFetch(() => getAlerts({ resolved: false, limit: 8 }), []);

  if (summary.loading) return <LoadingState />;
  if (summary.error || !summary.data) return <ErrorState message={t("book.apiDown")} />;

  const s = summary.data;
  const bands = RISK_ORDER.map((k) => ({
    key: k,
    label: t(`risk.${k}`),
    value: s.risk_level_distribution[k] ?? 0,
    color: BAND_HEX[k],
  }));

  return (
    <>
      <PageHeader
        title={t("book.title")}
        lede={t("book.lede")}
        aside={
          <div className="text-right">
            <div className="fig text-2xl font-medium text-ink">{fmtInt(s.total_customers)}</div>
            <div className="t-small text-ink-3">{t("common.accounts")}</div>
          </div>
        }
      />

      {/* The distribution is the reading a risk analyst opens this page for, so
          it gets the width a row of summary tiles would otherwise take. */}
      <Panel padded={false}>
        <div className="graph-field p-6 sm:p-8">
          <h2 className="t-h3 mb-5 text-ink">{t("book.measureLabel")}</h2>
          <BandMeasure bands={bands} formatValue={fmtInt} formatShare={(f) => fmtPct(f, 1)} />
        </div>
        <div className="grid gap-px border-t border-rule bg-rule sm:grid-cols-2">
          <div className="bg-paper px-6 py-5">
            <Readout row label={t("book.avgPd")} value={fmtPct(s.avg_probability_of_default)} />
          </div>
          <div className="bg-paper px-6 py-5">
            <Readout row label={t("book.onWatch")} value={fmtInt(s.active_alerts)} tone="signal" />
          </div>
        </div>
      </Panel>

      <div className="mt-8">
        <Panel title={t("book.watchlistTitle")} note={t("book.watchlistNote")}>
          {alerts.loading && <LoadingState />}
          {alerts.error && <ErrorState message={alerts.error} />}
          {alerts.data?.length === 0 && <p className="t-small py-8 text-ink-3">{t("book.empty")}</p>}
          {alerts.data && alerts.data.length > 0 && (
            <DataTable
              columns={[
                { key: "id", label: t("common.account") },
                { key: "from", label: t("common.from") },
                { key: "to", label: t("common.to") },
                { key: "pd", label: t("common.pdShort"), numeric: true },
                { key: "next", label: t("common.action") },
              ]}
            >
              {alerts.data.map((a) => (
                <Row key={a.id}>
                  <Cell strong>
                    <span className="fig">{a.customer_id}</span>
                  </Cell>
                  <Cell>
                    <RiskBadge level={a.previous_risk_level} />
                  </Cell>
                  <Cell>
                    <RiskBadge level={a.current_risk_level} />
                  </Cell>
                  <Cell numeric>{fmtPct(a.current_pd, 1)}</Cell>
                  <Cell>{recommendedAction(a.recommended_action, locale)}</Cell>
                </Row>
              ))}
            </DataTable>
          )}
        </Panel>
      </div>
    </>
  );
}
