import { shipping } from "./fixtures/operations-cockpit-data.mjs";
import { reference } from "./action-discovery-fixture.mjs";
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
let enabled = true;
let failCapability = false;
let rejectQuestion = false;
let simulation = "running";
let derivedState;
let failStatus = false;
let delayStatus = 0;
let statusReads = 0;
const requests = [];
const fixture = async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  requests.push(url.pathname);
  const respond = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (url.pathname.endsWith("/capabilities"))
    return failCapability
      ? respond({ detail: "Temporarily unavailable" }, 503)
      : respond({ enabled: enabled && url.pathname.includes("tenant_a") });
  if (
    url.pathname.endsWith("/operations-cockpit") &&
    (!enabled || !url.pathname.includes("tenant_a"))
  )
    return respond({ detail: "Cockpit unavailable" }, 404);
  if (url.pathname.endsWith("/operations-cockpit"))
    return respond({
      observed_at: "2026-10-06T12:30:00Z",
      shipping,
      deviations: [],
      deviation_total: 0,
    });
  if (url.pathname.endsWith("/operations-cockpit/orders"))
    return respond({
      items: [
        {
          order_id: "order_d",
          number: "SO-104",
          commitment_ids: ["com_d"],
          location_ids: ["loc_leipzig"],
          due_at: "2026-10-06T14:00:00Z",
          at_risk: true,
          plan_at: "2026-10-06T14:00:00Z",
          forecast_at: null,
          handover_at: null,
          risk_requirements: [],
          coverage_gaps: [],
          blockers: {
            com_d: [{ code: "commitment_on_hold", detail: "Dispatch paused by customer" }],
          },
        },
      ],
      total: 1,
      has_more: false,
      next_after: null,
      observed_at: shipping.observed_at,
      basis_key: shipping.basis_key,
      coverage: shipping.coverage,
      totals: shipping.totals,
      re_evaluated: false,
    });
  if (url.pathname.endsWith("/activity"))
    return respond({
      observed_at: "2026-10-06T12:30:00Z",
      start: "2026-10-06T12:30:00Z",
      coverage_start: "2026-10-06T12:30:00Z",
      minutes: 15,
      bucket_seconds: 60,
      total: 0,
      counts: {},
      buckets: [],
      events: [],
      has_more: false,
    });
  if (url.pathname.endsWith("/agents"))
    return respond({
      observed_at: "2026-10-06T12:30:00Z",
      total: 0,
      items: [],
      has_more: false,
      next_after: null,
      scope: "active",
      coverage: { manual: "available", oauth: "available", runtime: "unavailable" },
    });
  if (url.pathname.endsWith("/register"))
    return respond({
      adopted: false,
      counts: null,
      total: 0,
      items: [],
      has_more: false,
      next_after: null,
    });
  if (url.pathname.endsWith("/operational-cases/status"))
    return respond({ adopted: true, can_control: true, can_adopt: false });
  if (url.pathname.endsWith("/operational-cases/objects/document/order_d"))
    return respond({ case_ids: ["case_d"] });
  if (url.pathname.endsWith("/operational-cases/case_d"))
    return respond({
      case_id: "case_d",
      kind: "order_fulfillment",
      order_document_id: "order_d",
      control_mode: "automation",
      control_revision: 1,
      business_reference: "SO-104",
      goal_state: "outstanding",
      source_record_ids: ["src_order"],
      coverage_gaps: [],
      actions: [],
      work: [{ commitment_id: "com_d", open_quantity: "1", status: "open" }],
      related_case_ids: [],
      unsettled_actions: [],
      unavailable_capabilities: [],
      control: null,
    });
  if (url.pathname.endsWith("/delivery-work"))
    return respond({ items: [], page: { number: 1, size: 50, total: 0, pages: 1 } });
  if (url.pathname.endsWith("/evidence-documents"))
    return respond({
      items: [
        {
          id: "order_d",
          date: "2026-10-06",
          number: "SO-104",
          type: "sales_order",
          party: "Customer D",
          party_id: "customer_d",
          gross_amount: "10",
          currency: "EUR",
          line_count: 1,
          reality_link_count: 1,
          status: "recorded",
          source: { system: "manual", type: "order", external_id: "104" },
        },
      ],
      page: { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false },
    });
  if (url.pathname.includes("/inspector/"))
    return respond({
      title: "SO-104",
      subtitle: "Exact order evidence",
      meaning: "Recorded business evidence",
      sections: [],
      metrics: [],
      technical_rows: [],
    });
  if (url.pathname.endsWith("/application-reference")) return respond(reference);
  if (url.pathname === "/api/auth/me") return respond(user);
  if (url.pathname === "/api/company-setup/playground")
    return respond({
      requested: false,
      enabled: true,
      eligible: false,
      archived: false,
      receipt: null,
    });
  if (url.pathname === "/api/v1/bootstrap")
    return respond({ tenants, default_tenant_id: "tenant_a" });
  if (url.pathname.endsWith("/timeline"))
    return respond({ events: [], activities: [], has_more: false });
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
};
await page.route("**/api/**", fixture);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
try {
  await page.setViewportSize({ width: 1440, height: 1050 });
  enabled = false;
  await page.goto(`${base}/?lang=en`);
  await page.locator("[data-primary-navigation]").waitFor();
  assert.equal(
    await page
      .locator("[data-primary-navigation]")
      .getByRole("link", { name: "Control Tower", exact: true })
      .count(),
    1,
    "a fresh default-company entry always exposes Control Tower",
  );
  await page
    .locator("[data-primary-navigation]")
    .getByRole("link", { name: "Control Tower", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Control Tower is unavailable for this company", exact: true })
    .waitFor();
  assert.equal(
    requests.filter((path) => path.endsWith("/operations-cockpit")).length,
    0,
    "disabled capability never mounts operational reads",
  );
  enabled = true;
  await page.goto(`${base}/app?tenant=tenant_a&lang=en`);
  const nav = page.locator("[data-primary-navigation]"),
    chat = page.locator("[data-global-chat]"),
    header = page.locator("[data-shell-header]");
  await nav.getByRole("link", { name: "Control Tower", exact: true }).waitFor();
  assert.equal(new URL(page.url()).pathname, "/app", "Home remains the default entry");
  await nav.getByRole("link", { name: "Control Tower", exact: true }).click();
  await page.getByRole("heading", { name: "Shipping by end of day", exact: true }).waitFor();
  await chat.waitFor({ state: "hidden" });
  assert.equal(
    await page.getByRole("heading", { level: 1, name: "Control Tower", exact: true }).count(),
    1,
    "shared Shell owns the single Control Tower title",
  );
  assert.equal(await page.locator("main h1").count(), 0, "no duplicate body hero");
  for (const name of ["About this page", "Show chat"])
    assert(
      await header.getByRole("button", { name, exact: true }).isVisible(),
      `canonical header retains ${name}`,
    );
  const inset = await page.locator("main").evaluate((main) => {
    const content = main.querySelector(".operations-cockpit");
    const toolbar = main.querySelector("[data-cockpit-toolbar]");
    return {
      padding: getComputedStyle(content).padding,
      x: toolbar.getBoundingClientRect().left - main.getBoundingClientRect().left,
      expected: parseFloat(getComputedStyle(main).paddingLeft),
      gap: toolbar.getBoundingClientRect().top - content.getBoundingClientRect().top,
    };
  });
  assert.equal(
    inset.padding,
    "0px",
    "standard Shell content inset without additional page padding",
  );
  assert(Math.abs(inset.x - inset.expected) < 1, "toolbar aligned to other workspace content");
  assert.equal(inset.gap, 0, "no extra hero gap before scope toolbar");
  await page.getByRole("button", { name: "At risk: 1", exact: true }).click();
  await page.getByText("Dispatch paused by customer", { exact: true }).waitFor();
  await page.getByRole("link", { name: "SO-104", exact: true }).click();
  await page.waitForURL((url) => url.pathname === "/app/orders-deliveries");
  assert.equal(new URL(page.url()).searchParams.get("entry"), "order_d");
  await page
    .locator('[data-case-id="case_d"]')
    .getByText("Automation owns this work", { exact: true })
    .waitFor();
  await page
    .locator('[data-case-id="case_d"]')
    .getByRole("button", { name: "Take over manually / stop automation", exact: true })
    .click();
  await page.getByLabel("Takeover reason", { exact: true }).waitFor();
  const evidenceLinks = await page.locator('[data-case-id="case_d"] a').all();
  assert.equal(evidenceLinks.length, 3, "Document, commitment and original Source remain linked");
  for (const link of evidenceLinks) {
    const target = new URL(await link.getAttribute("href"), base);
    assert.equal(target.searchParams.get("tenant"), "tenant_a");
    assert.equal(
      JSON.parse(target.searchParams.get("cockpit_origin") || "null")?.measure,
      "risk",
      "Every case evidence link preserves the selected cockpit origin",
    );
  }
  await header.getByRole("link", { name: "Return to Control Tower", exact: true }).click();
  await page.waitForURL((url) => url.pathname === "/app/cockpit");
  assert.equal(new URL(page.url()).searchParams.get("cockpit_measure"), "risk");
  await header.getByRole("button", { name: "Show chat", exact: true }).click();
  await chat.waitFor({ state: "visible" });
  await chat.locator("textarea").fill("Inspect this company context");
  await header.getByRole("button", { name: "Hide chat", exact: true }).click();
  await header.getByRole("button", { name: "Show chat", exact: true }).click();
  assert.equal(await chat.locator("textarea").inputValue(), "Inspect this company context");
  await page.locator("[data-company-id]").click();
  const secondCapability = page.waitForResponse(
    (r) => r.url().includes("tenant_b") && r.url().endsWith("/capabilities"),
  );
  await page
    .getByRole("dialog", { name: "Switch company", exact: true })
    .getByText("Second company", { exact: true })
    .click();
  await secondCapability;
  await page.waitForURL(
    (url) => url.pathname === "/app/cockpit" && url.searchParams.get("tenant") === "tenant_b",
  );
  await chat.waitFor({ state: "hidden" });
  await page
    .getByRole("heading", { name: "Control Tower is unavailable for this company", exact: true })
    .waitFor();
  assert.equal(
    await chat.locator("textarea").inputValue(),
    "",
    "Company switching clears the old company draft while preserving Home's existing chat behavior",
  );
  assert.equal(
    await nav.getByRole("link", { name: "Control Tower", exact: true }).count(),
    1,
    "A disabled company retains the destination with an explanation",
  );
  await page.locator("[data-company-id]").click();
  const restoredCapability = page.waitForResponse(
    (r) => r.url().includes("tenant_a") && r.url().endsWith("/capabilities"),
  );
  await page
    .getByRole("dialog", { name: "Switch company", exact: true })
    .getByText("Northstar Commerce", { exact: true })
    .click();
  await restoredCapability;
  await nav.getByRole("link", { name: "Control Tower", exact: true }).click();
  await page.waitForURL((url) => url.pathname === "/app/cockpit");
  await chat.waitFor({ state: "hidden" });
  await header.getByRole("button", { name: "Show chat", exact: true }).click();
  await chat.waitFor({ state: "visible" });
  assert.equal(
    await chat.locator("textarea").inputValue(),
    "",
    "Returning to the prior company does not restore its old cockpit draft",
  );
  enabled = false;
  const capability = page.waitForResponse((r) => r.url().endsWith("/capabilities"));
  await page.goto(`${base}/app?tenant=tenant_a&lang=en`);
  await capability;
  await page.locator("[data-company-id]").waitFor();
  assert.equal(
    await page
      .locator("[data-primary-navigation]")
      .getByRole("link", { name: "Control Tower", exact: true })
      .count(),
    1,
  );
  const beforeDisabled = requests.filter((path) => path.endsWith("/operations-cockpit")).length;
  await page.goto(`${base}/app/cockpit?tenant=tenant_a&lang=en`);
  await page
    .getByRole("heading", { name: "Control Tower is unavailable for this company", exact: true })
    .waitFor();
  assert.equal(
    requests.filter((path) => path.endsWith("/operations-cockpit")).length,
    beforeDisabled,
  );
  await page.getByRole("button", { name: "Back to Inbox", exact: true }).click();
  await page.waitForURL((url) => url.pathname === "/app");
  failCapability = true;
  await page.goto(`${base}/app/cockpit?tenant=tenant_a&lang=en`);
  await page
    .getByRole("heading", { name: "Control Tower is unavailable for this company", exact: true })
    .waitFor();
  assert.equal(await nav.getByRole("link", { name: "Control Tower", exact: true }).count(), 1);
  assert.equal(
    requests.filter((path) => path.endsWith("/operations-cockpit")).length,
    beforeDisabled,
  );
  assert.equal(
    await page.locator(".operations-cockpit").count(),
    0,
    "Disabled or failed capabilities expose no operational data",
  );
  assert.deepEqual(errors, []);
  console.log(
    "Full-shell optional entry, unchanged Home, on-demand stable chat and company capability reset passed",
  );
} catch (error) {
  console.log(JSON.stringify({ requests, errors, body: await page.locator("body").innerText() }));
  throw error;
} finally {
  await browser.close();
}
