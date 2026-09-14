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
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenants = [
  { id: "tenant_a", name: "Northstar Commerce" },
  { id: "tenant_b", name: "Second company" },
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
      series: [],
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
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const out = process.env.UNIFIED_SCREENSHOTS || "/private/tmp/reality-107-browser";
await mkdir(out, { recursive: true });
try {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/app?tenant=tenant_a`);
  await page.getByRole("heading", { name: "Your business, in focus." }).waitFor();
  await page.screenshot({ path: `${out}/home-desktop.png`, fullPage: true });
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="tenant_b"]').click();
  await page.getByRole("heading", { name: "No open commitments" }).waitFor();
  assert.ok(new URL(page.url()).searchParams.get("tenant") === "tenant_b");
  if (!(await page.locator("[data-global-chat]").isVisible()))
    await page.getByRole("button", { name: "Show chat", exact: true }).click();
  await page.getByRole("textbox", { name: "Ask about your company" }).fill("What is open?");
  await page.getByRole("button", { name: "Send question" }).click();
  await page.getByRole("alert").filter({ hasText: "Provider unavailable" }).waitFor();
  assert.equal(await page.getByRole("textbox").inputValue(), "What is open?");
  assert.ok(rejectQuestion);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: `${out}/chat-mobile.png`, fullPage: true });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.getByRole("button", { name: "Navigation", exact: true }).click();
  await page.getByRole("link", { name: "Home", exact: true }).click();
  await page.getByRole("heading", { name: "Your business, in focus." }).waitFor();
  await page.goto(`${base}/app?tenant=foreign`);
  await page.getByRole("heading", { name: "Company unavailable" }).waitFor();
  assert.equal(
    requests.some((path) => path.includes("/foreign/")),
    false,
  );
  assert.deepEqual(errors, []);
  console.log(
    "PASS: shell, company switch, foreign scope, chat failure retention and mobile navigation. Delivery and action journeys run in the companion harness.",
  );
} finally {
  await browser.close();
}
