import { test, expect, type APIRequestContext, type Locator, type Page } from "@playwright/test";

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
 * The narration for this take lives in
 * docs/tutorials/demo-narration.srt, timed against this file.
 *
 * Run with:  just web-demo-video
 * Skipped by the normal e2e suite (see the testIgnore below).
 */

/** Pause long enough for a viewer to read the screen. */
const beat = (page: Page, ms = 2200) => page.waitForTimeout(ms);

/**
 * Scroll a target into view with a real wheel gesture.
 *
 * `scrollIntoViewIfNeeded` teleports the viewport, which reads as a jump cut
 * in the recording. A wheel scroll animates, so the viewer can follow where
 * the page went.
 */
async function glideTo(page: Page, target: Locator) {
  await target.scrollIntoViewIfNeeded();
  const box = await target.boundingBox();
  const viewport = page.viewportSize();
  if (!box || !viewport) return;
  // `box.y` is viewport-relative and already on screen, so this centres it.
  const delta = box.y - viewport.height / 2;
  if (Math.abs(delta) > 8) {
    const steps = 6;
    for (let i = 1; i <= steps; i += 1) {
      await page.mouse.wheel(0, Math.round(delta / steps));
      await page.waitForTimeout(45);
    }
  }
  await page.waitForTimeout(250);
}

/** Type like a person: select the old value, then type one character at a time. */
async function typeInto(page: Page, field: Locator, text: string) {
  await glideTo(page, field);
  await field.click();
  // `pressSequentially` appends, so the previous query would otherwise still
  // be sitting in the box and both would be searched at once.
  await field.press("ControlOrMeta+a");
  await field.press("Delete");
  await field.pressSequentially(text, { delay: 42 });
  await page.waitForTimeout(320);
}

/** Hover, settle, then click, so the pointer visibly travels to the target. */
async function pressNatural(page: Page, target: Locator) {
  await glideTo(page, target);
  await target.hover();
  await page.waitForTimeout(220);
  await target.click();
}

async function sendChat(page: Page, text: string) {
  const input = page.getByPlaceholder("Ask a follow-up question...");
  await typeInto(page, input, text);
  await pressNatural(page, page.getByRole("button", { name: "Send message" }));
  await beat(page, 3400);
}

async function runSearch(page: Page, text: string) {
  const input = page.getByPlaceholder("email not syncing on mobile");
  await typeInto(page, input, text);
  await pressNatural(page, page.getByRole("button", { name: "Search" }));
}

/**
 * Block until the backend answers.
 *
 * The web server can be listening before the engine finishes loading
 * embeddings, and the first page would otherwise render "Failed to fetch"
 * and record that on camera. This uses the standalone request fixture rather
 * than `page.request` so no page exists yet: the video starts at the first
 * `goto` instead of opening on a blank screen while the engine builds.
 */
