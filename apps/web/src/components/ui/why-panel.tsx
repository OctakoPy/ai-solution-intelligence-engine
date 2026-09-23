import { Check, Info, TriangleAlert } from "lucide-react";
import type { RetrievedSolution, SignalKey } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface WhyPanelProps {
  solution: RetrievedSolution;
  className?: string;
}

const SIGNAL_LABELS: Record<SignalKey, string> = {
  semantic: "Text similarity",
  error_code: "Error-code match",
  module: "System / module match",
  environment: "Environment match",
  success: "Historical success",
  recency: "Recency",
  feedback: "Consultant feedback",
};

const SIGNAL_ORDER: SignalKey[] = [
  "semantic",
  "error_code",
  "module",
  "environment",
  "success",
  "recency",
  "feedback",
];

function PriorSuccess({ solution }: { solution: RetrievedSolution }) {
  if (solution.attempted === undefined || solution.worked === undefined) {
    return null;
  }
  if (solution.attempted === 0) {
    return (
      <p className="text-sm text-gray-500">
        No confirmed outcomes yet — history unknown.
      </p>
    );
  }
  const pct = Math.round((solution.worked / solution.attempted) * 100);
  return (
    <p className="inline-flex items-center gap-1 text-sm font-medium text-green-700">
      <Check className="h-3.5 w-3.5" />
      Worked {solution.worked} of {solution.attempted} times ({pct}%)
    </p>
  );
}

export function WhyPanel({ solution, className }: WhyPanelProps) {
  const breakdown = solution.signal_breakdown ?? {};
  const contributions = SIGNAL_ORDER.filter((key) => (breakdown[key] ?? 0) > 0);
  const caveats = solution.caveats ?? [];

  return (
    <div
      className={cn("space-y-3 rounded-lg bg-gray-50 p-3", className)}
      data-testid="why-panel"
    >
      <p className="text-xs font-semibold tracking-wide text-gray-500 uppercase">
        Why this
      </p>

      <div>
        <p className="text-sm font-medium text-gray-500">Score breakdown</p>
        {contributions.length === 0 ? (
          <p className="text-sm text-gray-500">
            No signals contributed — confidence is near zero.
          </p>
        ) : (
          <ul className="mt-1 space-y-1">
            {contributions.map((key) => (
              <li
                key={key}
                className="flex items-center justify-between gap-2 text-sm"
              >
                <span className="text-gray-700">{SIGNAL_LABELS[key]}</span>
                <span className="font-medium text-gray-900">
                  +{(breakdown[key] ?? 0).toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <p className="text-sm font-medium text-gray-500">Prior success</p>
        <PriorSuccess solution={solution} />
      </div>

      {solution.evidence && solution.evidence.length > 1 && (
        <div>
          <p className="text-sm font-medium text-gray-500">Evidence</p>
          <ul className="mt-1 space-y-1">
            {solution.evidence.map((e) => (
              <li key={e.id} className="text-sm text-gray-700">
                <span className="font-medium">{e.id}</span> · {e.source}
                {e.date && e.date !== "—"
                  ? ` · ${e.date}`
                  : ""}
                {e.attempted > 0 ? ` · ${e.worked}/${e.attempted} worked` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      {caveats.length > 0 && (
        <div>
          <p className="inline-flex items-center gap-1 text-sm font-medium text-gray-500">
            <Info className="h-3.5 w-3.5" />
            Caveats
          </p>
          <ul className="mt-1 space-y-1">
            {caveats.map((c) => (
              <li
                key={c}
                className="inline-flex items-start gap-1 text-sm text-amber-700"
              >
                <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
