import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";
import { ChevronDown } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/ui/page-header";
import { search } from "@/lib/api";
import type { RetrievedSolution } from "@/lib/types";
import { StatusBadge } from "@/components/ui/status-badge";
import { LanguageBadge } from "@/components/ui/language-badge";
import { SolutionDetails } from "@/components/ui/solution-details";

export default function FindSolution() {
  const [query, setQuery] = useState("email not syncing on mobile");
  const [results, setResults] = useState<RetrievedSolution[]>([]);
  const [searched, setSearched] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const searchMut = useMutation({
    mutationFn: (q: string) => search({ query: q, top_k: 5 }),
    onSuccess: (res) => {
      setResults(res.results);
      setSearched(true);
    },
  });

  const handleSearch = (q: string) => {
    setQuery(q);
    searchMut.mutate(q);
  };

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

        <h2 className="mt-6 text-xl font-semibold text-gray-900">
          Top Matches
        </h2>

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
                  <span className="rounded-full bg-green-600 px-3 py-1 text-sm font-bold text-white">
                    {pct}%
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {r.title}
                      </h3>
                      <LanguageBadge language={r.language} />
                    </div>
                    <p className="text-base text-gray-500 mt-0.5">
                      {r.description}
                    </p>
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
                <div className="mt-2 flex items-center gap-2 text-sm">
                  <StatusBadge state="added" />
                  <span className="text-gray-500">
                    Confidence: {Math.round(r.confidence * 100)}%
                  </span>
                </div>
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
