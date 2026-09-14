import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface StatCardProps {
  icon?: LucideIcon;
  label: string;
  value: string;
  delta?: string;
  up?: boolean;
  className?: string;
}

export function StatCard({
  icon: Icon,
  label,
  value,
  delta,
  up = true,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl bg-white p-5 shadow-card border border-gray-200 flex-1",
        className,
      )}
    >
      <div className="flex items-center gap-2">
        {Icon && <Icon className="h-5 w-5 text-gray-500" />}
        <span className="text-sm font-semibold uppercase text-gray-500">
          {label}
        </span>
      </div>
      <div className="text-3xl font-bold text-gray-900 mt-2">{value}</div>
      {delta && (
        <div className="mt-1 text-sm text-gray-500">
          <span className={up ? "text-green-600" : "text-red-500"}>{delta}</span>
        </div>
      )}
    </div>
  );
}
