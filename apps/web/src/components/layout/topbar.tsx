import { Play, Square } from "lucide-react";
import { useUIStore } from "@/stores/ui";
import { usePlaybackStore } from "@/stores/playback";

export function Topbar() {
  const page = useUIStore((s) => s.page);
  const gpuLevel = useUIStore((s) => s.gpuLevel);
  const setGpuLevel = useUIStore((s) => s.setGpuLevel);
  const gpuLevels = useUIStore((s) => s.gpuLevels);

  const status = usePlaybackStore((s) => s.status);
  const play = usePlaybackStore((s) => s.play);
  const end = usePlaybackStore((s) => s.end);

  const controlsDisabled = status === "playing";

  const titles: Record<string, string> = {
    overview: "ResolveIQ",
    pipeline: "ResolveIQ",
    find: "ResolveIQ",
    chat: "Chat with ResolveIQ",
    analytics: "ResolveIQ",
  };
  const subtitles: Record<string, string> = {
    overview: "Ingest. Understand. Retrieve. Respond.",
    pipeline: "Watch the pipeline process records in real time.",
    find: "Search and discover solutions from the knowledge base.",
    chat: "Ask questions in natural language. Get answers with sourced solutions.",
    analytics: "Ingest. Understand. Retrieve. Respond.",
  };

  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          🧠 {titles[page] ?? titles.overview}
        </h1>
        {subtitles[page] && (
          <p className="text-sm text-gray-500">
            {subtitles[page]}
          </p>
        )}
      </div>
      <div className="flex items-center gap-6">
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs text-gray-500">Compute Speed</span>
          <select
            value={gpuLevel}
            onChange={(e) => setGpuLevel(e.target.value as typeof gpuLevel)}
            className="text-sm font-medium text-gray-900"
          >
            {gpuLevels.map((lvl) => (
              <option key={lvl} value={lvl}>
                {lvl}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={play}
            disabled={controlsDisabled}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-semibold ${
              controlsDisabled
                ? "cursor-not-allowed opacity-40"
                : "border-blue-600 bg-blue-600 text-white hover:bg-blue-700"
            }`}
          >
            <Play className="h-4 w-4" />
            Start
          </button>
          <button
            onClick={end}
            disabled={status === "idle" || status === "ended"}
            className="flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-semibold text-gray-900 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Square className="h-3.5 w-3.5" />
            End
          </button>
        </div>
      </div>
    </header>
  );
}
