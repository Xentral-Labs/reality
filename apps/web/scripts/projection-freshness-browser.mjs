// The stored-result notice must say what a Refresh did (spec 180, FR-009).
// Fixtures control the response delay and the completed time, which is the only way
// to observe the in-flight state and the "nothing changed" outcome.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177",
  out = "/private/tmp/reality-freshness-browser";
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  completedAt = "2026-09-16T19:45:00Z",
  processed = 900,
  target = 900,
  delay = 0;

const metadata = () => ({
  projection: "exceptions",
  calculation_mode: "stored",
  state: "ready",
  processed_event_sequence: processed,
  target_event_sequence: target,
  completed_at: completedAt,
  projection_version: 1,
  upstream_freshness: "unknown",
  consistency: "completed_snapshot",
});

await page.route("**/api/**", async (route) => {
  const u = new URL(route.request().url()),
    path = u.pathname;
  const reply = (data) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      display_name: "Operator",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "t1", name: "Northstar" }], default_tenant_id: "t1" });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path === "/api/playground/exception-catalog")
    return reply({
      version: 1,
      classes: [
        {
          id: "late_delivery",
          label: "Late customer delivery",
          description: "A delivery promised to a customer is late.",
          severity: "high",
          owner: "sales",
        },
      ],
    });
  if (path.endsWith("/attention/summary")) {
    if (delay) await new Promise((resolve) => setTimeout(resolve, delay));
    return reply({
      classes: [{ class_id: "late_delivery", open: 3 }],
      total: 3,
      observed_at: completedAt,
      metadata: metadata(),
    });
  }
  return reply({
    metadata: metadata(),
    items: [],
    page: { number: 1, size: 50, total: 0, pages: 1, has_next: false, has_previous: false },
  });
});

const notice = () => page.locator("[data-projection-freshness]");
const refreshButton = () => notice().getByRole("button");

await mkdir(out, { recursive: true });
try {
  await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=exceptions`);
  await notice().waitFor();

  // 1. In flight: the control says so and cannot be pressed twice.
  delay = 1200;
  await refreshButton().click();
  await page.waitForFunction(
    () =>
      document.querySelector("[data-projection-freshness]")?.getAttribute("aria-busy") === "true",
  );
  assert.equal(
    await refreshButton().isDisabled(),
    true,
    "the control stays pressable while reading",
  );
  assert.match(await notice().innerText(), /Updating/, "no in-flight wording");
  await page.screenshot({ path: `${out}/in-flight.png` });

  // 2. Nothing changed upstream: say so instead of leaving the view identical.
  await page.waitForFunction(
    () =>
      document.querySelector("[data-projection-freshness]")?.getAttribute("aria-busy") !== "true",
  );
  assert.match(
    await notice().innerText(),
    /Unchanged/,
    "an unchanged result must be stated, not left silent",
  );
  assert.equal(await refreshButton().isDisabled(), false);
  await page.screenshot({ path: `${out}/unchanged.png` });

  // 3. A newer generation arrived: say that too.
  completedAt = "2026-09-16T20:15:00Z";
  await refreshButton().click();
  await page.locator('[data-projection-outcome="updated"]').waitFor();
  assert.match(await notice().innerText(), /Updated/, "a newer result must be announced");
  await page.screenshot({ path: `${out}/updated.png` });

  // 4. A backlog is the reason to press the control at all.
  delay = 0;
  processed = 880;
  target = 900;
  await refreshButton().click();
  await page.locator("[data-projection-behind]").waitFor();
  assert.equal(
    await page.locator("[data-projection-behind]").getAttribute("data-projection-behind"),
    "20",
    "the backlog behind the stored result is not stated",
  );
  assert.match(await notice().innerText(), /Events not yet included: 20/);
  await page.screenshot({ path: `${out}/behind.png` });

  // 5. Every wording exists in all four languages.
  for (language of ["de", "nl", "es"]) {
    await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=exceptions`);
    await notice().waitFor();
    await refreshButton().click();
    await page.waitForFunction(
      () =>
        document.querySelector("[data-projection-freshness]")?.getAttribute("aria-busy") !== "true",
    );
    const text = await notice().innerText();
    assert.doesNotMatch(
      text,
      /Unchanged|Updating|Events not yet included/,
      `${language} untranslated`,
    );
    assert.notEqual(text.trim(), "", `${language}: the notice is empty`);
    await page.screenshot({ path: `${out}/notice-${language}.png` });
  }

  assert.deepEqual(errors, []);
  console.log(
    "Projection freshness: in-flight state, unchanged and updated outcomes, backlog and four languages passed.",
  );
} catch (error) {
  console.error(errors, page.url(), (await page.locator("body").innerText()).slice(-2000));
  throw error;
} finally {
  await browser.close();
}
