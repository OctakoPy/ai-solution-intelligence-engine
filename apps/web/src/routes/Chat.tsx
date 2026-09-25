import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Bot, Trash2, ChevronDown } from "lucide-react";
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

const BOLD = /\*\*([^*]+)\*\*/g;

function renderInline(text: string, keyPrefix: string) {
  const nodes: React.ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;
  BOLD.lastIndex = 0;
  while ((match = BOLD.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    nodes.push(
      <strong key={`${keyPrefix}-b${match.index}`} className="font-semibold text-gray-900">
        {match[1]}
      </strong>,
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function showEvidence(turn: DisplayTurn): boolean {
  return turn.nextAction === null && !!turn.candidates && turn.candidates.length > 0;
}

function AssistantReply({ text }: { text: string }) {
  const paragraphs = text.split(/\n{2,}/);
  return (
    <div className="space-y-2 leading-relaxed">
      {paragraphs.map((paragraph, i) => (
        <p key={i}>
          {paragraph.split("\n").map((line, j, lines) => (
            <span key={j}>
              {renderInline(line, `${i}-${j}`)}
              {j < lines.length - 1 && <br />}
            </span>
          ))}
        </p>
      ))}
    </div>
  );
}

const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const SESSION_ID = "default";

export default function Chat() {
  const [turns, setTurns] = useState<DisplayTurn[]>([]);
  const [input, setInput] = useState("");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [showSources, setShowSources] = useState<Set<number>>(new Set());

  const toggleExpand = (id: string) =>
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const toggleSources = (turnIndex: number) =>
    setShowSources((prev) => {
      const next = new Set(prev);
      if (next.has(turnIndex)) next.delete(turnIndex);
      else next.add(turnIndex);
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
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-3">
      <PageHeader
        title="Chat with ResolveIQ"
        subtitle="Ask questions in natural language. Get answers with sourced solutions."
      />

      <div className="flex min-h-[24rem] flex-1 flex-col gap-3">
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
                <div className="mt-1 text-right text-sm text-gray-500">{turn.timestamp}</div>
              </div>
            </div>
          ) : (
            <div key={i} className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200">
                <Bot className="h-4 w-4 text-gray-500" />
              </div>
              <div className="min-w-0 flex-1 rounded-xl border border-gray-200 bg-white p-4 text-base">
                <AssistantReply text={turn.text} />
                {turn.nextAction && (
                  <NextBestActionBanner action={turn.nextAction} className="mt-3" />
                )}
                {showEvidence(turn) && turn.candidates && (
                  <div className="mt-4 border-t border-gray-100 pt-3">
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      {turn.candidates.slice(0, 3).map((c) => (
                        <span key={c.id} className="rounded-md bg-gray-50 px-2 py-1 text-gray-600">
                          <span className="font-medium text-gray-800">{c.id}</span>
                          <span className="mx-1 text-gray-300">·</span>
                          worked {c.worked}/{c.attempted}
                          <span className="ml-1.5 inline-flex align-middle">
                            <LanguageBadge language={c.language} />
                          </span>
                        </span>
                      ))}
                      <button
                        type="button"
                        onClick={() => toggleSources(i)}
                        className="ml-auto inline-flex items-center gap-1 rounded-md px-2 py-1 font-medium text-blue-700 hover:bg-blue-50"
                      >
                        {showSources.has(i) ? "Hide" : "Show"} sources ({turn.candidates.length})
                        <ChevronDown
                          className={`h-3.5 w-3.5 transition-transform ${
                            showSources.has(i) ? "rotate-180" : ""
                          }`}
                        />
                      </button>
                    </div>
                    {showSources.has(i) && (
                      <div className="mt-3 space-y-2">
                        {turn.candidates.map((c) => {
                          const isExpanded = expandedIds.has(c.id);
                          return (
                            <div key={c.id} className="rounded-lg border border-gray-200 p-3">
                              <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                  <div className="flex items-center gap-2">
                                    <p className="truncate text-sm font-semibold text-gray-900">
                                      {c.title}
                                    </p>
                                    <LanguageBadge language={c.language} />
                                  </div>
                                  <p className="mt-0.5 text-sm text-gray-500">
                                    {c.source} – {c.date} · worked {c.worked}/{c.attempted}
                                  </p>
                                </div>
                                <button
                                  type="button"
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
                    <div className="mt-3 flex items-center gap-2">
                      <OutcomeFeedback entryId={turn.candidates[0].id} />
                      <span className="ml-auto text-sm text-gray-400">{turn.timestamp}</span>
                    </div>
                  </div>
                )}
                {!showEvidence(turn) && (
                  <div className="mt-2 text-right text-sm text-gray-400">{turn.timestamp}</div>
                )}
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

      <div className="flex flex-wrap gap-2">
        {turns.length === 0 ? (
          <button
            type="button"
            onClick={() =>
              send(
                "the nightly sap batch job for inventory reconciliation keeps short dumping. how do i fix it?",
              )
            }
            className="rounded-full border border-blue-600 bg-white px-3 py-1 text-sm font-medium text-blue-600 hover:bg-blue-50"
          >
            Nightly SAP batch job keeps short dumping
          </button>
        ) : (
          <>
            <button
              type="button"
              onClick={() => send("Which environment is this in - UAT or production?")}
              className="rounded-full border border-gray-300 bg-white px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Which environment is this in - UAT or production?
            </button>
            <button
              type="button"
              onClick={() => send("Still not working, what next?")}
              className="rounded-full border border-gray-300 bg-white px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Still not working, what next?
            </button>
            <button
              type="button"
              onClick={() => setTurns([])}
              className="ml-auto inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium text-gray-500 hover:bg-gray-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              New chat
            </button>
          </>
        )}
      </div>
    </div>
  );
}
