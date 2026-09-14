import { create } from "zustand";
import type { View } from "@/lib/types";
import { useUIStore, type GpuLevel } from "./ui";

export type PlaybackStatus = "idle" | "playing" | "ended" | "error";

export type Phase =
  | "title"
  | "desc"
  | "reso"
  | "checks"
  | "result"
  | "tally"
  | "transition"
  | "done";

export interface RecentRow {
  source: string;
  title: string;
  status: "added" | "rejected" | "flagged";
  completedAt: number;
}

export interface PlaybackState {
  status: PlaybackStatus;
  views: View[];
  currentIndex: number;
  phase: Phase;
  checkIndex: number;
  typedDescription: string;
  typedResolution: string;
  descCaretVisible: boolean;
  resoCaretVisible: boolean;
  tallyProcessed: number;
  tallyAdded: number;
  tallyFlagged: number;
  tallyRejected: number;
  recent: RecentRow[];
  startedAt: number;
  lastTickAt: number;
  error: string | null;
  setViews: (views: View[]) => void;
  play: () => void;
  end: () => void;
  reset: () => void;
  setError: (msg: string | null) => void;
  tick: (now: number) => void;
  progressPct: number;
  stageProgress: number; // 0..4 within current ticket (0=before stage1, 1=after stage1, 2=after judge, 3=after dup, 4=after result)
}

export const TIMING: Record<
  GpuLevel,
  { char: number; check: number; pause: number; initial: number; charsPerFrame?: number }
> =
  {
    "GPU Level 1 (Slow)": { char: 22, check: 700, pause: 1400, initial: 16 },
    "GPU Level 2 (Medium)": { char: 14, check: 375, pause: 750, initial: 16 },
    // GPU Level 3: ~150 chars/sec (5 chars per ~33ms tick on a 60Hz
    // display) with the same check/pause pacing as Level 2.
    "GPU Level 3 (Fast)": {
      char: 33,
      check: 375,
      pause: 750,
      initial: 16,
      charsPerFrame: 5,
    },
  };

/**
 * Characters to append per tick. Defaults to 1; GPU Level 3 types several
 * characters per frame to reach its target speed.
 */
function charsPerFrame(t: { charsPerFrame?: number }): number {
  return t.charsPerFrame ?? 1;
}

/**
 * Deterministic demo age for a record: hash the id into an offset of
 * roughly 3 to 365 days so the "Recent Processed Records" time column
 * shows a believable spread instead of a single timestamp.
 */
function demoAgeMs(id: string): number {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  }
  const days = 3 + (hash % 363);
  return days * 86_400_000;
}

const base = (): Omit<
  PlaybackState,
  "setViews" | "play" | "end" | "reset" | "setError" | "tick"
> => ({
  status: "idle",
  views: [],
  currentIndex: 0,
  phase: "title",
  checkIndex: 0,
  typedDescription: "",
  typedResolution: "",
  descCaretVisible: true,
  resoCaretVisible: true,
  tallyProcessed: 0,
  tallyAdded: 0,
  tallyFlagged: 0,
  tallyRejected: 0,
  recent: [],
  startedAt: 0,
  lastTickAt: 0,
  error: null,
  progressPct: 0,
  stageProgress: 0,
});

