import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import type { RetrievedSolution, Signal } from "@/lib/types";

const api = vi.hoisted(() => ({ search: vi.fn() }));

vi.mock("@/lib/api", () => ({ ...api, chatRespond: vi.fn(), chatStart: vi.fn() }));

import FindSolution from "@/routes/FindSolution";

const result = (overrides: Partial<RetrievedSolution> = {}): RetrievedSolution => ({
  id: "TIC-3011",
  title: "SAP MM goods receipt posting error",
  source: "Ticketing System",
  category: "sap_mm",
  score: 0.88,
  confidence: 0.88,
  description: "d",
  resolution: "r",
  date: "2025-03-14",
  worked: 8,
  attempted: 9,
  ...overrides,
});

const askContext = {
  action: "ask_context" as const,
  message: "Not confident enough to recommend a fix.",
  missing_fields: ["error_code"],
  nearest_record_id: "TIC-3011",
  nearest_record_title: "SAP MM goods receipt posting error",
};

function wrap(node: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{node}</MemoryRouter>
    </QueryClientProvider>,
  );
}

async function runSearch() {
  await userEvent.click(screen.getByRole("button", { name: "Search" }));
}

beforeEach(() => {
  api.search.mockReset();
});

describe("FindSolution next-best-action banner", () => {
  it("hides the ask-for-context banner when the supplied context matches the top record", async () => {
    api.search.mockResolvedValue({
      results: [result({ signals: ["environment"] as Signal[] })],
      next_best_action: askContext,
    });

    wrap(<FindSolution />);
    await userEvent.click(screen.getByRole("button", { name: /Incident details/ }));
    await userEvent.type(screen.getByLabelText("Environment"), "PROD");
    await runSearch();

    await waitFor(() => expect(api.search).toHaveBeenCalled());
    expect(screen.getByText("SAP MM goods receipt posting error")).toBeInTheDocument();
    expect(screen.queryByText(/Not confident enough/)).toBeNull();
  });

  it("keeps the ask-for-context banner when the context does not match the top record", async () => {
    api.search.mockResolvedValue({
      results: [result({ signals: [] as Signal[] })],
      next_best_action: askContext,
    });

    wrap(<FindSolution />);
    await userEvent.click(screen.getByRole("button", { name: /Incident details/ }));
    await userEvent.type(screen.getByLabelText("Environment"), "PROD");
    await runSearch();

    await waitFor(() =>
      expect(screen.getAllByText(/Not confident enough/).length).toBeGreaterThan(0),
    );
  });

  it("keeps the escalate banner and hides look-alike cards", async () => {
    api.search.mockResolvedValue({
      results: [result()],
      next_best_action: {
        ...askContext,
        action: "escalate_sme" as const,
        message: "Nothing in the knowledge base matches this.",
      },
    });

    wrap(<FindSolution />);
    await runSearch();

    await waitFor(() =>
      expect(screen.getByText(/Nothing in the knowledge base matches/)).toBeInTheDocument(),
    );
    expect(screen.queryByText("SAP MM goods receipt posting error")).toBeNull();
  });
});
