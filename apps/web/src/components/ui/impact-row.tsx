import { cn } from "@/lib/utils";

export interface ImpactRowProps {
  label: string;
  before: string;
  after: string;
  delta: string;
  className?: string;
}

export function ImpactRow({
  label,
  before,
  after,
  delta,
  className,
}: ImpactRowProps) {
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-semibold text-gray-900">{label}</span>
        <span className="text-sm font-bold text-green-600">{delta}</span>
      </div>
      <span className="text-sm text-gray-500">
        Before: {before} → After: {after}
      </span>
    </div>
  );
}
