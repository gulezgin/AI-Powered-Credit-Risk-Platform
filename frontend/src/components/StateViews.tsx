import { useI18n } from "../i18n";

/* A quiet measured bar stands in while a reading is being taken — the loading
   state belongs to the same instrument language as the rest of the page. */
export function LoadingState({ label }: { label?: string }) {
  const { t } = useI18n();
  return (
    <div className="py-16">
      <p className="t-small text-ink-3">{label ?? t("common.loading")}</p>
      <div className="mt-3 h-1.5 w-40 overflow-hidden bg-paper-sunk">
        <div className="h-full w-1/3 animate-pulse bg-ink-3" />
      </div>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <p className="t-small rounded-[2px] border-l-2 border-signal bg-signal-wash px-4 py-3 leading-relaxed text-signal">
      {message}
    </p>
  );
}
