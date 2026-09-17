// HTTP fixtures prove UI interaction; PostgreSQL tests prove business semantics.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
const tenant = "analytics_fixture";
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5185";
let language = "en",
  calls = 0,
  fail = false;
let createdChats = 0,
  failChatCreation = false;
const sentChatMessages = [];
const errors = [],
  reports = new Map();
page.on("pageerror", (error) => errors.push(error.message));
const dimensions = [
  { key: "customer_id", label: "Customer", type: "id", operators: ["eq", "ne"] },
  { key: "product_id", label: "Product", type: "id", operators: ["eq", "ne"] },
  { key: "ordered_at", label: "Order date", type: "datetime", operators: ["gte", "lt"] },
  { key: "unit", label: "Unit", type: "text", operators: ["eq"] },
];
const measures = [
  { key: "order_count", label: "Order count", aggregation: "distinct", partition: null },
  { key: "ordered_quantity", label: "Ordered quantity", aggregation: "sum", partition: "unit" },
];
await page.route("**/api/**", async (route) => {
  const request = route.request(),
    path = new URL(request.url()).pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
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
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.endsWith("/copilot/sessions")) {
    if (failChatCreation) return reply({ detail: "Chat creation failed" }, 503);
    createdChats++;
    return reply({ id: `analysis_chat_${createdChats}`, title: "New chat" });
  }
  if (path.endsWith("/messages")) {
    sentChatMessages.push({ path, body: request.postDataJSON() });
    return reply({
      user: { id: "analysis-question", content: request.postDataJSON().message },
      assistant: { id: "analysis-answer", content: "Analysis received." },
    });
  }
  if (path.endsWith("/copilot")) {
    const active = new URL(request.url()).searchParams.get("session_id") || "previous_chat";
    return reply({
      sessions: [
        { id: "previous_chat", title: "Previous discussion" },
        ...Array.from({ length: createdChats }, (_, i) => ({
          id: `analysis_chat_${i + 1}`,
          title: "New chat",
        })),
      ],
      active_session_id: active,
      messages:
        active === "previous_chat"
          ? [
              {
                id: "old_message",
                role: "user",
                content: "Keep my previous discussion",
                created_at: "2026-09-13T08:00:00Z",
              },
            ]
          : [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  }
  if (path.endsWith("/analytics/catalog"))
    return reply({
      version: 1,
      datasets: [
        {
          key: "sales_order_lines",
          label: "Sales order lines",
          grain: "document_line",
          dimensions,
          measures,
        },
      ],
      starters: [],
      limits: {},
    });
  if (path.endsWith("/analytics/query")) {
    calls++;
    if (fail)
      return reply(
        { detail: { message: "Please narrow this query.", code: "query_too_broad" } },
        422,
      );
    const definition = request.postDataJSON().definition;
    return reply({
      executed_definition: definition,
      definition_fingerprint: "fixture",
      columns: [
        { key: "customer_id", label: "Customer", type: "id" },
        { key: "unit", label: "Unit", type: "text" },
        ...measures
          .filter((m) => definition.measures.includes(m.key))
          .map((m) => ({
            key: m.key,
            label: m.label,
            type: m.key === "order_count" ? "integer" : "decimal",
          })),
      ],
      rows: [
        {
          currency: "EUR",
          customer_id: "customer_one",
          customer: "Nordlicht GmbH",
          unit: "pcs",
          order_count: 4,
          ordered_quantity: "12.125",
        },
        {
          currency: "USD",
          customer_id: "customer_two",
          customer: "Studio West",
          unit: "pcs",
          order_count: 2,
          ordered_quantity: "7",
        },
      ],
      population_totals: [{ unit: "pcs", order_count: 6, ordered_quantity: "19.125" }],
      comparison: null,
      page: { has_more: false, next_cursor: null, total: 2 },
      metadata: {
        observed_at: "2026-09-13T08:00:00Z",
        resolved_window: null,
        missing_values: { ordered_quantity: 0 },
        undated_excluded: 0,
        history_scope: "matching_interpreted_retained_records",
      },
    });
  }
  if (path.endsWith("/analytics/query/contributors"))
    return reply({
      records: [
        {
          record_id: "line_one",
          record_kind: "document_line",
          order: "SO-1007",
          customer: "Nordlicht GmbH",
        },
      ],
      total: 1,
      has_more: false,
    });
  if (path.endsWith("/analytics/export"))
    return reply({
      csv: "customer,quantity\nNordlicht,12.125\n",
      filename: "analysis.csv",
      row_count: 1,
    });
  if (path.endsWith("/analytics/reports/changes")) {
    const body = request.postDataJSON();
    const old = reports.get(body.report_id);
    if (body.operation === "delete") {
      reports.delete(body.report_id);
      return reply({ ...old, deleted: true });
    }
    const report = {
      id: body.operation === "duplicate" ? body.request_id : old?.id || body.request_id,
      name: body.name,
      definition: body.definition || old?.definition,
      revision: (old?.revision || 0) + 1,
      updated_at: "2026-09-13T08:00:00Z",
      deleted: false,
    };
    reports.set(report.id, report);
    return reply(report);
  }
  if (path.endsWith("/analytics/reports"))
    return reply({ records: [...reports.values()], has_more: false, next_cursor: null });
  if (path.includes("/inspector/"))
    return reply({
      title: "SO-1007",
      subtitle: "Order evidence",
      sections: [],
      technical_rows: [],
      source_payload: '{"quantity":"12.125"}',
    });
  if (path.includes("/suggestions/")) return reply({ items: [], allow_custom: true });
  return reply({ detail: "Unavailable fixture endpoint" }, 404);
});
const out = "/private/tmp/reality-185-browser";
await mkdir(out, { recursive: true });
try {
  const retiredReads = [];
  page.on("request", (request) => {
    if (
      request.method() === "GET" &&
      /\/analytics(?:\/contributors)?$/.test(new URL(request.url()).pathname) &&
      request.url().includes("/api/")
    )
      retiredReads.push(request.url());
  });
  for (const query of [
    "",
    "&analytics_view=overview&days=90&metric=shipped",
    "&analytics_view=invalid",
  ]) {
    await page.goto(`${base}/app/analytics?tenant=${tenant}${query}`);
    const tabs = page.getByRole("navigation", { name: "Analytics views" });
    await tabs.getByRole("button", { name: "Explore", exact: true }).waitFor();
    assert.deepEqual(await tabs.getByRole("button").allTextContents(), ["Explore", "My reports"]);
    assert.equal(
      await tabs.getByRole("button", { name: "Explore", exact: true }).getAttribute("aria-pressed"),
      "true",
    );
    await page.getByRole("button", { name: "Run analysis", exact: true }).waitFor();
  }
  const analyticsLink = page.getByRole("link", { name: "Analytics", exact: true });
  await analyticsLink.waitFor();
  assert.equal(await page.locator("#analytics-navigation-label").count(), 0);
  assert.equal(await analyticsLink.getAttribute("data-sidebar-tooltip"), "Analytics");
  assert.equal(await analyticsLink.getAttribute("aria-current"), "page");
  assert.deepEqual(
    await page
      .getByRole("navigation", { name: "Workspaces", exact: true })
      .getByRole("link")
      .allTextContents(),
    ["Sales", "Purchasing", "Warehouse", "Finance", "Master data", "Analytics"],
  );
  await page.getByRole("button", { name: "Collapse sidebar", exact: true }).click();
  await analyticsLink.focus();
  assert.equal(await analyticsLink.getAttribute("aria-label"), "Analytics");
  await page.getByRole("button", { name: "Expand sidebar", exact: true }).click();
  const activeView = page
    .getByRole("navigation", { name: "Analytics views" })
    .getByRole("button", { name: "Explore", exact: true });
  await activeView.waitFor();
  assert.equal(
    await page.getByRole("heading", { name: "Reports", exact: true }).count(),
    1,
    "Reports has one title in the shared shell, without a duplicate below the tabs",
  );
  assert.deepEqual(
    await activeView.evaluate((button) => {
      const style = getComputedStyle(button);
      return [
        button.getAttribute("aria-pressed"),
        style.borderBottomWidth,
        style.borderRadius,
        style.backgroundColor,
      ];
    }),
    ["true", "2px", "0px", "rgba(0, 0, 0, 0)"],
    "Analytics uses the shared underlined page tabs, not filled action buttons",
  );
  for (const name of ["Data perspective", "Sort by"]) {
    const control = page.getByRole("combobox", { name, exact: true });
    const style = await control.evaluate((element) => {
      const css = getComputedStyle(element);
      return { border: css.borderTopWidth, height: element.getBoundingClientRect().height };
    });
    assert.equal(style.border, "1px", `${name} has a visible control boundary`);
    assert.ok(style.height >= 44, `${name} has a full-size click target`);
    await control.focus();
    assert.equal(await control.evaluate((element) => element === document.activeElement), true);
  }
  const sort = page.getByRole("combobox", { name: "Sort by", exact: true });
  await sort.press("c");
  await sort.press("Tab");
  assert.notEqual(await sort.inputValue(), "", "native keyboard selection works");
  await sort.selectOption("");
  const filters = page.locator("summary").filter({ hasText: /^Filters$/ });
  await filters.focus();
  await filters.press("Enter");
  await page.getByRole("combobox", { name: "Match conditions" }).waitFor();
  await filters.press("Enter");
  await page.getByRole("button", { name: "Run analysis", exact: true }).click();
  await page.getByRole("heading", { name: "Analysis results" }).waitFor();
  assert.equal(calls, 1);
  await page.getByRole("checkbox", { name: "Order count", exact: true }).uncheck();
  await page.getByText("Results show the last executed settings.", { exact: false }).waitFor();
  assert.equal(calls, 1, "editing does not execute automatically");
  fail = true;
  await page.getByRole("button", { name: "Run analysis", exact: true }).click();
  await page.getByText("This analysis is too broad. Narrow the period or filters.").waitFor();
  assert.equal(
    await page.getByRole("heading", { name: "Analysis results" }).count(),
    1,
    "errors retain previous successful results",
  );
  fail = false;
  await page.getByRole("button", { name: "Bar chart", exact: true }).click();
  await page.getByRole("img", { name: "Analysis chart", exact: true }).waitFor();
  const partitionChoices = page.getByRole("group", { name: "Show in chart" });
  const chart = page.getByRole("img", { name: "Analysis chart", exact: true });
  assert.equal(
    await partitionChoices
      .getByRole("button", { name: "EUR · pcs", exact: true })
      .getAttribute("aria-pressed"),
    "true",
  );
  assert.match(await chart.textContent(), /Nordlicht/);
  assert.doesNotMatch(await chart.textContent(), /Studio West/);
  const beforeSwitch = calls;
  await partitionChoices.getByRole("button", { name: "USD · pcs", exact: true }).click();
  assert.match(await chart.textContent(), /Studio West/);
  assert.doesNotMatch(await chart.textContent(), /Nordlicht/);
  assert.equal(calls, beforeSwitch, "partition selection does not execute another query");
  await page.getByRole("button", { name: "Line chart", exact: true }).click();
  await partitionChoices.getByRole("button", { name: "USD · pcs", exact: true }).click();
  assert.match(await chart.textContent(), /Studio West/);
  await page.getByRole("button", { name: "Bar chart", exact: true }).click();
  await page.screenshot({ path: `${out}/desktop.png`, fullPage: true });
  await page
    .getByRole("button", { name: "Supporting records: Ordered quantity", exact: true })
    .first()
    .click();
  await page.getByRole("button", { name: "SO-1007 Nordlicht GmbH" }).waitFor();
  await page.getByRole("button", { name: "Save report", exact: true }).click();
  await page.getByRole("textbox", { name: "Report name" }).fill("Customer demand");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByText("Report saved.", { exact: true }).waitFor();
  await page.getByRole("button", { name: "My reports", exact: true }).click();
  await page.getByRole("heading", { name: "Customer demand" }).waitFor();
  await page.getByRole("button", { name: "Customer demand", exact: false }).first().click();
  await page.getByRole("heading", { name: "Customer demand" }).waitFor();
  assert.equal(
    reports.values().next().value.definition.presentation.kind,
    "bar",
    "saved presentation is retained",
  );
  await page.getByRole("button", { name: "My reports", exact: true }).click();
  await page.getByRole("button", { name: "Rename", exact: true }).click();
  await page.getByRole("textbox", { name: "Report name" }).fill("Updated demand");
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page.getByRole("heading", { name: "Updated demand", exact: true }).waitFor();
  await page.getByRole("button", { name: "Duplicate", exact: true }).click();
  await page.getByRole("textbox", { name: "Report name" }).fill("Demand copy");
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page.getByRole("heading", { name: "Demand copy", exact: true }).waitFor();
  const copied = page
    .locator("article")
    .filter({ has: page.getByRole("heading", { name: "Demand copy", exact: true }) });
  await copied.getByRole("button", { name: "Delete", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page.getByRole("dialog", { name: "Change report" }).waitFor({ state: "hidden" });
  assert.equal(reports.size, 1);
  await page.getByRole("heading", { name: "Updated demand", exact: true }).click();
  const discuss = page.getByRole("button", { name: "Start new chat about analysis", exact: true });
  const dock = page.locator("[data-global-chat]");
  const composer = dock.getByRole("textbox", { name: "Ask about your company", exact: true });
  await composer.fill("Keep my draft");
  failChatCreation = true;
  await discuss.click();
  await dock.getByRole("alert").filter({ hasText: "Chat creation failed" }).waitFor();
  assert.equal(await composer.inputValue(), "Keep my draft");
  assert.equal(createdChats, 0);
  failChatCreation = false;
  await discuss.click();
  await page.waitForURL(/session=analysis_chat_1/);
  await page.getByText("Attached analysis", { exact: false }).waitFor();
  assert.equal(createdChats, 1);
  assert.equal(sentChatMessages.length, 0, "opening a chat does not send a message");
  assert.equal(await dock.getByText("Keep my previous discussion", { exact: true }).count(), 0);
  assert.equal(await composer.inputValue(), "");
  await composer.fill("Explain this analysis");
  const messageResponse = page.waitForResponse((response) =>
    new URL(response.url()).pathname.endsWith("/messages"),
  );
  await composer.press("Enter");
  await messageResponse;
  assert.ok(sentChatMessages[0].path.includes("analysis_chat_1"));
  assert.ok(JSON.stringify(sentChatMessages[0].body).includes("sales_order_lines"));
  await dock.getByRole("button", { name: "Conversation history" }).click();
  await dock
    .getByRole("combobox", { name: "Conversation", exact: true })
    .selectOption("previous_chat");
  await dock.getByText("Keep my previous discussion", { exact: true }).waitFor();
  assert.equal(await dock.getByText("Attached analysis", { exact: false }).count(), 0);

  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export CSV", exact: true }).click();
  assert.equal((await downloaded).suggestedFilename(), "analysis.csv");
  await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: `${out}/mobile.png`, fullPage: true });
  assert.ok(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    "no page-level horizontal overflow",
  );
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  await page.waitForFunction(() => {
    const style = getComputedStyle(document.querySelector(".analytics-explorer select"));
    return style.backgroundColor === "rgb(16, 24, 40)" && style.color === "rgb(245, 246, 248)";
  });
  await page.screenshot({ path: `${out}/controls-dark.png`, fullPage: true });
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
  for (language of ["de", "nl", "es"]) {
    await page.goto(
      `${base}/app/analytics?tenant=${tenant}&analytics_view=explore&lang=${language}`,
    );
    await page
      .getByRole("button", {
        name: { de: "Auswertung starten", nl: "Analyse uitvoeren", es: "Ejecutar análisis" }[
          language
        ],
        exact: true,
      })
      .waitFor();
    const link = page.getByRole("link", { name: "Analytics", exact: true });
    assert.equal(await link.textContent(), "Analytics");
    assert.equal(await link.getAttribute("data-sidebar-tooltip"), "Analytics");
    assert.equal(
      await link.evaluate((node) => node.closest("nav").querySelector("a:last-child") === node),
      true,
    );
  }
  assert.equal(
    await page.getByRole("link", { name: "Analytics", exact: true }).textContent(),
    "Analytics",
  );
  assert.deepEqual(errors, []);
  assert.deepEqual(retiredReads, [], "No retired overview GET requests");
  console.log(
    "PASS: draft/results separation, errors, chart, contributors, private save/reopen, CSV, mobile and four languages",
  );
} finally {
  await browser.close();
}
