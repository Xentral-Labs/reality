import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { reference } from "./tool-catalog-fixture.mjs";
import { openPageActions } from "./page-actions.mjs";
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
await page.route("**/api/**", (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname;
  if (!["GET", "HEAD"].includes(req.method())) writes.push(path);
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
      tenants: [{ id: "discovery_company", name: "Discovery test", role: "owner" }],
      default_tenant_id: "discovery_company",
    };
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
await mkdir("/private/tmp/action-discovery-screens", { recursive: true });
await go("inspector?inspector_view=commands");
const tree = page.locator("[data-tool-catalog]");
await tree.waitFor();
await tree.locator('[data-tool-capability="form:movement_create"] > button').focus();
await page.keyboard.press("Enter");
assert.equal(await tree.getByRole("button", { name: "Record shipment", exact: true }).count(), 1);
await tree.locator('[data-tool-capability="form:receipt"] > button').click();
assert.equal(await tree.getByRole("button", { name: "Receive goods", exact: true }).count(), 1);
await tree.getByRole("searchbox").fill("state_lot_expiry");
assert.equal(await tree.locator('[data-tool-capability="command:state_lot_expiry"]').count(), 1);
await tree.getByRole("searchbox").fill("no-match-985");
assert.equal(await tree.getByText("No matching records", { exact: true }).count(), 1);
await tree.getByRole("button", { name: "Reset filters", exact: true }).click();
if (process.env.DIRECTORY_ONLY === "1") {
  await browser.close();
  console.log("Action directory keyboard, search, expansion and preserved state checks passed.");
  process.exit(0);
}
if (process.env.LAUNCHER_ONLY !== "1") {
  // Page actions sit behind "More actions" in catalog order (menus are the default
  // presentation); read them back from the menu.
  const pageActions = async () => {
    await openPageActions(page);
    return page.locator(".register-action-menu button").allTextContents();
  };
  for (const view of ["stock", "reservations", "movements"]) {
    await go("warehouse?warehouse_view=" + view);
    const expected = {
      stock: [],
      reservations: ["Reserve stock", "Release reservation"],
      movements: [
        "Record opening stock",
        "Receive goods",
        "Record shipment",
        "Decide returned goods",
        "Dispatch package",
        "Receive package",
        "Correct movement",
      ],
    }[view];
    if (!expected.length) {
      assert.equal(await page.getByText("More actions", { exact: true }).count(), 0);
      continue;
    }
    await page.getByText("More actions", { exact: true }).click();
    const buttons = await page.locator(".register-action-menu button").allTextContents();
    assert.deepEqual(buttons, expected);
  }
  for (const flow of ["receivable", "payable", "customer-credit", "supplier-balance"]) {
    for (const view of ["open-items", "payments", "journal"]) {
      await go(`finance?finance_view=${view}&flow=${flow}`);
      const buttons = await pageActions();
      if (flow === "payable" || flow === "supplier-balance")
        assert.ok(!buttons.some((s) => /credit note|refund|customer/i.test(s)), buttons.join(","));
      if (view === "journal")
        assert.deepEqual(buttons, ["Reverse posting", "Import opening positions"]);
    }
  }
  await go("finance?finance_view=payments&flow=receivable&direction=outgoing");
  assert.deepEqual(await pageActions(), ["Record supplier payment", "Import opening positions"]);
}
// The global launcher is the command palette inside the [data-action-menu] popover: typed
// queries list actions as options.
const launcher = page.locator("[data-action-menu]");
const search = (query) =>
  launcher
    .getByRole("combobox", { name: "Search or start an action" })
    .or(launcher.getByRole("textbox", { name: "Search or start an action" }))
    .first()
    .fill(query);
await go("warehouse?warehouse_view=movements");
await page.locator("[data-action-launcher] > button").click();
await search("New supplier invoice");
await launcher
  .getByRole("option", { name: /^New supplier invoice/ })
  .first()
  .waitFor();
await search("Record shipment");
await launcher
  .getByRole("option", { name: /^Record shipment/ })
  .first()
  .click();
await page.locator("dialog").waitFor();
await page.keyboard.press("Control+k");
assert.equal(await page.locator("[data-action-menu]:popover-open").count(), 0);
assert.equal(writes.length, 0, JSON.stringify(writes));
// A failed catalog is visible and retryable, rather than displaying stale candidates.
failCatalog = true;
await go("warehouse?warehouse_view=stock");
await page.locator("[data-action-launcher] > button").click();
// The catalog's own failure, not the separately unavailable report templates.
const catalogRetry = launcher
  .locator("div", { has: page.getByText("Could not load this view", { exact: true }) })
  .last()
  .getByRole("button", { name: "Retry", exact: true });
await catalogRetry.waitFor();
failCatalog = false;
await catalogRetry.click();
await search("Reserve stock");
await launcher
  .getByRole("option", { name: /^Reserve stock/ })
  .first()
  .waitFor();
language = "de";
await page.setViewportSize({ width: 390, height: 844 });
await go("inspector?inspector_view=commands");
await page.locator("[data-tool-catalog]").getByRole("searchbox").fill("Haltbarkeit");
assert.ok((await page.locator("[data-tool-capability]:visible").count()) > 0);
assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
await page.screenshot({
  path: "/private/tmp/action-discovery-screens/mobile-de.png",
  fullPage: true,
});
await page.locator("[data-navigation-opener]").click();
await page.locator("[data-action-launcher] > button").click();
const bounds = await page.locator("[data-action-menu]").boundingBox();
assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= 390, JSON.stringify(bounds));
await page.screenshot({
  path: "/private/tmp/action-discovery-screens/mobile-menu-de.png",
  animations: "disabled",
});
assert.deepEqual(errors, []);
assert.deepEqual(writes, []);
await browser.close();
console.log("Action directory and context browser checks passed; zero business writes.");
