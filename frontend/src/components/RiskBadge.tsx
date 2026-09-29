import type { RiskLevel } from "../api/types";
import { useI18n } from "../i18n";
import { BandChip } from "./ui";

export default function RiskBadge({ level }: { level: RiskLevel | string }) {
  const { t } = useI18n();
  return <BandChip level={level} label={t(`risk.${level}`)} />;
}
