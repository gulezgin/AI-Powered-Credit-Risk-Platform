import { useState } from "react";
import PageHeader from "../components/PageHeader";
import { ErrorState, LoadingState } from "../components/StateViews";
import {
  BandMeasure,
  Button,
  Cell,
  DataTable,
  Field,
  Panel,
  Readout,
  Row,
  Select,
  Slider,
} from "../components/ui";
import { postStressTest } from "../api/client";
import type { StressTestResponse } from "../api/types";
import { useI18n } from "../i18n";
import { BAND_HEX, RISK_ORDER, useFormat } from "../lib/format";

export default function StressTestLab() {
  const { t } = useI18n();
  const { fmtInt, fmtMoney, fmtPct, fmtCompact, fmtDec } = useFormat();

  const [unemployment, setUnemployment] = useState(3);
  const [rate, setRate] = useState(2);
  const [sample, setSample] = useState(5000);
  const [result, setResult] = useState<StressTestResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setRunning(true);
    setError(null);
    try {
      setResult(
        await postStressTest({
          unemployment_shock_pp: unemployment,
          rate_shock_pp: rate,
          sample_size: sample,
        }),
      );
    } catch (e: any) {
      setError(e?.response?.data?.detail ? JSON.stringify(e.response.data.detail) : e.message);
    } finally {
      setRunning(false);
    }
  }

  const toBands = (dist: Record<string, number>) =>
    RISK_ORDER.map((k) => ({
      key: k,
      label: t(`risk.${k}`),
      value: dist[k] ?? 0,
      color: BAND_HEX[k],
    }));

  const lossDelta = result
    ? result.stressed_expected_loss.total_expected_loss -
      result.baseline_expected_loss.total_expected_loss
    : 0;

  return (
    <>
      <PageHeader title={t("scenario.title")} lede={t("scenario.lede")} />

      <Panel title={t("scenario.how")}>
        <ol className="mb-7 space-y-2 border-l border-rule pl-4">
          {["how1", "how2", "how3", "how4"].map((k) => (
            <li key={k} className="t-small max-w-[78ch] text-ink-2">
              {t(`scenario.${k}`)}
            </li>
          ))}
        </ol>

        <div className="grid gap-6 md:grid-cols-3">
          <Field label={`${t("scenario.unemployment")} — +${fmtDec(unemployment, 1)} pp`}>
            <Slider
              min={0}
              max={8}
              step={0.5}
              value={unemployment}
              onChange={(e) => setUnemployment(Number(e.target.value))}
            />
          </Field>
          <Field label={`${t("scenario.rate")} — +${fmtDec(rate, 1)} pp`}>
            <Slider
              min={0}
              max={8}
              step={0.5}
              value={rate}
              onChange={(e) => setRate(Number(e.target.value))}
            />
          </Field>
          <Field label={t("scenario.sample")}>
            <Select value={sample} onChange={(e) => setSample(Number(e.target.value))}>
              {[1000, 3000, 5000, 10000, 20000].map((n) => (
                <option key={n} value={n}>
                  {fmtInt(n)}
                </option>
              ))}
            </Select>
          </Field>
        </div>

        <div className="mt-7">
          <Button onClick={run} disabled={running}>
            {running ? t("scenario.running") : t("scenario.run")}
          </Button>
        </div>
      </Panel>

      {running && <LoadingState label={t("scenario.running")} />}
      {error && (
        <div className="mt-6">
          <ErrorState message={error} />
        </div>
      )}

      {result && !running && (
        <>
          {/* The same measure twice: the mass visibly moves right under stress. */}
          <div className="mt-8">
            <Panel padded={false}>
              <div className="graph-field space-y-8 p-6 sm:p-8">
                <div>
                  <div className="t-small mb-3 text-ink-2">{t("scenario.baseline")}</div>
                  <BandMeasure bands={toBands(result.baseline_risk_distribution)} formatValue={fmtInt} formatShare={(f) => fmtPct(f, 1)} />
                </div>
                <div>
                  <div className="t-small mb-3 font-medium text-signal">{t("scenario.stressed")}</div>
                  <BandMeasure bands={toBands(result.stressed_risk_distribution)} formatValue={fmtInt} formatShare={(f) => fmtPct(f, 1)} />
                </div>
              </div>
              <div className="grid gap-px border-t border-rule bg-rule sm:grid-cols-3">
                <div className="bg-paper px-6 py-5">
                  <Readout label={t("scenario.baselinePd")} value={fmtPct(result.baseline_avg_pd)} />
                </div>
                <div className="bg-paper px-6 py-5">
                  <Readout
                    label={t("scenario.stressedPd")}
                    value={fmtPct(result.stressed_avg_pd)}
                    sub={`+${fmtDec(result.avg_pd_delta_pp, 2)} pp`}
                    tone="signal"
                  />
                </div>
                <div className="bg-paper px-6 py-5">
                  <Readout
                    label={t("scenario.lossTitle")}
                    value={fmtMoney(result.stressed_expected_loss.total_expected_loss)}
                    sub={t("scenario.delta", { value: fmtCompact(lossDelta) })}
                    tone="signal"
                  />
                </div>
              </div>
            </Panel>
          </div>

          <div className="mt-6">
            <Panel title={t("scenario.lossByBandTitle")}>
              <DataTable
                minWidth="min-w-[460px]"
                columns={[
                  { key: "band", label: t("common.riskBand") },
                  { key: "base", label: t("scenario.baseline"), numeric: true },
                  { key: "stress", label: t("scenario.stressed"), numeric: true },
                  { key: "delta", label: "Δ", numeric: true },
                ]}
              >
                {RISK_ORDER.map((k) => {
                  const base = result.baseline_expected_loss.expected_loss_by_risk_level[k] ?? 0;
                  const stressed = result.stressed_expected_loss.expected_loss_by_risk_level[k] ?? 0;
                  const delta = stressed - base;
                  return (
                    <Row key={k}>
                      <Cell strong>
                        <span className="inline-flex items-center gap-2">
                          <span
                            aria-hidden
                            className="inline-block h-2.5 w-2.5 rounded-[1px]"
                            style={{ background: BAND_HEX[k] }}
                          />
                          {t(`risk.${k}`)}
                        </span>
                      </Cell>
                      <Cell numeric>{fmtCompact(base)}</Cell>
                      <Cell numeric>{fmtCompact(stressed)}</Cell>
                      <Cell numeric className={delta > 0 ? "text-signal" : "text-band-low"}>
                        {delta > 0 ? "+" : ""}
                        {fmtCompact(delta)}
                      </Cell>
                    </Row>
                  );
                })}
              </DataTable>
              <p className="t-small mt-5 text-ink-2">
                {t("scenario.ratioLine", {
                  from: fmtPct(result.baseline_expected_loss.expected_loss_ratio),
                  to: fmtPct(result.stressed_expected_loss.expected_loss_ratio),
                  n: fmtInt(result.sample_size),
                })}
              </p>
            </Panel>
          </div>
        </>
      )}
    </>
  );
}
