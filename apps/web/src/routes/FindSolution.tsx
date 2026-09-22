import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";
import { ChevronDown } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/ui/page-header";
import { search } from "@/lib/api";
import type { RetrievedSolution, SearchContext } from "@/lib/types";
import { LanguageBadge } from "@/components/ui/language-badge";
import { SignalBadge } from "@/components/ui/signal-badge";
import { SolutionDetails } from "@/components/ui/solution-details";

interface SearchMutationArgs {
  query: string;
  context?: SearchContext;
}

export default function FindSolution() {
  const [query, setQuery] = useState("email not syncing on mobile");
  const [errorCode, setErrorCode] = useState("");
  const [module, setModule] = useState("");
  const [environment, setEnvironment] = useState("");
  const [showIncident, setShowIncident] = useState(false);
  const [activeContext, setActiveContext] = useState<SearchContext | null>(null);
  const [results, setResults] = useState<RetrievedSolution[]>([]);
  const [searched, setSearched] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const searchMut = useMutation({
    mutationFn: ({ query, context }: SearchMutationArgs) =>
      search({ query, top_k: 5, context }),
    onSuccess: (res) => {
      setResults(res.results);
      setSearched(true);
    },
  });

  const buildContext = (): SearchContext | undefined => {
    const ctx: SearchContext = {};
    if (errorCode.trim()) ctx.error_code = errorCode.trim();
    if (module.trim()) ctx.module = module.trim();
    if (environment.trim()) ctx.environment = environment.trim();
    return Object.keys(ctx).length > 0 ? ctx : undefined;
  };

  const handleSearch = (q: string) => {
    setQuery(q);
    const ctx = buildContext();
    setActiveContext(ctx ?? null);
    searchMut.mutate({ query: q, context: ctx });
  };

  const contextIsActive = Object.values(activeContext ?? {}).some(Boolean);

  return (
    <div>
      <PageHeader
        title="Find a Solution"
        subtitle="Search and discover solutions from the knowledge base."
      />
      <div className="flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch(query)}
            placeholder="email not syncing on mobile"
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-10 pr-4 text-base text-gray-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-50"
          />
        </div>
        <button
          onClick={() => handleSearch(query)}
          className="rounded-lg bg-blue-600 px-5 py-2 text-base font-semibold text-white hover:bg-blue-700"
        >
          Search
        </button>
      </div>

      <button
        onClick={() => setShowIncident((s) => !s)}
        className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-blue-600 hover:underline"
      >
        <ChevronDown
          className={`h-4 w-4 transition-transform ${showIncident ? "rotate-180" : ""}`}
        />
        Incident details (optional)
      </button>

      {showIncident && (
        <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-3">
          <div className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-1 text-xs font-medium text-gray-600">
              Error code
              <input
                type="text"
                value={errorCode}
                onChange={(e) => setErrorCode(e.target.value)}
                placeholder="M8149, S_RS_COMP"
                className="rounded-md border border-gray-200 bg-white px-2 py-1.5 text-sm text-gray-900 outline-none focus:border-blue-600"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-gray-600">
              System / module
              <input
                type="text"
                value={module}
                onChange={(e) => setModule(e.target.value)}
                placeholder="SAP MM, VPN"
                className="rounded-md border border-gray-200 bg-white px-2 py-1.5 text-sm text-gray-900 outline-none focus:border-blue-600"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-gray-600">
              Environment
              <input
                type="text"
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                placeholder="PROD, UAT"
                className="rounded-md border border-gray-200 bg-white px-2 py-1.5 text-sm text-gray-900 outline-none focus:border-blue-600"
              />
            </label>
            <button
              onClick={() => {
                setErrorCode("");
                setModule("");
                setEnvironment("");
              }}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              Clear
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Match these details against the knowledge base for an exact
            recommendation. Leave blank to search by text only.
          </p>
        </div>
      )}

      {contextIsActive && (
        <p className="mt-2 text-sm text-gray-600">
          Searching with: {activeContext!.error_code && <span className="font-medium">error {activeContext!.error_code} · </span>}
          {activeContext!.module && <span className="font-medium">{activeContext!.module} · </span>}
          {activeContext!.environment && <span className="font-medium">{activeContext!.environment}</span>}
        </p>
      )}

      <h2 className="mt-6 text-xl font-semibold text-gray-900">Top Matches</h2>

      <div className="mt-3 space-y-3">
        {searchMut.isPending && (
          <div className="text-base text-gray-500">Searching...</div>
        )}

        {searched && results.length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-4 text-base text-gray-500">
            No results.
          </div>
        )}

        {!searched && (
          <div className="rounded-lg border border-gray-200 bg-white p-4 text-base text-gray-500">
            Run a search to see matching solutions.
          </div>
        )}

        {results.map((r) => {
          const pct = Math.round(r.score * 100);
          const isExpanded = expandedIds.has(r.id);
          const toggleExpand = () =>
            setExpandedIds((prev) => {
              const next = new Set(prev);
              if (next.has(r.id)) next.delete(r.id);
              else next.add(r.id);
              return next;
            });
          return (
            <div
              key={r.id}
              className="rounded-xl border border-gray-200 bg-white p-4 shadow-card"
            >
              <div className="flex items-start gap-3">
                <span
                  className="rounded-full bg-green-600 px-3 py-1 text-sm font-bold text-white"
                  title="Outcome-aware score (similarity + context + history)"
                >
                  {pct}%
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {r.title}
                    </h3>
                    <LanguageBadge language={r.language} />
                  </div>
                  <p className="text-base text-gray-500 mt-0.5">{r.description}</p>
                  <p className="mt-2 text-sm text-gray-500">
                    Source: {r.source} · {r.date} · Category: {r.category}
                  </p>
                  {isExpanded && <SolutionDetails solution={r} />}
                </div>
                <button
                  onClick={toggleExpand}
                  className="rounded-md border border-blue-600 px-3 py-1 text-sm font-semibold text-blue-600 hover:bg-blue-50 flex items-center gap-1"
                >
                  {isExpanded ? (
                    <>
                      <ChevronDown className="h-4 w-4 rotate-180 transition-transform" />
                      Hide Details
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4 transition-transform" />
                      View Details
                    </>
                  )}
                </button>
              </div>
              {r.signals && r.signals.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {r.signals.map((s) => (
                    <SignalBadge key={s} signal={s} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {searched && results.length > 0 && (
        <div className="mt-4 text-base text-gray-500">
          Can't find what you need?{" "}
          <button
            onClick={() => navigate("/chat")}
            className="font-medium text-blue-600 hover:underline"
          >
            Ask the Engine
          </button>
        </div>
      )}
    </div>
  );
}