import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { reference } from "./tool-catalog-fixture.mjs";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const errors = [],
  writes = [];
let language = "en",
  failCatalog = false;
page.on("pageerror", (e) => errors.push(e.message));
const pager = { number: 1, size: 50, total: 0, pages: 1, has_next: false, has_previous: false };
const itemHit = {
  key: "item:exact_item",
  family: "item",
  group: "items_locations",
  label: "Hidden list item",
  secondary: "SKU-42",
  roles: [],
  tier: 0,
  sort_key: [0, 1, 1, 1, "hidden list item", "item", "exact_item"],
  target: { kind: "record", record_kind: "item", id: "exact_item" },
};
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname;
  if (!["GET", "HEAD"].includes(req.method()) && !/\/search\/(query|resolve)$/.test(path))
    writes.push(path);
  let body = {},
    status = 200;
  if (path === "/api/auth/me")
    body = {
      id: "discovery_user",
      email: "discovery@example.test",
      status: "active",
      language,
      locale: language === "de" ? "de-DE" : "en-GB",
      timezone: "UTC",
    };
  else if (path === "/api/v1/bootstrap")
    body = {
      tenants: [
        { id: "discovery_company", name: "Discovery test", role: "owner" },
        { id: "second_company", name: "Second company", role: "member" },
      ],
      default_tenant_id: "discovery_company",
    };
  else if (path.endsWith("/search/query")) {
    const input = req.postDataJSON();
    if (input.query === "slow-old") await new Promise((resolve) => setTimeout(resolve, 500));
    body = {
      provider: input.provider,
      scope: "fixture",
      items:
        input.provider === "items_locations" &&
        input.query === "SKU-42" &&
        path.includes("discovery_company")
          ? [itemHit]
          : [],
      has_more: false,
      next_cursor: null,
    };
  } else if (path.endsWith("/search/resolve"))
    body = { items: path.includes("discovery_company") ? [itemHit] : [] };
  else if (path.endsWith("/analytics/graph/templates"))
    body = {
      templates: [
        {
          key: "historical-fixture",
          label: "Historical fixture",
          about: "Choose a date",
          snapshot: "snapshot_date",
          question: {},
        },
      ],
    };
  else if (path.endsWith("/master-data/item/exact_item"))
    body = {
      id: "exact_item",
      name: "Hidden list item",
      sku: "SKU-42",
      family: "item",
      is_active: false,
      preview_sections: [],
      contributing_systems: [],
    };
  else if (path.endsWith("/master-data")) body = { items: [], page: pager };
  else if (path.endsWith("/application-reference")) {
    body = failCatalog ? { detail: "Fixture unavailable" } : reference;
    status = failCatalog ? 503 : 200;
  } else if (path.endsWith("/copilot"))
    body = {
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
      active_session_id: null,
    };
  else if (path.includes("/warehouse/"))
    body = { scope: { view: path.split("/").at(-1) }, items: [], page: pager };
  else if (path.includes("/finance/"))
    body = { view: path.split("/").at(-1), items: [], totals: [], page: pager };
  else if (path.endsWith("/reference-choices")) body = { items: [], page: pager };
  else {
    body = { detail: "Fixture read unavailable" };
    status = 503;
  }
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
});
const base = process.env.BASE_URL || "http://localhost:8091";
const go = async (path) => {
  await page.goto(
    base + "/app/" + path + (path.includes("?") ? "&" : "?") + "tenant=discovery_company",
  );
  await page.locator("[data-shell-header]").waitFor();
};
await go("inspector?inspector_view=commands");
await page.keyboard.press("Control+k");
const palette = page.locator("[data-action-menu]:popover-open");
await palette.getByRole("combobox").waitFor();
await palette.getByRole("combobox").fill("Warehouse");
await page.keyboard.press("ArrowDown");
await page.keyboard.press("Enter");
await page.waitForURL(/warehouse/);
await page.keyboard.press("Control+k");
await palette.getByRole("combobox").fill("Record shipment");
await palette.getByRole("option").filter({ hasText: "Record shipment" }).first().click();
await page.locator("dialog[open]").waitFor();
await page.keyboard.press("Control+k");
assert.equal(await palette.count(), 0);
assert.deepEqual(writes, []);
await page.keyboard.press("Escape");
await page.locator("[data-action-launcher] > button").click();
await palette.getByRole("combobox").waitFor();
assert.equal(await palette.getByRole("combobox").inputValue(), "");
await page.keyboard.press("Escape");
assert.equal(await palette.count(), 0);
await page.keyboard.press("Control+k");
const oldRequest = page.waitForRequest(
  (request) =>
    request.url().endsWith("/search/query") && request.postDataJSON()?.query === "slow-old",
);
await palette.getByRole("combobox").fill("slow-old");
await oldRequest;
await palette.getByRole("combobox").fill("SKU-42");
const exact = palette.getByRole("option").filter({ hasText: "Hidden list item" });
await exact.waitFor();
await page.waitForTimeout(650);
await exact.waitFor();
await palette.getByRole("button", { name: "Pin Hidden list item", exact: true }).click();
assert(!(await page.evaluate(() => JSON.stringify(localStorage).includes("Hidden list item"))));
await palette.getByRole("combobox").focus();
await page.keyboard.press("ArrowDown");
await page.keyboard.press("Enter");
await page.waitForURL(/record=exact_item/);
await page
  .locator("[data-selected-master-detail]")
  .getByText("Hidden list item", { exact: true })
  .waitFor();
await page.keyboard.press("Control+k");
await palette.getByRole("combobox").fill("Historical fixture");
await palette.getByRole("option").filter({ hasText: "Historical fixture" }).click();
await page.locator('input[type="date"]').waitFor();
assert.equal(await page.locator('input[type="date"]').inputValue(), "");
assert.equal(
  await page.getByRole("button", { name: "Use template", exact: true }).isDisabled(),
  true,
);
await page.keyboard.press("Control+k");
await palette.getByRole("combobox").fill("Second company");
await palette.getByRole("option").filter({ hasText: "Second company" }).click();
await page.waitForURL(/tenant=second_company/);
await page.keyboard.press("Control+k");
assert.equal(await palette.getByText("Hidden list item", { exact: true }).count(), 0);
await page.keyboard.press("Escape");
assert.deepEqual(errors, []);
assert.deepEqual(writes, []);
await browser.close();
console.log(
  "Command palette navigation, keyboard and form cancellation passed; zero business writes.",
);
