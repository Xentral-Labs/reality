import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const errors = [],
  writes = [];
let platformAdmin = false;
let referenceReads = 0;
let lookupFailure = true;
let starterScenario = "";
let projectionMode = "rows";
let codeMode = "ready";
let failMutation = false,
  language = "en";
page.on("pageerror", (e) => errors.push(e.message));
let gap = {
  gap: {
    id: "g1",
    question: "Dispatch priority",
    intended_use: "Prioritize delivery",
    status: "accepted",
    destination: "fact",
    revision: 1,
  },
  entries: [],
  rules: [
    {
      id: "r1",
      logical_name: "Dispatch priority",
      version: 1,
      status: "draft",
      source_system: "shop",
      source_type: "order",
      predicate: "priority",
      summary: { counts: {} },
    },
  ],
};
const pager = { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false };
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname,
    body = req.postDataJSON();
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (req.method() !== "GET") writes.push({ path, body });
  if (path.endsWith("/catalog-code")) {
    if (codeMode === "error")
      return route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Source unavailable" }),
      });
    const kind = new URL(route.request().url()).searchParams.get("kind");
    return reply({
      kind,
      key: "example",
      relationship: kind === "view" ? "view_reader" : "action_command",
      sources: [
        {
          path: "packages/reality-core/src/reality/services/core.py",
          function: "reserve",
          code: "def reserve(session, tenant_id, commitment_id):\n    return reservation\n",
          truncated: false,
        },
        {
          path: "packages/reality-core/src/reality/services/core.py",
          function: "related",
          code: "def related():\n    return []\n",
          truncated: true,
        },
      ],
    });
  }
  if (path.endsWith("/application-reference")) referenceReads++;
  if (path === "/api/auth/me")
    return reply({
      is_platform_admin: platformAdmin,
      id: "u",
      email: "fixture@test.local",
      language,
      locale: "en-GB",
      timezone: "UTC",
      status: "active",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "t1", name: "Test company", role: "owner" },
        { id: "t2", name: "Read-only company", role: "member" },
      ],
      default_tenant_id: "t1",
    });
  if (path.endsWith("/attention/summary"))
    return reply({
      classes: [{ class_id: "shortage", open: 3 }],
      total: 3,
      observed_at: "2026-09-08T10:00:00Z",
    });
  if (path.endsWith("/attention")) {
    const classId = new URL(req.url()).searchParams.get("class_id");
    const findings = [1, 2, 3].map((n) => ({
      id: `exc__shortage__c${n}`,
      class_id: "shortage",
      severity: "high",
      title: "Stock shortage",
      impact: `${n * 4} units short`,
      record_type: "commitment",
      record_id: `c${n}`,
      cause_ids: [],
      causal_values: {},
      trace: {},
      target: { kind: "commitment", id: `c${n}`, delivery_id: `c${n}` },
      context: `Customer ${n} · Catalog item`,
    }));
    return reply({
      items: classId && classId !== "shortage" ? [] : findings,
      page: { ...pager, total: findings.length },
      observed_at: "2026-09-08T10:00:00Z",
    });
  }
  if (path.endsWith("/exception-catalog"))
    return reply({
      version: 1,
      classes: [
        {
          id: "shortage",
          label: "Stock shortage",
          labels: { de: "Bestandsmangel" },
          description: "Insufficient stock",
          severity: "high",
          owner: "Warehouse",
          clears_through: "Receive stock",
        },
      ],
    });
  if (path.endsWith("/items")) return reply([{ id: "catalog-item", name: "Catalog item data" }]);
  if (path.endsWith("/timeline"))
    return reply({
      events: [
        {
          id: "evt1",
          sequence: 1,
          type: "item.created",
          subject_type: "item",
          subject_id: "i1",
          occurred_at: "2026-09-08T10:00:00Z",
          recorded_at: "2026-09-08T10:00:00Z",
          status: "completed",
          business_context: {},
          payload: {},
        },
      ],
      has_more: false,
    });
  if (path.endsWith("/copilot"))
    return reply({ sessions: [], messages: [], proposals: [], suggestions: [] });
  if (path.endsWith("/application-reference"))
    return reply({
      command_count: 1,
      event_count: 2,
      projection_count: 1,
      fact_predicate_count: 3,
      commands: [
        {
          service: "reserve",
          name: "Reserve stock",
          effect: "Reserve available stock for a commitment.",
          mode: "mutation",
          adapters: ["web", "cli"],
          reads: ["commitment", "movement"],
          writes: ["reservation"],
          contracts: [
            {
              service: "reserve",
              inputs: [
                {
                  name: "commitment_id",
                  description: "The delivery commitment to reserve for.",
                  type: "str",
                  required: true,
                  default: "—",
                },
              ],
              returns: "Reservation",
              source: {
                path: "packages/reality-core/src/reality/services/core.py",
                function: "reserve",
              },
            },
          ],
        },
      ],
      projections: [
        {
          name: "Inventory",
          materialized_as: "inventory",
          calculation: "Received minus shipped",
          reads: ["movement", "reservation"],
          consumers: ["warehouse"],
          outputs: ["available"],
          invalidated_by: ["movement"],
        },
      ],
      workspaces: [
        {
          key: "warehouse",
          label: "Warehouse",
          views: [
            {
              key: "items",
              label: "Catalog items",
              kind: "authoritative_register",
              route: "items",
            },
            {
              key: "inventory",
              label: "Inventory",
              route: "inventory",
              kind: "materialized_projection",
              projection: "inventory",
            },
          ],
          actions: [
            {
              key: "reserve_stock",
              label: "Reserve stock",
              command: "reserve",
              description: "Prepare a reservation",
              prerequisites: ["commitment"],
              confirmation: "summary",
            },
          ],
        },
      ],
    });
  if (path.includes("/projections/") || path.includes("/projection-snapshots/")) {
    if (projectionMode === "error")
      return reply({ detail: "Projection temporarily unavailable" }, 503);
    const items = ["empty", "uninitialized"].includes(projectionMode)
      ? []
      : [{ item_id: "i1", available: "4" }];
    return reply(
      path.includes("/projection-snapshots/")
        ? {
            items,
            metadata: {
              projection: "inventory",
              calculation_mode: "stored",
              state: ["pending", "failed", "uninitialized"].includes(projectionMode)
                ? projectionMode
                : "ready",
              processed_event_sequence: projectionMode === "uninitialized" ? null : 1,
              target_event_sequence: projectionMode === "pending" ? 2 : 1,
              completed_at: projectionMode === "uninitialized" ? null : "2026-09-12T09:00:00Z",
              projection_version: 4,
              upstream_freshness: "unknown",
              consistency: "completed_snapshot",
            },
          }
        : items,
    );
  }
  if (path.endsWith("/inspector-records")) {
    const params = new URL(req.url()).searchParams;
    const kind = params.get("kind");
    const items = [
      { id: "p1", kind: "party", label: "Parties", title: "Müller GmbH", details: [] },
      {
        id: "s1",
        kind: "source_record",
        label: "Source records",
        title: "Original payload",
        details: [],
      },
      { id: "d1", kind: "document", label: "Documents", title: "Order 2087", details: [] },
      {
        id: "f1",
        kind: "fact",
        label: "Facts",
        title: "Priority fact",
        details: [{ label: "Value", value: true }],
      },
    ].filter(
      (row) =>
        (!kind || kind === "all" || row.kind === kind) &&
        (!params.get("q") || row.title.includes(params.get("q"))),
    );
    return reply({ items, types: [], page: { ...pager, total: items.length } });
  }
  if (path.endsWith("/facts"))
    return reply({
      items: [
        {
          id: "f1",
          predicate: "priority",
          value: "high",
          subject_type: "commitment",
          subject_id: "c1",
          observed_at: "2026-09-08T10:00:00Z",
          source_record_id: "s1",
        },
      ],
      page: pager,
      subject_types: ["commitment"],
    });
  if (starterScenario && path.includes("/inspector/") && path.includes("starter-")) {
    const parts = path.split("/");
    const recordId = parts.at(-1),
      recordKind = parts.at(-2);
    const title =
      recordId === "starter-linked"
        ? "Linked delivery"
        : recordId === "starter-item"
          ? "Bike Light"
          : "Recent delivery";
    return reply({
      id: recordId,
      kind: recordKind,
      title,
      subtitle: "",
      sections:
        recordId === "starter-linked"
          ? [
              {
                title: "Reality",
                rows: [
                  {
                    label: "Item",
                    value: "Bike Light",
                    link: { kind: "item", id: "starter-item" },
                  },
                ],
              },
            ]
          : [],
      technical_rows: [],
      metrics: [],
      events: [],
      trail: [],
    });
  }
  if (path.includes("/inspector/")) {
    const source = path.endsWith("/s1");
    return reply({
      kind: source ? "source_record" : "fact",
      id: source ? "s1" : "f1",
      title: source ? "Original payload" : "Priority fact",
      subtitle: "Fixture record",
      meaning: "Received value",
      sections: source
        ? []
        : [
            {
              title: "Provenance",
              rows: [
                {
                  label: "Source record",
                  value: "Original payload",
                  link: { kind: "source_record", id: "s1" },
                },
              ],
            },
          ],
      technical_rows: [],
      metrics: [],
      events: [],
      trail: [],
      source_payload: source ? "{}" : null,
    });
  }
  if (starterScenario && path.endsWith("/explorer")) {
    if (starterScenario === "error")
      return reply({ detail: "Temporary start lookup failure" }, 503);
    const kind = new URL(req.url()).searchParams.get("kind");
    if (starterScenario === "delayed") await new Promise((resolve) => setTimeout(resolve, 700));
    const rows =
      starterScenario === "empty" || path.includes("/t2/")
        ? []
        : kind === "commitment"
          ? [
              { id: "starter-light", title: "Recent delivery" },
              { id: "starter-linked", title: "Linked delivery" },
            ]
          : kind === "item"
            ? [{ id: "starter-item", title: "Bike Light" }]
            : [];
    return reply({
      limit_per_collection: 10,
      sections: [
        {
          name: "Reality",
          description: "",
          collections: [
            { name: kind, label: kind, records: rows.map((row) => ({ ...row, fields: [] })) },
          ],
        },
      ],
    });
  }
  if (path.endsWith("/explorer") && new URL(req.url()).searchParams.get("q") === "slow") {
    await new Promise((resolve) => setTimeout(resolve, 900));
    return reply({
      limit_per_collection: 10,
      sections: [
        {
          name: "Reality",
          description: "",
          collections: [
            {
              name: "fact",
              label: "Facts",
              records: [{ id: "late", title: "Obsolete result", fields: [] }],
            },
          ],
        },
      ],
    });
  }
  if (path.endsWith("/explorer") && new URL(req.url()).searchParams.get("q") === "lookup-error") {
    if (lookupFailure) {
      lookupFailure = false;
      return reply({ detail: "Temporary lookup failure" }, 503);
    }
    return reply({
      limit_per_collection: 10,
      sections: [
        {
          name: "Reality",
          description: "",
          collections: [
            {
              name: "fact",
              label: "Facts",
              records: [{ id: "f1", title: "Priority fact", fields: [] }],
            },
          ],
        },
      ],
    });
  }
  if (path.endsWith("/explorer"))
    return reply({
      limit_per_collection: 10,
      sections: [
        {
          name: "Reality",
          description: "Scoped records",
          collections: [
            {
              name: "fact",
              label: "Facts",
              records:
                (!new URL(req.url()).searchParams.get("kind") ||
                  new URL(req.url()).searchParams.get("kind") === "fact") &&
                (!new URL(req.url()).searchParams.get("q") ||
                  /priority|f1/i.test(new URL(req.url()).searchParams.get("q")))
                  ? [{ id: "f1", title: "Priority fact", fields: [] }]
                  : [],
            },
          ],
        },
      ],
    });
  if (path.endsWith("/reality-gaps") && req.method() === "GET") {
    const state = new URL(req.url()).searchParams.get("rule_status");
    const states = [...new Set(gap.rules.map((rule) => rule.status))];
    const items = !state || states.includes(state) ? [{ ...gap.gap, rule_statuses: states }] : [];
    return reply({
      items,
      total: items.length,
      page: 1,
      size: 25,
      counts: { all: 1, open: 1, completed: 0 },
    });
  }
  if (path.includes("/reality-gaps")) {
    if (req.method() === "GET") return reply(gap);
    if (failMutation) return reply({ detail: "Result unavailable" }, 503);
    if (path.endsWith("/simulate"))
      return reply({
        sources_considered: 1,
        matches: 1,
        expected_facts: 1,
        invalid_values: 0,
        ambiguous_subjects: 0,
        not_applicable: 0,
        conflicts: 0,
        examples: [],
      });
    if (path.endsWith("/reality-gaps"))
      gap = {
        gap: {
          id: "g2",
          question: body.question,
          intended_use: body.intended_use,
          status: "open",
          destination: null,
          revision: 1,
        },
        entries: [],
        rules: [],
      };
    if (path.endsWith("/entries")) gap.entries.push(body);
    if (path.endsWith("/decide")) gap.gap.destination = "fact";
    if (path.endsWith("/implementation"))
      gap.rules = [{ ...body.draft, id: "r2", status: "draft", version: 1 }];
    if (path.endsWith("/activate")) gap.rules[0].status = "active";
    gap.gap.revision++;
    return reply(gap);
  }
  return reply({ detail: "Fixture not provided" }, 404);
});
const tab = async (name) => {
  const groups = {
    Overview: "Understand context",
    "Record graph": "Understand context",
    Facts: "Facts & origins",
    "Reality records": "Facts & origins",
    "Fact rules": "Rules & insights",
    "Exception catalog": "Rules & insights",
    "Projections & views": "Rules & insights",
    "Commands & actions": "Actions & history",
    "Execution history": "Actions & history",
  };
  await page
    .getByRole("navigation", { name: "Reality Inspector", exact: true })
    .getByRole("link", { name: groups[name], exact: true })
    .click();
  await page
    .locator("[data-shell-header] .register-tabs")
    .getByRole("button", { name, exact: true })
    .click();
};
if (process.env.PROJECTION_ONLY === "1") {
  try {
    await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=views");
    const column = page.getByRole("region", { name: "Projections", exact: true });
    const entry = column.locator(".inspector-disclosure").first();
    await entry.locator("summary").waitFor();
    assert.equal(await page.locator("[data-catalog-explanation]").count(), 0);
    const search = page.getByRole("searchbox", { name: "Search inspector" });
    await search.fill("shipped");
    await column.locator("summary").first().waitFor();
    await search.fill("");
    await entry.locator("summary").focus();
    await page.keyboard.press("Enter");
    await entry.locator("[data-catalog-explanation]").waitFor();
    await entry.getByRole("button", { name: "Open view data", exact: true }).click();
    const dialog = page.getByRole("dialog", { name: "View data", exact: true });
    await dialog.getByRole("cell", { name: "4", exact: true }).waitFor();
    for (const mode of ["pending", "failed", "uninitialized", "rows"]) {
      projectionMode = mode;
      await dialog.getByRole("button", { name: "Refresh", exact: true }).click();
      await dialog
        .locator(`[data-projection-freshness="${mode === "rows" ? "ready" : mode}"]`)
        .waitFor();
      if (mode === "uninitialized")
        assert.equal(await dialog.getByText("No results", { exact: true }).count(), 0);
      else await dialog.getByRole("cell", { name: "4", exact: true }).waitFor();
    }
    await mkdir("/private/tmp/reality-179-browser", { recursive: true });
    await page.screenshot({ path: "/private/tmp/reality-179-browser/projection-ready.png" });
    await dialog.getByRole("button", { name: "Close", exact: true }).click();
    await entry.locator("summary").first().click();
    await entry.locator("[data-catalog-explanation]").waitFor({ state: "detached" });
    assert.deepEqual(writes, []);
    assert.deepEqual(errors, []);
    console.log(
      "PASS: lazy projection directory, metadata search, keyboard disclosure and read-only data.",
    );
  } finally {
    await browser.close();
  }
  process.exit(0);
}
try {
  await mkdir("/private/tmp/reality-138-browser", { recursive: true });
  await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=exceptions");
  const shortageRow = page.locator(
    '[data-inline-exception-catalog] tr[data-exception-class="shortage"]',
  );
  await shortageRow.waitFor();
  // Every finding type is one table row: catalog description, severity and the open count.
  await shortageRow.getByText("Insufficient stock", { exact: true }).waitFor();
  assert.equal(await shortageRow.locator("[data-open-count]").innerText(), "3");
  await shortageRow.getByRole("button", { name: "Preview · Stock shortage" }).click();
  const shortagePreview = page.locator("#exception-preview-shortage");
  await shortagePreview.getByText("Receive stock", { exact: true }).waitFor();
  assert.equal(await shortagePreview.locator("[data-open-findings] li").count(), 3);
  await shortagePreview.getByText("Customer 2 · Catalog item", { exact: true }).waitFor();
  // The counts come from a stored generation and say when it was calculated.
  await page
    .locator('[data-inline-exception-catalog] [data-projection-freshness="ready"]')
    .waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/exception-rules-open.png" });
  await shortagePreview.getByRole("button", { name: "Open in Exceptions" }).click();
  await page.waitForURL(/\/app\/attention\?/);
  assert.equal(new URL(page.url()).searchParams.get("q"), "shortage");
  await page.goBack();
  await page
    .locator('[data-inline-exception-catalog] tr[data-exception-class="shortage"]')
    .waitFor();
  // The global action launcher reads twice under development StrictMode; Inspector adds no read.
  assert.equal(referenceReads, 2);
  await page.getByRole("searchbox", { name: "Search inspector" }).fill("no-such-definition");
  await page
    .locator("[data-inline-exception-catalog]")
    .getByText("No matching records", { exact: true })
    .waitFor();
  await page.getByRole("searchbox", { name: "Search inspector" }).fill("");
  await page.getByText("Stock shortage", { exact: true }).waitFor();
  await page.goto("http://localhost:5177/app/inspector?tenant=t1");
  await page.locator("[data-page-introduction] h1").waitFor();
  assert.equal(await page.locator("[data-page-tabs] .register-tabs").count(), 1);
  const inspectorNav = page.getByRole("navigation", { name: "Reality Inspector", exact: true });
  await inspectorNav.getByRole("link").first().waitFor();
  assert.deepEqual(
    (await inspectorNav.getByRole("link").allTextContents()).map((s) => s.trim()),
    ["Understand context", "Facts & origins", "Rules & insights", "Actions & history"],
  );
  assert.equal(
    await page.getByRole("link", { name: "Technology & system", exact: true }).count(),
    0,
  );
  await page.getByRole("heading", { name: "Understand context", exact: true }).waitFor();
  await page.locator('[data-recorder-event="evt1"]').waitFor();
  await tab("Reality records");
  await page.getByText("Facts · 1", { exact: true }).click();
  await page.getByRole("button", { name: "Record graph", exact: true }).last().click();
  await page.locator("[data-object-graph]").waitFor();
  const recordInput = page.getByRole("combobox", { name: "Record ID", exact: true });
  const slowRequest = page.waitForRequest(
    (request) =>
      request.url().includes("/explorer?") &&
      new URL(request.url()).searchParams.get("q") === "slow",
  );
  const slowResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/explorer?") &&
      new URL(response.url()).searchParams.get("q") === "slow",
  );
  await recordInput.fill("slow");
  await slowRequest;
  await recordInput.fill("Priority");
  await page.getByRole("option", { name: /Priority fact/ }).waitFor();
  await slowResponse;
  assert.equal(await page.getByRole("option", { name: /Obsolete result/ }).count(), 0);
  await recordInput.press("ArrowDown");
  await recordInput.press("Enter");
  assert.equal(await recordInput.inputValue(), "f1");
  await recordInput.fill("lookup-error");
  await page.getByRole("alert").getByText("Could not load this view", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.getByRole("option", { name: /Priority fact/ }).waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/graph-autocomplete.png" });
  await page.getByRole("option", { name: /Priority fact/ }).click();
  assert.equal(await page.getByRole("listbox").count(), 0);
  await page.getByRole("combobox", { name: "Record type", exact: true }).selectOption("item");
  assert.equal(await recordInput.inputValue(), "");
  await recordInput.fill("no-match");
  await page.getByText("No matching records", { exact: true }).waitFor();
  await recordInput.press("Escape");
  await page.getByRole("combobox", { name: "Record type", exact: true }).selectOption("fact");
  await recordInput.fill("f1");
  await page.getByRole("button", { name: "Open", exact: true }).click();
  await page.locator("[data-object-graph]").waitFor();
  await tab("Facts");
  await page.locator('[data-inspector-record="source_record:s1"]').waitFor();
  await page
    .getByRole("combobox", { name: "Record type", exact: true })
    .selectOption("source_record");
  await page.reload();
  assert.equal(
    await page.getByRole("combobox", { name: "Record type", exact: true }).inputValue(),
    "source_record",
  );
  await page
    .locator('[data-inspector-record="source_record:s1"]')
    .getByRole("button", { name: "Details", exact: true })
    .click();
  await page.getByRole("dialog").waitFor();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.locator(".erp-table-scroll").evaluate((node) => {
    node.scrollLeft = 0;
  });
  await page.screenshot({
    path: "/private/tmp/reality-138-browser/all-record-register.png",
    fullPage: true,
  });
  await page.getByRole("combobox", { name: "Record type", exact: true }).selectOption("fact");
  await page.locator("[data-fact-row]").waitFor();
  assert.equal(await page.getByText("About this view", { exact: true }).count(), 0);
  await page.getByRole("button", { name: "Record graph", exact: true }).last().click();
  await page
    .locator("[data-object-graph]")
    .getByRole("button")
    .filter({ hasText: "Original payload" })
    .click();
  await page
    .locator("[data-object-graph]")
    .getByRole("button")
    .filter({ hasText: "Original payload" })
    .waitFor();
  await page.getByText("No linked records returned.", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await page.locator("[data-object-graph]").getByText("Source record", { exact: true }).waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/graph.png" });
  await tab("Commands & actions");
  await page.locator("[data-inspector-catalog] .inspector-disclosure").first().waitFor();
  await page.getByRole("searchbox", { name: "Search inspector" }).fill("no-such-definition");
  await page.getByText("No matching records", { exact: true }).waitFor();
  await page.getByRole("searchbox", { name: "Search inspector" }).fill("");
  const commandsViewport = page.viewportSize();
  await page.setViewportSize({ width: 1440, height: 1000 });
  const actionColumn = page.locator("[data-action-command-columns] > section").first();
  const commandColumn = page.locator("[data-action-command-columns] > section").last();
  const actionBox = await actionColumn.boundingBox(),
    commandBox = await commandColumn.boundingBox();
  assert.ok(commandBox.x > actionBox.x && Math.abs(commandBox.y - actionBox.y) < 2);
  await page.getByLabel("Actions: Information", { exact: true }).hover();
  await page.getByRole("tooltip").waitFor();
  await page.mouse.move(0, 0);
  await page.getByRole("tooltip").waitFor({ state: "hidden" });
  await page.getByLabel("Commands: Information", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await page
    .getByText(
      "A command is the application operation behind a task. Example: after you confirm Reserve stock, the reserve command receives the order commitment and quantity and creates the reservation. This catalog describes the inputs and results; some commands only read data.",
      { exact: true },
    )
    .waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/action-columns-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  if (await page.getByRole("button", { name: "Hide chat", exact: true }).count())
    await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  const actionMobile = await actionColumn.boundingBox(),
    commandMobile = await commandColumn.boundingBox();
  assert.ok(commandMobile.y >= actionMobile.y + actionMobile.height);
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: "/private/tmp/reality-138-browser/action-columns-mobile.png" });
  await page.setViewportSize(commandsViewport);
  await page
    .locator("[data-action-command-columns] > section")
    .first()
    .getByText("Reserve stock", { exact: true })
    .click();
  const actionCard = actionColumn
    .locator(".inspector-disclosure")
    .filter({ has: page.locator("summary").filter({ hasText: /^Reserve stock$/ }) });
  assert.equal(await actionCard.locator("pre:visible").count(), 0);
  const actionRow = await actionCard.locator("[data-catalog-actions]").boundingBox();
  const secondary = await actionCard.locator("[data-catalog-secondary]").boundingBox();
  assert.ok(actionRow.y < secondary.y);
  await page.screenshot({ path: "/private/tmp/reality-138-browser/catalog-card-structured.png" });
  const cardViewport = page.viewportSize();
  await page.setViewportSize({ width: 390, height: 844 });
  await actionCard.scrollIntoViewIfNeeded();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: "/private/tmp/reality-138-browser/catalog-card-mobile.png" });
  await page.setViewportSize(cardViewport);

  await actionCard.getByText("Illustrative example", { exact: true }).waitFor();
  await actionCard.getByText("How it works", { exact: true }).click();
  await actionCard.getByText("Writes to", { exact: true }).waitFor();
  await actionCard
    .locator("summary")
    .filter({ hasText: /^reserve$/ })
    .click();
  await actionCard.getByText("The delivery commitment to reserve for.", { exact: true }).waitFor();
  assert.ok(
    (
      await actionCard.getByRole("link", { name: /View implementation/ }).getAttribute("href")
    ).endsWith("/packages/reality-core/src/reality/services/core.py"),
  );
  await page.screenshot({ path: "/private/tmp/reality-138-browser/catalog-explanation.png" });
  const codeButton = actionCard.getByRole("button", { name: "View code", exact: true });
  await codeButton.click();
  const codeDialog = page.getByRole("dialog", { name: "Python code", exact: true });
  await codeDialog
    .getByLabel("Python source code", { exact: true })
    .filter({ hasText: "def reserve(" })
    .waitFor();
  await codeDialog.getByLabel("Function", { exact: true }).selectOption("1");
  await codeDialog
    .getByText("Code preview truncated to 600 lines or 64 KiB.", { exact: true })
    .waitFor();
  await codeDialog
    .getByLabel("Python source code", { exact: true })
    .filter({ hasText: "def related(" })
    .waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/catalog-code-dialog.png" });
  await page.keyboard.press("Escape");
  assert.equal(await codeButton.evaluate((node) => document.activeElement === node), true);
  codeMode = "error";
  await codeButton.click();
  await codeDialog.getByRole("alert").waitFor();
  codeMode = "ready";
  await codeDialog.getByRole("button", { name: "Retry", exact: true }).click();
  await codeDialog.getByLabel("Python source code", { exact: true }).waitFor();
  await codeDialog.getByRole("button", { name: "Close", exact: true }).click();

  await page.getByRole("button", { name: "Open action form", exact: true }).click();
  await page.getByRole("dialog").waitFor();
  await page.keyboard.press("Escape");
  await tab("Projections & views");
  await page.locator("[data-inspector-catalog] .inspector-disclosure").first().waitFor();
  assert.equal(await page.locator("[data-catalog-explanation]").count(), 0);
  const originalViewport = page.viewportSize();
  await page.setViewportSize({ width: 1440, height: 1000 });
  const projectionColumn = page.getByRole("region", { name: "Projections", exact: true });
  const viewColumn = page.getByRole("region", { name: "Views", exact: true });
  const left = await projectionColumn.boundingBox(),
    right = await viewColumn.boundingBox();
  assert.ok(right.x > left.x && Math.abs(right.y - left.y) < 2);
  await page.getByLabel("Projections: Information", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await page
    .getByText(
      "A projection is a calculated overview, like an ERP stock report. Example: 100 units in stock minus 30 reserved gives 70 available. It uses existing records and does not create a new stock posting.",
      { exact: true },
    )
    .waitFor();
  await page.getByLabel("Views: Information", { exact: true }).click();
  await page
    .getByText(
      "A view is a screen or list you work with in the application, like an ERP stock list. It can show a calculated projection or stored records such as items. Several views can use the same projection.",
      { exact: true },
    )
    .waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/catalog-columns-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  if (await page.getByRole("button", { name: "Hide chat", exact: true }).count())
    await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  await page.getByLabel("Projections: Information", { exact: true }).click();
  await page.getByRole("tooltip").waitFor();
  const top = await projectionColumn.boundingBox(),
    bottom = await viewColumn.boundingBox();
  assert.ok(bottom.y >= top.y + top.height);
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: "/private/tmp/reality-138-browser/catalog-columns-mobile.png" });
  await page.setViewportSize(originalViewport);
  await projectionColumn
    .locator("summary")
    .filter({ hasText: /^Inventory$/ })
    .click();
  const projectionCard = projectionColumn
    .locator(".inspector-disclosure")
    .filter({ has: page.locator("summary").filter({ hasText: /^Inventory$/ }) });
  assert.equal(await projectionCard.locator("pre:visible").count(), 0);
  await projectionCard.getByText("How it works", { exact: true }).click();
  await projectionCard.getByText("Result fields", { exact: true }).waitFor();
  await projectionCard.getByText("Technical definition", { exact: true }).click();
  await projectionCard.locator("pre:visible").waitFor();

  await page.getByRole("button", { name: "Open view data", exact: true }).click();
  const projectionDialog = page.getByRole("dialog", { name: "View data", exact: true });
  await projectionDialog.getByRole("cell", { name: "4", exact: true }).waitFor();
  await projectionDialog.getByRole("columnheader", { name: "available", exact: true }).waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/projection-dialog.png" });
  await page.keyboard.press("Escape");
  assert.equal(
    await page
      .getByRole("button", { name: "Open view data", exact: true })
      .evaluate((node) => node === document.activeElement),
    true,
  );
  const catalogUrl = page.url();
  await page.getByText("Catalog items", { exact: true }).click();
  const itemView = page
    .locator("details")
    .filter({ has: page.getByText("Catalog items", { exact: true }) });
  const itemDocs = itemView.getByRole("link", { name: /Documentation/ });
  assert.ok((await itemDocs.getAttribute("href")).endsWith("/catalogs/workspaces"));
  assert.equal(await itemDocs.getAttribute("target"), "_blank");
  await itemView.getByRole("button", { name: "Open view data", exact: true }).click();
  await projectionDialog.getByRole("cell", { name: "Catalog item data", exact: true }).waitFor();
  assert.equal(page.url(), catalogUrl);
  await projectionDialog.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByText("Catalog items", { exact: true }).click();
  await viewColumn
    .locator("summary")
    .filter({ hasText: /^Inventory$/ })
    .click();
  const inventoryView = viewColumn
    .locator(".inspector-disclosure")
    .filter({ has: page.locator("summary").filter({ hasText: /^Inventory$/ }) });
  await inventoryView.getByRole("button", { name: "Open view data", exact: true }).click();
  await projectionDialog.getByRole("cell", { name: "4", exact: true }).waitFor();
  assert.equal(page.url(), catalogUrl);
  await page.keyboard.press("Escape");
  await viewColumn
    .locator("summary")
    .filter({ hasText: /^Inventory$/ })
    .click();
  projectionMode = "error";
  await page.getByRole("button", { name: "Open view data", exact: true }).click();
  await projectionDialog.getByRole("alert").waitFor();
  projectionMode = "empty";
  await projectionDialog.getByRole("button", { name: "Retry", exact: true }).click();
  await projectionDialog.getByText("No results", { exact: true }).waitFor();
  await projectionDialog.getByRole("button", { name: "Close", exact: true }).click();
  projectionMode = "rows";
  await page.getByRole("button", { name: "Open view data", exact: true }).click();
  await projectionDialog.getByRole("cell", { name: "i1", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  await page.getByText("Catalog items", { exact: true }).click();
  await itemView.getByRole("button", { name: "Open in application", exact: true }).click();
  await page.waitForURL((url) => url.pathname.includes("master-data"));
  assert.equal(new URL(page.url()).searchParams.get("tenant"), "t1");
  await page.goto(catalogUrl);
  await page.reload();
  await page.getByRole("button", { name: "Projections & views", exact: true }).waitFor();
  await tab("Exception catalog");
  await page
    .locator("[data-inline-exception-catalog]")
    .getByRole("button", { name: "Preview · Stock shortage" })
    .click();
  await page.getByText("Receive stock", { exact: true }).waitFor();
  await page.locator("[data-inline-exception-catalog] tr[data-exception-class]").waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/catalog-pattern.png" });
  assert.equal(await page.getByRole("dialog").count(), 0);
  await tab("Execution history");
  await page.locator("[data-inline-activity] tbody tr").waitFor();
  assert.equal(await page.getByLabel("Rows per page", { exact: true }).count(), 0);
  assert.equal(await page.locator("[data-inline-activity] .erp-sort").count(), 0);
  assert.equal(await page.getByRole("dialog").count(), 0);
  await page.screenshot({ path: "/private/tmp/reality-138-browser/inline-history.png" });
  await tab("Fact rules");
  assert.equal(await page.getByText(/Catalog definitions:/).count(), 0);
  assert.equal(await page.getByRole("dialog").count(), 0);
  await page.screenshot({ path: "/private/tmp/reality-138-browser/rule-register.png" });
  assert.equal(
    await page.getByRole("combobox", { name: "Rows per page", exact: true }).inputValue(),
    "50",
  );
  await page.getByRole("combobox", { name: "Rows per page", exact: true }).selectOption("25");
  await page.getByRole("button", { name: "Edit: Dispatch priority", exact: true }).click();
  await page.getByRole("dialog", { name: "Edit rule", exact: true }).waitFor();
  assert.equal(await page.getByRole("button", { name: "Previous", exact: true }).count(), 0);
  await page.getByRole("button", { name: "Use as draft", exact: true }).click();
  assert.ok(
    await page
      .getByLabel("Rule draft JSON", { exact: true })
      .evaluate((node) => node.getBoundingClientRect().height >= 340),
  );
  await page.getByText("Add evidence or context", { exact: true }).click();
  assert.ok(
    await page
      .getByLabel("Context JSON", { exact: true })
      .evaluate((node) => node.getBoundingClientRect().height >= 140),
  );
  await page.getByText("Add evidence or context", { exact: true }).click();
  await page.getByLabel("Rule draft JSON", { exact: true }).focus();
  assert.equal(
    await page
      .getByLabel("Rule draft JSON", { exact: true })
      .evaluate((node) => node === document.activeElement),
    true,
  );
  await page.getByText("Rule draft", { exact: true }).click();
  assert.equal(
    await page.getByRole("button", { name: "Activate rule", exact: true }).isDisabled(),
    true,
  );
  await page.getByRole("button", { name: "Simulate rule", exact: true }).click();
  await page.getByRole("button", { name: "Activate rule", exact: true }).click();
  assert.equal(writes.filter((x) => x.path.endsWith("/activate")).length, 0);
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page
    .getByText("This version is active and is applied to matching data.", { exact: true })
    .waitFor();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("combobox", { name: "Rule status", exact: true }).selectOption("disabled");
  await page.getByText("No matching records", { exact: true }).waitFor();
  assert.equal(await page.locator("[data-rule-version]").count(), 0);
  await page.getByRole("combobox", { name: "Rule status", exact: true }).selectOption("active");
  await page.getByRole("button", { name: /Dispatch priority/ }).click();
  await page.locator("[data-rule-version]").waitFor();
  assert.equal(await page.locator("[data-rule-version]").count(), 1);
  await page.getByRole("button", { name: "Close", exact: true }).click();
  const newRule = page.getByRole("button", { name: "New rule", exact: true });
  await newRule.click();
  await page.getByRole("dialog", { name: "New rule", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  assert.equal(await newRule.evaluate((node) => node === document.activeElement), true);
  await newRule.click();
  await page
    .getByRole("dialog")
    .getByLabel("Business question", { exact: true })
    .fill("Shipping class");
  await page
    .getByRole("dialog")
    .getByLabel("Intended use", { exact: true })
    .fill("Plan deliveries");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  assert.equal(writes.filter((x) => x.path.endsWith("/reality-gaps")).length, 0);
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page.getByRole("heading", { name: "Shipping class", exact: true }).waitFor();
  await page.getByRole("button", { name: "Choose Fact interpretation", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page.getByText("Rule draft", { exact: true }).click();
  await page.getByLabel("Rule draft JSON", { exact: true }).fill(
    JSON.stringify({
      logical_name: "Shipping class",
      predicate: "shipping_class",
      source_system: "shop",
      source_type: "order",
      subject_type: "commitment",
      subject_resolver: "source_document_commitments",
      value_type: "string",
      value_path: "shipping.class",
      observed_at_mode: "source_received_at",
    }),
  );
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page.locator('[data-rule-version="r2"]').waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/rules.png" });

  await page.getByRole("button", { name: "Simulate rule", exact: true }).click();
  await page.getByRole("button", { name: "Activate rule", exact: true }).click();
  failMutation = true;
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page
    .getByText(
      "The result is uncertain. Reload and inspect the current state before another change.",
      { exact: true },
    )
    .waitFor();
  assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).count(), 0);
  assert.equal(
    await page.getByRole("combobox", { name: "Rule status", exact: true }).isDisabled(),
    true,
  );
  assert.equal(writes.filter((row) => row.path.endsWith("r2/activate")).length, 1);
  failMutation = false;
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="t2"]').click();
  await page
    .getByText("Rule changes require company owner or platform administrator access.", {
      exact: true,
    })
    .waitFor();
  assert.equal(
    await page.getByRole("button", { name: "New rule", exact: true }).isDisabled(),
    true,
  );
  platformAdmin = true;
  await page.reload();
  await page.getByRole("button", { name: "New rule", exact: true }).waitFor();
  assert.equal(await page.getByRole("button", { name: "New rule", exact: true }).isEnabled(), true);
  platformAdmin = false;
  await page.reload();
  await page.setViewportSize({ width: 390, height: 844 });
  if (await page.getByRole("button", { name: "Hide chat", exact: true }).count())
    await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/mobile.png", fullPage: true });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  starterScenario = "linked";
  await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=graph");
  await page.locator("[data-graph-start]").getByText("Linked delivery", { exact: true }).waitFor();
  assert.equal(
    await page.getByRole("combobox", { name: "Record ID", exact: true }).inputValue(),
    "starter-linked",
  );
  await page
    .getByRole("navigation", { name: "Graph starting points" })
    .getByRole("button", { name: "Item", exact: true })
    .click();
  await page.locator("[data-graph-start]").getByText("Bike Light", { exact: true }).waitFor();
  await page.screenshot({ path: "/private/tmp/reality-138-browser/graph-start.png" });
  await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=overview");
  await page.getByRole("heading", { name: "Understand context", exact: true }).waitFor();
  await page.locator('[data-recorder-event="evt1"]').waitFor();
  await page.getByText("Beginning of recorded history", { exact: true }).waitFor();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: "/private/tmp/reality-138-browser/overview-start.png" });
  let failOlder = true;
  const cursors = [];
  const recorderRoute = async (route) => {
    const url = new URL(route.request().url());
    assert.equal(url.searchParams.get("hours"), "0");
    const cursor = url.searchParams.get("before_sequence");
    cursors.push(cursor);
    if (cursor && failOlder) return route.fulfill({ status: 500, body: "Unavailable" });
    const types = {
      16: ["party", "p1"],
      17: ["source_record", "source-1"],
      18: ["document", "d1"],
      19: ["commitment", "c1"],
      20: ["reservation", "r1"],
      21: ["movement", "move-1"],
    };
    const payloads = {
      16: { name: "Müller GmbH" },
      17: { external_id: "SO-2087", source_system: "Shopify" },
      18: { number: "SO-2087", party_id: "p1" },
      19: { document_id: "d1", item_id: "i1" },
      20: { commitment_id: "c1" },
      21: { reservation_id: "r1", commitment_id: "c1" },
    };
    const event = (sequence) => ({
      id: `flight-${sequence}`,
      sequence,
      type:
        { 17: "source_record.received", 18: "document.recorded", 21: "movement.recorded" }[
          sequence
        ] || `${(types[sequence] || ["fact"])[0]}.created`,
      subject_type: (types[sequence] || ["fact"])[0],
      subject_id: (types[sequence] || ["fact", `f${sequence}`])[1],
      source_record_id: "source-1",
      causation_id: "cause-1",
      recorded_at: sequence > 1 ? "2026-09-08T10:00:00Z" : "2026-09-06T08:00:00Z",
      occurred_at: "2026-09-05T08:00:00Z",
      business_context: { item: "Bike Light", quantity: "5", unit: "pcs" },
      payload: payloads[sequence] || {},
      status: "completed",
    });
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        events: cursor ? [event(1)] : Array.from({ length: 20 }, (_, i) => event(21 - i)),
        has_more: !cursor,
      }),
    });
  };
  await page.route("**/timeline?**", recorderRoute);
  await page.reload();
  await page.locator('[data-recorder-event="flight-21"]').waitFor();
  await page.getByRole("region", { name: "Event history" }).count();
  await page.locator('[aria-label="Event history"]').evaluate((node) => {
    node.scrollLeft = 0;
  });
  await page.getByText("Activity could not be loaded.", { exact: true }).waitFor();
  assert.equal(await page.locator("[data-recorder-event]").count(), 20);
  failOlder = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.locator('[data-recorder-event="flight-1"]').waitFor();
  assert.equal(await page.locator("[data-recorder-event]").count(), 21);
  assert.deepEqual(cursors.filter(Boolean), ["2", "2"]);
  await page.getByText("Beginning of recorded history", { exact: true }).waitFor();
  assert.equal(await page.locator('[data-flight-node="source_record:source-1"]').count(), 1);
  // Spec 162: the paper is a fixed time raster up to now; prepending an older recording day
  // extends the raster to the left and keeps chronology, with the band's own scrolling.
  const paper = await page.locator("[data-flight-band]").evaluate((node) => ({
    scrollWidth: node.scrollWidth,
    clientWidth: node.clientWidth,
  }));
  assert.ok(paper.scrollWidth >= paper.clientWidth, "the raster fills the band");
  const [olderX, newerX] = await page.evaluate(() =>
    ["flight-1", "flight-21"].map(
      (id) => document.querySelector(`[data-recorder-event="${id}"]`).offsetLeft,
    ),
  );
  assert.ok(olderX < newerX, "older recording days sit to the left of newer ones");
  await page.locator('[data-flight-node="source_record:source-1"]').click();
  await page
    .locator("[data-flight-selection]")
    .getByRole("button", { name: "Details", exact: true })
    .click();
  await page.getByRole("dialog").waitFor();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator('[aria-label="Event history"]').evaluate((node) => {
    node.scrollTop = 0;
    node.scrollLeft = node.scrollWidth;
  });
  await page.screenshot({ path: "/private/tmp/reality-138-browser/flight-recorder-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: "/private/tmp/reality-138-browser/flight-recorder-mobile.png" });
  await page.unroute("**/timeline?**", recorderRoute);
  let releaseOld;
  const oldRead = new Promise((resolve) => {
    releaseOld = resolve;
  });
  const isolationRoute = async (route) => {
    if (route.request().url().includes("/t1/")) await oldRead;
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ events: [], has_more: false }),
    });
  };
  await page.route("**/timeline?**", isolationRoute);
  const pendingOld = page.waitForRequest((request) => request.url().includes("/t1/timeline"));
  await page.reload({ waitUntil: "domcontentloaded" });
  await pendingOld;
  await page.evaluate(() => {
    history.pushState({}, "", "/app/inspector?tenant=t2&inspector_view=overview");
    dispatchEvent(new PopStateEvent("popstate"));
  });
  await page.getByText("No recorded events yet.", { exact: true }).waitFor();
  releaseOld();
  assert.equal(await page.locator("[data-recorder-event]").count(), 0);
  await page.unroute("**/timeline?**", isolationRoute);

  starterScenario = "empty";
  await page.goto("http://localhost:5177/app/inspector?tenant=t2&inspector_view=graph");
  await page
    .getByText("No records are available for this starting point yet.", { exact: true })
    .waitFor();
  assert.equal(await page.locator("[data-object-graph]").count(), 0);
  starterScenario = "error";
  await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=graph");
  await page.getByText("Could not load this view", { exact: true }).waitFor();
  starterScenario = "linked";
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.locator("[data-graph-start]").getByText("Linked delivery", { exact: true }).waitFor();
  starterScenario = "delayed";
  await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=graph");
  const pendingStarter = page.waitForResponse(
    (response) =>
      response.url().includes("/explorer?") &&
      new URL(response.url()).searchParams.get("kind") === "commitment",
  );
  await page.getByRole("combobox", { name: "Record ID", exact: true }).fill("manual-choice");
  await pendingStarter;
  assert.equal(
    await page.getByRole("combobox", { name: "Record ID", exact: true }).inputValue(),
    "manual-choice",
  );
  assert.equal(await page.locator("[data-object-graph]").count(), 0);
  starterScenario = "";
  for (language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: 1000 });
        await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=overview");
        await page.locator("[data-page-introduction] h1").waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await page.screenshot({
          path: `/private/tmp/reality-138-browser/${language}-${theme}-${width}.png`,
          animations: "disabled",
        });
      }
  assert.deepEqual(errors, []);
  console.log(
    "PASS: Inspector graph, catalogs, action form, projection data, route reload, rule simulation/review/create/draft and tenant/member boundaries.",
  );
} catch (error) {
  console.error({
    language,
    errors,
    url: page.url(),
    navs: await page.locator("nav").evaluateAll((nodes) => nodes.map((node) => node.outerHTML)),
  });
  await page.screenshot({ path: "/private/tmp/reality-138-browser/error.png", fullPage: true });
  throw error;
} finally {
  await browser.close();
}
