import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for the TutorCare Security Diagnostic Dashboard.
 *
 * Targets the static site deployed to GitHub Pages.
 * Override BASE_URL to test a local server:
 *   BASE_URL=http://localhost:5500 npx playwright test
 */
export default defineConfig({
  // Directory containing all Playwright test files
  testDir: "./tests/playwright",

  // Run tests in parallel across workers
  fullyParallel: true,

  // Fail CI build if test.only() is accidentally left in code
  forbidOnly: !!process.env.CI,

  // Retry failed tests once in CI (flakiness guard)
  retries: process.env.CI ? 1 : 0,

  // Number of parallel workers (single in CI keeps logs readable)
  workers: process.env.CI ? 1 : undefined,

  // Reporters: GitHub Actions annotation + HTML report saved as artifact
  reporter: process.env.CI
    ? [["github"], ["html", { open: "never" }]]
    : [["list"], ["html", { open: "on-failure" }]],

  use: {
    // Default base URL; override with BASE_URL env var
    baseURL: process.env.BASE_URL || "https://philr029.github.io/TutorCare-Tests",

    // Capture a screenshot on every test failure for debugging
    screenshot: "only-on-failure",

    // Save a video clip on failure
    video: "retain-on-failure",

    // Keep a full trace on first retry so failures are debuggable
    trace: "on-first-retry",

    // Give Alpine.js / Tailwind CDN time to hydrate on slow connections
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
    // Mobile viewport smoke-test
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 5"] },
    },
  ],

  // Folder for test output artefacts (screenshots, traces, videos)
  outputDir: "playwright-results/",
});
