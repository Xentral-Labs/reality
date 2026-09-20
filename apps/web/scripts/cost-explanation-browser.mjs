import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";

if (!process.env.PLAYWRIGHT_MODULE || !process.env.PLAYWRIGHT_EXECUTABLE)
  throw new Error("Set PLAYWRIGHT_MODULE and PLAYWRIGHT_EXECUTABLE.");
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const visible = process.env.PLAYWRIGHT_VISIBLE === "1";
const browser = await chromium.launch({
  headless: !visible,
  slowMo: visible ? 650 : 0,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const requests = [],
  errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenant = "cost_ui_company",
  other = "cost_ui_other",
  item = "cost_ui_item";
let costState = "ready";
const pager = { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false };
const reply = (route, body, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

await page.route("**/api/**", async (route) => {
  const request = route.request(),
    url = new URL(request.url()),
    path = url.pathname;
  requests.push({ path, method: request.method(), query: url.search });
  if (path === "/api/auth/me")
    return reply(route, {
      id: "cost_operator",
      email: "operator@example.test",
      display_name: "Operator",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply(route, {
      tenants: [
        { id: tenant, name: "Northstar Commerce" },
        { id: other, name: "Other company" },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference"))
    return reply(route, {
      command_count: 0,
      event_count: 0,
      projection_count: 0,
      fact_predicate_count: 0,
      projections: [],
      workspaces: [],
    });
  if (path.endsWith("/copilot"))
    return reply(route, {
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path.endsWith("/warehouse/stock"))
    return reply(route, {
      items: [
        {
          id: item,
          name: "Desk lamp",
          sku: "LAMP",
          unit: "pcs",
          physical: "40",
          reserved: "0",
          available: "40",
          incoming: "0",
          projected: "40",
        },
      ],
      page: pager,
      scope: { view: "stock", item_id: item, item: "Desk lamp" },
      observed_at: "2026-09-20T12:00:00Z",
    });
  if (path.endsWith("/cost-query")) {
    assert.equal(url.searchParams.get("kind"), "inventory");
    assert.equal(url.searchParams.get("scope_id"), item);
    const initialized = costState !== "uninitialized";
    const basis = {
      item_id: item,
      review_id: initialized ? "inventory_review_fixture" : null,
      currency: "EUR",
      base_unit: "pcs",
      acquisition_value: costState === "ready" ? "420.0000" : null,
      basis_acquisition_value: initialized ? "420.0000" : null,
      carrying_value: null,
      unit_cost: "10.500000",
      missing_basis: initialized
        ? ["carrying_value_not_assessed"]
        : ["inventory_scope_not_reviewed"],
    };
    return reply(route, {
      requested: { kind: "inventory", scope_id: item, review_id: null },
      resolved: initialized
        ? {
            currency: "EUR",
            base_unit: "pcs",
            effective_at: "2026-09-20T10:00:00Z",
            knowledge_at: "2026-09-20T12:00:00Z",
            review_id: "inventory_review_fixture",
          }
        : null,
      context_id: initialized ? "cost_context_fixture" : null,
      freshness: {
        state: costState,
        processed_event_sequence: initialized ? 7 : null,
        target_event_sequence: costState === "ready" ? 7 : initialized ? 8 : null,
      },
      result: costState === "ready" ? basis : null,
      basis_result: basis,
      persistence: { business_writes: false, projection_writes: false },
    });
  }
  if (path.includes("/inspector/"))
    return reply(route, {
      kind: "item",
      id: item,
      eyebrow: "Master data",
      title: "Desk lamp",
      subtitle: "LAMP",
      status: "Active",
      meaning: "Inventory item",
      business_reference: null,
      guidance: null,
      technical_rows: [],
      metrics: [],
      trail: [],
      sections: [],
    });
  return reply(route, { detail: "Fixture endpoint unavailable" }, 404);
});

const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const out = "/private/tmp/reality-234-cost-browser";
await mkdir(out, { recursive: true });
const url = (company = tenant) =>
  `${base}/app/warehouse?tenant=${company}&warehouse_view=stock&item=${item}&entry=${item}`;
try {
  await page.goto(url());
  const cost = page.getByRole("region", { name: "Cost explanation", exact: true });
  await cost.getByText("€420.00", { exact: true }).waitFor();
  await cost.getByText("Exact retained value: 420.0000", { exact: true }).waitFor();
  await cost.getByText("10.500000", { exact: true }).waitFor();
  await cost.getByText("carrying_value_not_assessed", { exact: true }).waitFor();
  const href = await cost.getByRole("link", { name: "Inspect cost basis" }).getAttribute("href");
  assert.ok(href?.includes("inspector_target_kind=cost_inventory_review"));

  costState = "stale";
  await page.reload();
  await cost.getByText("Retained basis — not current", { exact: false }).waitFor();
  assert.equal(await cost.getByText("€420.00", { exact: true }).count(), 0);

  costState = "uninitialized";
  await page.reload();
  await cost.getByText("No reviewed cost basis exists for this scope.", { exact: true }).waitFor();
  assert.equal(await cost.getByRole("link", { name: "Inspect cost basis" }).count(), 0);

  costState = "ready";
  await page.goto(url(other));
  await cost.getByText("€420.00", { exact: true }).waitFor();
  assert.ok(requests.some((row) => row.path === `/api/tenants/${other}/cost-query`));
  assert.ok(
    requests
      .filter((row) => row.method !== "GET")
      .every((row) => row.method === "POST" && row.path.endsWith("/search/resolve")),
  );
  assert.deepEqual(errors, []);
  await page.screenshot({ path: `${out}/inventory-cost-explanation.png`, fullPage: true });
  console.log(
    "PASS: exact inventory cost explanation, stale/missing states, Inspector trace, tenant scope and GET-only browser behavior.",
  );
} catch (error) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  console.log(errors, requests.slice(-30));
  throw error;
} finally {
  await browser.close();
}
