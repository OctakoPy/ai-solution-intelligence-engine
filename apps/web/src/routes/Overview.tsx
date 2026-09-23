import { useQuery } from "@tanstack/react-query";
import {
  Database,
  CheckCircle,
  XCircle,
  Timer,
  Flag,
  Clock,
  Brain,
} from "lucide-react";
import { StatCard } from "@/components/ui/stat-card";
import { DonutChart } from "@/components/ui/donut-chart";
import { BarList } from "@/components/ui/bar-list";
import { ImpactRow } from "@/components/ui/impact-row";
import { DataTable } from "@/components/ui/data-table";
import { StatusBadge } from "@/components/ui/status-badge";
import { PageHeader } from "@/components/ui/page-header";
import { fetchOverview } from "@/lib/api";
import { useUIStore } from "@/stores/ui";
import type { OverviewFlaggedRow, OverviewRecentRow } from "@/lib/types";

const RECENT_COLUMNS = [
  {
    key: "source" as const,
    header: "Source",
  },
  {
    key: "title" as const,
    header: "Record / Title",
  },
  {
    key: "category" as const,
    header: "Category",
  },
  {
    key: "status" as const,
    header: "Status",
    render: (row: OverviewRecentRow) => (
      <StatusBadge state={row.status as "added" | "rejected" | "flagged"} />
    ),
  },
  {
    key: "time_label" as const,
    header: "Time",
    render: (row: OverviewRecentRow) => (
      <span className="text-gray-500">{row.time_label}</span>
    ),
  },
];

