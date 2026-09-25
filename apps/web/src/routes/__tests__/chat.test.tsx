import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { RetrievedSolution } from "@/lib/types";

const api = vi.hoisted(() => ({
  chatStart: vi.fn(),
  chatRespond: vi.fn(),
}));

vi.mock("@/lib/api", () => api);

import Chat from "@/routes/Chat";

function renderChat() {
  const client = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <Chat />
    </QueryClientProvider>,
  );
}

const candidate = (overrides: Partial<RetrievedSolution> = {}): RetrievedSolution => ({
  id: "TIC-1001",
  title: "User cannot access FI reports in SAP",
  source: "Ticketing System",
  category: "sap_authorization",
  score: 0.9,
  confidence: 0.9,
  description: "d",
  resolution: "r",
  date: "2025-03-14",
  worked: 8,
  attempted: 8,
  ...overrides,
});

async function send(text: string) {
  const user = userEvent.setup();
  await user.type(screen.getByPlaceholderText("Ask a follow-up question..."), text);
  await user.click(screen.getByRole("button", { name: "Send message" }));
}

beforeEach(() => {
  api.chatStart.mockReset();
  api.chatRespond.mockReset();
});

describe("Chat reply rendering", () => {
  it("renders bold markdown as emphasis instead of literal asterisks", async () => {
    api.chatStart.mockResolvedValue({
      turns: [
        { role: "user", text: "q", timestamp: null },
        {
          role: "assistant",
          text: "The best answer is **Password reset**.\n\n**How to fix it**\nUse the portal.",
          timestamp: null,
        },
      ],
      candidates: [candidate()],
      next_best_action: null,
    });

    renderChat();
    await send("q");

    await waitFor(() => expect(screen.getByText("Password reset")).toBeInTheDocument());
    expect(screen.getByText("Password reset").tagName).toBe("STRONG");
    expect(screen.getByText("How to fix it").tagName).toBe("STRONG");
    expect(screen.queryByText(/\*\*/)).toBeNull();
  });

  it("shows ticket evidence when the engine proceeds with a recommendation", async () => {
    api.chatStart.mockResolvedValue({
      turns: [
        { role: "user", text: "q", timestamp: null },
        { role: "assistant", text: "The best answer is **Reset**.", timestamp: null },
      ],
      candidates: [candidate()],
      next_best_action: null,
    });

    renderChat();
    await send("q");

    expect(await screen.findByText("TIC-1001")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Show sources/ })).toBeInTheDocument();
  });

  it("hides ticket evidence when the engine is not confident", async () => {
    api.chatStart.mockResolvedValue({
      turns: [
        { role: "user", text: "q", timestamp: null },
        {
          role: "assistant",
          text: "Not confident enough to recommend a fix.",
          timestamp: null,
        },
      ],
      candidates: [candidate()],
      next_best_action: {
        action: "ask_context",
        message: "Not confident enough to recommend a fix.",
        missing_fields: ["error_code"],
        nearest_record_id: "TIC-1001",
        nearest_record_title: "User cannot access FI reports in SAP",
      },
    });

    renderChat();
    await send("q");

    await waitFor(() =>
      expect(screen.getAllByText(/Not confident enough/).length).toBeGreaterThan(0),
    );
    expect(screen.queryByText("TIC-1001")).toBeNull();
    expect(screen.queryByRole("button", { name: /Show sources/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Yes" })).toBeNull();
    expect(screen.queryByRole("button", { name: "No" })).toBeNull();
  });
});
