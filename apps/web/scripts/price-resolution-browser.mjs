// Spec 279 FR-013: the Price determination report asks for a business partner and an
// item, reads the existing live price service, and explains when no price applies.
import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177",
  out = "/private/tmp/reality-279-price-browser";
const errors = [],
  priceReads = [];
page.on("pageerror", (error) => errors.push(error.message));
let priced = false;
const guidanceCatalog = JSON.parse(
  await readFile(
    new URL("../../../packages/reality-core/config/resolution_guidance.json", import.meta.url),
    "utf8",
  ),
);

await page.route("**/api/**", async (route) => {
  const url = new URL(route.request().url()),
    path = url.pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (path === "/api/auth/me")
    return reply({
      id: "u1",
      email: "clerk@example.test",
      display_name: "Clerk",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "t1", name: "Northstar" }], default_tenant_id: "t1" });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path.endsWith("/application-reference"))
    return reply({
      command_count: 0,
      event_count: 0,
      projection_count: 1,
      fact_predicate_count: 0,
      commands: [],
      projections: [
        {
          name: "price_resolution",
          materialized_as: "price_resolution",
          calculation: "Original calculation",
          consumers: [],
          outputs: [],
          invalidated_by: [],
        },
      ],
      workspaces: [],
      resolution_guidance: guidanceCatalog,
      tool_catalog: {
        version: 1,
        topics: [{ key: "sales", label: "Sales" }],
        entries: [
          {
            id: "report:price_resolution",
            title: "Price determination",
            labels: {},
            description: "Understand how a price is selected.",
            topic: "sales",
            purpose: "read",
            commands: [],
            actions: [],
            views: [],
            projections: ["price_resolution"],
            mcp: [],
            discovery: [],
            related: [],
          },
        ],
        mcp_tools: [],
      },
    });
  if (path.endsWith("/suggestions/parties"))
    return reply({
      items: [{ value: "party_1", label: "Northwind Retail", description: "customer" }],
      allow_custom: false,
    });
  if (path.endsWith("/suggestions/items"))
    return reply({
      items: [{ value: "item_1", label: "Desk lamp", description: "LAMP" }],
      allow_custom: false,
    });
  if (path.endsWith("/prices/resolve")) {
    priceReads.push(Object.fromEntries(url.searchParams));
    return priced
      ? reply({
          unit_price: "12.5000",
          currency: "EUR",
          unit: "pcs",
          price_list_id: "pl_1",
          price_list_entry_id: "ple_1",
          source: "party",
          assignment_id: "asg_1",
          party_group_id: null,
          evaluated_at: "2026-09-26T10:00:00Z",
        })
      : reply({ detail: "No applicable price found." }, 404);
  }
  return reply({ detail: "Fixture endpoint unavailable" }, 404);
});

await mkdir(out, { recursive: true });
try {
  await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=views`);
  const capability = page.locator('[data-tool-capability="report:price_resolution"]');
  await capability.locator("button.tool-capability").click();
  await capability.locator("[data-tool-report-open]").click();
  const dialog = page.getByRole("dialog", { name: "Price determination", exact: true });
  const form = dialog.locator("[data-price-resolution]");
  await form.waitFor();
  await form.getByLabel("Business partner", { exact: true }).selectOption("party_1");
  await form.getByLabel("Item", { exact: true }).selectOption("item_1");
  await form.getByLabel("Unit", { exact: true }).fill("pcs");
  await form.getByRole("button", { name: "Determine price" }).click();
  await dialog
    .getByText("No price applies to this business partner and item", { exact: true })
    .waitFor();
  assert.deepEqual(priceReads[0], {
    party_id: "party_1",
    item_id: "item_1",
    quantity: "1",
    direction: "sales",
    currency: "EUR",
    unit: "pcs",
  });

  priced = true;
  await form.getByRole("button", { name: "Determine price" }).click();
  await dialog.locator("[data-price-result]").getByText("€12.50 / pcs", { exact: true }).waitFor();
  await dialog
    .locator("[data-price-result]")
    .getByText("Price list assigned to the business partner", { exact: true })
    .waitFor();
  assert.equal(
    await dialog.getByText("No price applies to this business partner and item").count(),
    0,
  );
  assert.deepEqual(errors, []);
  await page.screenshot({ path: `${out}/price-determination.png` });
  console.log("PASS: price determination inputs, live price read and the no-price explanation.");
} catch (error) {
  await page.screenshot({ path: `${out}/error.png` });
  console.log(errors);
  throw error;
} finally {
  await browser.close();
}
