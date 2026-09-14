import { cn } from "@/lib/utils";

export interface BarListDatum {
  label: string;
  value: number;
}

export interface BarListProps {
  items: BarListDatum[];
  className?: string;
  maxLabelWidth?: string;
}

export function BarList({ items, className, maxLabelWidth = "40%" }: BarListProps) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2">
          <span
            className="text-sm text-gray-500"
            style={{ maxWidth: maxLabelWidth, minWidth: "90px" }}
            title={item.label}
          >
            {item.label}
          </span>
          <div className="relative flex-1 h-2 bg-gray-200 rounded">
            <div
              className="h-full rounded bg-gradient-to-r from-blue-600 to-blue-50"
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
          <span className="w-8 text-right text-sm font-semibold text-gray-900">
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}
