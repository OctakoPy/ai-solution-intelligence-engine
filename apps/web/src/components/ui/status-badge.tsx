import { cn } from "@/lib/utils";
import {
  CheckCircle,
  CircleAlert,
  CircleX,
} from "lucide-react";

export type StatusBadgeState =
  | "added"
  | "pass"
  | "rejected"
  | "reject"
  | "flag"
  | "flagged"
  | "review";

export interface StatusBadgeProps {
  state: StatusBadgeState;
  className?: string;
}

const MAPPING: Record<
  StatusBadgeState,
  { icon: typeof CheckCircle; label: string; color: string }
> = {
  added: { icon: CheckCircle, label: "Added", color: "text-green-600" },
  pass: { icon: CheckCircle, label: "Passed", color: "text-green-600" },
  review: { icon: CircleAlert, label: "Review", color: "text-amber-500" },
  flag: { icon: CircleAlert, label: "Review", color: "text-amber-500" },
  flagged: { icon: CircleAlert, label: "Flagged", color: "text-amber-500" },
  reject: { icon: CircleX, label: "Rejected", color: "text-red-500" },
  rejected: { icon: CircleX, label: "Rejected", color: "text-red-500" },
};

export function StatusBadge({ state, className }: StatusBadgeProps) {
  const { icon: Icon, label, color } = MAPPING[state] ?? MAPPING.pass;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-sm font-semibold",
        color,
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}
