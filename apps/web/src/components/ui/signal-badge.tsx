import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import type { Signal } from "@/lib/types";

export interface SignalBadgeProps {
  signal: Signal;
  className?: string;
}

const LABELS: Record<Signal, string> = {
  error_code: "Error code match",
  module: "System match",
  environment: "Environment match",
};

export function SignalBadge({ signal, className }: SignalBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700",
        className,
      )}
      title={`Incident detail matched: ${LABELS[signal]}`}
    >
      <Check className="h-3 w-3" />
      {LABELS[signal]}
    </span>
  );
}