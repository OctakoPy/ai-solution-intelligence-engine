import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { OutcomeFeedback } from "@/components/ui/outcome-feedback";

const { recordOutcome } = vi.hoisted(() => ({ recordOutcome: vi.fn() }));
vi.mock("@/lib/api", () => ({ recordOutcome }));

describe("OutcomeFeedback", () => {
  it("renders the confirmation question with yes/no actions", () => {
    render(<OutcomeFeedback entryId="TIC-1001" />);
    expect(screen.getByText("Did this work?")).toBeTruthy();
    expect(screen.getByTitle(/rank it higher/)).toBeTruthy();
    expect(screen.getByTitle(/rank it lower/)).toBeTruthy();
  });

  it("records a confirmed outcome and shows the learned readout", async () => {
    recordOutcome.mockResolvedValue({
      recorded: true,
      entry_id: "TIC-1001",
      success: true,
      worked_count: [5, 5],
      total_outcomes: 1,
    });
    render(<OutcomeFeedback entryId="TIC-1001" />);
    fireEvent.click(screen.getByText("Yes"));
    await waitFor(() =>
      expect(screen.getByText(/Confirmed worked/)).toBeTruthy(),
    );
    expect(recordOutcome).toHaveBeenCalledWith(
      "TIC-1001",
      true,
      "confirmed from UI",
    );
    expect(screen.getByText(/1 outcome/)).toBeTruthy();
  });

  it("records a failure and shows the failed readout", async () => {
    recordOutcome.mockResolvedValue({
      recorded: true,
      entry_id: "TIC-1002",
      success: false,
      worked_count: [3, 5],
      total_outcomes: 2,
    });
    render(<OutcomeFeedback entryId="TIC-1002" />);
    fireEvent.click(screen.getByText("No"));
    await waitFor(() =>
      expect(screen.getByText(/Marked failed/)).toBeTruthy(),
    );
  });

  it("returns to the buttons when recording fails", async () => {
    recordOutcome.mockRejectedValue(new Error("HTTP 500: boom"));
    render(<OutcomeFeedback entryId="TIC-1003" />);
    fireEvent.click(screen.getByText("Yes"));
    await waitFor(() =>
      expect(screen.getByText("Did this work?")).toBeTruthy(),
    );
  });
});