export const usePlaybackStore = create<PlaybackState>((set, get) => ({
  ...base(),

  setViews: (views) =>
    set({
      views,
      status: "idle",
      currentIndex: 0,
      phase: "title",
      checkIndex: 0,
      typedDescription: "",
      typedResolution: "",
      descCaretVisible: true,
      resoCaretVisible: true,
      tallyProcessed: 0,
      tallyAdded: 0,
      tallyFlagged: 0,
      tallyRejected: 0,
      recent: [],
      startedAt: 0,
      lastTickAt: 0,
      error: null,
      progressPct: 0,
      stageProgress: 0,
    }),

  play: () =>
    set((s) => ({
      status: "playing",
      currentIndex: 0,
      phase: "title",
      checkIndex: 0,
      typedDescription: "",
      typedResolution: "",
      descCaretVisible: true,
      resoCaretVisible: true,
      tallyProcessed: 0,
      tallyAdded: 0,
      tallyFlagged: 0,
      tallyRejected: 0,
      recent: [],
      startedAt: s.startedAt && s.status === "playing" ? s.startedAt : Date.now(),
      lastTickAt: Date.now(),
      error: null,
      progressPct: 0,
      stageProgress: 0,
    })),

  end: () => set({ status: "ended", phase: "done" }),

  reset: () => set({ ...base(), progressPct: 0, stageProgress: 0 }),

  setError: (error) => set({ error, status: "error" }),

  tick(now: number) {
    const { status, views } = get();
    if (status !== "playing" || views.length === 0) return;
    // The GPU level lives in the UI store (the topbar selector writes it);
    // read it imperatively so every tick uses the user's actual selection.
    const t = TIMING[useUIStore.getState().gpuLevel as GpuLevel];
    const view = views[get().currentIndex];
    if (!view) {
      set({ status: "ended", phase: "done" });
      return;
    }
    const desc = view.description;
    const reso = view.resolution;

    switch (get().phase) {
      case "title":
        set({ phase: "desc", typedDescription: desc[0] ?? "", lastTickAt: now, stageProgress: 0, progressPct: 0 });
        break;

      case "desc":
        if (desc.length === 0) {
          set({ phase: "reso", typedResolution: reso[0] ?? "", lastTickAt: now, stageProgress: 0, progressPct: 0 });
          break;
        }
        if (get().typedDescription.length < desc.length) {
          const elapsed = now - get().lastTickAt;
          if (elapsed < t.char) return;
          set((s) => ({
            typedDescription: desc.slice(0, s.typedDescription.length + charsPerFrame(t)),
            descCaretVisible: true,
            lastTickAt: now,
            stageProgress: 0,
            progressPct: 0,
          }));
        } else {
          set({ phase: "reso", typedResolution: reso[0] ?? "", descCaretVisible: false, lastTickAt: now, stageProgress: 0, progressPct: 0 });
        }
        break;

      case "reso":
        if (reso.length === 0) {
          set({ phase: "checks", checkIndex: 0, resoCaretVisible: false, lastTickAt: now, stageProgress: 0, progressPct: 0 });
          break;
        }
        if (get().typedResolution.length < reso.length) {
          const elapsed = now - get().lastTickAt;
          if (elapsed < t.char) return;
          set((s) => ({
            typedResolution: reso.slice(0, s.typedResolution.length + charsPerFrame(t)),
            resoCaretVisible: true,
            lastTickAt: now,
            stageProgress: 0,
            progressPct: 0,
          }));
        } else {
          set({ phase: "checks", checkIndex: 0, resoCaretVisible: false, lastTickAt: now, stageProgress: 0, progressPct: 0 });
        }
        break;

      case "checks": {
        const sinceCheck = now - get().lastTickAt;
        if (sinceCheck < t.check) return;
        const ci = get().checkIndex;
        if (ci < view.checks.length) {
          set((s) => ({
            checkIndex: s.checkIndex + 1,
            lastTickAt: now,
            stageProgress: s.checkIndex + 1,
            progressPct: (s.checkIndex + 1) * 25,
          }));
        } else {
          set({ phase: "result", lastTickAt: now, stageProgress: 3, progressPct: 75 });
        }
        break;
      }

      case "result":
        // Result card revealed in parallel with resolution typing (spec §2.1 step 6)
        // Resolution typing happens during "reso" phase; result card reveals here
        set({ phase: "tally", lastTickAt: now, stageProgress: 4, progressPct: 100 });
        break;

      case      "tally": {
        const sinceTally = now - get().lastTickAt;
        if (sinceTally < t.pause) return;
        set((s) => {
          const added = view.outcome === "added" ? 1 : 0;
          const flagged = view.outcome === "flagged" ? 1 : 0;
          const rejected = view.outcome === "rejected" ? 1 : 0;
          const row: RecentRow = {
            source: view.source_label,
            title: view.title,
            status: view.outcome,
            completedAt: Date.now() - demoAgeMs(view.id),
          };
          const isLast = s.currentIndex >= s.views.length - 1;
          return {
            tallyProcessed: s.tallyProcessed + 1,
            tallyAdded: s.tallyAdded + added,
            tallyFlagged: s.tallyFlagged + flagged,
            tallyRejected: s.tallyRejected + rejected,
            recent: [...s.recent, row].slice(-20),
            phase: isLast ? "done" : "transition",
            lastTickAt: now,
            stageProgress: 4,
            progressPct: 100,
          };
        });
        if (get().phase === "done") {
          set({ status: "ended", phase: "done", stageProgress: 4, progressPct: 100 });
        }
        break;
      }

      case "transition": {
        // Brief pause showing completed ticket before advancing
        const transitionDelay = Math.min(500, t.pause / 2);
        if (now - get().lastTickAt < transitionDelay) return;
        const nextIndex = get().currentIndex + 1;
        const nextView = get().views[nextIndex];
        if (!nextView) {
          set({ status: "ended", phase: "done", stageProgress: 4, progressPct: 100 });
          break;
        }
        const nextDesc = nextView.description;
        set((s) => ({
          currentIndex: s.currentIndex + 1,
          phase: "desc",
          typedDescription: nextDesc[0] ?? "",
          stageProgress: 0,
          checkIndex: 0,
          typedResolution: "",
          descCaretVisible: true,
          resoCaretVisible: true,
          lastTickAt: now,
          progressPct: 0,
        }));
        break;
      }

      case "done":
        set({ status: "ended", phase: "done", stageProgress: 4, progressPct: 100 });
        break;
    }
  },
}));
