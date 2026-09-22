import type {
  IngestResponse,
  OverviewResponse,
  RetrievedSolution,
  View,
} from "@/lib/types";

const baseURL =
  (import.meta.env?.VITE_API_BASE as string | undefined) ??
  ((import.meta.env?.PROD ? "" : "http://localhost:8004") as string);

async function api<T>(input: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseURL}${input}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const ingest = (max_entries: number) =>
  api<IngestResponse>("/api/ingest", {
    method: "POST",
    body: JSON.stringify({ max_entries }),
  });

export const fetchViews = (max_entries: number) =>
  api<View[]>(`/api/pipeline/views?max_entries=${max_entries}`);

export interface SearchArgs {
  query: string;
  top_k?: number;
  context?: {
    error_code?: string | null;
    module?: string | null;
    environment?: string | null;
  };
}

export const search = (args: SearchArgs) =>
  api<{ results: RetrievedSolution[] }>("/api/search", {
    method: "POST",
    body: JSON.stringify({
      query: args.query,
      top_k: args.top_k ?? 5,
      ...(args.context
        ? {
            context: Object.fromEntries(
              Object.entries(args.context).filter(([_, v]) => v?.trim()),
            ),
          }
        : {}),
    }),
  });

export const chatStart = (query: string, session_id = "default") =>
  api<{ turns: Array<{ role: string; text: string; timestamp: string | null }>; candidates: RetrievedSolution[] }>(
    "/api/chat/start",
    {
      method: "POST",
      body: JSON.stringify({ query, session_id }),
    },
  );

export const chatRespond = (session_id: string, message: string) =>
  api<{ turns: Array<{ role: string; text: string; timestamp: string | null }>; candidates: RetrievedSolution[] }>(
    "/api/chat/respond",
    {
      method: "POST",
      body: JSON.stringify({ session_id, message }),
    },
  );

export const fetchOverview = (max_entries: number) =>
  api<OverviewResponse>(`/api/analytics/overview?max_entries=${max_entries}`);