async function waitForBackend(request: APIRequestContext) {
  const deadline = Date.now() + 300_000;
  while (Date.now() < deadline) {
    try {
      const response = await request.get("http://localhost:8004/api/analytics/overview");
      if (response.ok()) return;
    } catch {
      // not listening yet
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error("backend did not become ready in time");
}

test.describe("ResolveIQ demo walkthrough", () => {
  test.skip(({ browserName }) => browserName !== "chromium", "recorded for chromium only");

  test("records the full product story", async ({ page, request }) => {
    test.slow();
    // The walkthrough now types character by character and holds on each
    // answer, so it runs for several minutes by design rather than because
    // something is stuck.
    test.setTimeout(20 * 60 * 1000);

    // ---- 1. Overview: the learning loop is already populated --------------
    // The whole corpus is always loaded, so there is no selector to set.
    await waitForBackend(request);
    await page.goto("http://localhost:5179/overview");
    await beat(page, 1200);
    await expect(page.getByText("Processed Records")).toBeVisible({
      timeout: 60000,
    });
    await expect(page.getByText("Resolution Memory")).toBeVisible();
    await beat(page, 4200);

    // Scroll down to the resolution memory panel: the write-back loop that
    // makes outcomes from real tickets count.
    await glideTo(page, page.getByText("Resolution Memory"));
    await beat(page, 3800);

    // ---- 2. Pipeline: four sources, three checks -------------------------
    await page.goto("http://localhost:5179/pipeline");
    await beat(page, 1400);
    await expect(page.getByRole("heading", { name: "Live Tally" })).toBeVisible({
      timeout: 60000,
    });
    await beat(page, 2000);
    await pressNatural(page, page.locator("main").getByRole("button", { name: "Start" }));
    // Let the animation run long enough to read the tally changing.
    await beat(page, 7000);

    // ---- 3. Find: the context trap ---------------------------------------
    await page.goto("http://localhost:5179/find");
    await beat(page, 1400);

    // Find cards show the record title, not its id.
    const goodsReceipt = page.getByRole("heading", {
      name: /goods receipt posting error - account determination not found/i,
    });
    const uatReceipt = page.getByRole("heading", {
      name: /M8149 goods receipt posting error in UAT sandbox/i,
    });

    await runSearch(page, "goods receipt posting error account determination not found");
    await expect(goodsReceipt).toBeVisible({ timeout: 30000 });
    await beat(page, 3200);

    // Add the structured detail: three green badges light up.
    await pressNatural(page, page.getByRole("button", { name: "Incident details (optional)" }));
    await beat(page, 1200);
    await typeInto(page, page.getByLabel("Error code"), "M8149");
    await typeInto(page, page.getByLabel("System / module"), "SAP MM");
    await typeInto(page, page.getByLabel("Environment"), "PROD");
    await pressNatural(page, page.getByRole("button", { name: "Search" }));
    await expect(goodsReceipt).toBeVisible();
    // The context resolved to a matching ticket, so there is nothing left to
    // ask for: the hedge must not appear here.
    await expect(page.getByText(/Check not satisfied/)).toHaveCount(0);
    await beat(page, 3600);

    // Change one field: a different root cause takes over.
    await typeInto(page, page.getByLabel("Environment"), "UAT");
    await pressNatural(page, page.getByRole("button", { name: "Search" }));
    await expect(uatReceipt).toBeVisible({ timeout: 30000 });
    await beat(page, 4200);

    // ---- 4. Find: one English question, three languages -----------------
    // Clear the incident detail first: the M8149 context would otherwise
    // force this query to the goods-receipt records.
    await pressNatural(page, page.getByRole("button", { name: "Clear" }));
    await beat(page, 800);
    await runSearch(page, "user cannot access financial reports in sap, authorization error");
    const chinese = page.getByRole("heading", {
      name: "用户无法访问SAP中的FI财务报告",
    });
    await expect(chinese).toBeVisible({ timeout: 30000 });
    await glideTo(page, chinese);
    await beat(page, 3800);

    // Open the Chinese card and translate it to English.
    await chinese
      .locator("xpath=ancestor::div[contains(@class,'rounded-xl')]")
      .getByRole("button", { name: "View Details" })
      .click();
    await beat(page, 1800);
    await pressNatural(page, page.getByRole("button", { name: "Translate to English" }));
    await expect(page.getByText("User cannot access FI financial reports in SAP")).toBeVisible();
    await beat(page, 4000);

    // ---- 5. Find: an SAP AMS question, answered ------------------------
    // Clear the context first: the M8149 detail would force the goods-receipt
    // records again.
    await pressNatural(page, page.getByRole("button", { name: "Clear" }));
    await beat(page, 800);
    await runSearch(page, "production order will not create component allocation incomplete");
    await expect(
      page.getByRole("heading", {
        name: /Production order will not create - component allocation incomplete/i,
      }),
    ).toBeVisible({ timeout: 30000 });
    await beat(page, 4200);

    // The same category, a record that has failed before: it declines.
    await runSearch(page, "nightly mrp background job failing after release update");
    await expect(page.getByText(/Check not satisfied/).first()).toBeVisible({
      timeout: 30000,
    });
    await beat(page, 3800);

    // ---- 6. Find: the scoring detail is there, but opt-in ---------------
    const whyButton = page.getByRole("button", { name: "Show scoring detail" }).first();
    if (await whyButton.isVisible().catch(() => false)) {
      await pressNatural(page, whyButton);
      await beat(page, 3000);
      await pressNatural(page, page.getByRole("button", { name: "Hide scoring detail" }).first());
      await beat(page, 1200);
    }

    // ---- 6. Chat: a plain question, answered -----------------------------
    await page.goto("http://localhost:5179/chat");
    await beat(page, 1400);
    await sendChat(page, "I forgot my password and cannot log in to my computer");
    await expect(page.getByText(/worked 45 of 45/).first()).toBeVisible({
      timeout: 30000,
    });
    await beat(page, 3200);

    // ---- 7. Chat: too vague, so it asks ---------------------------------
    // Each beat starts a new chat. A session re-ranks against its opening
    // question, so asking about something else mid-thread would answer the
    // first question instead of the latest one.
    await pressNatural(page, page.getByRole("button", { name: "New chat" }));
    await beat(page, 1000);
    await sendChat(page, "finance user cannot open the report");
    await expect(page.getByText(/Check not satisfied/).first()).toBeVisible({
      timeout: 30000,
    });
    // A hedged answer must not present ticket numbers or a success count as if
    // they were evidence for a recommendation that was not made.
    await expect(page.getByRole("button", { name: /Show sources/ })).toHaveCount(0);
    await expect(page.getByText(/worked \d+\/\d+/)).toHaveCount(0);
    await beat(page, 3200);

    // Supplying the detail makes it commit.
    await sendChat(page, "error code S_RS_COMP, module SAP FICO, environment PROD");
    await expect(page.getByText(/worked 8 of 8/).first()).toBeVisible({
      timeout: 30000,
    });
    await beat(page, 3600);

    // ---- 8. Chat: the first fix failed, so it finds another --------------
    await pressNatural(page, page.getByRole("button", { name: "New chat" }));
    await beat(page, 1000);
    await sendChat(page, "my email is not arriving");
    await beat(page, 2600);
    await sendChat(page, "that did not work, still nothing");
    await expect(page.getByText(/Ruling that out/).first()).toBeVisible({
      timeout: 30000,
    });
    // Scoped to the newest reply. The first answer is still on screen above,
    // so a `.first()` locator here passed even when the follow-up repeated
    // the record the user had just rejected. The rejected title legitimately
    // appears twice - once in the reply that names it, once in the older
    // card - so the record offered last is what distinguishes the two.
    await expect(page.getByText(/Ruling that out: Outlook not syncing new emails/)).toBeVisible();
    await expect(page.getByText(/Cannot send emails with large attachments/).last()).toBeVisible();
    await beat(page, 4200);

    // ---- 9. Chat: not only a bug-fix tool -------------------------------
    await pressNatural(page, page.getByRole("button", { name: "New chat" }));
    await beat(page, 1000);
    await sendChat(page, "a new starter needs a laptop for their first day");
    await expect(page.getByText(/New Employee Laptop Setup/).first()).toBeVisible({
      timeout: 30000,
    });
    await beat(page, 4200);

    // ---- 10. Chat: nothing relevant, so it declines ----------------------
    await pressNatural(page, page.getByRole("button", { name: "New chat" }));
    await beat(page, 1000);
    await sendChat(page, "i ran out of milk in my house");
    await expect(page.getByText(/Check not satisfied/).first()).toBeVisible({
      timeout: 30000,
    });
    await expect(page.getByRole("button", { name: /Show sources/ })).toHaveCount(0);
    await beat(page, 4000);

    // ---- 11. Close on the dashboard -------------------------------------
    await page.goto("http://localhost:5179/overview");
    await beat(page, 1400);
    await glideTo(page, page.getByText("Resolution Memory"));
    await beat(page, 5000);
  });
});
