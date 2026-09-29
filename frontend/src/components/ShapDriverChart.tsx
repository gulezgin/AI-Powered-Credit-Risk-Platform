import type { RiskDriver } from "../api/types";
import { useI18n } from "../i18n";
import { featureLabel } from "../i18n/modelLabels";

/* Contributions read as deflections either side of a zero line, the way a
   calibration trace does: right of the line raises the estimate, left lowers it. */
export default function ShapDriverChart({ drivers }: { drivers: RiskDriver[] }) {
  const { locale } = useI18n();
  const data = [...drivers].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const max = Math.max(...data.map((d) => Math.abs(d.contribution)), 0.0001);

  return (
    <ul className="space-y-3">
      {data.map((d) => {
        const raises = d.contribution > 0;
        const pct = (Math.abs(d.contribution) / max) * 50;
        return (
          <li key={d.code} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
            <div>
              <div className="t-small mb-1.5 text-ink-2">{featureLabel(d.code, locale)}</div>
              <div className="relative h-3 bg-paper-sunk">
                <div aria-hidden className="absolute inset-y-[-3px] left-1/2 w-px bg-ink" />
                <div
                  className="absolute top-0 h-full"
                  style={{
                    width: `${pct}%`,
                    left: raises ? "50%" : `${50 - pct}%`,
                    background: raises ? "var(--color-signal)" : "var(--color-band-low)",
                  }}
                />
              </div>
            </div>
            <span
              className={`fig t-small w-20 text-right ${raises ? "text-signal" : "text-band-low"}`}
            >
              {raises ? "+" : ""}
              {d.contribution.toFixed(4)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
