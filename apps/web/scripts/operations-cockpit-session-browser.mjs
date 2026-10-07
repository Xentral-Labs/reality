// Controlled browser time and HTTP fixtures; this is not the separate real-time pilot soak.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
page.setDefaultTimeout(10000);
const failures = [],
  counts = new Map(),
  supportingDays = [];
let hidden = false,
  fail = false,
  version = 1,
  denied = false;
page.on("pageerror", (error) => failures.push(error.message));
// Keep host execution time out of the controlled eight-hour budget.
await page.clock.install({ time: new Date("2026-10-06T23:00:00Z") });
await page.clock.pauseAt(new Date("2026-10-06T23:30:00Z"));
await page.addInitScript(() => {
  Object.defineProperty(document, "visibilityState", {
    configurable: true,
    get: () => (window.__testHidden ? "hidden" : "visible"),
  });
});
const row = {
  case_id: "case_stable",
  kind: "order_fulfillment",
  order_document_id: "order_stable",
  return_announcement_id: null,
  control_mode: "automation",
  control_revision: 1,
  goal_state: "outstanding",
  source_record_ids: [],
  unavailable_capabilities: [],
  related_case_ids: [],
  unsettled_actions: [],
  coverage_gaps: [],
  actions: [],
  work: [],
};
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  assert.equal(req.method(), "GET", "Following and reading never confirm business work");
  counts.set(path, (counts.get(path) || 0) + 1);
  const observed = await page.evaluate(() => new Date().toISOString());
  const day =
    url.searchParams.get("day") && url.searchParams.get("day") !== "today"
      ? url.searchParams.get("day")
      : observed.slice(0, 10);
  const start = `${day}T00:00:00Z`,
    end = new Date(Date.parse(start) + 86400000).toISOString();
  const shipping = {
    observed_at: observed,
    business_day: day,
    time_zone: "UTC",
    location_id: null,
    day_start: start,
    day_end: end,
    basis_key: `basis-${version}`,
    basis: { sources: {}, policy_version: "completion-slot-v1" },
    coverage: { cohort: "complete", handover: "complete", forecast: "complete" },
    totals: {
      due: 4,
      handed_over: 1,
      forecast: observed >= end ? null : 3,
      risk: observed >= end ? null : 1,
    },
    sites: [],
    gaps: [],
    excluded: [],
    opening_baseline: { handover: 0, plan: 0 },
    forecast_horizon: observed >= end ? "ended" : "future",
    series: {
      plan: [
        { at: start, count: 0 },
        { at: end, count: 4 },
      ],
      handover: [
        { at: start, count: 0 },
        { at: observed >= end ? end : observed, count: 1 },
      ],
      forecast:
        observed >= end
          ? []
          : [
              { at: observed, count: 1 },
              { at: end, count: 3 },
            ],
    },
  };
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/operations-cockpit"))
    return denied
      ? reply({ detail: "Access revoked" }, 403)
      : fail
        ? reply({ detail: "Controlled outage" }, 503)
        : reply({ observed_at: observed, shipping, deviations: [], deviation_total: 0 });
  if (path.endsWith("/activity"))
    return reply({
      observed_at: observed,
      start: new Date(Date.parse(observed) - 900000).toISOString(),
      coverage_start: new Date(Date.parse(observed) - 900000).toISOString(),
      minutes: 15,
      bucket_seconds: 60,
      total: version,
      counts: { orders: version },
      buckets: Array.from({ length: 16 }, (_, i) => ({
        start: new Date(Date.parse(observed) - i * 60000).toISOString(),
        end: observed,
        partial: i === 0,
        counts: { orders: i === 1 ? version : 0 },
        total: i === 1 ? version : 0,
      })),
      events: [
        {
          id: `event_${version}`,
          sequence: version,
          type: "document.recorded",
          subject_type: "document",
          subject_id: `doc_${version}`,
          recorded_at: observed,
          occurred_at: observed,
          source_record_id: null,
        },
      ],
      has_more: false,
    });
  if (path.endsWith("/agents"))
    return reply({
      observed_at: observed,
      total: 0,
      items: [],
      has_more: false,
      next_after: null,
      scope: "active",
      coverage: { manual: "available", oauth: "unavailable", runtime: "unavailable" },
    });
  if (path.endsWith("/register"))
    return reply({
      adopted: true,
      total: 1,
      items: [row],
      counts: { automation: 1, human: 0, outstanding: 1, completed: 0, abandoned: 0 },
      has_more: false,
      next_after: null,
    });
  if (path.endsWith("/status"))
    return reply({ adopted: true, can_control: true, can_adopt: false });
  if (path.endsWith("/orders")) {
    supportingDays.push(day);
    return reply({
      observed_at: observed,
      items: [],
      total: 0,
      has_more: false,
      next_after: null,
      basis_key: `basis-${version}`,
      coverage: shipping.coverage,
      totals: shipping.totals,
      re_evaluated: false,
    });
  }
  return reply(row);
});
async function settle() {
  await page.evaluate(() => Promise.resolve());
}
async function step(ms = 5000) {
  await page.clock.runFor(ms - 32);
  await settle();
  await page.clock.runFor(32);
  await settle();
}
try {
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
  await page.getByText("Live observation", { exact: true }).waitFor();
  for (const selector of ["[data-business-case-overview]", "[data-case-management]"]) {
    await page.locator(`${selector} > summary`).click();
  }
  await page.getByRole("button", { name: "Select a case", exact: true }).click();
  await page
    .locator('[data-case-id="case_stable"]')
    .getByRole("button", { name: "Case details", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Take over manually / stop automation", exact: true })
    .click();
  await page.getByLabel("Takeover reason").fill("Keep this exact review while the company runs");
  const workspace = {
    async selectOption(view) {
      assert(
        await page
          .locator(
            view === "activity"
              ? ".cockpit-activity"
              : view === "agents"
                ? "[data-agent-access]"
                : "[data-case-inspection]",
          )
          .isVisible(),
      );
    },
  };
  await workspace.selectOption("activity");
  await page.getByRole("button", { name: "Pause following", exact: true }).click();
  await page.getByRole("button", { name: "At risk: 1", exact: true }).click();
  const analysis = page.getByRole("combobox", { name: "Analysis area", exact: true });
  await workspace.selectOption("responsibility");
  await analysis.selectOption("messages");
  assert.equal(await page.locator("[data-shipping-investigation]").isVisible(), false);
  assert.equal(
    await page.getByLabel("Takeover reason").inputValue(),
    "Keep this exact review while the company runs",
  );
  assert.equal(
    await page
      .getByRole("button", { name: "Resume following", exact: true, includeHidden: true })
      .getAttribute("aria-pressed"),
    "true",
  );
  await workspace.selectOption("agents");
  await workspace.selectOption("responsibility");
  assert.equal(
    await page.getByLabel("Takeover reason").inputValue(),
    "Keep this exact review while the company runs",
  );
  await analysis.selectOption("shipping");
  assert(await page.locator("[data-shipping-inspection]").isVisible());
  for (let tick = 0; tick < 5760; tick++) {
    if (tick === 6) version = 2;
    if (tick === 120) fail = true;
    if (tick === 126) fail = false;
    if (tick === 360) {
      hidden = true;
      await page.evaluate(() => {
        window.__testHidden = true;
        document.dispatchEvent(new Event("visibilitychange"));
      });
    }
    if (tick === 372) {
      hidden = false;
      await page.evaluate(() => {
        window.__testHidden = false;
        document.dispatchEvent(new Event("visibilitychange"));
      });
    }
    if (tick === 400) await page.getByRole("button", { name: "Refresh", exact: true }).click();
    await step();
    if (tick === 6) {
      await workspace.selectOption("activity");
      await page.getByText("New activity available", { exact: true }).waitFor();
      await workspace.selectOption("responsibility");
    }
    if (tick === 121)
      await page
        .getByText("Previous observation — refresh failed", { exact: true })
        .first()
        .waitFor();
    if (tick === 390) {
      assert.equal(
        await page.getByLabel("Takeover reason").inputValue(),
        "Keep this exact review while the company runs",
      );
      assert.equal(await page.locator('[data-activity-event="event_1"]').count(), 1);
    }
    if (tick % 720 === 719) {
      await workspace.selectOption("agents");
      await workspace.selectOption("responsibility");
      assert(await page.locator("[data-case-inspection]").isVisible());
      assert((await page.locator(".cockpit-event-list li").count()) <= 50);
      assert((await page.locator(".cockpit-activity-chart>div").count()) <= 61);
      console.log(`Controlled hour ${(tick + 1) / 720}: bounded charts, stable inspection/review`);
    }
  }
  assert.equal(
    await page
      .locator("[data-cockpit-toolbar] time")
      .getAttribute("datetime")
      .then((value) => value.slice(0, 10)),
    "2026-10-07",
    "Automatic business day crosses midnight during the controlled session",
  );
  assert.equal(
    await page.getByLabel("Takeover reason").inputValue(),
    "Keep this exact review while the company runs",
  );
  assert.equal(await page.locator('[data-activity-event="event_1"]').count(), 1);
  await workspace.selectOption("activity");
  await page.getByRole("button", { name: "Resume following", exact: true }).click();
  await page.locator('[data-activity-event="event_2"]').waitFor();
  assert(
    [...counts.values()].every((count) => count < 5800),
    `Each endpoint has a bounded five-second request rate: ${JSON.stringify(Object.fromEntries(counts))}`,
  );
  assert.deepEqual(
    supportingDays,
    ["2026-10-06", "2026-10-06"],
    "An opened investigation retains its original company day across midnight",
  );
  await page.getByRole("combobox", { name: /^Business day/ }).selectOption("pinned");
  await page.getByLabel("Date", { exact: true }).waitFor();
  assert.equal(await page.getByLabel("Date", { exact: true }).inputValue(), "2026-10-07");
  await page.clock.setSystemTime(new Date("2026-10-08T00:01:00Z"));
  await step();
  assert.equal(await page.getByLabel("Date", { exact: true }).inputValue(), "2026-10-07");
  await page.evaluate(() => window.__cockpitNavigate({ tenant: "other-company" }));
  await step();
  assert.equal(
    await page.getByLabel("Takeover reason").count(),
    0,
    "Company change clears the previous exact review",
  );
  assert.equal(await page.locator("[data-case-inspection]").count(), 0);
  denied = true;
  await step();
  await page.locator("[data-home-fallback]").waitFor();
  assert.equal(
    await page.locator("[data-case-register]").count(),
    0,
    "Revocation removes company observations",
  );
  assert.deepEqual(failures, []);
  console.log(
    JSON.stringify({
      controlled_hours: 8,
      requests: Object.fromEntries(counts),
      hidden,
      errors: failures,
    }),
  );
} finally {
  await browser.close();
}
