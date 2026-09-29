import type { Decision } from "../api/types";
import { useI18n } from "../i18n";

const STYLES: Record<Decision, string> = {
  APPROVE: "bg-band-low-wash text-band-low",
  MANUAL_REVIEW: "bg-band-mid-wash text-band-mid",
  REJECT: "bg-signal-wash text-signal",
};

export default function DecisionBadge({ decision }: { decision: Decision | string }) {
  const { t } = useI18n();
  const style = STYLES[decision as Decision] ?? "bg-paper-sunk text-ink-2";
  return (
    <span className={`inline-block rounded-[2px] px-2.5 py-1 text-[0.84rem] font-medium ${style}`}>
      {t(`decision.${decision}`)}
    </span>
  );
}
