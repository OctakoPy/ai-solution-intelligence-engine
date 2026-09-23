import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, ThumbsUp, ThumbsDown, Share2, Bot, Trash2, ChevronDown } from "lucide-react";
import { chatRespond, chatStart } from "@/lib/api";
import type { NextBestAction, RetrievedSolution } from "@/lib/types";
import { PageHeader } from "@/components/ui/page-header";
import { NextBestActionBanner } from "@/components/ui/next-best-action-banner";
import { LanguageBadge } from "@/components/ui/language-badge";
import { OutcomeFeedback } from "@/components/ui/outcome-feedback";
import { SolutionDetails } from "@/components/ui/solution-details";

interface DisplayTurn {
  role: "user" | "assistant";
  text: string;
  timestamp: string | null;
  candidates?: RetrievedSolution[];
  nextAction?: NextBestAction | null;
}

const FOLLOW_UPS = [
  "How to clear cache in Outlook mobile?",
  "Re-authentication steps",
  "Still not working, what next?",
];

const now = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const SESSION_ID = "default";

export default function Chat() {
  const [turns, setTurns] = useState<DisplayTurn[]>([]);
  const [input, setInput] = useState("");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) =>
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const start = useMutation({
    mutationFn: (q: string) => chatStart(q, SESSION_ID),
    onSuccess: (data, q) => {
      setTurns((prev) => [
        ...prev,
        { role: "user", text: q, timestamp: now() },
        {
          role: "assistant",
          text: data.turns[1]?.text ?? "",
          timestamp: now(),
          candidates: data.candidates,
          nextAction: data.next_best_action ?? null,
        },
      ]);
    },
  });

  const respond = useMutation({
    mutationFn: (m: string) => chatRespond(SESSION_ID, m),
    onSuccess: (data, m) => {
      setTurns((prev) => [
        ...prev,
        { role: "user", text: m, timestamp: now() },
        {
          role: "assistant",
          text: data.turns[data.turns.length - 1]?.text ?? "",
          timestamp: now(),
          candidates: data.candidates,
          nextAction: data.next_best_action ?? null,
        },
      ]);
    },
  });

  const send = (text: string) => {
    const t = text.trim();
    if (!t) return;
    setInput("");
    if (turns.length === 0) start.mutate(t);
    else respond.mutate(t);
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
      <div className="flex flex-col gap-3 lg:col-span-3">
        <PageHeader
          title="Chat with Intelligence Engine"
          subtitle="Ask questions in natural language. Get answers with sourced solutions."
        />

        <div className="flex flex-1 flex-col gap-3 overflow-y-auto pb-4">
          {turns.length === 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 text-base text-gray-500">
              Ask a question to start the conversation.
            </div>
          )}

          {turns.map((turn, i) =>
            turn.role === "user" ? (
              <div key={i} className="flex justify-end">
                <div className="max-w-[80%] rounded-xl bg-blue-50 px-4 py-2 text-base text-gray-900">
                  {turn.text}
                  <div className="mt-1 text-right text-sm text-gray-500">
                    {turn.timestamp}
                  </div>
                </div>
              </div>
            ) : (
              <div key={i} className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200">
                  <Bot className="h-4 w-4 text-gray-500" />
                </div>
                <div className="max-w-[80%] rounded-xl border border-gray-200 bg-white p-4 text-base">
                  <div className="whitespace-pre-line">{turn.text}</div>
                  {turn.nextAction && (
                    <NextBestActionBanner
                      action={turn.nextAction}
                      className="mt-3"
                    />
                  )}
                  {turn.candidates && turn.candidates.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <h4 className="text-sm font-semibold text-gray-500">
                        Sources
                      </h4>
                      {turn.candidates.map((c) => {
                        const isExpanded = expandedIds.has(c.id);
                        return (
                          <div
                            key={c.id}
                            className="rounded-lg border border-gray-200 p-3"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                  <p className="truncate text-sm font-semibold text-gray-900">
                                    {c.title}
                                  </p>
                                  <LanguageBadge language={c.language} />
                                </div>
                                <p className="mt-0.5 text-sm text-gray-500">
                                  {c.source} – {c.date} (
                                  {Math.round(c.score * 100)}%)
                                </p>
                              </div>
                              <button
                                onClick={() => toggleExpand(c.id)}
                                className="flex shrink-0 items-center gap-1 rounded-md border border-blue-600 px-2 py-0.5 text-sm font-semibold text-blue-600 hover:bg-blue-50"
                              >
                                <ChevronDown
                                  className={`h-4 w-4 transition-transform ${
                                    isExpanded ? "rotate-180" : ""
                                  }`}
                                />
                                {isExpanded ? "Hide" : "View"}
                              </button>
                            </div>
                            {isExpanded && <SolutionDetails solution={c} />}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  <div className="mt-3 flex items-center gap-2 text-gray-500">
                    {turn.candidates && turn.candidates.length > 0 ? (
                      <OutcomeFeedback entryId={turn.candidates[0].id} />
                    ) : (
                      <>
                        <ThumbsUp className="h-3.5 w-3.5" />
                        <ThumbsDown className="h-3.5 w-3.5" />
                      </>
                    )}
                    <Share2 className="h-3.5 w-3.5" />
                    <span className="ml-auto text-sm">{turn.timestamp}</span>
                  </div>
                </div>
              </div>
            ),
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder="Ask a follow-up question..."
            className="flex-1 rounded-lg border border-gray-200 bg-white px-4 py-2 text-base outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-50"
          />
          <button
            onClick={() => send(input)}
            aria-label="Send message"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-2 flex flex-wrap gap-2">
          {FOLLOW_UPS.map((chip) => (
            <button
              key={chip}
              onClick={() => send(chip)}
              className="rounded-full border border-blue-600 bg-white px-3 py-1 text-sm font-medium text-blue-600 hover:bg-blue-50"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      <aside>
        <PageHeader title="Conversation History" />
        <button
          onClick={() => setTurns([])}
          className="mb-3 flex w-full items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-base font-semibold text-gray-900 hover:bg-gray-50"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Clear History
        </button>
        <div className="space-y-2">
          {turns
            .filter((t) => t.role === "user")
            .slice()
            .reverse()
            .map((t, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-200 bg-white p-3"
              >
                <div className="line-clamp-2 text-base font-semibold text-gray-900">
                  {t.text}
                </div>
                <div className="mt-1 text-sm text-gray-500">
                  {t.timestamp}
                </div>
              </div>
            ))}
          {turns.filter((t) => t.role === "user").length === 0 && (
            <div className="text-base text-gray-500">No conversations yet.</div>
          )}
        </div>
      </aside>
    </div>
  );
}
