import { render, screen } from "@testing-library/react";
import { LanguageBadge } from "@/components/ui/language-badge";
import { describe, it, expect } from "vitest";

describe("LanguageBadge", () => {
  it("renders nothing for English", () => {
    const { container } = render(<LanguageBadge language="en" />);
    expect(container.innerHTML).toBe("");
  });

  it("renders Bahasa Malaysia badge", () => {
    render(<LanguageBadge language="bm" />);
    expect(screen.getByText("BM")).toBeTruthy();
    expect(screen.getByTitle("Bahasa Malaysia")).toBeTruthy();
  });

  it("renders Chinese badge", () => {
    render(<LanguageBadge language="zh" />);
    expect(screen.getByText("中文")).toBeTruthy();
    expect(screen.getByTitle("Chinese")).toBeTruthy();
  });

  it("renders nothing when language is undefined", () => {
    const { container } = render(<LanguageBadge />);
    expect(container.innerHTML).toBe("");
  });
});
