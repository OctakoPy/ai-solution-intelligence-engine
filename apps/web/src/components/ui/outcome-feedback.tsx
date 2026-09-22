import { useState } from "react";
import { Check, X } from "lucide-react";
import { recordOutcome } from "@/lib/api";
import { cn } from "@/lib/utils";

export interface OutcomeFeedbackProps {
  entryId: string;
  className?: string;
}

export function OutcomeFeedback({ entryId, className }: OutcomeFeedbackProps) {
  const [choice, setChoice] = useState<boolean | null>(null);
  const [learnedCount, setLearnedCount] = useState<number | null>(null);

  const record = (success: boolean) => {
    if (choice !== null) return;
    setChoice(success);
    recordOutcome(entryId, success, "confirmed from UI")
      .then((res) => setLearnedCount(res.total_outcomes))
      .catch(() => setChoice(null));
  };

  if (choice !== null) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
          choice
            ? "bg-green-50 text-green-700"
            : "bg-red-50 text-red-700",
          className,
        )}
      >
        {choice ? (
          <>
            <Check className="h-3 w-3" /> Confirmed worked
          </>
        ) : (
          <>
            <X className="h-3 w-3" /> Marked failed
          </>
        )}
        {learnedCount !== null && (
          <span className="font-normal opacity-75">
            · engine learned ({learnedCount} outcome
            {learnedCount === 1 ? "" : "s"})
          </span>
        )}
      </span>
    );
  }

  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      <span className="text-xs text-gray-500">Did this work?</span>
      <button
        onClick={() => record(true)}
        title="Confirm this resolution worked — future searches rank it higher"
        className="inline-flex items-center gap-1 rounded-full border border-green-200 px-2 py-0.5 text-xs font-medium text-green-700 hover:bg-green-50"
      >
        <Check className="h-3 w-3" /> Yes
      </button>
      <button
        onClick={() => record(false)}
        title="Mark this resolution as failed — future searches rank it lower"
        className="inline-flex items-center gap-1 rounded-full border border-red-200 px-2 py-0.5 text-xs font-medium text-red-700 hover:bg-red-50"
      >
        <X className="h-3 w-3" /> No
      </button>
    </span>
  );
}
