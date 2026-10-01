import { create } from "zustand";

export type GpuLevel = "GPU Level 1 (Slow)" | "GPU Level 2 (Medium)" | "GPU Level 3 (Fast)";

export type NavPage = "overview" | "pipeline" | "find" | "chat";

const GPU_LEVELS: GpuLevel[] = ["GPU Level 1 (Slow)", "GPU Level 2 (Medium)", "GPU Level 3 (Fast)"];

/**
 * The application always runs the whole corpus.
 *
 * There used to be a Debug (3) / Small (8) / Full selector in the sidebar,
 * and it defaulted to 8 - so the app silently served a subset that excluded
 * the manufacturing AMS records and most of the multilingual coverage. The
 * subsets were a convenience for early development and are gone.
 */
export const DATASET_SIZE = 104;

interface UIState {
  page: NavPage;
  gpuLevel: GpuLevel;
  setPage: (page: NavPage) => void;
  setGpuLevel: (level: GpuLevel) => void;
  gpuLevels: typeof GPU_LEVELS;
}

export const useUIStore = create<UIState>((set) => ({
  page: "overview",
  gpuLevel: "GPU Level 2 (Medium)",
  gpuLevels: GPU_LEVELS,
  setPage: (page) => set({ page }),
  setGpuLevel: (gpuLevel) => set({ gpuLevel }),
}));
