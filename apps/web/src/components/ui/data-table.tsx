import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface DataTableColumn<T> {
  key: keyof T;
  header: string;
  className?: string;
  render?: (row: T) => ReactNode;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  empty?: ReactNode;
  className?: string;
}

export function DataTable<T>({ columns, rows, empty, className }: DataTableProps<T>) {
  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full border-collapse text-base">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={cn(
                  "border-b border-gray-200 px-4 py-2 text-left text-sm font-semibold uppercase text-gray-500",
                  col.className,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="p-4 text-center">
                {empty ?? <span className="text-gray-500">No rows</span>}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr
                key={i}
                className="border-t border-gray-200 last:border-0"
              >
                {columns.map((col) => (
                  <td
                    key={String(col.key)}
                    className="px-4 py-2 align-middle text-gray-900"
                  >
                    {col.render
                      ? col.render(row)
                      : ((row as Record<string, unknown>)[String(col.key)] as ReactNode)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
