import type {
  IngestResponse,
  NextBestAction,
  OutcomeResponse,
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

/** Ingestion always runs the whole corpus; there is no size to choose. */
export const ingest = () => api<IngestResponse>("/api/ingest", { method: "POST" });

export const fetchViews = () => api<View[]>("/api/pipeline/views");

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
  api<{ results: RetrievedSolution[]; next_best_action: NextBestAction | null }>("/api/search", {
    method: "POST",
    body: JSON.stringify({
      query: args.query,
      top_k: args.top_k ?? 5,
      ...(args.context
        ? {
            context: Object.fromEntries(Object.entries(args.context).filter(([_, v]) => v?.trim())),
          }
        : {}),
    }),
  });

interface ChatApiResponse {
  turns: Array<{ role: string; text: string; timestamp: string | null }>;
  candidates: RetrievedSolution[];
  next_best_action: NextBestAction | null;
}

export const chatStart = (query: string, session_id = "default") =>
  api<ChatApiResponse>("/api/chat/start", {
    method: "POST",
    body: JSON.stringify({ query, session_id }),
  });

export const chatRespond = (session_id: string, message: string) =>
  api<ChatApiResponse>("/api/chat/respond", {
    method: "POST",
    body: JSON.stringify({ session_id, message }),
  });

export const fetchOverview = () => api<OverviewResponse>("/api/analytics/overview");

export const recordOutcome = (entry_id: string, success: boolean, note = "") =>
  api<OutcomeResponse>("/api/outcomes", {
    method: "POST",
    body: JSON.stringify({ entry_id, success, note }),
  });
