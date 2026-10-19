import { useEffect } from "react";
import { usePlaybackStore } from "@/stores/playback";
import { fetchViews, ingest } from "@/lib/api";
import { usePlaybackMachine, useFormatTime } from "@/components/pipeline/usePlaybackMachine";
import { CheckCircle, CircleAlert, CircleX, Play, Loader2, ShieldCheck } from "lucide-react";
import { LanguageBadge } from "@/components/ui/language-badge";
import type { View } from "@/lib/types";

function CheckIcon({ result }: { result: "pass" | "flag" | "reject" }) {
  if (result === "pass") return <CheckCircle className="h-5 w-5 text-green-600" />;
  if (result === "flag") return <CircleAlert className="h-5 w-5 text-amber-500" />;
  return <CircleX className="h-5 w-5 text-red-500" />;
}

function resultLabel(result: "pass" | "flag" | "reject") {
  if (result === "pass") return "Passed";
  if (result === "flag") return "Review";
  return "Rejected";
}

/**
 * What was kept out of the index, and why.
 *
 * The filtering already happens at ingest. Without this the work is invisible,
 * so the exclusion reads as "records we did not have" rather than as a
 * deliberate control over what is allowed to be searched.
 */
function ExclusionPanel({ views }: { views: View[] }) {
  const excluded = new Map<string, number>();
  for (const v of views) {
    if (v.outcome !== "rejected") continue;
    excluded.set(v.reason, (excluded.get(v.reason) ?? 0) + 1);
  }
  if (excluded.size === 0) return null;
  const rows = [...excluded.entries()].sort((a, b) => b[1] - a[1]);

  return (
    <div className="rounded-xl border border-gray-200 bg-gray-100 p-5 shadow-card">
      <div className="flex items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-green-600" />
        <h2 className="text-lg font-semibold text-gray-900">Kept out of the search index</h2>
      </div>
      <p className="mt-1 text-sm text-gray-500">
        These records were excluded during ingestion, so they can never be retrieved or quoted as a
        recommendation.
      </p>
      <ul className="mt-3 space-y-1">
        {rows.map(([reason, count]) => (
          <li key={reason} className="flex items-baseline justify-between gap-4 text-base">
            <span className="text-gray-700">{reason}</span>
            <span className="font-semibold text-gray-900">{count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Pipeline() {
  const status = usePlaybackStore((s) => s.status);
  const views = usePlaybackStore((s) => s.views);
  const setViews = usePlaybackStore((s) => s.setViews);
  const currentIndex = usePlaybackStore((s) => s.currentIndex);
  const typedDescription = usePlaybackStore((s) => s.typedDescription);
  const typedResolution = usePlaybackStore((s) => s.typedResolution);
  const descCaretVisible = usePlaybackStore((s) => s.descCaretVisible);
  const resoCaretVisible = usePlaybackStore((s) => s.resoCaretVisible);
  const tallyProcessed = usePlaybackStore((s) => s.tallyProcessed);
  const tallyAdded = usePlaybackStore((s) => s.tallyAdded);
  const tallyFlagged = usePlaybackStore((s) => s.tallyFlagged);
  const tallyRejected = usePlaybackStore((s) => s.tallyRejected);
  const recent = usePlaybackStore((s) => s.recent);
  const play = usePlaybackStore((s) => s.play);
  const reset = usePlaybackStore((s) => s.reset);

  usePlaybackMachine();

  // The corpus is fixed, so there is one ingestion and nothing to re-trigger.
  useEffect(() => {
    if (views.length === 0 && status === "idle") {
      ingest().then(() => {
        fetchViews()
          .then(setViews)
          .catch((e) => {
            console.error("Failed to fetch views:", e);
          });
      });
    }
  }, [status, views.length, setViews]);

  const view = views[currentIndex];
  const isReady = views.length > 0;

  return (
    <div className="flex flex-col gap-4">
      {!isReady && (
        <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-100 p-6 text-base text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Preparing pipeline data...
        </div>
      )}

      {isReady && status === "idle" && (
        <div className="rounded-xl border border-gray-200 bg-gray-100 p-8 text-center">
          <div className="text-4xl">▶️</div>
          <h2 className="mt-3 text-xl font-bold text-gray-900">Execute Pipeline</h2>
          <button
            onClick={play}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2 text-base font-semibold text-white hover:bg-blue-700"
          >
            <Play className="h-4 w-4" />
            Start
          </button>
        </div>
      )}

      {(status === "playing" || status === "ended") && view && (
        <PlayingView
          view={view}
          typedDescription={typedDescription}
          typedResolution={typedResolution}
          descCaretVisible={descCaretVisible}
          resoCaretVisible={resoCaretVisible}
        />
      )}

      <div className="rounded-xl border border-gray-200 bg-gray-100 p-5 shadow-card">
        <h2 className="mb-3 text-lg font-semibold text-gray-900">Live Tally</h2>
        <div className="grid grid-cols-2 gap-4 text-center sm:grid-cols-4">
          <div>
            <div className="text-3xl font-bold text-gray-900">{tallyProcessed}</div>
            <div className="text-sm text-gray-500">Processed</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-green-600">{tallyAdded}</div>
            <div className="text-sm text-gray-500">Added</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-amber-500">{tallyFlagged}</div>
            <div className="text-sm text-gray-500">Flagged</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-red-500">{tallyRejected}</div>
            <div className="text-sm text-gray-500">Rejected</div>
          </div>
        </div>
      </div>

      {status === "ended" && (
        <div className="rounded-xl border border-green-300 bg-green-50 p-4 text-base font-semibold text-green-700">
          ✅ All records processed.
          <button
            onClick={reset}
            className="ml-3 rounded-md border border-gray-200 bg-gray-100 px-3 py-1 text-sm font-semibold text-gray-900 hover:bg-gray-200"
          >
            Restart
          </button>
        </div>
      )}

      <ExclusionPanel views={views} />

      <div className="rounded-xl border border-gray-200 bg-gray-100 p-5 shadow-card">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Processed Records</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-base">
            <thead>
              <tr>
                {["Source", "Record / Title", "Status", "Time"].map((h) => (
                  <th
                    key={h}
                    className="border-b border-gray-200 px-3 py-2 text-left text-sm font-semibold uppercase text-gray-500"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recent.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-4 text-center text-gray-500">
                    No records yet
                  </td>
                </tr>
              ) : (
                recent
                  .slice()
                  .reverse()
                  .map((row, i) => <RowItem key={i} row={row} />)
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function RowItem({
  row,
}: {
  row: {
    source: string;
    title: string;
    status: "added" | "rejected" | "flagged";
    completedAt: number;
  };
}) {
  const now = Date.now();
  return (
    <tr className="border-b border-gray-200 last:border-0">
      <td className="px-3 py-2">{row.source}</td>
      <td className="px-3 py-2">{row.title}</td>
      <td className="px-3 py-2">
        {row.status === "added" ? (
          <span className="inline-flex items-center gap-1 text-sm font-semibold text-green-600">
            <CheckCircle className="h-3.5 w-3.5" /> Added
          </span>
        ) : row.status === "flagged" ? (
          <span className="inline-flex items-center gap-1 text-sm font-semibold text-amber-500">
            <CircleAlert className="h-3.5 w-3.5" /> Flagged
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-sm font-semibold text-red-500">
            <CircleX className="h-3.5 w-3.5" /> Rejected
          </span>
        )}
      </td>
      <td className="px-3 py-2 text-gray-500">{useFormatTime(row.completedAt, now)}</td>
    </tr>
  );
}

interface PlayingViewProps {
  view: import("@/lib/types").View;
  typedDescription: string;
  typedResolution: string;
  descCaretVisible: boolean;
  resoCaretVisible: boolean;
}

function PlayingView({
  view,
  typedDescription,
  typedResolution,
  descCaretVisible,
  resoCaretVisible,
}: PlayingViewProps) {
  const stageProgress = usePlaybackStore((s) => s.stageProgress);

  const stageCards: Array<{
    label: string;
    revealed: boolean;
    result?: "pass" | "flag" | "reject";
  }> = [
    { label: "Stage 1\nStructural", revealed: stageProgress >= 1, result: view.checks[0]?.result },
    { label: "AI Judge\nQuality", revealed: stageProgress >= 2, result: view.checks[1]?.result },
    {
      label: "Duplicate\nSimilarity",
      revealed: stageProgress >= 3,
      result: view.checks[2]?.result,
    },
  ];
  const checkScores: Array<{
    label: string;
    show: boolean;
    result?: "pass" | "flag" | "reject";
    score: number | null | undefined;
  }> = [
    {
      label: "Structural",
      show: stageProgress >= 1,
      result: view.checks[0]?.result,
      score: view.checks[0]?.score,
    },
    {
      label: "Quality",
      show: stageProgress >= 2,
      result: view.checks[1]?.result,
      score: view.checks[1]?.score,
    },
    {
      label: "Similarity",
      show: stageProgress >= 3,
      result: view.checks[2]?.result,
      score: view.checks[2]?.score,
    },
    {
      label:
        view.outcome === "added" ? "Added" : view.outcome === "flagged" ? "Flagged" : "Rejected",
      show: stageProgress >= 4,
      result: view.outcome === "added" ? "pass" : view.outcome === "flagged" ? "flag" : "reject",
      score: null,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="rounded-xl border border-gray-200 bg-gray-100 p-5 shadow-card">
        <div className="flex items-center justify-between">
          <span className="text-base">
            {view.source_icon} <b>{view.source_label}</b>
          </span>
          <span className="flex items-center gap-2 text-sm text-gray-500">
            <LanguageBadge language={view.language} />#{view.id}
          </span>
        </div>
        <h2 className="mt-2 text-xl font-bold text-gray-900">{view.title}</h2>
        <div className="mt-1 text-sm text-gray-500">
          Category: {view.category} · {view.date}
        </div>
        <div className="mt-3 text-sm font-bold uppercase text-gray-500">Description</div>
        <div className="mt-1 min-h-[44px] text-base text-gray-900">
          {typedDescription}
          {descCaretVisible && (
            <span className="ml-0.5 inline-block h-4 w-2 align-text-bottom bg-blue-600 animate-blink" />
          )}
        </div>
        <div className="mt-3 text-sm font-bold uppercase text-gray-500">Resolution</div>
        <div className="mt-1 min-h-[44px] text-base text-gray-900">
          {typedResolution}
          {resoCaretVisible && (
            <span className="ml-0.5 inline-block h-4 w-2 align-text-bottom bg-blue-600 animate-blink" />
          )}
        </div>
      </div>

      <div className="rounded-xl border border-gray-200 bg-gray-100 p-5 shadow-card">
        <h3 className="text-lg font-semibold text-gray-900">Pipeline Progress</h3>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {stageCards.map((s, i) => (
            <div
              key={i}
              className={`rounded-lg border border-gray-200 p-2 text-center transition-colors ${
                s.revealed ? "bg-gray-200" : "bg-gray-50"
              }`}
            >
              <div className="flex justify-center">
                {s.revealed && s.result ? (
                  <CheckIcon result={s.result} />
                ) : (
                  <span className="text-gray-500">⏳</span>
                )}
              </div>
              <div className="mt-1 whitespace-pre-line text-sm font-semibold text-gray-900">
                {s.label}
              </div>
              <div className="mt-1 text-sm text-gray-500">
                {s.revealed && s.result ? resultLabel(s.result) : "Waiting"}
              </div>
            </div>
          ))}
          <div
            className={`rounded-lg border border-gray-200 p-2 text-center transition-colors ${
              stageProgress >= 4 ? "bg-gray-200" : "bg-gray-50"
            }`}
          >
            <div className="flex justify-center">
              {stageProgress >= 4 ? (
                view.outcome === "added" ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : view.outcome === "flagged" ? (
                  <CircleAlert className="h-5 w-5 text-amber-500" />
                ) : (
                  <CircleX className="h-5 w-5 text-red-500" />
                )
              ) : (
                <Loader2 className="h-5 w-5 animate-spin text-blue-300" />
              )}
            </div>
            <div className="mt-1 text-sm font-semibold text-gray-900">Result</div>
            <div className="mt-1 text-sm text-gray-500">
              {view.outcome === "added"
                ? "Added to Knowledge Index"
                : view.outcome === "flagged"
                  ? "Flagged"
                  : "Rejected"}
            </div>
          </div>
        </div>
        <div className="mt-4">
          <div className="flex gap-1">
            {checkScores.map(({ label, show, result, score }) => {
              const done = show;
              // 400 is the fill step for each semantic ramp; 500 and above
              // are the text steps and read as muddy bars.
              const color =
                result === "pass"
                  ? "bg-green-400"
                  : result === "flag"
                    ? "bg-amber-400"
                    : "bg-red-400";
              return (
                <div key={label} className="min-w-0 flex-1">
                  <div
                    className={`h-3 rounded-md transition-colors duration-300 ${
                      done ? color : "bg-gray-200"
                    }`}
                  />
                  <div className="mt-1 flex flex-col items-center text-center leading-tight">
                    <span
                      className={`max-w-full truncate text-sm ${
                        done ? "font-medium text-gray-900" : "text-gray-400"
                      }`}
                      title={label}
                    >
                      {label}
                    </span>
                    <span
                      className={`text-sm tabular-nums ${
                        done
                          ? score != null
                            ? "text-gray-500"
                            : "text-gray-400"
                          : "text-transparent"
                      }`}
                    >
                      {done ? (score != null ? `${Math.round(score * 100)}%` : "—") : "0%"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Pipeline;
