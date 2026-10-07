// Real API/DB proof: no HTTP fixtures and no simulated browser clock.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.UNIFIED_BASE_URL;
const tenant = process.env.TENANT;
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
const errors = [];
try {
  const login = await context.request.post(`${base}/api/auth/login`, {
    data: { email: "cockpit-owner@example.test", password: "a-long-account-password" },
  });
  assert(login.ok(), `Real login failed: ${login.status()}`);
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`${base}/app/cockpit?tenant=${tenant}&lang=en`);
  await page.getByRole("button", { name: "Due today: 3", exact: true }).waitFor();
  await page.getByRole("button", { name: "Handed over: 1", exact: true }).waitFor();
  await page.getByRole("button", { name: "Forecast by day end: 3", exact: true }).waitFor();
  await page.getByText("Dispatch Agent", { exact: true }).waitFor();
  const began = Date.now();
  const hold = await context.request.post(
    `${base}/api/tenants/${tenant}/commitments/${process.env.COMMITMENT}/holds`,
    {
      data: { reason_code: "customer_request", note: "Committed browser proof hold" },
    },
  );
  assert.equal(hold.status(), 201, await hold.text());
  await page.getByRole("button", { name: "At risk: 1", exact: true }).waitFor({ timeout: 10000 });
  const displayMilliseconds = Date.now() - began;
  assert(
    displayMilliseconds <= 10000,
    "A committed business change must reach the browser within ten seconds.",
  );
  await page.getByRole("button", { name: "Forecast by day end: 2", exact: true }).waitFor();
  await page.getByRole("button", { name: "At risk: 1", exact: true }).click();
  await page.getByRole("link", { name: "LIVE-C", exact: true }).first().click();
  await page.waitForURL((url) => url.pathname === "/app/orders-deliveries");
  const casePanel = page.locator(`[data-case-id="${process.env.CASE}"]`);
  await casePanel.getByText("Automation owns this work", { exact: true }).waitFor();
  await casePanel
    .getByRole("button", { name: "Take over manually / stop automation", exact: true })
    .click();
  await casePanel
    .getByLabel("Takeover reason", { exact: true })
    .fill("I will complete this customer appointment");
  await casePanel.getByRole("button", { name: "Confirm manual takeover", exact: true }).click();
  await casePanel.getByText("Manually owned — automation stopped", { exact: true }).waitFor();
  const actual = await context.request
    .get(`${base}/api/tenants/${tenant}/operational-cases/${process.env.CASE}`)
    .then((r) => r.json());
  assert.equal(actual.control_mode, "human");
  assert.equal(actual.control.reason, "I will complete this customer appointment");
  await page.getByRole("link", { name: "Return to Control Tower", exact: true }).click();
  await page.getByRole("button", { name: "Manually taken over", exact: true }).click();
  await page.locator("[data-case-register]").getByText("LIVE-C", { exact: true }).first().waitFor();
  await page.screenshot({ path: `${process.env.SHOTS}/live-cockpit.png`, fullPage: true });
  assert.deepEqual(errors, []);
  console.log(
    JSON.stringify({
      committed_change_to_display_ms: displayMilliseconds,
      case_id: process.env.CASE,
      proof:
        "Real committed hold, three-action takeover review, confirmed takeover and stopped-case register",
    }),
  );
} catch (error) {
  const observed = await context.request
    .get(`${base}/api/tenants/${tenant}/operations-cockpit`)
    .then((r) => r.json());
  console.log(
    JSON.stringify({
      shipping: observed.shipping?.totals,
      gaps: observed.shipping?.gaps,
      readiness: observed.shipping?.basis?.readiness,
      sites: observed.shipping?.sites,
    }),
  );
  throw error;
} finally {
  await browser.close();
}
