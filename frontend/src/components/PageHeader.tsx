import type { ReactNode } from "react";

export default function PageHeader({
  title,
  lede,
  aside,
}: {
  title: string;
  lede?: string;
  aside?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-6 border-b border-ink pb-5">
      <div className="max-w-[62ch]">
        <h1 className="t-h1 text-ink">{title}</h1>
        {lede && <p className="t-body mt-2 text-ink-2">{lede}</p>}
      </div>
      {aside && <div className="shrink-0">{aside}</div>}
    </div>
  );
}
