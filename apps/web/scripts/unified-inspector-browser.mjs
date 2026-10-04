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
      // The counts come from a stored, completed generation.
      metadata: {
        projection: "attention_summary",
        calculation_mode: "stored",
        state: "ready",
        processed_event_sequence: 12,
        target_event_sequence: 12,
        completed_at: "2026-09-08T10:00:00Z",
        projection_version: 1,
        upstream_freshness: "unknown",
        consistency: "completed_snapshot",
      },
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
  // The company timeline shows decisions beside events (spec 263); none in this fixture.
  if (path.endsWith("/change-proposals"))
    return reply({
      items: [],
      page: { number: 1, size: 100, total: 0, pages: 1, has_previous: false, has_next: false },
    });
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
    const items =
      path.includes("fulfillment_queue") &&
      (process.env.REPORTS_ONLY === "1" || process.env.PROJECTION_ONLY === "1")
        ? [
            {
              lines: [{ sku: "P01", quantity: "999999999999999999.123456" }],
              party_id: "party-exact",
              order_key: "order-exact",
              party: "Maple Retail",
              external_order_id: "SO-1042",
              due_at: "2026-09-19T12:00:00Z",
              ship_ready: false,
              blocking_reasons: ["delivery_hold"],
              priority: "normal",
            },
          ]
        : ["empty", "uninitialized"].includes(projectionMode)
          ? []
          : process.env.REPORTS_ONLY === "1" || process.env.PROJECTION_ONLY === "1"
            ? Array.from({ length: 100 }, (_, i) => ({
                item_id: `i${i + 1}`,
                available: i === 0 ? "4" : "100",
              }))
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
if (process.env.REPORTS_ONLY === "1" || process.env.PROJECTION_ONLY === "1") {
  const { parseCatalogs } = await import("./i18n-audit-lib.mjs");
  const catalogs = parseCatalogs(new URL("../src/localization.tsx", import.meta.url).pathname);
  const tr = (key) => (language === "en" ? key : catalogs[language].get(key) || key);
  const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
  const readPaths = [];
  page.on("request", (req) => {
    if (req.url().includes("/api/")) readPaths.push(req.url());
  });
  await page.route("**/application-reference", async (route) => {
    const makeProjection = (key) => ({
      name: key,
      materialized_as: key,
      calculation: "Original calculation",
      consumers: [],
      outputs: [],
      invalidated_by: [],
    });
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        command_count: 0,
        event_count: 0,
        projection_count: 4,
        fact_predicate_count: 0,
        commands: [],
        projections: [
          "inventory",
          "fulfillment_queue",
          "open_financial_items",
          "price_resolution",
        ].map(makeProjection),
        workspaces: [
          {
            key: "warehouse",
            label: "Warehouse",
            actions: [],
            views: [
              { key: "inventory", label: "Inventory", projection: "inventory", route: "inventory" },
              { key: "orders", label: "Orders", projection: "fulfillment_queue", route: "orders" },
              {
                key: "warehouse_queue",
                label: "Warehouse Queue",
                projection: "fulfillment_queue",
                route: "warehouse-queue",
              },
              { key: "items", label: "Items", route: "items", kind: "authoritative_register" },
            ],
          },
        ],
      }),
    });
  });
  try {
    await mkdir("/private/tmp/reality-219-browser", { recursive: true });
    for (language of ["en", "de", "nl", "es"]) {
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=views`);
      const catalog = page.locator("[data-report-catalog]");
      await catalog.waitFor();
      const row = catalog.locator('[data-report="inventory"]');
      const openReport = async (target) => {
        const entry = catalog.locator(`[data-report="${target}"]`);
        if ((await entry.getAttribute("open")) === null) await entry.locator("summary").click();
        await entry.locator("[data-report-open]").click();
      };
      assert.equal(await catalog.locator("[data-report]").count(), 5);
      assert.equal(await row.isVisible(), false);
      await catalog.getByRole("button", { name: tr("Expand all"), exact: true }).click();
      await row.waitFor();
      await row.locator("summary").focus();
      await page.keyboard.press("Enter");
      await row
        .getByText(tr("See physical, reserved, available and expected stock."), { exact: true })
        .waitFor();
      await catalog.getByRole("button", { name: tr("Collapse all"), exact: true }).click();
      assert.equal(await row.isVisible(), false);
      const search = catalog.getByRole("searchbox");
      await search.fill(tr("Stock overview"));
      await row.waitFor();
      assert.equal(
        await catalog.getByRole("button", { name: tr("Expand all"), exact: true }).isDisabled(),
        true,
      );
      await search.fill("");
      assert.equal(await row.isVisible(), false);
      await catalog.getByRole("button", { name: tr("Expand all"), exact: true }).click();
      await search.fill("does-not-exist");
      await catalog.getByText(tr("No matching reports"), { exact: true }).waitFor();
      await search.fill(tr("Stock overview"));
      assert.equal(await catalog.locator("[data-report]").count(), 1);
      if ((await row.getAttribute("open")) === null) await row.locator("summary").click();
      await row.locator("[data-report-open]").focus();
      await page.keyboard.press("Enter");
      const dialog = page.getByRole("dialog", { name: tr("Stock overview"), exact: true });
      await dialog.waitFor();
      await dialog.getByRole("cell", { name: "4", exact: true }).waitFor();
      if (language === "en") {
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
      }

      assert.ok(
        readPaths.some((path) => path.includes("/tenants/t1/") && path.includes("inventory")),
      );
      assert.notEqual(await dialog.locator("[data-report-details]").getAttribute("open"), null);
      const explanationBox = await dialog.locator("[data-report-details]").boundingBox();
      const tableBox = await dialog.getByRole("table").boundingBox();
      assert.ok(
        explanationBox.x >= tableBox.x + tableBox.width - 1,
        "Explanation sits beside data",
      );
      const header = dialog.locator("header");
      const headerBefore = await header.boundingBox();
      await dialog.locator("[data-report-data]").evaluate((el) => {
        el.scrollTop = el.scrollHeight;
      });
      assert.deepEqual(
        await header.boundingBox(),
        headerBefore,
        "Report header stays visible while data scrolls",
      );
      await dialog.getByText(tr("About this report"), { exact: true }).click();
      assert.equal(await dialog.locator("[data-report-details]").getAttribute("open"), null);
      await dialog.getByText(tr("About this report"), { exact: true }).focus();
      await page.keyboard.press("Enter");
      assert.equal(
        await dialog.getByRole("button", { name: tr("View code"), exact: true }).count(),
        0,
      );
      assert.equal(
        await dialog
          .getByRole("link", { name: /Documentation|Dokumentation|Documentatie|Documentación/ })
          .count(),
        1,
      );
      assert.equal(
        await dialog.getByRole("button", { name: tr("Filter records"), exact: true }).count(),
        0,
      );
      await dialog.locator("[data-report-technical] > summary").click();
      assert.equal(
        await dialog.getByRole("button", { name: tr("View code"), exact: true }).count(),
        1,
      );
      assert.equal(await dialog.locator("[data-catalog-secondary]").count(), 0);
      await dialog
        .getByRole("button", { name: tr("View code"), exact: true })
        .first()
        .waitFor();
      await dialog
        .getByRole("link", { name: /Documentation|Dokumentation|Documentatie|Documentación/ })
        .first()
        .waitFor();
      await dialog.locator("[data-report-technical] > summary").click();
      await dialog.locator("[data-report-data]").evaluate((el) => {
        el.scrollTop = 0;
      });
      await dialog
        .getByRole("button", { name: tr("Show details"), exact: true })
        .first()
        .click();
      await dialog.getByText("i1", { exact: true }).waitFor();
      await dialog
        .getByRole("button", { name: tr("Show details"), exact: true })
        .first()
        .click();
      await page.screenshot({
        path: `/private/tmp/reality-219-browser/${language}-report-desktop.png`,
      });
      await page.keyboard.press("Escape");
      await dialog.waitFor({ state: "detached" });
      assert.equal(
        await row.locator("[data-report-open]").evaluate((el) => el === document.activeElement),
        true,
      );
      assert.equal(await search.inputValue(), tr("Stock overview"));
      await search.fill("");
      await openReport("fulfillment_queue");
      const dispatch = page.getByRole("dialog", { name: tr("Dispatch readiness"), exact: true });
      await dispatch.getByRole("cell", { name: "Maple Retail", exact: true }).waitFor();
      await dispatch
        .getByRole("columnheader")
        .first()
        .getByText(tr("Customer"), { exact: true })
        .waitFor();
      assert.equal(
        await dispatch.getByRole("columnheader", { name: "party_id", exact: true }).count(),
        0,
      );
      assert.equal(await dispatch.locator("[data-report-technical]").count(), 1);
      await dispatch.getByRole("button", { name: tr("Show details"), exact: true }).click();
      await dispatch.getByText("party-exact", { exact: true }).waitFor();
      await dispatch.getByRole("button", { name: tr("Show details"), exact: true }).click();
      await dispatch.locator(".erp-table-scroll").evaluate((el) => {
        el.scrollLeft = 0;
      });
      await page.screenshot({
        path: `/private/tmp/reality-219-browser/${language}-dispatch-desktop.png`,
      });
      await dispatch.locator("[data-report-technical] > summary").click();
      assert.equal(
        await dispatch.getByRole("button", { name: tr("View code"), exact: true }).count(),
        1,
      );
      await page.screenshot({
        path: `/private/tmp/reality-219-browser/${language}-dispatch-technical.png`,
      });
      if (language === "de") {
        await page.evaluate(() => {
          document.documentElement.dataset.theme = "dark";
        });
        await page.screenshot({ path: "/private/tmp/reality-219-browser/de-dispatch-dark.png" });
        await page.evaluate(() => {
          document.documentElement.dataset.theme = "light";
        });
      }
      await page.keyboard.press("Escape");
      await openReport("price_resolution");
      await page.getByRole("dialog", { name: tr("Price determination"), exact: true }).waitFor();
      assert.equal(
        readPaths.some((path) => path.includes("projection-snapshots/price_resolution")),
        false,
      );
      await page.keyboard.press("Escape");
      await openReport("view:items");
      await page.getByRole("dialog").getByText("Catalog item data", { exact: true }).waitFor();
      await page.keyboard.press("Escape");
      const hideChat = page.getByRole("button", { name: tr("Hide chat"), exact: true });
      if (await hideChat.isVisible()) await hideChat.click();
      await page.screenshot({ path: `/private/tmp/reality-219-browser/${language}-desktop.png` });
      await page.setViewportSize({ width: 390, height: 844 });
      await openReport("inventory");
      await page.getByRole("dialog", { name: tr("Stock overview"), exact: true }).waitFor();
      const mobileDialog = page.getByRole("dialog");
      assert.equal(await mobileDialog.locator("[data-report-details]").getAttribute("open"), null);
      await mobileDialog.getByText(tr("About this report"), { exact: true }).click();
      await mobileDialog.locator("[data-report-explanation]").waitFor();
      await mobileDialog.getByText(tr("About this report"), { exact: true }).click();
      const mobileDetails = await mobileDialog.locator("[data-report-details]").boundingBox();
      const mobileData = await mobileDialog.locator("[data-report-data]").boundingBox();
      assert.ok(mobileDetails.y < mobileData.y, "Mobile explanation precedes data");
      assert.ok(await mobileDialog.evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
      await page.screenshot({
        path: `/private/tmp/reality-219-browser/${language}-report-mobile.png`,
      });
      await page.keyboard.press("Escape");
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: `/private/tmp/reality-219-browser/${language}-mobile.png` });
      console.log(
        `Report UX passed: ${language}, desktop/mobile, filters/search, keyboard/focus, stored/live readers and technical details`,
      );
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(writes, []);
  } catch (error) {
    console.error(await page.locator("body").innerText());
    console.error(errors);
    throw error;
  } finally {
    await browser.close();
  }
  process.exit(0);
}

if (process.env.NAVIGATION_ONLY === "1") {
  const { parseCatalogs } = await import("./i18n-audit-lib.mjs");
  const catalogs = parseCatalogs(new URL("../src/localization.tsx", import.meta.url).pathname);
  const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
  const tr = (key) => (language === "en" ? key : catalogs[language].get(key) || key);
  const tabs = () => page.locator("[data-page-tabs] .register-tabs");
  const sidebar = () => page.getByRole("navigation", { name: "Reality Inspector", exact: true });
  const heading = async (key) =>
    page
      .locator("[data-shell-header] h1")
      .filter({ hasText: tr(key) })
      .waitFor();
  try {
    await mkdir("/private/tmp/reality-218-browser", { recursive: true });
    for (language of ["en", "de", "nl", "es"]) {
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=rules`);
      await heading("Fact rules");
      await page.locator('[data-navigation-item][aria-label="Commitments"]').waitFor();
      assert.equal(
        await page.locator('[data-navigation-item][aria-label="Commitments"]').innerText(),
        "Commitments",
      );
      assert.equal(
        await page.getByRole("link", { name: "Business commitments", exact: true }).count(),
        0,
      );

      await page.locator("[data-rules-register]").waitFor();
      assert.deepEqual(
        (await sidebar().getByRole("link").allTextContents()).map((x) => x.trim()),
        ["Business Recorder", "Business Facts", tr("Activities"), "Tools"],
      );
      assert.equal(
        await sidebar()
          .getByRole("link", { name: "Business Facts", exact: true })
          .getAttribute("aria-current"),
        "page",
      );
      assert.deepEqual(
        (await tabs().getByRole("button").allTextContents()).map((x) => x.trim()),
        [tr("All records"), tr("Fact rules")],
      );
      for (const [key, selector] of [
        ["Activities", "[data-inline-activity]"],
        ["Tools", "[data-action-directory]"],
      ]) {
        await sidebar()
          .getByRole("link", { name: tr(key), exact: true })
          .click();
        await heading(key === "Tools" ? "Actions" : key);
        await page.locator(selector).waitFor();
        assert.equal(await tabs().count(), key === "Tools" ? 1 : 0);
        assert.equal(
          await sidebar()
            .getByRole("link", { name: tr(key), exact: true })
            .getAttribute("aria-current"),
          "page",
        );
      }
      assert.deepEqual(
        (await tabs().getByRole("button").allTextContents()).map((x) => x.trim()),
        [tr("Actions"), tr("Calculated views")],
      );
      await tabs()
        .getByRole("button", { name: tr("Calculated views"), exact: true })
        .click();
      await page.locator("[data-report-catalog]").waitFor();
      await heading("Calculated views");
      assert.equal(
        await sidebar()
          .getByRole("link", { name: "Tools", exact: true })
          .getAttribute("aria-current"),
        "page",
      );
      assert.equal(new URL(page.url()).searchParams.get("inspector_view"), "views");
      await page.reload();
      await heading("Calculated views");
      await page.goBack();
      await heading("Actions");
      await page.goForward();
      await heading("Calculated views");
      await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=exceptions`);
      await heading("Exception rules");
      await page.locator('[data-exception-class="shortage"]').waitFor();
      assert.equal(
        await page
          .locator('[data-navigation-item][aria-current="page"]')
          .getAttribute("aria-label"),
        tr("Exceptions"),
      );
      await tabs()
        .getByRole("button", { name: tr("Open exceptions"), exact: true })
        .click();
      await page.locator('[data-work-list="exceptions"]').waitFor();
      await tabs()
        .getByRole("button", { name: tr("Exception rules"), exact: true })
        .click();
      assert.equal(new URL(page.url()).searchParams.get("attention_view"), "rules");
      await page.reload();
      await heading("Exception rules");
      await page.locator('[data-exception-class="shortage"]').waitFor();
      await page.goBack();
      await page.locator('[data-work-list="exceptions"]').waitFor();
      await page.goForward();
      await heading("Exception rules");
      await page.locator('[data-exception-class="shortage"] button').first().click();
      await page
        .locator("#exception-preview-shortage")
        .getByRole("button", { name: tr("Open in Exceptions"), exact: true })
        .click();
      await page.locator('[data-work-list="exceptions"]').waitFor();
      assert.equal(new URL(page.url()).searchParams.get("attention_view"), null);
      assert.equal(new URL(page.url()).searchParams.get("tenant"), "t1");
      const hideChat = page.getByRole("button", { name: tr("Hide chat"), exact: true });
      if (await hideChat.isVisible()) await hideChat.click();
      await page.setViewportSize({ width: 390, height: 844 });
      await tabs()
        .getByRole("button", { name: tr("Exception rules"), exact: true })
        .click();
      await heading("Exception rules");
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: `/private/tmp/reality-218-browser/${language}-mobile.png` });
      await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=views`);
      await heading("Calculated views");
      assert.deepEqual(
        (await tabs().getByRole("button").allTextContents()).map((x) => x.trim()),
        [tr("Actions"), tr("Calculated views")],
      );
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({
        path: `/private/tmp/reality-218-browser/${language}-tools-mobile.png`,
      });
      console.log(
        `Navigation passed: ${language}, desktop/mobile, legacy links, reload/history, rules to findings`,
      );
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(writes, []);
  } catch (error) {
    console.error(await page.locator("body").innerText());
    console.error(errors);
    throw error;
  } finally {
    await browser.close();
  }
  process.exit(0);
}

