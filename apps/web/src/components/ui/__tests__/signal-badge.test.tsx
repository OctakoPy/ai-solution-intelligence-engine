import { render, screen } from "@testing-library/react";
import { SignalBadge } from "@/components/ui/signal-badge";
import { describe, it, expect } from "vitest";

describe("SignalBadge", () => {
  it("renders error code match badge", () => {
    render(<SignalBadge signal="error_code" />);
    expect(screen.getByText("Error code match")).toBeTruthy();
  });

  it("renders system match badge", () => {
    render(<SignalBadge signal="module" />);
    expect(screen.getByText("System match")).toBeTruthy();
  });

  it("renders environment match badge", () => {
    render(<SignalBadge signal="environment" />);
    expect(screen.getByText("Environment match")).toBeTruthy();
    expect(screen.getByTitle("Incident detail matched: Environment match")).toBeTruthy();
  });
});