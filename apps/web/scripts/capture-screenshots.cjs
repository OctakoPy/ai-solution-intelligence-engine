const { chromium } = require("@playwright/test");
const path = require("node:path");

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  const out = path.resolve(__dirname, "../../../docs/assets");

  const shots = [
    { url: "http://localhost:5179/overview", name: "overview.png" },
    { url: "http://localhost:5179/pipeline", name: "pipeline.png" },
    { url: "http://localhost:5179/find", name: "find-a-solution.png" },
    { url: "http://localhost:5179/chat", name: "chat.png" },
  ];

  for (const shot of shots) {
    await page.goto(shot.url, { waitUntil: "networkidle" });
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(out, shot.name), fullPage: false });
    console.log("captured", shot.name);
  }

  await browser.close();
})().catch((err) => {
  console.error(err);
  process.exit(1);
});