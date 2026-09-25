import { test, expect, type Page } from "@playwright/test";

/**
 * Recorded demo walkthrough.
 *
 * A single continuous take through the verified beats, so the resulting video
 * is one file rather than a folder of fragments. Every query here is copied
 * from the checked-in demo scripts, so the video cannot drift from the
 * documented behaviour:
 *
 *   docs/tutorials/demo-find-script.md
 *   docs/tutorials/demo-conversations.md
 *
 * Run with:  just web-demo-video
 * Skipped by the normal e2e suite (see the tagIgnore below).
 */

/** Pause long enough for a viewer to read the screen. */
const beat = (page: Page, ms = 2200) => page.waitForTimeout(ms);

async function sendChat(page: Page, text: string) {
  await page.fill('input[placeholder="Ask a follow-up question..."]', text);
  await page.getByRole("button", { name: "Send message" }).click();
  await beat(page, 3200);
}

test.describe("ResolveIQ demo walkthrough", () => {
  test.skip(({ browserName }) => browserName !== "chromium", "recorded for chromium only");

  test("records the full product story", async ({ page }) => {
    test.slow();

    // ---- 1. Overview: the learning loop is already populated --------------
    // The dataset selector defaults to the small set; the demo needs the full
    // one, which is what Overview and Pipeline report on.
    await page.goto("http://localhost:5179/overview");
    const dataset = page.getByRole("combobox").first();
    await dataset.selectOption({ label: "Full (76)" });
    await expect(page.getByText("Processed Records")).toBeVisible({
      timeout: 60000,
    });
    await expect(page.getByText("Resolution Memory")).toBeVisible();
    await beat(page, 4000);

    // ---- 2. Find: the context trap ---------------------------------------
    await page.goto("http://localhost:5179/find");

    // Find cards show the record title, not its id.
    const goodsReceipt = page.getByRole("heading", {
      name: /goods receipt posting error - account determination not found/i,
    });
    const uatReceipt = page.getByRole("heading", {
      name: /M8149 goods receipt posting error in UAT sandbox/i,
    });

    const search = page.getByPlaceholder("email not syncing on mobile");
    await search.fill("goods receipt posting error account determination not found");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(goodsReceipt).toBeVisible({ timeout: 30000 });
    await beat(page, 3000);

    // Add the structured detail: three green badges light up.
    await page.getByRole("button", { name: "Incident details (optional)" }).click();
    await page.getByLabel("Error code").fill("M8149");
    await page.getByLabel("System / module").fill("SAP MM");
    await page.getByLabel("Environment").fill("PROD");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(goodsReceipt).toBeVisible();
    // The context resolved to a matching ticket, so there is nothing left to
    // ask for: the hedge must not appear here.
    await expect(page.getByText(/Not confident enough/)).toHaveCount(0);
    await beat(page, 3500);

    // Change one field: a different root cause takes over.
    await page.getByLabel("Environment").fill("UAT");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(uatReceipt).toBeVisible({ timeout: 30000 });
    await beat(page, 4000);

    // ---- 3. Find: one English question, three languages -----------------
    // Clear the incident detail first: the M8149 context would otherwise
    // force this query to the goods-receipt records.
    await page.getByRole("button", { name: "Clear" }).click();
    await search.fill("user cannot access financial reports in sap, authorization error");
    await page.getByRole("button", { name: "Search" }).click();
    const chinese = page.getByRole("heading", { name: "用户无法访问SAP中的FI财务报告" });
    await expect(chinese).toBeVisible({ timeout: 30000 });
    await beat(page, 3500);

    // Open the Chinese card and translate it to English.
    await chinese
      .locator("xpath=ancestor::div[contains(@class,'rounded-xl')]")
      .getByRole("button", { name: "View Details" })
      .click();
    await page.getByRole("button", { name: "Translate to English" }).click();
    await expect(page.getByText("User cannot access FI financial reports in SAP")).toBeVisible();
    await beat(page, 4000);

    // ---- 4. Chat: a plain question, answered ------------------------------
    await page.goto("http://localhost:5179/chat");
    await sendChat(page, "I forgot my password and cannot log in to my computer");
    await expect(page.getByText(/worked 45 of 45/).first()).toBeVisible({
      timeout: 30000,
    });
    await beat(page, 3000);

    // ---- 5. Chat: too vague, so it asks ----------------------------------
    // Each beat starts a new chat. A session re-ranks against its opening
    // question, so asking about something else mid-thread would answer the
    // first question instead of the latest one.
    await page.getByRole("button", { name: "New chat" }).click();
    await sendChat(page, "finance user cannot open the report");
    await expect(page.getByText(/Not confident enough/).first()).toBeVisible({
      timeout: 30000,
    });
    // A hedged answer must not present ticket numbers or a success count as if
    // they were evidence for a recommendation that was not made.
    await expect(page.getByRole("button", { name: /Show sources/ })).toHaveCount(0);
    await expect(page.getByText(/worked \d+\/\d+/)).toHaveCount(0);
    await beat(page, 3000);

    // Supplying the detail makes it commit.
    await sendChat(page, "error code S_RS_COMP, module SAP FICO, environment PROD");
    await expect(page.getByText(/worked 8 of 8/).first()).toBeVisible({ timeout: 30000 });
    await beat(page, 3500);

    // ---- 6. Chat: the first fix failed, so it finds another --------------
    // New chat again: a new topic in the same thread would still be ranked
    // against the opening question.
    await page.getByRole("button", { name: "New chat" }).click();
    await sendChat(page, "my email is not arriving");
    await beat(page, 2500);
    await sendChat(page, "that did not work, still nothing");
    await expect(page.getByText(/Ruling that out/).first()).toBeVisible({
      timeout: 30000,
    });
    await expect(page.getByText(/Outlook not syncing new emails/).first()).toBeVisible();
    await beat(page, 4000);

    // ---- 7. Chat: nothing relevant, so it declines -----------------------
    await page.getByRole("button", { name: "New chat" }).click();
    await sendChat(page, "i ran out of milk in my house");
    await expect(page.getByText(/Nothing in the knowledge base matches/).first()).toBeVisible({
      timeout: 30000,
    });
    await expect(page.getByRole("button", { name: /Show sources/ })).toHaveCount(0);
    await beat(page, 4000);
  });
});
