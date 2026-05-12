import { Badge } from "@/components/ui/badge";
import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";

interface TrustScoreBadgeProps {
  score: number;
  showLabel?: boolean;
}

export function TrustScoreBadge({ score, showLabel = true }: TrustScoreBadgeProps) {
  const pct = Math.round(score * 100);

  if (score >= 0.75) {
    return (
      <Badge variant="success" className="gap-1">
        <ShieldCheck className="h-3 w-3" />
        {showLabel && <span>Trust {pct}%</span>}
      </Badge>
    );
  }
  if (score >= 0.5) {
    return (
      <Badge variant="warning" className="gap-1">
        <ShieldAlert className="h-3 w-3" />
        {showLabel && <span>Trust {pct}%</span>}
      </Badge>
    );
  }
  return (
    <Badge variant="danger" className="gap-1">
      <ShieldX className="h-3 w-3" />
      {showLabel && <span>Trust {pct}%</span>}
    </Badge>
  );
}
