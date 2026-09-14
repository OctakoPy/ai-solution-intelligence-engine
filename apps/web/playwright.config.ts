import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  use: {
    baseURL: "http://localhost:5179",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run dev & sleep 1 & (cd ../.. && uv run --no-sync uvicorn apps.api.main:app --port 8004)",
    timeout: 60000,
    reuseExistingServer: true,
  },
});
