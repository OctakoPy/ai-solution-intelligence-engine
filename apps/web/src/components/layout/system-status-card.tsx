import { useUIStore } from "@/stores/ui";

export function SystemStatusCard() {
  const gpuLevel = useUIStore((s) => s.gpuLevel);
  const datasetSize = useUIStore((s) => s.datasetSize);
  return (
    <div className="rounded-xl bg-gray-900 p-4 text-xs text-gray-400">
      <div className="mb-1 flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-green-500" />
        <span className="font-medium text-green-400">
          All systems operational
        </span>
      </div>
      <div className="mt-2">
        <span className="text-gray-500">Compute Speed:</span>{" "}
        <span className="text-blue-400">{gpuLevel}</span>
      </div>
      <div className="mt-1">
        <span className="text-gray-500">Dataset Size:</span>{" "}
        <span className="text-blue-400">{datasetSize}</span>
      </div>
    </div>
  );
}
