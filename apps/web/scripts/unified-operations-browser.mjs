// HTTP fixtures exercise the rendered UI; PostgreSQL tests verify all business semantics.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const errors = [],
  requests = [];
page.on("pageerror", (error) => errors.push(error.message));
let language = "en",
  resolved = false,
  failWarehouse = false,
  failCatalog = true;
const tenant = "operations_fixture",
  item = "item_fixture",
  commitment = "commitment_fixture",
  finding = "exception_fixture";
const pager = (total) => ({
  number: 1,
  size: 50,
  total,
  pages: 1,
  has_next: false,
  has_previous: false,
});
const stock = {
  id: item,
  name: "Desk lamp",
  sku: "LAMP",
  unit: "pcs",
  physical: "20",
  reserved: "12",
  available: "8",
};
const reservation = {
  id: "reservation_fixture",
  item_id: item,
  item: "Desk lamp",
  sku: "LAMP",
  unit: "pcs",
  quantity: "12",
  status: "active",
  at: "2026-09-07T12:00:00Z",
  location: "Main warehouse",
  commitment_id: commitment,
  delivery_id: commitment,
};
const movement = {
  id: "movement_fixture",
  item_id: item,
  item: "Desk lamp",
  sku: "LAMP",
  unit: "pcs",
  quantity: "20",
  type: "receipt",
  at: "2026-09-07T10:00:00Z",
  from_location: null,
  to_location: "Main warehouse",
  correction_role: "normal",
};
const issue = {
  id: finding,
  class_id: "delivery_at_risk",
  context: "Müller · Desk lamp",
  severity: "high",
  title: "Delivery at risk",
  impact: "4 lamps need a reservation",
  record_type: "commitment",
  record_id: commitment,
  cause_ids: ["insufficient_reservation"],
  causal_values: { unreserved_quantity: "4", unit: "pcs" },
  trace: {},
  target: { kind: "commitment", id: commitment, delivery_id: commitment },
  guidance: "Reserve the remaining quantity or review the commitment.",
  observed_at: "2026-09-07T12:00:00Z",
};
const delivery = {
  id: commitment,
  tenant_id: tenant,
  party_id: "customer_fixture",
  counterparty: "Müller",
  item_id: item,
  item: "Desk lamp",
  unit: "pcs",
  location_id: "location_fixture",
  location: "Main warehouse",
  promised: "16",
  reserved: "12",
  fulfilled: "0",
  open: "16",
  status: "open",
  blockers: [],
  due_at: null,
};
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  requests.push({ path, method: req.method(), query: url.search });
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
    });
  if (path === "/api/playground/exception-catalog" && failCatalog)
    return reply({ detail: "Catalog unavailable" }, 503);
  if (path === "/api/playground/exception-catalog")
    return reply({
      version: 1,
      classes: [
        {
          id: "overdue",
          label: "Overdue delivery",
          description: "A delivery is past its due date.",
          owner: "Operations",
          clears_through: "Resolve the delivery cause.",
          severity: "high",
        },
      ],
    });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: tenant, name: "Northstar Commerce" },
        { id: "second_company", name: "Other company" },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference"))
    return reply({
      workspaces: [{ actions: [{ command: "reserve" }, { command: "record_movement" }] }],
    });
  if (path.endsWith("/dashboard"))
    return reply({
      totals: { open_deliveries: 1, exceptions: 1, pending_decisions: 0 },
      exceptions: [],
      inventory: [],
      facts: [],
      capabilities: {},
    });
  if (path.endsWith("/analytics"))
    return reply({
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
  if (path.includes("/warehouse/")) {
    if (failWarehouse) return reply({ detail: "Warehouse unavailable" }, 503);
    const view = path.split("/warehouse/")[1],
      empty = url.searchParams.get("q") === "missing";
    return reply({
      items: empty
        ? []
        : [view === "stock" ? stock : view === "reservations" ? reservation : movement],
      page: pager(empty ? 0 : 1),
      scope: {
        view,
        item_id: url.searchParams.get("item_id"),
        item: url.searchParams.has("item_id") ? "Desk lamp" : null,
      },
      observed_at: "2026-09-07T12:00:00Z",
    });
  }
  // Spec 180: the register reads the stored generation and reports its freshness.
  const generation = {
    projection: "exceptions",
    calculation_mode: "stored",
    state: resolved ? "pending" : "ready",
    processed_event_sequence: 7,
    target_event_sequence: resolved ? 8 : 7,
    completed_at: "2026-09-07T12:00:00Z",
    projection_version: 4,
    upstream_freshness: "unknown",
    consistency: "completed_snapshot",
  };
  if (path.endsWith("/attention"))
    return reply({
      items: resolved || url.searchParams.get("q") === "missing" ? [] : [issue],
      page: pager(resolved ? 0 : 1),
      observed_at: "2026-09-07T12:00:00Z",
      metadata: generation,
    });
  if (path.includes("/attention/"))
    return resolved
      ? reply(
          {
            detail: "This finding has cleared since the last calculation.",
            code: "finding_cleared",
            completed_at: "2026-09-07T12:00:00Z",
          },
          404,
        )
      : reply(issue);
  if (path.endsWith("/delivery-work")) return reply({ items: [delivery], page: pager(1) });
  if (path.endsWith(`/delivery-work/${commitment}`))
    return reply({
      case: delivery,
      inventory: {
        item_id: item,
        location_id: "location_fixture",
        unit: "pcs",
        physical: "20",
        reserved: "12",
        available: "8",
      },
      links: [],
      history: { items: [], has_more: false, next_cursor: null },
      observation: { observed_at: "2026-09-07T12:00:00Z", evidence_available: false },
    });
  if (path.includes("/inspector/"))
    return reply({
      title: "Supporting records",
      subtitle: "Desk lamp",
      meaning: "Recorded values",
      sections: [],
      technical_rows: [],
      source_payload: '{"untrusted":"<script>alert(1)</script>"}',
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const out = process.env.UNIFIED_OPERATIONS_SCREENSHOTS || "/private/tmp/reality-109-browser";
await mkdir(out, { recursive: true });
try {
  await page.goto(`${base}/app?tenant=${tenant}`);
  await page.getByRole("button").filter({ hasText: "Needs attention" }).click();
  await page.getByRole("heading", { name: "See what needs a closer look.", exact: true }).waitFor();
  await page.getByRole("button").filter({ hasText: "Delivery at risk" }).click();
  await page.getByRole("button", { name: "Open delivery", exact: true }).waitFor();
  const issueUrl = page.url();
  await page.reload();
  assert.equal(page.url(), issueUrl);
  await page.getByRole("button", { name: "Open delivery", exact: true }).click();
  await page.getByRole("heading", { name: "Müller", exact: true }).waitFor();
  await page.getByRole("link", { name: "Open inventory", exact: true }).click();
  await page.locator("[data-page-introduction] h1").waitFor();
  assert.ok(page.url().includes(`item=${item}`));
  await page.locator("tbody").getByRole("button", { name: "Reservations", exact: true }).click();
  await page.getByRole("button", { name: "Open delivery", exact: true }).waitFor();
  assert.ok(
    requests.some(
      (req) =>
        req.path.endsWith("/warehouse/reservations") && req.query.includes(`item_id=${item}`),
    ),
  );
  const inspect = page.getByRole("button", { name: "Inspect · Desk lamp", exact: true });
  await inspect.focus();
  await page.keyboard.press("Enter");
  await page.getByRole("dialog").waitFor();
  assert.ok(page.url().includes("entry=reservation_fixture"));
  await page.keyboard.press("Escape");
  assert.equal(await inspect.evaluate((node) => node === document.activeElement), true);
  await inspect.click();
  await page.reload();
  await page.getByRole("dialog").waitFor();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Movements", exact: true }).click();
  await page.locator("tbody").getByText("Receipt", { exact: true }).waitFor();
  await page.getByRole("textbox", { name: "Search warehouse", exact: true }).fill("missing");
  await page.getByText("No matching records", { exact: true }).waitFor();
  failWarehouse = true;
  await page.reload();
  await page.getByRole("alert").waitFor();
  failWarehouse = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.getByText("No matching records", { exact: true }).waitFor();
  await page.goto(`${base}/app/attention?tenant=${tenant}&exception=${finding}`);
  await page.getByRole("button", { name: "Check current state", exact: true }).waitFor();
  const catalogLink = page.getByRole("button", { name: "View all possible findings", exact: true });
  await catalogLink.click();
  const catalog = page.getByRole("dialog", { name: "Exception catalog", exact: true });
  await catalog.getByText("Could not load the exception catalog.", { exact: true }).waitFor();
  failCatalog = false;
  await catalog.getByRole("button", { name: "Retry", exact: true }).click();
  await catalog.getByText("Overdue delivery", { exact: true }).click();
  await page.screenshot({ path: `${out}/catalog.png`, fullPage: true });
  await catalog.getByText("A delivery is past its due date.", { exact: true }).waitFor();
  await catalog.getByRole("searchbox").fill("nothing-matches");
  await catalog.getByText("No matching exception classes.", { exact: true }).waitFor();
  await page.keyboard.press("Escape");
  assert.equal(await catalog.count(), 0);
  assert.equal(await catalogLink.evaluate((node) => node === document.activeElement), true);

  resolved = true;
  await page.getByRole("button", { name: "Check current state", exact: true }).click();
  await page.getByRole("alert").waitFor();
  await page.getByText("No current findings", { exact: true }).waitFor();
  resolved = false;
  await page.goto(
    `${base}/app/warehouse?tenant=${tenant}&warehouse_view=reservations&item=${item}&entry=reservation_fixture`,
  );
  await page.getByRole("dialog").waitFor();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="second_company"]').click();
  assert.equal(new URL(page.url()).searchParams.get("item"), null);
  assert.equal(new URL(page.url()).searchParams.get("entry"), null);
  for (language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        for (const view of ["stock", "reservations", "movements", "attention"]) {
          await page.goto(
            `${base}/app/${view === "attention" ? "attention" : "warehouse"}?tenant=${tenant}&warehouse_view=${view === "attention" ? "stock" : view}&${view === "attention" ? `exception=${finding}` : `item=${item}`}`,
          );
          await page.locator("h1").waitFor();
          if (view === "attention") await page.locator("pre").waitFor({ state: "attached" });
          else await page.locator("tbody tr").waitFor();
          assert.ok(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            `${language}/${theme}/${width}/${view} overflows`,
          );
          await page.screenshot({
            path: `${out}/${language}-${theme}-${width}-${view}.png`,
            fullPage: true,
          });
        }
      }
  assert.equal(requests.filter((row) => row.method !== "GET").length, 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: Home → finding → delivery → exact-item warehouse, reservation/movement views, Inspector reload/focus, empty/error/resolved states, company reset, no writes and 64 localized screenshots.",
  );
} catch (error) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  console.log(
    await page.locator("dialog").allTextContents(),
    errors,
    requests.filter((row) => row.path.includes("catalog")),
  );
  throw error;
} finally {
  await browser.close();
}