// The Inspector's sections and tab names changed; the section navigation has its own check
// below. Other steps open a view by its route key, as back/forward navigation does.
const tab = async (name) => {
  const views = {
    Overview: "overview",
    "Record graph": "graph",
    Facts: "facts",
    "Reality records": "facts",
    "Additional fact rules": "rules",
    "Exception catalog": "exceptions",
    "Projections & views": "views",
    "Commands & actions": "commands",
    "Execution history": "history",
  };
  await page.evaluate((view) => {
    const url = new URL(location.href);
    url.searchParams.set("inspector_view", view);
    history.pushState({}, "", url);
    dispatchEvent(new PopStateEvent("popstate"));
  }, views[name]);
};

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
  await shortagePreview.locator("[data-open-findings] li").first().waitFor();
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
    ["Business Recorder", "Business Facts", "Activities", "Tools"],
  );
  assert.equal(
    await page.getByRole("link", { name: "Technology & system", exact: true }).count(),
    0,
  );
  // The Inspector opens on the Business Recorder's Timeline.
  await page.getByRole("heading", { name: "Timeline", exact: true }).waitFor();
  await page.locator('[data-journey-history="evt1"]').waitFor();
  await tab("Reality records");
  // The records view lists every record type in one table; the fact is its last row.
  await page
    .locator("tr")
    .filter({ hasText: "Priority fact" })
    .getByRole("button", { name: "Record graph", exact: true })
    .click();
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
  // Tools (commands, actions and calculated views) are covered by
  // unified-tool-catalog-browser.mjs.
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
  // Fact rules (guided setup, simulation, review and drafts) are covered by
  // fact-rule-wizard-browser.mjs and guided-rules-browser.mjs.
  // Spec233 replaces recorder pulses and the secondary trace with order journeys.
  // Exact membership, paging, collisions and responsive behavior are exercised by
  // order-journey-browser.mjs; this suite retains the shared Inspector handoff.
  await page.goto("http://localhost:5177/app/inspector?tenant=t1&inspector_view=overview");
  await page.locator('[data-journey-history="evt1"]').waitFor();
  await page.locator('[data-journey-history="evt1"]').click();
  await page.getByRole("button", { name: "Inspect record", exact: true }).click();
  await page.getByRole("dialog").waitFor();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: "/private/tmp/reality-138-browser/order-journey-desktop.png" });
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
  await page.getByText("No recorded changes for this selection.", { exact: true }).waitFor();
  releaseOld();
  assert.equal(await page.locator("[data-journey-history]").count(), 0);
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
    "PASS: Inspector sections, timeline, records, record graph, exception catalog, history, route reload and tenant/member boundaries.",
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
