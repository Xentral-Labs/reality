// Synthetic HTTP fixtures exercise presentation only; PostgreSQL tests prove business effects.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
if (!process.env.PLAYWRIGHT_MODULE)
  throw new Error("Set PLAYWRIGHT_MODULE; browser acceptance must not be silently skipped.");
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const context = await browser.newContext();
const page = await context.newPage();
page.setDefaultTimeout(10000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenants = [
  { id: "tenant_a", name: "Northstar Commerce", role: "owner", purpose: "playground" },
  { id: "tenant_b", name: "Second company" },
  { id: "tenant_practice", name: "Practice company", sandbox_run_id: "run_fixture" },
];
const user = {
  id: "user_test",
  email: "test@example.test",
  display_name: "Operator",
  status: "active",
  language: "en",
  locale: "en-GB",
  timezone: "UTC",
  is_platform_admin: false,
};
let rejectQuestion = false;
let simulation = "running";
let derivedState;
let failStatus = false;
let delayStatus = 0;
let statusReads = 0;
const requests = [];
await page.route("**/api/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  requests.push(url.pathname);
  const respond = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (url.pathname.endsWith("/application-reference"))
    return respond({
      workspaces: [{ actions: [{ command: "reserve" }, { command: "record_movement" }] }],
    });
  if (url.pathname === "/api/auth/me") return respond(user);
  if (url.pathname === "/api/v1/bootstrap")
    return respond({ tenants, default_tenant_id: "tenant_a" });
  if (url.pathname.endsWith("/demo-data")) {
    statusReads++;
    const captured = simulation;
    if (delayStatus) await new Promise((resolve) => setTimeout(resolve, delayStatus));
    return respond(
      {
        state: captured,
        derived_state: derivedState || captured,
        revision: 1,
        rate: 60,
        imported: 3,
        generated: 3,
        pending: 0,
        failed: 0,
        next_arrival: null,
      },
      failStatus ? 503 : 200,
    );
  }
  if (url.pathname.endsWith("/demo-data/imports"))
    return respond({ items: [], has_more: false, next_cursor: null });
  const tenant = tenants.find((row) => url.pathname.includes(row.id));
  if (url.pathname.endsWith("/analytics"))
    return respond({
      position: {
        open: 1,
        fully_reserved: 0,
        needs_reservation: 1,
        overdue: 0,
        unknown_due: 1,
        coverage_percent: "0",
      },
      series: [{ day: "2026-09-08", date: "2026-09-08", created: 1, shipped: 0 }],
    });
  if (url.pathname.endsWith("/dashboard")) {
    if (tenant?.id === "tenant_a") await new Promise((resolve) => setTimeout(resolve, 120));
    return respond({
      tenant,
      totals: {
        exceptions: 0,
        open_commitments: tenant?.id === "tenant_a" ? 12 : 0,
        open_deliveries: tenant?.id === "tenant_a" ? 12 : 0,
        pending_decisions: 0,
      },
      exceptions: [],
      inventory: [],
      facts: [],
      capabilities: {},
    });
  }
  if (url.pathname.endsWith("/copilot"))
    return respond({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (url.pathname.endsWith("/copilot/sessions"))
    return respond({ id: "chat_a", title: "New conversation" });
  if (url.pathname.endsWith("/messages")) {
    rejectQuestion = true;
    return respond({ detail: "Provider unavailable" }, 503);
  }
  if (url.pathname.endsWith("/change-proposals"))
    return respond({
      items: [],
      page: { number: 1, size: 50, total: 0, pages: 1, has_previous: false, has_next: false },
    });
  return respond({ detail: `Unexpected fixture request: ${url.pathname}` }, 404);
});
const base = process.env.WEB_BASE_URL || "http://localhost:5177";
const indicator = page.locator("[data-live-simulation]");
const refresh = () =>
  page.evaluate(() =>
    window.dispatchEvent(
      new CustomEvent("reality:demo-data-changed", { detail: { tenantId: "tenant_a" } }),
    ),
  );
try {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${base}/app?tenant=tenant_a`);
  await indicator.waitFor();
  assert.equal(await indicator.getAttribute("aria-label"), "Live simulation");
  await indicator.focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(/demo-data/);
  assert.equal(new URL(page.url()).searchParams.get("tenant"), "tenant_a");
  await page.getByRole("heading", { name: "Live simulation", exact: true }).waitFor();
  await mkdir("/tmp/reality-live-simulation", { recursive: true });
  await page.screenshot({ path: "/tmp/reality-live-simulation/desktop.png" });
  // Return to Home so only the header reader is under test.
  await page.goto(`${base}/app?tenant=tenant_a`);
  await indicator.waitFor();
  for (const state of [
    "paused",
    "stopped",
    "disconnected",
    "not_connected",
    "throttled",
    "error",
  ]) {
    simulation = state;
    await refresh();
    await indicator.waitFor({ state: "detached" });
    simulation = "running";
    await refresh();
    await indicator.waitFor();
  }
  derivedState = "error";
  await refresh();
  await indicator.waitFor({ state: "detached" });
  derivedState = undefined;
  await refresh();
  await indicator.waitFor();
  failStatus = true;
  await refresh();
  await indicator.waitFor({ state: "detached" });
  failStatus = false;
  await refresh();
  await indicator.waitFor();
  // A stalled read times out, clears the positive state and allows recovery.
  delayStatus = 10000;
  await refresh();
  await indicator.waitFor({ state: "detached", timeout: 9500 });
  delayStatus = 0;
  await refresh();
  await indicator.waitFor({ timeout: 12000 });
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, value: true });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await indicator.waitFor({ state: "detached" });
  const hiddenReads = statusReads;
  await page.waitForTimeout(5500);
  assert.equal(statusReads, hiddenReads);
  await page.evaluate(() => {
    delete document.hidden;
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await indicator.waitFor();
  await page.evaluate(() => {
    localStorage.setItem("reality.theme", "dark");
    window.dispatchEvent(new Event("reality:theme-changed"));
  });
  await page.screenshot({ path: "/tmp/reality-live-simulation/dark.png" });
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await indicator.locator("[data-live-dot]").evaluate((n) => getComputedStyle(n).animationName),
    "none",
  );
  await page.emulateMedia({ reducedMotion: "no-preference" });
  assert.notEqual(
    await indicator.locator("[data-live-dot]").evaluate((n) => getComputedStyle(n).animationName),
    "none",
  );
  for (const width of [1280, 1024, 768, 390]) {
    await page.setViewportSize({ width, height: 900 });
    if (width < 1024 && !(await page.locator("[data-primary-navigation]").isVisible()))
      await page.locator("[data-navigation-opener]").click();
    assert.equal(await indicator.isVisible(), true);
    const box = await indicator.boundingBox();
    assert.ok(box.x >= 0 && box.x + box.width <= width);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  }
  await page.screenshot({ path: "/tmp/reality-live-simulation/mobile.png" });
  await page.setViewportSize({ width: 1440, height: 900 });
  delayStatus = 500;
  await refresh();
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="tenant_b"]').click();
  await indicator.waitFor({ state: "detached" });
  await page.waitForTimeout(700);
  assert.equal(await indicator.count(), 0);
  assert.ok(statusReads > 0);
  assert.deepEqual(errors, []);
  console.log("Live simulation header browser acceptance passed");
} finally {
  await browser.close();
}
