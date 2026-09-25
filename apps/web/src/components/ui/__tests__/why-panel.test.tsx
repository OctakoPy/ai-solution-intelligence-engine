import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WhyPanel } from "@/components/ui/why-panel";
import { describe, it, expect } from "vitest";
import type { RetrievedSolution } from "@/lib/types";

const baseSolution: RetrievedSolution = {
  id: "TIC-1001",
  title: "SAP FI report access denied",
  source: "Ticketing System",
  category: "sap_authorization",
  score: 0.82,
  confidence: 0.82,
  description: "User cannot open FI reports.",
  resolution: "Assign role Z_FI_REPORT_DISPLAY.",
  date: "2026-08-01",
  worked: 8,
  attempted: 8,
  signal_breakdown: {
    semantic: 0.2,
    success: 0.2,
    error_code: 0.15,
  },
  evidence: [
    {
      id: "TIC-1001",
      title: "SAP FI report access denied",
      source: "Ticketing System",
      date: "2026-08-01",
      worked: 8,
      attempted: 8,
    },
    {
      id: "SAP-0001",
      title: "Missing Z_FI_REPORT_DISPLAY role",
      source: "SAP System",
      date: "2026-07-15",
      worked: 5,
      attempted: 6,
    },
  ],
  caveats: ["Unverified record: no linked recurrence."],
};

describe("WhyPanel", () => {
  it("leads with plain-language reasons and keeps the numbers behind a toggle", async () => {
    render(<WhyPanel solution={baseSolution} />);
    expect(screen.getByText("The description reads like your question")).toBeTruthy();
    expect(
      screen.getByText("It has worked every time it was tried (8 of 8)"),
    ).toBeTruthy();
    expect(screen.queryByText("Text similarity")).toBeNull();

    await userEvent.click(screen.getByRole("button", { name: "Show scoring detail" }));

    expect(screen.getByText("Text similarity")).toBeTruthy();
    expect(screen.getByText("Historical success")).toBeTruthy();
    expect(screen.getByText("Error-code match")).toBeTruthy();
    expect(screen.getAllByText("+0.20")).toHaveLength(2);
    expect(screen.getByText("+0.15")).toBeTruthy();
  });

  it("hides zero-contribution signals", () => {
    render(<WhyPanel solution={baseSolution} />);
    expect(screen.queryByText("Recency")).toBeNull();
    expect(screen.queryByText("Consultant feedback")).toBeNull();
  });

  it("shows prior success with percentage", () => {
    render(<WhyPanel solution={baseSolution} />);
    expect(screen.getByText("Worked 8 of 8 times (100%)")).toBeTruthy();
  });

  it("shows unknown history when the record was never attempted", () => {
    const never = { ...baseSolution, worked: 0, attempted: 0 };
    render(<WhyPanel solution={never} />);
    expect(
      screen.getByText("No confirmed outcomes yet — history unknown."),
    ).toBeTruthy();
  });

  it("lists supporting evidence records", () => {
    render(<WhyPanel solution={baseSolution} />);
    expect(screen.getByText("TIC-1001")).toBeTruthy();
    expect(screen.getByText("SAP-0001")).toBeTruthy();
    expect(screen.getByText(/6 worked/)).toBeTruthy();
  });

  it("renders caveats", () => {
    render(<WhyPanel solution={baseSolution} />);
    expect(
      screen.getByText("Unverified record: no linked recurrence."),
    ).toBeTruthy();
  });

  it("renders a neutral note when no signals contributed", () => {
    const empty = {
      ...baseSolution,
      signal_breakdown: {},
      worked: 0,
      attempted: 0,
      evidence: [],
    };
    render(<WhyPanel solution={empty} />);
    expect(screen.getByText("No strong signals — this is a weak match")).toBeTruthy();
  });
});
