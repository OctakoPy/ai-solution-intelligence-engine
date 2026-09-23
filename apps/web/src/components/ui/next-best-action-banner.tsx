import { HelpCircle } from "lucide-react";
import type { NextBestAction } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface NextBestActionBannerProps {
  action: NextBestAction;
  className?: string;
}

const TITLE: Record<NextBestAction["action"], string> = {
  ask_context: "Not confident enough to guess — add context",
  escalate_sme: "Knows when not to guess — escalate",
};

export function NextBestActionBanner({
  action,
  className,
}: NextBestActionBannerProps) {
  return (
    <div
      data-testid="next-best-action"
      className={cn(
        "rounded-lg border border-amber-300 bg-amber-50 p-3",
        className,
      )}
    >
      <p className="inline-flex items-center gap-1.5 text-sm font-semibold text-amber-800">
        <HelpCircle className="h-4 w-4" />
        {TITLE[action.action]}
      </p>
      <p className="mt-1 text-sm text-amber-900">{action.message}</p>
      {action.missing_fields.length > 0 && (
        <p className="mt-1 text-xs text-amber-700">
          Missing: {action.missing_fields.join(", ")}
        </p>
      )}
    </div>
  );
}
