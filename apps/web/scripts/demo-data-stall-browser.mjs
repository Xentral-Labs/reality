// Spec 256 FR-015/FR-016: a stalled live source is visible in the integrations
// overview, says why, and its settings lead to the simulation itself.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const tenant = "demo_fixture";
const recovery = "2026-09-24T03:00:00Z";
// The second phase asks the same page about a source that is simply not executed.
let phase = "suspended",
  workerReady = false;
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    path = u.pathname;
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
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
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        {
          id: tenant,
          name: "My demo company",
          company_kind: "sandbox",
          demo_data_state: "running",
        },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.endsWith("/readiness"))
    return reply({
      status: workerReady ? "ready" : "unavailable",
      components: {
        connection: "ready",
        scheduler: "ready",
        worker: workerReady ? "ready" : "unavailable",
      },
      observed_at: "2026-09-23T09:00:00Z",
    });
  if (path.endsWith("/demo-data"))
    return reply(
      phase === "overdue"
        ? {
            id: "ddc_1",
            state: "running",
            derived_state: "overdue",
            revision: 3,
            rate: 60,
            schedule_id: "sch_1",
            next_arrival: "2026-09-23T06:00:00Z",
            last_success: "2026-09-23T06:00:00Z",
            scheduler_error: null,
            stall: {
              kind: "overdue",
              code: null,
              stopped_at: null,
              attempts: 0,
              recovery_at: null,
              automatic: false,
            },
            generated: 883,
            imported: 883,
            failed: 0,
            pending: 0,
          }
        : {
            id: "ddc_1",
            state: "running",
            derived_state: "suspended",
            revision: 3,
            rate: 60,
            schedule_id: "sch_1",
            next_arrival: null,
            last_success: "2026-09-19T19:06:01Z",
            scheduler_error: "database_error",
            stall: {
              kind: "suspended",
              code: "database_error",
              stopped_at: "2026-09-19T19:09:00Z",
              attempts: 3,
              recovery_at: recovery,
              automatic: true,
            },
            generated: 883,
            imported: 883,
            failed: 0,
            pending: 0,
          },
    );
  if (path.endsWith("/demo-data/imports"))
    return reply({ items: [], page: { number: 1, size: 25, total: 0, pages: 0 } });
  if (path.includes("/data-sources/"))
    return reply({
      items: path.endsWith("/systems")
        ? [
            {
              id: "sys_demo",
              code: "demo_data",
              name: "Demo Data",
              description: "Synthetic incoming orders",
              is_active: true,
              record_count: 2617,
            },
          ]
        : [],
      page: { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false },
    });
  if (path.endsWith("/integrations"))
    return reply({
      systems: [
        {
          id: "sys_demo",
          code: "demo_data",
          name: "Demo Data",
          description: "Synthetic incoming orders",
          is_active: true,
          base_url: null,
          connector_code: null,
          record_count: 2617,
        },
      ],
      capabilities: [],
      recent_records: [],
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
await page.goto(`${base}/app/data-sources?tenant=${tenant}&data_view=systems`);

// FR-015: the overview says the simulation is not producing, and marks it.
const badge = page.locator("[data-demo-attention]");
await badge.waitFor();
assert.match(await badge.innerText(), /Waiting to resume/);
const cell = page.locator('[data-demo-source-state="suspended"]');
await cell.waitFor();
// A narrow column carries the state; the reason travels in its title.
assert.match(await cell.innerText(), /^Waiting$/);
assert.match(await cell.getAttribute("title"), /interrupted and will resume by itself/);

// FR-001: the reason, and that it comes back by itself.
const reason = page.locator("[data-demo-source-stall]");
await reason.waitFor();
const reasonText = await reason.innerText();
assert.match(reasonText, /interrupted and will resume by itself/);
assert.match(reasonText, /database could not be reached/);
assert.match(reasonText, /Next attempt/);

// FR-016: what a person sets for this source is set where the source is configured.
await page
  .locator("[data-source-row]")
  .filter({ hasText: "Demo Data" })
  .getByRole("button", { name: "Settings" })
  .click();
const dialog = page.locator("[data-source-configuration]");
await dialog.waitFor();
const settings = dialog.locator("[data-source-simulation-settings]");
await settings.waitFor();
await settings.getByRole("heading", { name: "Live simulation" }).waitFor();
assert.match(await settings.innerText(), /database could not be reached/);
// The settable things are here: the state, the rate and the controls.
await settings.getByLabel("Orders per hour").waitFor();
await settings.getByRole("button", { name: "Pause" }).waitFor();
// The observations are not: they belong to the simulation's own page.
assert.equal(await settings.locator(".demo-data-counts").count(), 0);
assert.equal(await settings.locator(".demo-live-activity").count(), 0);
assert.equal(await settings.locator(".demo-order-to-cash").count(), 0);

// FR-004/FR-005: an occurrence that was never executed names the missing role.
phase = "overdue";
await page.reload();
await page.getByRole("heading", { name: "Live simulation" }).waitFor();
const overdue = page.locator('[data-demo-stall="overdue"]');
await overdue.waitFor();
assert.match(await overdue.innerText(), /No arrival has been executed as scheduled/);
const roles = page.locator('[data-demo-readiness="unavailable"]');
await roles.waitFor();
assert.match(await roles.innerText(), /Background processing/);

assert.deepEqual(errors, [], `page errors: ${errors.join(" | ")}`);
await browser.close();
console.log("demo-data-stall-browser: ok");
