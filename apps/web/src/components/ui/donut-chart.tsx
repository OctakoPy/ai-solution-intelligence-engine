import { cn } from "@/lib/utils";

export interface DonutChartDatum {
  label: string;
  value: number;
  color: string;
}

export interface DonutChartProps {
  data: DonutChartDatum[];
  total?: number;
  size?: number;
  className?: string;
}

export function DonutChart({
  data,
  total,
  size = 110,
  className,
}: DonutChartProps) {
  const sum =
    total ?? data.reduce((acc, d) => acc + d.value, 0);
  const nonzero = data.filter((d) => d.value > 0);
  let offset = 0;
  const rings = nonzero.map((d) => {
    const pct = (d.value / sum) * 100;
    const seg = (pct / 100) * 360;
    const start = offset;
    offset += seg;
    return { ...d, pct, start, end: offset, seg };
  });

  const radius = size / 2 - 8;
  const circum = 2 * Math.PI * radius;

  return (
    <div
      className={cn(
        "flex items-center gap-4",
        className,
      )}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="block"
      >
        {rings.map((d, i) => {
          const segLen = (d.seg / 360) * circum;
          const gap = 0.5;
          const adjustedLen = segLen - gap;
          const rotation = d.start - 90;
          return (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={d.color}
              strokeWidth={12}
              strokeDasharray={`${adjustedLen} ${circum}`}
              transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
              style={{
                transition: "stroke-dasharray 0.4s ease",
              }}
            />
          );
        })}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius - 18}
          fill="white"
          className="drop-shadow"
        />
      </svg>
      <div className="flex flex-col gap-2">
        {data.map((d, i) => (
          <div
            key={i}
            className="flex items-center gap-2 text-base"
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: d.color }}
            />
            <span className="text-gray-900">{d.label}</span>
            <span className="ml-auto text-sm text-gray-500">
              {sum > 0 ? `${((d.value / sum) * 100).toFixed(1)}%` : "0.0%"}{" "}
              ({d.value})
            </span>
          </div>
        ))}
        <div className="mt-1 border-t border-gray-200 pt-1 text-sm text-gray-500">
          Total — {sum.toLocaleString()}
        </div>
      </div>
    </div>
  );
}
