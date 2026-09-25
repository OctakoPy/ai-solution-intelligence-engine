import { defineConfig } from "@playwright/test";

// Video recording is opt-in so the normal e2e suite stays fast and does not
// fill test-results with .webm files. Set DEMO_VIDEO=1 for the recorded
// walkthrough (see just web-demo-video).
const isDemo = process.env.DEMO_VIDEO === "1";

export default defineConfig({
  testDir: "./tests/e2e",
  // The recorded walkthrough is a single slow continuous take, so it is
  // excluded from the normal suite and run explicitly via `just web-demo-video`.
  testIgnore: isDemo ? undefined : /demo\.spec\.ts/,
  // The walkthrough must not run alongside the parallel smoke tests.
  workers: isDemo ? 1 : undefined,
  ...(isDemo
    ? { outputDir: "demo-video", reporter: [["list"], ["html", { open: "never" }]] }
    : {}),
  use: {
    baseURL: "http://localhost:5179",
    trace: "on-first-retry",
    ...(isDemo
      ? {
          video: { mode: "on" as const, size: { width: 1920, height: 1080 } },
          viewport: { width: 1920, height: 1080 },
          // Paced so a viewer can read each answer before the next beat.
          slowMo: 400,
        }
      : {}),
  },
  webServer: {
    command: "npm run dev & sleep 1 & (cd ../.. && uv run --no-sync uvicorn apps.api.main:app --port 8004)",
    timeout: 60000,
    reuseExistingServer: true,
  },
});
