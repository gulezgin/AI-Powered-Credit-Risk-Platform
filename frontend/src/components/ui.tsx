import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

/* Primitives for the "calibrated instrument" system.
   Panels are separated by rules and ground shifts rather than shadows and
   large radii; every figure goes through `.fig` so columns align. */

/* ── Surfaces ─────────────────────────────────────────────────── */

export function Panel({
  title,
  note,
  action,
  children,
  className = "",
  padded = true,
}: {
  title?: ReactNode;
  note?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <section className={`rounded-[3px] border border-rule bg-paper ${className}`}>
      {(title || action) && (
        <header className="flex items-start justify-between gap-6 border-b border-rule px-5 py-4">
          <div>
            {title && <h2 className="t-h3 text-ink">{title}</h2>}
            {note && <p className="t-small mt-1.5 max-w-[68ch] text-ink-2">{note}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div className={padded ? "p-5" : ""}>{children}</div>
    </section>
  );
}

/** A labelled figure. `scale="hero"` is reserved for one number per screen. */
export function Readout({
  label,
  value,
  sub,
  scale = "panel",
  tone = "ink",
  row = false,
}: {
  label: string;
  value: string;
  sub?: string;
  scale?: "hero" | "panel" | "inline";
  tone?: "ink" | "signal" | "verify";
  /** Label and figure on one line, so a wide cell does not read as empty. */
  row?: boolean;
}) {
  const size =
    scale === "hero" ? "t-readout" : scale === "panel" ? "fig text-3xl font-medium" : "fig text-xl";
  const color = tone === "signal" ? "text-signal" : tone === "verify" ? "text-verify" : "text-ink";

  if (row) {
    return (
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <div>
          <span className="t-small text-ink-2">{label}</span>
          {sub && <span className="t-small ml-2 text-ink-3">{sub}</span>}
        </div>
        <div className={`${size} ${color}`}>{value}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="t-small text-ink-2">{label}</div>
      <div className={`mt-1.5 ${size} ${color}`}>{value}</div>
      {sub && <div className="t-small mt-1 text-ink-3">{sub}</div>}
    </div>
  );
}

/* ── The measure: the system's signature device ───────────────── */

export interface Band {
  key: string;
  label: string;
  value: number;
  color: string;
}

/**
 * One horizontal scale carrying the whole distribution, with a tick rule
 * beneath it. This is the portfolio view a risk analyst actually reads, so it
 * gets the space a row of summary tiles would otherwise take.
 */
export function BandMeasure({
  bands,
  formatValue,
  formatShare,
  height = "h-12",
}: {
  bands: Band[];
  formatValue: (n: number) => string;
  /** Takes a fraction. Goes through the locale formatter so the percent sign
      lands where the language puts it. */
  formatShare: (fraction: number) => string;
  height?: string;
}) {
  const total = bands.reduce((sum, b) => sum + b.value, 0) || 1;

  return (
    <div>
      <div className={`flex w-full overflow-hidden rounded-[2px] border border-ink ${height}`}>
        {bands.map((b) => {
          const pct = (b.value / total) * 100;
          if (pct <= 0) return null;
          return (
            <div
              key={b.key}
              style={{ width: `${pct}%`, background: b.color }}
              title={`${b.label}: ${formatValue(b.value)}`}
            />
          );
        })}
      </div>
      <div className="tick-rule mt-0" />
      <dl className="mt-3 flex flex-wrap gap-x-8 gap-y-2">
        {bands.map((b) => (
          <div key={b.key} className="flex items-baseline gap-2">
            <span
              aria-hidden
              className="inline-block h-2.5 w-2.5 shrink-0 translate-y-[1px] rounded-[1px]"
              style={{ background: b.color }}
            />
            <dt className="t-small text-ink-2">{b.label}</dt>
            <dd className="fig t-small font-medium text-ink">{formatValue(b.value)}</dd>
            <dd className="fig t-micro text-ink-3">{formatShare(b.value / total)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/** A single value plotted on a 0–max scale — used for per-row magnitudes. */
export function MiniMeasure({
  value,
  max,
  color,
}: {
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="h-1.5 w-full bg-paper-sunk" role="presentation">
      <div className="h-full" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

/* ── Status ───────────────────────────────────────────────────── */

type BandKey = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

const BAND_CHIP: Record<BandKey, string> = {
  LOW: "bg-band-low-wash text-band-low",
  MEDIUM: "bg-band-mid-wash text-band-mid",
  HIGH: "bg-band-high-wash text-band-high",
  CRITICAL: "bg-band-crit-wash text-band-crit",
};

export function BandChip({ level, label }: { level: string; label: string }) {
  return (
    <span
      className={`inline-block rounded-[2px] px-2 py-0.5 text-[0.78rem] font-medium ${
        BAND_CHIP[level as BandKey] ?? "bg-paper-sunk text-ink-2"
      }`}
    >
      {label}
    </span>
  );
}

/** A marked event on the record — used where something needs attention. */
export function EventMark({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-signal">
      <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-signal" />
      <span className="t-small font-medium">{children}</span>
    </span>
  );
}

export function Note({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "verify" | "caution" | "signal";
  children: ReactNode;
}) {
  const tones = {
    neutral: "border-rule bg-ground text-ink-2",
    verify: "border-band-low bg-band-low-wash text-band-low",
    caution: "border-band-mid bg-band-mid-wash text-band-mid",
    signal: "border-signal bg-signal-wash text-signal",
  };
  return (
    <p className={`t-small rounded-[2px] border-l-2 px-4 py-3 leading-relaxed ${tones[tone]}`}>
      {children}
    </p>
  );
}

/* ── Controls ─────────────────────────────────────────────────── */

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: {
  variant?: "primary" | "quiet";
} & ButtonHTMLAttributes<HTMLButtonElement>) {
  const styles =
    variant === "primary"
      ? "bg-ink text-paper hover:bg-ink-2 disabled:bg-ink-4"
      : "border border-rule bg-paper text-ink hover:border-ink disabled:text-ink-4";
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-[2px] px-5 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="t-small block text-ink-2">{label}</span>
      <span className="mt-1.5 block">{children}</span>
      {hint && <span className="t-micro mt-1 block text-ink-3">{hint}</span>}
    </label>
  );
}

const CONTROL =
  "h-10 w-full rounded-[2px] border border-rule bg-paper px-3 text-[0.9375rem] text-ink outline-none transition-colors focus:border-ink";

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  const numeric = props.type === "number";
  return <input {...props} className={`${CONTROL} ${numeric ? "fig" : ""} ${props.className ?? ""}`} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`${CONTROL} ${props.className ?? ""}`} />;
}

export function Slider(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="range"
      {...props}
      className={`mt-2 w-full accent-ink ${props.className ?? ""}`}
    />
  );
}

/* ── Tables: the printout ─────────────────────────────────────── */

export interface Column {
  key: string;
  label: string;
  numeric?: boolean;
  width?: string;
}

export function DataTable({
  columns,
  children,
  minWidth = "min-w-[560px]",
}: {
  columns: Column[];
  children: ReactNode;
  minWidth?: string;
}) {
  return (
    <div className="overflow-x-auto">
      <table className={`w-full border-collapse ${minWidth}`}>
        <thead>
          <tr className="border-b border-ink">
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                style={c.width ? { width: c.width } : undefined}
                className={`t-micro pb-2 pr-4 font-medium text-ink-3 last:pr-0 ${
                  c.numeric ? "text-right" : "text-left"
                }`}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Row({ children }: { children: ReactNode }) {
  return <tr className="border-b border-rule-soft last:border-0">{children}</tr>;
}

export function Cell({
  children,
  numeric = false,
  strong = false,
  className = "",
}: {
  children: ReactNode;
  numeric?: boolean;
  strong?: boolean;
  className?: string;
}) {
  return (
    <td
      className={`py-2.5 pr-4 align-middle last:pr-0 ${numeric ? "fig t-small text-right" : "t-small"} ${
        strong ? "font-medium text-ink" : "text-ink-2"
      } ${className}`}
    >
      {children}
    </td>
  );
}
