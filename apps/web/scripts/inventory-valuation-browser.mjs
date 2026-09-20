// Synthetic HTTP fixtures verify the real editor; PostgreSQL tests prove financial admission.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
if (!process.env.PLAYWRIGHT_MODULE)
  throw new Error("Set PLAYWRIGHT_MODULE to run browser acceptance.");
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const page = await browser.newPage({ viewport: { width: 1280, height: 950 } });
const errors = [];
page.on("pageerror", (error) => {
  errors.push(error.message);
  console.error(error.message);
});
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5189";
const out = process.env.UNIFIED_SCREENSHOTS || "/private/tmp/reality-inventory-selector";
const context = (id) => ({ action_id: id, mode: "historical" });
const question = {
  from: "inventory_valuation",
  as: "o",
  measures: ["inventory_acquisition_value"],
  group_by: [{ field: "o.currency" }],
};
const node = {
  key: "inventory_valuation",
  label: "Confirmed inventory valuation",
  category: "Warehouse",
  properties: [{ key: "currency", label: "Currency", kind: "text" }],
  edges: [],
  edges_in: [],
  measures: [
    {
      key: "inventory_acquisition_value",
      label: "Inventory acquisition value",
      unit: { kind: "currency", column: "currency" },
      never_across: ["currency", "time"],
    },
  ],
};
const options = ["newer", "older"].map((action_id, index) => ({
  action_id,
  effective_at: `2026-09-${18 - index}T12:00:00Z`,
  knowledge_at: "2026-09-19T10:00:00Z",
  owner_party_id: "owner",
  owner_name: "Northstar Commerce",
  currency: "EUR",
  item_count: 2,
}));
let saved,
  listState = "ready",
  fail = false,
  asks = [];
