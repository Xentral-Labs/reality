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
const out = process.env.UNIFIED_SCREENSHOTS || "/private/tmp/reality-contribution-selector";
const context = (id) => ({ action_id: id, mode: "historical" });
const question = {
  from: "contribution_valuation",
  as: "o",
  measures: [
    "contribution_db1",
    "contribution_db2",
    "contribution_db2_covered",
    "contribution_db2_required",
  ],
  group_by: [{ field: "o.currency" }, { field: "o.base_unit" }],
};
const node = {
  key: "contribution_valuation",
  label: "Confirmed contribution valuation",
  category: "Warehouse",
  properties: [
    { key: "currency", label: "Currency", kind: "text" },
    { key: "base_unit", label: "Base unit", kind: "text" },
  ],
  edges: [],
  edges_in: [],
  measures: [
    ...["db2", "db2_covered", "db2_required"].map((key) => ({
      key: `contribution_${key}`,
      label: {
        db2: "DB2",
        db2_covered: "DB2 covered positions",
        db2_required: "DB2 required positions",
      }[key],
      unit: key === "db2" ? "currency" : "count",
      never_across: [],
    })),
    {
      key: "contribution_db1",
      label: "DB1",
      unit: "currency",
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
  position_count: 2,
}));
let saved,
  listState = "ready",
  fail = false,
  pending = false,
  asks = [];
await page.route("**/__contribution-selector", (route) =>
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
    window.openContribution = (question) => root.render(React.createElement(GraphSteps, { key: JSON.stringify(question), tenant: 'tenant', initialQuestion: question }));
    window.openContribution(${JSON.stringify(question)});
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
  if (url.pathname.endsWith("/graph/contribution-reviews")) {
    if (listState === "error") return respond({ detail: "Discovery unavailable" }, 503);
    if (listState === "empty") return respond({ items: [], next_cursor: null });
    const old = url.searchParams.has("cursor");
    return respond({ items: [options[old ? 1 : 0]], next_cursor: old ? null : "newer" });
  }
  if (url.pathname.endsWith("/graph/ask")) {
    const { question: q } = request.postDataJSON();
    asks.push(q);
    if (pending && q.contribution_cost_context?.mode === "current")
      return respond({ detail: { code: "cost_basis_pending", message: "New company data" } }, 422);
    if (fail)
      return respond(
        { detail: { code: "cost_basis_unavailable", message: "Selected cache unavailable" } },
        422,
      );
    const option = options.find(
      (item) => item.action_id === q.contribution_cost_context?.action_id,
    );
    assert.ok(option, "No implicit valuation allowed");
    return respond({
      question: q,
      rows: [
        {
          "o.currency": "EUR",
          "o.base_unit": "pcs",
          contribution_db2: null,
          contribution_db2_covered: 1,
          contribution_db2_required: 2,
          contribution_db1: option.action_id === "older" ? "840.0000" : "900.0000",
        },
      ],
      model_version: "sales.1",
      statements: 10,
      path: [],
      sql: "SELECT ...",
      editor: { path: null, parameters: {}, reason: "Contribution context requires JSON" },
      cost_basis: {
        kind: "contribution",
        action_id: option.action_id,
        generation_ids: ["gen-a", "gen-b"],
        context: {
          ...option,
          algorithm_version: "contribution-v1",
          review_ids: ["review-a", "review-b"],
        },
        coverage: { expected_positions: 2, available_positions: 2 },
        freshness: {
          state: q.contribution_cost_context.mode === "current" ? "ready" : "historical",
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
  await page.goto(`${base}/__contribution-selector`);
  const selector = page.getByLabel("Valuation basis", { exact: true });
  await selector.waitFor();
  assert.equal(await selector.inputValue(), "");
  assert.equal(asks.length, 0);
  assert.equal(await page.getByRole("alert").count(), 0);
  await page.getByRole("button", { name: "Older valuations", exact: true }).click();
  await selector.locator('option[value="older"]').waitFor({ state: "attached" });
  await selector.selectOption("older");
  await page.getByRole("heading", { name: "Historical valuation basis" }).waitFor();
  assert.equal(asks.at(-1).contribution_cost_context.action_id, "older");
  await page
    .getByText(
      "Historical contribution for the selected positions. Missing costs leave final margins unknown; coverage counts show which positions are complete.",
      { exact: true },
    )
    .waitFor();
  const unchanged = page.getByRole("checkbox", {
    name: "Require unchanged data since confirmation",
    exact: true,
  });
  await unchanged.check();
  await page
    .getByText(
      "No newer company data at read time. The selected scope and valuation cutoff remain unchanged.",
      { exact: true },
    )
    .waitFor();
  assert.equal(asks.at(-1).contribution_cost_context.mode, "current");
  await page.screenshot({ path: `${out}/valuation-desktop.png`, fullPage: true });
  await page.getByText("Valuation references", { exact: true }).click();
  assert.match(
    await page.getByRole("link", { name: "review-a", exact: true }).getAttribute("href"),
    /cost_contribution_review/,
  );
  await page.getByRole("tab", { name: "Cypher", exact: true }).click();
  assert.equal(await page.getByRole("textbox", { name: "Cypher query" }).count(), 0);
  await page.getByRole("tab", { name: "Result", exact: true }).click();
  await page.locator('summary[aria-label="Table actions"]').click();
  await page.getByRole("button", { name: "Save analysis", exact: true }).click();
  await page.getByRole("textbox", { name: "Report name" }).fill("Historical contribution");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByText("Saved", { exact: true }).waitFor();
  assert.equal(saved.contribution_cost_context.action_id, "older");
  assert.equal(saved.contribution_cost_context.mode, "current");
  await page.evaluate((q) => window.openContribution(q), saved);
  await page.getByRole("heading", { name: "Historical valuation basis" }).waitFor();
  assert.equal(await selector.inputValue(), "older");
  assert.equal(await unchanged.isChecked(), true);
  pending = true;
  await selector.selectOption("newer");
  await page
    .getByText(
      "New data arrived after this confirmation. Turn off the freshness requirement to inspect its historical values, or select a newly confirmed basis.",
      { exact: true },
    )
    .waitFor();
  assert.equal(await page.getByRole("heading", { name: "Historical valuation basis" }).count(), 0);
  await unchanged.uncheck();
  await page.getByRole("heading", { name: "Historical valuation basis" }).waitFor();
  assert.equal(asks.at(-1).contribution_cost_context.mode, "historical");
  pending = false;
  fail = true;
  await unchanged.check();
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
  await page.evaluate((q) => window.openContribution(q), question);
  await page.getByText("Could not load this view", { exact: true }).waitFor();
  listState = "empty";
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page
    .getByText("No confirmed joint contribution valuations on this page.", { exact: true })
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
