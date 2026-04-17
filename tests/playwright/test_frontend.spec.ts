/**
 * Frontend browser tests for the TutorCare Security Diagnostic Dashboard.
 *
 * These tests run against the live GitHub Pages deployment (or a local server
 * when BASE_URL is set) and verify the page structure, navigation, and form
 * behaviour without relying on a real API backend.
 *
 * Design principles:
 * - No real API calls are made (API is not configured in tests)
 * - Tests assert visible UI state, not network responses
 * - Resilient to CDN latency: generous timeouts + waitFor helpers
 * - Easy to extend: add new describe blocks for additional panels
 */

import { test, expect, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Navigate to the dashboard and wait for Alpine.js to finish hydrating.
 * Alpine.js removes the `x-cloak` attribute once it is ready; we use that
 * as a reliable "app is ready" signal.
 */
async function loadDashboard(page: Page): Promise<void> {
  await page.goto("/");
  // Wait for Alpine's x-cloak removal (the root div becomes visible)
  await page.waitForSelector('[x-data="app()"]', { state: "attached" });
  // Small buffer to let Alpine initialise reactive data
  await page.waitForTimeout(500);
}

/**
 * Click a sidebar navigation button by its visible label text.
 */
async function navigateTo(page: Page, label: string): Promise<void> {
  await page.getByRole("button", { name: label, exact: false }).first().click();
  await page.waitForTimeout(200);
}

// ---------------------------------------------------------------------------
// Page load & basic structure
// ---------------------------------------------------------------------------

test.describe("Page load", () => {
  test("loads successfully and returns 200", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.status()).toBeLessThan(400);
  });

  test("has the correct page title", async ({ page }) => {
    await loadDashboard(page);
    await expect(page).toHaveTitle(/Security Diagnostic Toolkit/i);
  });

  test("shows the sidebar branding", async ({ page }) => {
    await loadDashboard(page);
    await expect(page.getByText("Security Toolkit")).toBeVisible();
    await expect(page.getByText("Diagnostic Dashboard")).toBeVisible();
  });

  test("shows all four tool navigation buttons", async ({ page }) => {
    await loadDashboard(page);
    // The sidebar renders these as buttons
    await expect(page.getByRole("button", { name: /IP Reputation/i }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Domain/i }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Phone/i }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Site Health/i }).first()).toBeVisible();
  });

  test("shows the Settings and Documentation nav items", async ({ page }) => {
    await loadDashboard(page);
    await expect(page.getByRole("button", { name: /Settings/i }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Documentation/i }).first()).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// IP Reputation panel
// ---------------------------------------------------------------------------

test.describe("IP Reputation panel", () => {
  test.beforeEach(async ({ page }) => {
    await loadDashboard(page);
    // IP Reputation is the default panel; navigate anyway for clarity
    await navigateTo(page, "IP Reputation");
  });

  test("displays the panel heading", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /IP Reputation Check/i })).toBeVisible();
  });

  test("has an IP address input field with placeholder", async ({ page }) => {
    const input = page.getByPlaceholder("e.g. 8.8.8.8");
    await expect(input).toBeVisible();
    await expect(input).toBeEditable();
  });

  test("has a Check IP submit button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Check IP/i })).toBeVisible();
  });

  test("submit button is disabled when IP field is empty", async ({ page }) => {
    const btn = page.getByRole("button", { name: /Check IP/i });
    await expect(btn).toBeDisabled();
  });

  test("submit button becomes enabled when a valid IP is typed", async ({ page }) => {
    await page.getByPlaceholder("e.g. 8.8.8.8").fill("8.8.8.8");
    await expect(page.getByRole("button", { name: /Check IP/i })).toBeEnabled();
  });

  test("shows API-not-configured warning when no backend is set", async ({ page }) => {
    await expect(page.getByText("API not configured")).toBeVisible();
  });

  test("can clear the IP input", async ({ page }) => {
    const input = page.getByPlaceholder("e.g. 8.8.8.8");
    await input.fill("1.2.3.4");
    await input.clear();
    await expect(input).toHaveValue("");
  });

  test("has an optional DNSBL zones field", async ({ page }) => {
    await expect(
      page.getByPlaceholder("zen.spamhaus.org, bl.spamcop.net")
    ).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Domain Reputation panel
// ---------------------------------------------------------------------------

test.describe("Domain Reputation panel", () => {
  test.beforeEach(async ({ page }) => {
    await loadDashboard(page);
    await navigateTo(page, "Domain");
  });

  test("displays the panel heading", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /Domain Reputation Check/i })).toBeVisible();
  });

  test("has a domain input field", async ({ page }) => {
    await expect(page.getByPlaceholder("e.g. example.com")).toBeVisible();
  });

  test("submit button is disabled when domain field is empty", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Check Domain/i })).toBeDisabled();
  });

  test("submit button enables after typing a domain", async ({ page }) => {
    await page.getByPlaceholder("e.g. example.com").fill("example.com");
    await expect(page.getByRole("button", { name: /Check Domain/i })).toBeEnabled();
  });

  test("shows API-not-configured warning", async ({ page }) => {
    await expect(page.getByText("API not configured")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Phone Validation panel
// ---------------------------------------------------------------------------

test.describe("Phone Validation panel", () => {
  test.beforeEach(async ({ page }) => {
    await loadDashboard(page);
    await navigateTo(page, "Phone");
  });

  test("displays the panel heading", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /Phone Number Validation/i })
    ).toBeVisible();
  });

  test("has a phone number input with E.164 placeholder", async ({ page }) => {
    await expect(page.getByPlaceholder("e.g. +14155552671")).toBeVisible();
  });

  test("has an optional region hint input", async ({ page }) => {
    await expect(page.getByPlaceholder("US")).toBeVisible();
  });

  test("Validate button is disabled when phone field is empty", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Validate/i })).toBeDisabled();
  });

  test("Validate button enables after entering a phone number", async ({ page }) => {
    await page.getByPlaceholder("e.g. +14155552671").fill("+14155552671");
    await expect(page.getByRole("button", { name: /Validate/i })).toBeEnabled();
  });

  test("shows API-not-configured warning", async ({ page }) => {
    await expect(page.getByText("API not configured")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Site Health panel
// ---------------------------------------------------------------------------

test.describe("Site Health panel", () => {
  test.beforeEach(async ({ page }) => {
    await loadDashboard(page);
    await navigateTo(page, "Site Health");
  });

  test("displays the panel heading", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /Site Health.*Diagnostics/i })
    ).toBeVisible();
  });

  test("has a URL input field with placeholder", async ({ page }) => {
    await expect(page.getByPlaceholder("https://example.com")).toBeVisible();
  });

  test("has a timeout number input", async ({ page }) => {
    await expect(page.getByPlaceholder("10")).toBeVisible();
  });

  test("Diagnose button is disabled when URL is empty", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Diagnose/i })).toBeDisabled();
  });

  test("Diagnose button enables after entering a URL", async ({ page }) => {
    await page.getByPlaceholder("https://example.com").fill("https://example.com");
    await expect(page.getByRole("button", { name: /Diagnose/i })).toBeEnabled();
  });

  test("shows API-not-configured warning", async ({ page }) => {
    await expect(page.getByText("API not configured")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Settings panel
// ---------------------------------------------------------------------------

test.describe("Settings panel", () => {
  test.beforeEach(async ({ page }) => {
    await loadDashboard(page);
    await navigateTo(page, "Settings");
  });

  test("displays the Settings heading", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /Settings/i })).toBeVisible();
  });

  test("has an API Base URL input", async ({ page }) => {
    await expect(
      page.getByPlaceholder("https://your-api-host.example.com")
    ).toBeVisible();
  });

  test("has an API Key password input", async ({ page }) => {
    await expect(
      page.getByPlaceholder("Leave empty if authentication is disabled")
    ).toBeVisible();
  });

  test("has Save Settings and Test Connection buttons", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Save Settings/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Test Connection/i })).toBeVisible();
  });

  test("saves a base URL and shows confirmation", async ({ page }) => {
    await page
      .getByPlaceholder("https://your-api-host.example.com")
      .fill("http://localhost:8000");
    await page.getByRole("button", { name: /Save Settings/i }).click();
    // The Alpine component shows "✅ Saved" briefly
    await expect(page.getByText(/Saved/i)).toBeVisible({ timeout: 3000 });
  });

  test("shows optional API keys reference table", async ({ page }) => {
    await expect(page.getByText("ABUSEIPDB_KEY")).toBeVisible();
    await expect(page.getByText("VIRUSTOTAL_KEY")).toBeVisible();
    await expect(page.getByText("NUMVERIFY_KEY")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Documentation panel
// ---------------------------------------------------------------------------

test.describe("Documentation panel", () => {
  test.beforeEach(async ({ page }) => {
    await loadDashboard(page);
    await navigateTo(page, "Documentation");
  });

  test("displays the Documentation heading", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /Documentation/i })).toBeVisible();
  });

  test("contains how-to-use instructions", async ({ page }) => {
    await expect(page.getByText(/How to Use the Dashboard/i)).toBeVisible();
  });

  test("contains the example JSON outputs section", async ({ page }) => {
    await expect(page.getByText(/Example Outputs/i)).toBeVisible();
  });

  test("contains badge colour guide", async ({ page }) => {
    await expect(page.getByText(/Badge Colour Guide/i)).toBeVisible();
  });

  test("contains the legal notice", async ({ page }) => {
    await expect(page.getByText(/Legal.*Ethical/i)).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Navigation – switching between panels
// ---------------------------------------------------------------------------

test.describe("Panel navigation", () => {
  test("can cycle through all tool panels without errors", async ({ page }) => {
    await loadDashboard(page);

    const panels: Array<{ navLabel: string; heading: RegExp }> = [
      { navLabel: "IP Reputation", heading: /IP Reputation Check/i },
      { navLabel: "Domain",        heading: /Domain Reputation Check/i },
      { navLabel: "Phone",         heading: /Phone Number Validation/i },
      { navLabel: "Site Health",   heading: /Site Health/i },
      { navLabel: "Settings",      heading: /Settings/i },
      { navLabel: "Documentation", heading: /Documentation/i },
    ];

    for (const panel of panels) {
      await navigateTo(page, panel.navLabel);
      await expect(
        page.getByRole("heading", { name: panel.heading }).first()
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test("API-not-configured warning links to Settings", async ({ page }) => {
    await loadDashboard(page);
    // Start on IP panel (default)
    await navigateTo(page, "IP Reputation");
    // Click the inline "Open Settings" link in the warning banner
    await page.getByRole("button", { name: /Open Settings/i }).first().click();
    await expect(page.getByRole("heading", { name: /Settings/i })).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Mobile viewport
// ---------------------------------------------------------------------------

test.describe("Mobile layout", () => {
  test("hamburger menu button is visible on small screens", async ({ page }) => {
    // Force a narrow viewport within the test (Pixel 5 project also runs this)
    await page.setViewportSize({ width: 375, height: 812 });
    await loadDashboard(page);
    // The mobile header contains a hamburger svg button
    const burger = page
      .locator("header")
      .getByRole("button")
      .first();
    await expect(burger).toBeVisible();
  });
});
