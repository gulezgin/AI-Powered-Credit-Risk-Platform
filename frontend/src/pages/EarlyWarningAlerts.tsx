import { useState } from "react";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import { ErrorState, LoadingState } from "../components/StateViews";
import { Cell, DataTable, Field, Panel, Row, Select, Slider } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { getAlerts } from "../api/client";
import { useI18n } from "../i18n";
import { recommendedAction } from "../i18n/modelLabels";
import { writeSignal } from "../i18n/signals";
import { RISK_ORDER, useFormat } from "../lib/format";

export default function EarlyWarningAlerts() {
  const { t, locale } = useI18n();
  const { fmtInt, fmtPct, fmtDateTime } = useFormat();

  const [band, setBand] = useState("All");
  const [state, setState] = useState("open");
  const [limit, setLimit] = useState(100);
  const [openRow, setOpenRow] = useState<number | null>(null);

  const resolved = state === "open" ? false : state === "closed" ? true : undefined;
  const { data, loading, error } = useFetch(
    () => getAlerts({ risk_level: band === "All" ? undefined : band, resolved, limit }),
    [band, state, limit],
  );

  return (
    <>
      <PageHeader
        title={t("watchlist.title")}
        lede={t("watchlist.lede")}
        aside={
          data ? (
            <div className="text-right">
              <div className="fig text-2xl font-medium text-ink">{fmtInt(data.length)}</div>
              <div className="t-small text-ink-3">{t("watchlist.count")}</div>
            </div>
          ) : undefined
        }
      />

      <Panel>
        <div className="grid gap-6 md:grid-cols-3">
          <Field label={t("watchlist.bandFilter")}>
            <Select value={band} onChange={(e) => setBand(e.target.value)}>
              <option value="All">{t("common.all")}</option>
              {RISK_ORDER.map((r) => (
                <option key={r} value={r}>
                  {t(`risk.${r}`)}
                </option>
              ))}
            </Select>
          </Field>
          <Field label={t("watchlist.stateFilter")}>
            <Select value={state} onChange={(e) => setState(e.target.value)}>
              <option value="open">{t("watchlist.open")}</option>
              <option value="closed">{t("watchlist.closed")}</option>
              <option value="all">{t("common.all")}</option>
            </Select>
          </Field>
          <Field label={`${t("watchlist.limit")} — ${fmtInt(limit)}`}>
            <Slider
              min={10}
              max={500}
              step={10}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
          </Field>
        </div>
      </Panel>

      <div className="mt-6">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {data?.length === 0 && (
          <Panel>
            <p className="t-small py-8 text-ink-3">{t("watchlist.empty")}</p>
          </Panel>
        )}
        {data && data.length > 0 && (
          <Panel padded={false}>
            <div className="px-5 pt-5">
              <DataTable
                minWidth="min-w-[680px]"
                columns={[
                  { key: "id", label: t("common.account"), width: "12%" },
                  { key: "from", label: t("common.from"), width: "13%" },
                  { key: "to", label: t("common.to"), width: "13%" },
                  { key: "pd", label: t("common.pdShort"), numeric: true, width: "16%" },
                  { key: "next", label: t("common.action") },
                  { key: "seen", label: t("watchlist.seen"), numeric: true, width: "18%" },
                ]}
              >
                {data.map((a) => {
                  const open = openRow === a.id;
                  return [
                    <Row key={a.id}>
                      <Cell strong>
                        <button
                          onClick={() => setOpenRow(open ? null : a.id)}
                          aria-expanded={open}
                          className="fig underline decoration-rule underline-offset-4 hover:decoration-ink"
                        >
                          {a.customer_id}
                        </button>
                      </Cell>
                      <Cell>
                        <RiskBadge level={a.previous_risk_level} />
                      </Cell>
                      <Cell>
                        <RiskBadge level={a.current_risk_level} />
                      </Cell>
                      <Cell numeric>
                        {fmtPct(a.previous_pd, 1)} → {fmtPct(a.current_pd, 1)}
                      </Cell>
                      <Cell>{recommendedAction(a.recommended_action, locale)}</Cell>
                      <Cell numeric>{fmtDateTime(a.created_at)}</Cell>
                    </Row>,
                    open ? (
                      <tr key={`${a.id}-detail`} className="border-b border-rule-soft">
                        <td colSpan={6} className="bg-ground px-4 py-4">
                          <div className="t-small mb-2 font-medium text-ink">
                            {t("watchlist.signals")}
                          </div>
                          <ul className="space-y-1.5">
                            {a.signals.map((sig, i) => (
                              <li key={i} className="t-small flex gap-2.5 text-ink-2">
                                <span aria-hidden className="mt-[7px] h-1.5 w-1.5 shrink-0 bg-signal" />
                                {writeSignal(sig, locale, fmtInt)}
                              </li>
                            ))}
                          </ul>
                        </td>
                      </tr>
                    ) : null,
                  ];
                })}
              </DataTable>
            </div>
            <div className="px-5 pb-5" />
          </Panel>
        )}
      </div>
    </>
  );
}
