import { useState } from "react";
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

/**
 * Plain-language reasons, strongest first.
 *
 * The weighted numbers behind these ("+0.21") are weighted contributions to a
 * composite score, not probabilities, and they read as noise to anyone
 * outside the project. The business-readable claim is what each signal
 * *means*, so that is what is shown by default. The numbers stay one toggle
 * away for anyone reviewing the method.
 */
function plainReasons(
  breakdown: Record<string, number>,
  solution: RetrievedSolution,
): string[] {
  const reasons: string[] = [];
  const has = (key: SignalKey) => (breakdown[key] ?? 0) > 0;

  if (has("error_code")) {
    reasons.push("The error code you gave matches this record exactly");
  }
  if (has("module")) {
    reasons.push("It is recorded against the same system");
  }
  if (has("environment")) {
    reasons.push("It was resolved in the same environment");
  }
  if (has("semantic")) {
    reasons.push("The description reads like your question");
  }
  const worked = solution.worked ?? 0;
  const attempted = solution.attempted ?? 0;
  if (attempted > 0) {
    if (worked === attempted) {
      reasons.push(`It has worked every time it was tried (${worked} of ${attempted})`);
    } else if (worked / attempted >= 0.8) {
      reasons.push(`It has usually worked (${worked} of ${attempted} times)`);
    } else {
      reasons.push(`It has a mixed history (${worked} of ${attempted} times)`);
    }
  }
  if (has("feedback")) {
    reasons.push("Consultants have rated it positively");
  }
  if (reasons.length === 0) {
    reasons.push("No strong signals — this is a weak match");
  }
  return reasons;
}

/**
 * One plain sentence answering the question a business user always asks:
 * why should I trust this?
 *
 * The wording is produced once, server-side, so Find and Chat cannot drift
 * apart. The fallback covers a record built before the field existed.
 */
export function confidenceSummary(solution: RetrievedSolution): string {
  if (solution.confidence_note) return solution.confidence_note;
  const worked = solution.worked ?? 0;
  const attempted = solution.attempted ?? 0;
  if (attempted > 0 && worked === attempted) {
    return "High confidence - this fix has worked every time it was tried.";
  }
  if (attempted > 0 && worked / attempted >= 0.8) {
    return "Good confidence - this fix has usually worked.";
  }
  return "Worth reviewing - this is a related record, not a confirmed match.";
}

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
  const [showNumbers, setShowNumbers] = useState(false);
  const reasons = plainReasons(breakdown, solution);

  return (
    <div
      className={cn("space-y-3 rounded-lg bg-gray-50 p-3", className)}
      data-testid="why-panel"
    >
      <p className="text-xs font-semibold tracking-wide text-gray-500 uppercase">
        Why this
      </p>

      <div>
        <p className="text-sm font-medium text-gray-500">Why we picked it</p>
        <ul className="mt-1 space-y-1">
          {reasons.map((reason) => (
            <li key={reason} className="flex gap-2 text-sm text-gray-700">
              <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-600" />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => setShowNumbers((v) => !v)}
          className="mt-2 text-xs font-medium text-blue-600 hover:underline"
        >
          {showNumbers ? "Hide scoring detail" : "Show scoring detail"}
        </button>
        {showNumbers && (
          <div className="mt-2 rounded border border-gray-200 bg-white p-2">
            <p className="text-xs text-gray-500">
              Weighted contributions to the confidence score. These are not
              probabilities.
            </p>
            {contributions.length === 0 ? (
              <p className="mt-1 text-sm text-gray-500">
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
        )}
      </div>

      <div>
        <p className="text-sm font-medium text-gray-500">Track record</p>
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
