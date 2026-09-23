import { test, expect } from "@playwright/test";

export default test.describe.parallel("Navigation smoke", () => {
  test("sidebar navigates between the four routes", async ({ page }) => {
    await page.goto("http://localhost:5179/overview");
    await expect(page).toHaveTitle(/ResolveIQ/);
    const main = page.getByRole("main");

    await page.getByRole("button", { name: "Ingestion Pipeline" }).click();
    await expect(page).toHaveURL(/\/pipeline/);
    await expect(page.getByRole("heading", { name: "Live Tally" })).toBeVisible();

    await page.getByRole("button", { name: "Find a Solution" }).click();
    await expect(page).toHaveURL(/\/find/);
    await expect(main.getByRole("heading", { name: "Find a Solution" })).toBeVisible();

    await page.getByRole("button", { name: "Chat with the Engine" }).click();
    await expect(page).toHaveURL(/\/chat/);
    await expect(
      main.getByRole("heading", { name: "Chat with ResolveIQ" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Overview" }).click();
    await expect(page).toHaveURL(/\/overview/);
  });

  test("overview renders stat cards and donut", async ({ page }) => {
    await page.goto("http://localhost:5179/overview");
    await expect(page.getByText("Processed Records")).toBeVisible({ timeout: 30000 });
    await expect(page.getByText("Ingestion Summary (Today)")).toBeVisible();
  });

  test("pipeline page renders idle state + play button", async ({ page }) => {
    await page.goto("http://localhost:5179/pipeline");
    await expect(page.getByRole("heading", { name: "Live Tally" })).toBeVisible();
    await expect(
      page.locator("main").getByRole("button", { name: "Start" }),
    ).toBeVisible({ timeout: 30000 });
    await page.locator("main").getByRole("button", { name: "Start" }).click();
  });

  test("find page searches and shows results", async ({ page }) => {
    await page.goto("http://localhost:5179/find");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.getByRole("heading", { name: "Top Matches" })).toBeVisible();
  });

  test("chat page sends a message and shows reply", async ({ page }) => {
    await page.goto("http://localhost:5179/chat");
    await page.fill('input[placeholder="Ask a follow-up question..."]', "VPN keeps dropping");
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(
      page.getByText(/This issue is usually caused|Here are the closest matches I could find/),
    ).toBeVisible({ timeout: 30000 });
  });
});