const FLAG_COLUMNS = [
  {
    key: "id" as const,
    header: "ID",
  },
  {
    key: "title" as const,
    header: "Record / Title",
  },
  {
    key: "category" as const,
    header: "Category",
  },
  {
    key: "source" as const,
    header: "Source",
  },
  {
    key: "reason" as const,
    header: "AI Reasoning",
  },
];

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const mins = Math.max(0, Math.round((Date.now() - then) / 60_000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export default function Overview() {
  const datasetSize = useUIStore((s) => s.datasetSize);
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["overview", datasetSize],
    queryFn: () => fetchOverview(datasetSize),
  });

  return (
    <div>
      <PageHeader
        title="Overview"
        subtitle="Ingest. Understand. Retrieve. Respond."
      />

      {isLoading && (
        <div className="text-base text-gray-500">Loading metrics...</div>
      )}

      {isError && (
        <div className="rounded-lg border border-red-500 bg-red-50 p-4 text-base text-red-700">
          Failed to load overview: {String((error as Error).message)}
        </div>
      )}

      {data && (
        <>
          <div className="flex flex-col gap-3 sm:flex-row">
            <StatCard
              icon={Database}
              label="Processed Records"
              value={data.processed.toLocaleString()}
              delta="+12 today"
            />
            <StatCard
              icon={CheckCircle}
              label="Added to Knowledge Base"
              value={data.added.toLocaleString()}
              delta={
                data.processed > 0
                  ? `${((data.added / data.processed) * 100).toFixed(1)}%`
                  : "0%"
              }
            />
            <StatCard
              icon={XCircle}
              label="Rejected / Duplicates"
              value={data.rejected.toLocaleString()}
              delta={
                data.processed > 0
                  ? `${((data.rejected / data.processed) * 100).toFixed(1)}%`
                  : "0%"
              }
            />
            <StatCard
              icon={Timer}
              label="Avg. Processing Time"
              value={data.avg_time}
              delta="-0.8s vs yesterday"
            />
          </div>

          <div className="mt-6 rounded-xl border border-amber-300 bg-amber-50 p-5 shadow-card">
            <div className="mb-3 flex items-center gap-2">
              <Flag className="h-5 w-5 text-amber-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Flagged for Human Review
              </h2>
              <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-sm font-semibold text-amber-700">
                {data.flagged.length}
              </span>
            </div>
            <DataTable
              columns={FLAG_COLUMNS}
              rows={data.flagged as OverviewFlaggedRow[]}
              empty={
                <span className="text-gray-500">No flagged items</span>
              }
            />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-12">
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card lg:col-span-4">
              <h2 className="mb-3 text-lg font-semibold text-gray-900">
                Ingestion Summary (Today)
              </h2>
              <DonutChart
                data={[
                  { label: "Added", value: data.added, color: "#0E9354" },
                  { label: "Rejected", value: data.rejected, color: "#E5484D" },
                  { label: "Processing", value: 0, color: "#175FEE" },
                  { label: "Review", value: data.flagged_count, color: "#F5A623" },
                ]}
                total={data.processed}
              />
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card lg:col-span-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Top Categories
                </h2>
              </div>
              <BarList
                items={data.top_categories.map((c) => ({
                  label: c.name,
                  value: c.count,
                }))}
              />
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card lg:col-span-4">
              <h2 className="mb-3 text-lg font-semibold text-gray-900">
                Before vs After (Impact)
              </h2>
              <div className="flex flex-col gap-4">
                {data.before_after.map((row) => (
                  <ImpactRow
                    key={row.label}
                    label={row.label}
                    before={row.before}
                    after={row.after}
                    delta={row.delta}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-gray-200 bg-white p-5 shadow-card">
            <div className="mb-3 flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Resolution Memory
              </h2>
              <span className="text-sm text-gray-400">
                confirmed outcomes feeding the learning loop
              </span>
            </div>
            {data.memory_stats && data.memory_stats.total_outcomes > 0 ? (
              <>
                <div className="flex flex-col gap-6 lg:flex-row lg:items-center">
                  <DonutChart
                    data={[
                      {
                        label: "Worked",
                        value: data.memory_stats.worked,
                        color: "#0E9354",
                      },
                      {
                        label: "Rejected",
                        value: data.memory_stats.rejected,
                        color: "#E5484D",
                      },
                    ]}
                    total={data.memory_stats.total_outcomes}
                  />
                  <div className="grid flex-1 grid-cols-2 gap-4 sm:grid-cols-4">
                    <div>
                      <div className="text-3xl font-bold text-gray-900">
                        {data.memory_stats.total_outcomes}
                      </div>
                      <div className="text-sm text-gray-500">
                        Outcomes recorded
                      </div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-green-600">
                        {Math.round(data.memory_stats.success_rate * 100)}%
                      </div>
                      <div className="text-sm text-gray-500">
                        Outcome success rate
                      </div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-gray-900">
                        {data.memory_stats.entries_learned}
                      </div>
                      <div className="text-sm text-gray-500">
                        Entries learned
                      </div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-blue-600">
                        {data.memory_stats.proven_fixes}
                      </div>
                      <div className="text-sm text-gray-500">
                        Proven fixes
                      </div>
                    </div>
                  </div>
                </div>
                {data.memory_stats.last_outcome_at && (
                  <div className="mt-3 text-sm text-gray-500">
                    Last outcome:{" "}
                    {relativeTime(data.memory_stats.last_outcome_at)}
                  </div>
                )}
              </>
            ) : (
              <p className="text-base text-gray-500">
                No outcomes recorded yet — confirm a fix from Find a Solution
                to start the learning loop.
              </p>
            )}
          </div>

          <div className="mt-6 rounded-xl border border-gray-200 bg-white p-5 shadow-card">
            <div className="mb-3 flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Resolution Time by Category
              </h2>
            </div>
            <div className="grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
              {data.resolution_by_category.map((row) => (
                <div
                  key={row.name}
                  className="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2"
                >
                  <span className="text-sm text-gray-600">{row.name}</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {row.avg_time}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-gray-200 bg-white p-5 shadow-card">
            <h2 className="mb-3 text-lg font-semibold text-gray-900">
              Recent Activity
            </h2>
            <DataTable
              columns={RECENT_COLUMNS}
              rows={data.recent}
              empty={<span className="text-gray-500">No activity yet</span>}
            />
          </div>
        </>
      )}
    </div>
  );
}
