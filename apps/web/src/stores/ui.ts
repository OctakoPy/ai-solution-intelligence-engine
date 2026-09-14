import { create } from "zustand";

export type GpuLevel = "GPU Level 1 (Slow)" | "GPU Level 2 (Medium)" | "GPU Level 3 (Fast)";

export type NavPage = "overview" | "pipeline" | "find" | "chat";

const GPU_LEVELS: GpuLevel[] = [
  "GPU Level 1 (Slow)",
  "GPU Level 2 (Medium)",
  "GPU Level 3 (Fast)",
];

const DATASET_OPTIONS: { label: string; size: number }[] = [
  { label: "Debug (3)", size: 3 },
  { label: "Small (8)", size: 8 },
  { label: "Full (76)", size: 76 },
];

interface UIState {
  page: NavPage;
  gpuLevel: GpuLevel;
  datasetSize: number;
  setPage: (page: NavPage) => void;
  setGpuLevel: (level: GpuLevel) => void;
  setDatasetSize: (size: number) => void;
  gpuLevels: typeof GPU_LEVELS;
  datasetOptions: typeof DATASET_OPTIONS;
}

export const useUIStore = create<UIState>((set) => ({
  page: "overview",
  gpuLevel: "GPU Level 2 (Medium)",
  datasetSize: 8,
  gpuLevels: GPU_LEVELS,
  datasetOptions: DATASET_OPTIONS,
  setPage: (page) => set({ page }),
  setGpuLevel: (gpuLevel) => set({ gpuLevel }),
  setDatasetSize: (datasetSize) => set({ datasetSize }),
}));