await page.route("**/__inventory-selector", (route) =>
  route.fulfill({
    contentType: "text/html",
    body: `
  <html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="root"></div>
  <script type="module">
    import RefreshRuntime from '/@react-refresh';
    RefreshRuntime.injectIntoGlobalHook(window);
    window.$RefreshReg$ = () => {}; window.$RefreshSig$ = () => (type) => type;
    window.__vite_plugin_react_preamble_installed__ = true;
    const { default: React } = await import('/node_modules/.vite/deps/react.js');
    const { default: ReactDOM } = await import('/node_modules/.vite/deps/react-dom_client.js');
    const { GraphSteps } = await import('/src/unified/analytics/GraphSteps.tsx');
    await import('/src/tailwind.css');
    const root = ReactDOM.createRoot(document.getElementById('root'));
    window.openInventory = (question) => root.render(React.createElement(GraphSteps, { key: JSON.stringify(question), tenant: 'tenant', initialQuestion: question }));
    window.openInventory(${JSON.stringify(question)});
  </script></body></html>`,
  }),
);
await page.route("**/api/**", async (route) => {
  const request = route.request(),
    url = new URL(request.url());
  const respond = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (url.pathname.endsWith("/graph/catalog"))
    return respond({ nodes: [node], limits: { result_rows: 1000 }, model_version: "sales.1" });
  if (url.pathname.endsWith("/graph/inventory-reviews")) {
    if (listState === "error") return respond({ detail: "Discovery unavailable" }, 503);
    if (listState === "empty") return respond({ items: [], next_cursor: null });
    const old = url.searchParams.has("cursor");
    return respond({ items: [options[old ? 1 : 0]], next_cursor: old ? null : "newer" });
  }
  if (url.pathname.endsWith("/graph/ask")) {
    const { question: q } = request.postDataJSON();
    asks.push(q);
    if (fail)
      return respond(
        { detail: { code: "cost_basis_unavailable", message: "Selected cache unavailable" } },
        422,
      );
    const option = options.find((item) => item.action_id === q.inventory_cost_context?.action_id);
    assert.ok(option, "No implicit valuation allowed");
    return respond({
      question: q,
      rows: [
        {
          "o.currency": "EUR",
          inventory_acquisition_value: option.action_id === "older" ? "840.0000" : "900.0000",
        },
      ],
      model_version: "sales.1",
      statements: 10,
      path: [],
      sql: "SELECT ...",
      editor: { path: null, parameters: {}, reason: "Inventory context requires JSON" },
      cost_basis: {
        action_id: option.action_id,
        generation_ids: ["gen-a", "gen-b"],
        context: {
          ...option,
          algorithm_version: "inventory-v1",
          review_ids: ["review-a", "review-b"],
        },
        coverage: { expected_items: 2, available_items: 2 },
        freshness: {
          state: "historical",
          processed_event_sequence: 4,
          target_event_sequence: null,
        },
      },
    });
  }
  if (url.pathname.endsWith("/graph/reports/changes") && request.method() === "POST") {
    const change = request.postDataJSON();
    saved = change.question;
    return respond({
      id: "report",
      name: change.name,
      kind: "graph",
      definition: saved,
      model_version: "sales.1",
      revision: 1,
    });
  }
  return respond({ detail: `Unexpected fixture request ${url.pathname}` }, 404);
});
try {
  await mkdir(out, { recursive: true });
  await page.goto(`${base}/__inventory-selector`);
  const selector = page.getByLabel("Valuation basis", { exact: true });
  await selector.waitFor();
  assert.equal(await selector.inputValue(), "");
  assert.equal(asks.length, 0);
  assert.equal(await page.getByRole("alert").count(), 0);
  await page.getByRole("button", { name: "Older valuations", exact: true }).click();
  await selector.locator('option[value="older"]').waitFor({ state: "attached" });
  await selector.selectOption("older");
  await page.getByRole("heading", { name: "Historical valuation basis" }).waitFor();
  assert.equal(asks.at(-1).inventory_cost_context.action_id, "older");
  await page.screenshot({ path: `${out}/valuation-desktop.png`, fullPage: true });
  await page.getByText("Valuation references", { exact: true }).click();
  assert.match(
    await page.getByRole("link", { name: "review-a", exact: true }).getAttribute("href"),
    /cost_inventory_review/,
  );
  await page.getByRole("tab", { name: "Cypher", exact: true }).click();
  assert.equal(await page.getByRole("textbox", { name: "Cypher query" }).count(), 0);
  await page.getByRole("tab", { name: "Result", exact: true }).click();
  await page.locator('summary[aria-label="Table actions"]').click();
  await page.getByRole("button", { name: "Save analysis", exact: true }).click();
  await page.getByRole("textbox", { name: "Report name" }).fill("Historical inventory");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByText("Saved", { exact: true }).waitFor();
  assert.equal(saved.inventory_cost_context.action_id, "older");
  await page.evaluate((q) => window.openInventory(q), saved);
  await page.getByRole("heading", { name: "Historical valuation basis" }).waitFor();
  assert.equal(await selector.inputValue(), "older");
  fail = true;
  await selector.selectOption("newer");
  await page
    .getByText("The selected valuation is not fully available yet.", { exact: true })
    .waitFor();
  assert.equal(await page.getByRole("heading", { name: "Historical valuation basis" }).count(), 0);
  await page.getByRole("button", { name: "Clear valuation selection", exact: true }).click();
  assert.equal(await selector.inputValue(), "");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: `${out}/valuation-mobile.png`, fullPage: true });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  fail = false;
  await selector.selectOption("newer");
  await page.getByRole("heading", { name: "Historical valuation basis" }).waitFor();
  await page.screenshot({ path: `${out}/valuation-mobile-selected.png`, fullPage: true });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  listState = "error";
  await page.evaluate((q) => window.openInventory(q), question);
  await page.getByText("Could not load this view", { exact: true }).waitFor();
  listState = "empty";
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page
    .getByText("No confirmed joint inventory valuations on this page.", { exact: true })
    .waitFor();
  listState = "ready";
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await selector.locator('option[value="newer"]').waitFor({ state: "attached" });
  assert.equal(await selector.inputValue(), "");
  assert.deepEqual(errors, []);
  console.log(
    "PASS: explicit paged selection, historical context, save/reopen, unavailable basis, clearing, trace links and mobile layout.",
  );
} catch (error) {
  console.error(await page.locator("body").innerText());
  await page.screenshot({ path: `${out}/failure.png`, fullPage: true });
  throw error;
} finally {
  await browser.close();
}
