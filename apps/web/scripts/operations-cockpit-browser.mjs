import { shipping, flows } from "./fixtures/operations-cockpit-data.mjs";
// Product component proof; PostgreSQL stories independently prove these shipping values.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
page.setDefaultTimeout(10000);
async function showWorkspace(view) {
  await page.locator(".cockpit-workspace-selector select").selectOption(view);
}
async function openCaseWorkspace() {
  await showWorkspace("responsibility");
  const toggle = page.getByRole("button", { name: "Select a case", exact: true });
  if (await toggle.count()) await toggle.click();
}
async function assertCaseEntry(label) {
  const layout = await page.evaluate(() => {
    const rect = (selector) => {
      const { top, bottom, left, right, width } = document
        .querySelector(selector)
        .getBoundingClientRect();
      return { top, bottom, left, right, width };
    };
    return {
      workspace: rect("[data-operations-workspace]"),
      analysis: rect("[data-operating-flows]"),
      console: rect(".operations-cockpit"),
      visible: document.querySelectorAll(".cockpit-workspace-pane:not([hidden])").length,
      headingFits: (() => {
        const h = document.querySelector("[data-operations-workspace] > header h2");
        return h.scrollWidth <= h.clientWidth;
      })(),
      nested: [...document.querySelectorAll(".cockpit-workspace-pane > .cockpit-card")].map(
        (el) => ({
          border: getComputedStyle(el).borderTopWidth,
          padding: getComputedStyle(el).paddingTop,
        }),
      ),
    };
  });
  assert(layout.headingFits, `${label}: workspace heading is not squeezed under its selector`);
  assert.equal(layout.visible, 1, `${label}: exactly one right view occupies layout`);
  assert(
    layout.nested.every((x) => x.border === "0px" && x.padding === "0px"),
    `${label}: secondary views have no nested frames or padding`,
  );
  assert(layout.workspace.width <= 1120, `${label}: bounded operations workspace`);
  if (label === "initial desktop")
    assert(
      layout.workspace.bottom < layout.analysis.bottom,
      `${label}: compact workspace keeps natural height`,
    );
  if (layout.console.width > 820) {
    assert(
      Math.abs(layout.analysis.top - layout.workspace.top) < 2,
      `${label}: analysis and operations workspace share the top row`,
    );
    assert(layout.workspace.left >= layout.analysis.right, `${label}: workspace beside analysis`);
  } else {
    assert(
      layout.workspace.top > layout.analysis.bottom,
      `${label}: workspace follows shared analysis`,
    );
  }
}
async function assertWorkspaceSurfaces(label) {
  const surfaces = await page.evaluate(() => {
    const tokens = getComputedStyle(document.documentElement);
    return {
      workspace: tokens.getPropertyValue("--surface").trim(),
      neutral: tokens.getPropertyValue("--surface-sunken").trim(),
      canvas: getComputedStyle(document.querySelector(".operations-cockpit")).backgroundColor,
      cards: [...document.querySelectorAll(".cockpit-card")].map(
        (element) => getComputedStyle(element).backgroundColor,
      ),
      details: [
        ...document.querySelectorAll(".cockpit-selection, .cockpit-basis, .cockpit-unavailable"),
      ].map((element) => getComputedStyle(element).backgroundColor),
    };
  });
  const rgb = (hex) =>
    `rgb(${hex
      .slice(1)
      .match(/../g)
      .map((part) => Number.parseInt(part, 16))
      .join(", ")})`;
  assert.equal(surfaces.canvas, rgb(surfaces.workspace), `${label}: shared workspace ground`);
  assert(surfaces.cards.length > 0 && surfaces.details.length > 0);
  assert(
    surfaces.cards.every((color) => color === rgb(surfaces.workspace)),
    `${label}: cards retain the shared surface`,
  );
  assert(
    surfaces.details.every((color) => color === rgb(surfaces.neutral)),
    `${label}: selection and explanation use the shared neutral surface`,
  );
}
async function assertTrafficPalette(label) {
  const palette = await page.locator("[data-status-area]").evaluateAll((elements) =>
    elements.map((element) => ({
      signal: element.getAttribute("data-signal"),
      dot: getComputedStyle(element.querySelector(".cockpit-status-indicator")).backgroundColor,
      border: getComputedStyle(element).borderTopColor,
      detail: getComputedStyle(
        document.querySelector(
          `[data-flow-area="${element.getAttribute("data-status-area")}"] .cockpit-flow-signal > span`,
        ),
      ).backgroundColor,
    })),
  );
  for (const tile of palette) {
    const expected =
      tile.signal === "critical"
        ? "rgb(200, 73, 54)"
        : tile.signal === "clear"
          ? "rgb(35, 132, 96)"
          : "rgb(217, 119, 6)";
    assert.equal(tile.dot, expected, `${label}: ${tile.signal} has a classic traffic-light dot`);
    assert.equal(tile.border, expected, `${label}: ${tile.signal} has the matching border`);
    assert.equal(tile.detail, expected, `${label}: the detail status uses the same color`);
  }
}
async function assertFlowAlignment(label) {
  await assertTrafficPalette(label);
  await assertWorkspaceSurfaces(label);
  await assertCaseEntry(label);
  const statusTiles = await page.locator("[data-status-area]").evaluateAll((elements) =>
    elements.map((element) => ({
      width: element.clientWidth,
      overflow: element.scrollWidth > element.clientWidth,
      indicator: element.querySelector(".cockpit-status-indicator")?.getBoundingClientRect().width,
    })),
  );
  assert.equal(statusTiles.length, 5, `${label}: summary retains all five areas`);
  assert(
    statusTiles.every((tile) => !tile.overflow && tile.indicator >= 16),
    `${label}: prominent status indicators do not clip`,
  );
  const cards = await page.locator("[data-flow-area]").evaluateAll((elements) =>
    elements
      .filter((element) => !element.hidden)
      .map((element) => ({
        area: element.getAttribute("data-flow-area"),
        top: element.getBoundingClientRect().top,
        metricTops: [...element.querySelectorAll("dd")].map(
          (node) => node.getBoundingClientRect().top,
        ),
        chartTop: element.querySelector(".cockpit-flow-curve")?.getBoundingClientRect().top,
      })),
  );
  for (const card of cards) {
    const peers = cards.filter((peer) => Math.abs(peer.top - card.top) < 2);
    for (const peer of peers) {
      for (let i = 0; i < Math.min(card.metricTops.length, peer.metricTops.length); i++) {
        assert(
          Math.abs(card.metricTops[i] - peer.metricTops[i]) <= 2,
          `${label}: metric row ${i} aligns for ${card.area}/${peer.area}`,
        );
      }
      if (card.chartTop !== undefined && peer.chartTop !== undefined) {
        assert(
          Math.abs(card.chartTop - peer.chartTop) <= 2,
          `${label}: charts align for ${card.area}/${peer.area}`,
        );
      }
    }
  }
  if (await page.locator("[data-flow-area]:not([hidden]) dl").count()) {
    const metricRows = await page
      .locator("[data-flow-area]:not([hidden]) dl")
      .evaluate((element) => {
        const columns = getComputedStyle(element).gridTemplateColumns.split(" ").length;
        const positions = [...element.querySelectorAll("dd")].map(
          (node) => node.getBoundingClientRect().top,
        );
        return { columns, positions };
      });
    for (let row = 0; row < metricRows.positions.length; row += metricRows.columns) {
      const peers = metricRows.positions.slice(row, row + metricRows.columns);
      assert(
        Math.max(...peers) - Math.min(...peers) < 2,
        `${label}: metric values align despite wrapping captions`,
      );
    }
    const metricSpacing = await page
      .locator("[data-flow-area]:not([hidden]) dl")
      .evaluate((element) => getComputedStyle(element).rowGap);
    assert.equal(
      metricSpacing,
      "16px",
      `${label}: selected analysis keeps explicit metric-row spacing`,
    );
  }
  const rhythm = await page.locator("[data-operating-flows]").evaluate((element) => ({
    margin: getComputedStyle(element).marginTop,
    headingHeight: element.querySelector("header").getBoundingClientRect().height,
    outerGap:
      element.getBoundingClientRect().top -
      element.closest(".cockpit-console-row").previousElementSibling.getBoundingClientRect().bottom,
    headingSize: getComputedStyle(element.querySelector("h2")).fontSize,
    sharedSize: getComputedStyle(document.querySelector(".cockpit-shipping h2")).fontSize,
    contentGap:
      element
        .querySelector("[data-shipping-analysis]:not([hidden]), [data-flow-area]:not([hidden])")
        .getBoundingClientRect().top -
      element.querySelector("header").getBoundingClientRect().bottom,
    selectorInHeader: Boolean(element.querySelector("header .cockpit-analysis-selector")),
    border: getComputedStyle(element).borderTopWidth,
    nestedCards: element.querySelectorAll(".cockpit-card").length,
    paddings: [
      ...document.querySelectorAll("[data-operations-workspace], [data-operating-flows]"),
    ].map((node) => getComputedStyle(node).paddingTop),
  }));
  assert(
    rhythm.headingHeight < 180,
    `${label}: analysis heading has no artificial vertical spacer`,
  );
  assert.equal(rhythm.margin, "0px", `${label}: section does not stack outer margins`);
  assert.equal(
    rhythm.headingSize,
    rhythm.sharedSize,
    `${label}: section headings share their hierarchy`,
  );
  assert(
    rhythm.outerGap >= 20 && rhythm.outerGap <= 24,
    `${label}: section follows the shared page rhythm`,
  );
  assert(
    rhythm.contentGap >= 16 && rhythm.contentGap <= 24,
    `${label}: heading is separated from analysis`,
  );
  assert(rhythm.selectorInHeader, `${label}: one selection belongs to the analysis header`);
  assert.equal(rhythm.border, "1px", `${label}: analysis has one outer frame`);
  assert.equal(rhythm.nestedCards, 0, `${label}: no nested analysis card`);
  assert(new Set(rhythm.paddings).size === 1, `${label}: equal card insets`);
}

const errors = [],
  writes = [],
  reads = [];
page.on("pageerror", (error) => errors.push(error.message));
let denseEvidence = true,
  missing = false,
  failure = false,
  nextDayCollection = false,
  largeCaseCounts = false,
  reconcilingCases = false,
  staleAccess = false,
  staleCases = false,
  summaryVariants = false,
  absentFlows = false;
let eventIndex = 1,
  restrictedAgents = false;
let controlMode = "automation",
  controlRevision = 1;
const caseRow = () => ({
  case_id: "case_d",
  kind: "order_fulfillment",
  order_document_id: "order_d",
  business_reference: "SO-104",
  return_announcement_id: null,
  control_mode: controlMode,
  control_revision: controlRevision,
  goal_state: "outstanding",
  source_record_ids: ["src_order"],
  unavailable_capabilities: [],
  related_case_ids: ["return_d"],
  unsettled_actions: [],
  coverage_gaps: [],
  actions: [],
  work: [{ commitment_id: "com_d", open_quantity: "2", status: "open" }],
  control:
    controlMode === "human"
      ? {
          actor_label: "Alex Operations",
          recorded_at: "2026-10-06T12:31:00Z",
          reason: "Customer appointment",
          revision: controlRevision,
          decision_id: "decision_takeover",
          event_id: "event_takeover",
        }
      : null,
});
const at = (time) => `2026-10-06T${time}:00+00:00`;
await page.route("**/api/**", (route) => {
  const request = route.request(),
    url = new URL(request.url());
  reads.push(url);
  if (request.method() !== "GET") writes.push(url.pathname);
  const reply = (value, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(value) });
  if (url.pathname.endsWith("/operational-cases/status"))
    return reply({ adopted: true, can_control: true, can_adopt: false });
  if (url.pathname.endsWith("/operational-cases/register")) {
    if (staleCases) return reply({ detail: "Temporarily unavailable" }, 503);
    return reply(
      reconcilingCases
        ? {
            observed_at: at("12:30"),
            adopted: true,
            coordination: { migration_ready: true, coverage_ready: false, last_error_code: null },
            total: 0,
            counts: { automation: 0, human: 0, outstanding: 0, completed: 0, abandoned: 0 },
            items: [],
            has_more: false,
            next_after: null,
          }
        : {
            observed_at: at("12:30"),
            adopted: true,
            total: largeCaseCounts ? 15801 : 1,
            counts: {
              automation: largeCaseCounts ? 12345 : controlMode === "automation" ? 1 : 0,
              human: largeCaseCounts ? 3456 : controlMode === "human" ? 1 : 0,
              outstanding: largeCaseCounts ? 15801 : 1,
              completed: 0,
              abandoned: 0,
            },
            items:
              controlMode === "human" || url.searchParams.get("control_mode") !== "human"
                ? [caseRow()]
                : [],
            has_more: largeCaseCounts,
            next_after: largeCaseCounts ? "remaining-cases" : null,
          },
    );
  }
  if (url.pathname.endsWith("/case_d/handback-review"))
    return reply({ ...caseRow(), digest: "a".repeat(64) });
  if (url.pathname.endsWith("/case_d/takeover")) {
    const body = request.postDataJSON();
    assert.equal(body.expected_revision, 1);
    assert.equal(body.confirmed, true);
    assert.equal(body.reason, "Customer appointment");
    assert(body.request_key);
    controlMode = "human";
    controlRevision = 2;
    return reply(caseRow());
  }
  if (url.pathname.endsWith("/case_d/handback")) {
    assert.equal(request.postDataJSON().review_digest, "a".repeat(64));
    controlMode = "automation";
    controlRevision = 3;
    return reply(caseRow());
  }
  if (url.pathname.endsWith("/operational-cases/case_d")) return reply(caseRow());
  if (url.pathname.endsWith("/capabilities")) return reply({ enabled: true });
  if (url.pathname.endsWith("/activity")) {
    if (failure) return reply({ detail: "Temporarily unavailable" }, 503);
    return reply({
      flows: absentFlows
        ? undefined
        : summaryVariants
          ? {
              ...flows,
              orders: { ...flows.orders, signal: "attention" },
              returns: { ...flows.returns, signal: "clear" },
            }
          : missing
            ? {
                ...flows,
                messages: {
                  ...flows.messages,
                  signal: "unknown",
                  coverage: "unavailable",
                  unanswered: null,
                  customer_requests: null,
                  unread: null,
                  series: flows.messages.series.map((point) => ({ ...point, unanswered: null })),
                },
              }
            : flows,
      observed_at: at("12:30"),
      start: at("12:15"),
      coverage_start: at("12:15"),
      minutes: Number(url.searchParams.get("minutes") || 15),
      bucket_seconds: 60,
      total: eventIndex,
      counts: { orders: eventIndex, reservations: 0, movements: 0, documents: 0 },
      buckets: [
        {
          start: at("12:29"),
          end: at("12:30"),
          partial: false,
          counts: { orders: eventIndex, reservations: 0, movements: 0, documents: 0 },
          total: eventIndex,
        },
      ],
      events: [
        {
          id: `event_${eventIndex}`,
          sequence: eventIndex,
          type: "document.recorded",
          subject_type: "document",
          subject_id: `doc_${eventIndex}`,
          recorded_at: at("12:29"),
          occurred_at: at("11:00"),
          source_record_id: null,
        },
      ],
      has_more: false,
    });
  }
  if (url.pathname.endsWith("/agents"))
    if (staleAccess) return reply({ detail: "Temporarily unavailable" }, 503);
    else
      return restrictedAgents
        ? reply({ detail: "Restricted" }, 403)
        : reply({
            observed_at: at("12:30"),
            coverage: { manual: "available", oauth: "available", runtime: "unavailable" },
            scope: "active",
            total: 1,
            items: [
              {
                identity: "manual:shipping",
                name: "Shipping <Agent>",
                connection_kind: "manual",
                access_state: "active",
                access_reason: null,
                last_used_at: at("12:29"),
                runtime_state: "unknown",
                permitted_tools: ["inventory"],
                observed_action: {
                  interaction_id: "interaction_1",
                  operation: "inventory",
                  outcome: "failed",
                  recorded_at: at("12:29"),
                  proposal_id: null,
                  business_references: [],
                  references_bounded: false,
                },
              },
            ],
            has_more: false,
            next_after: null,
          });
  if (url.pathname.endsWith("/orders"))
    return reply({
      items: [
        {
          order_id: "order_d",
          number: "SO-104",
          commitment_ids: ["com_d"],
          location_ids: ["loc_venlo"],
          due_at: at("14:00"),
          plan_at: at("13:30"),
          handover_at: null,
          forecast_at: null,
          at_risk: true,
          risk_at: at("14:00"),
          risk_requirements: [],
          blockers: {
            com_d: [
              {
                code: "commitment_hold",
                detail: "The delivery commitment has an active hold.",
                links: [{ kind: "commitment_hold", id: "hold_d" }],
              },
            ],
          },
          coverage_gaps: [],
          physical_contents: {},
        },
      ],
      total: 1,
      has_more: false,
      next_after: null,
      basis_key: "basis-current",
      observed_at: at("12:30"),
      re_evaluated: true,
      coverage: shipping.coverage,
      totals: shipping.totals,
    });
  if (url.pathname.endsWith("/operations-cockpit")) {
    if (failure) return reply({ detail: "Temporarily unavailable" }, 503);
    return reply({
      observed_at: shipping.observed_at,
      deviations: denseEvidence
        ? Array.from({ length: 8 }, (_, index) => ({
            order_id: `order_dense_${index}`,
            number: `SO-DENSE-${index}`,
            case_id: index === 2 ? null : `case_dense_${index}`,
            responsibility: index === 2 ? null : "automation",
            coverage_gaps: index === 1 ? ["handover_confirmation_missing"] : [],
            blockers:
              index === 1
                ? {}
                : {
                    [`com_dense_${index}`]: Array.from({ length: 4 }, (_, blocker) => ({
                      code: `dense_blocker_${blocker}`,
                      detail: `Recorded blocker ${index}-${blocker}`,
                    })),
                  },
            recorded_case_actions: Array.from({ length: 40 }, (_, action) => ({
              proposal_id: `act_dense_${index}_${action}`,
              type: `Recorded action ${action}`,
              status: "executed",
            })),
          }))
        : [],
      deviation_total: missing ? null : denseEvidence ? 321 : 0,
      deviations_has_more: denseEvidence,
      shipping: missing
        ? {
            ...shipping,
            daily_activity: {
              booked_orders: 8,
              handed_over_packages: 6,
              coverage: "complete",
              series: {
                booked_orders: [{ at: at("12:00"), count: 8 }],
                handed_over_packages: [{ at: at("12:05"), count: 6 }],
              },
              evidence: [
                {
                  movement_id: "mov_actual",
                  source_record_id: "src_actual",
                  occurred_at: at("12:00"),
                },
                {
                  package_id: "pkg_actual",
                  event_ids: ["sev_actual"],
                  source_ids: ["src_carrier_actual"],
                  occurred_at: at("12:05"),
                },
              ],
              evidence_total: 2,
              evidence_has_more: false,
            },
            totals: { due: null, handed_over: null, forecast: null, risk: null },
            series: { plan: null, handover: null, forecast: null },
            sites: [],
            coverage: { cohort: "unavailable", handover: "unavailable", forecast: "unavailable" },
            gaps: [{ code: "missing_shipping_plan" }],
          }
        : {
            ...shipping,
            sites: shipping.sites.map((site, index) =>
              denseEvidence && index === 0
                ? {
                    ...site,
                    cutoffs: Array.from({ length: 320 }, (_, index) => ({
                      at: new Date(Date.parse(at("14:00")) + index * 1000).toISOString(),
                      confirmation_state: "confirmed",
                      source_record_id: `src_cutoff_${index}`,
                    })),
                  }
                : nextDayCollection && index === 0
                  ? {
                      ...site,
                      cutoffs: site.cutoffs.map((cutoff) => ({
                        ...cutoff,
                        at: "2026-10-07T01:00:00Z",
                      })),
                    }
                  : site,
            ),
          },
    });
  }
  return reply({});
});
try {
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
  await page.getByRole("heading", { name: "Shipping by end of day" }).waitFor();
  const combinedSelector = page.getByRole("combobox", { name: "Analysis area", exact: true });
  assert.equal(await combinedSelector.inputValue(), "shipping", "shipping is the default analysis");
  assert.deepEqual(
    await combinedSelector
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.value)),
    ["shipping", "orders", "messages", "supply", "stock", "returns"],
    "shipping is the first of six analysis options",
  );
  assert.equal(
    await page.locator("[data-operating-flows] .cockpit-shipping").count(),
    1,
    "shipping occupies the shared analysis location",
  );
  await assertCaseEntry("initial desktop");
  await page.locator(".operations-cockpit").evaluate((el) => {
    el.style.maxWidth = "980px";
  });
  await assertCaseEntry("docked workspace");
  await page.locator(".operations-cockpit").evaluate((el) => {
    el.style.maxWidth = "";
  });
  const workspaceSelector = page.getByRole("combobox", { name: "Workspace view", exact: true });
  assert.match(
    await page.locator("[data-shipping-deviations] > summary").textContent(),
    new RegExp(`Affected orders: ${denseEvidence ? 321 : 0}`),
    "collapsed disclosure retains the actual cohort count",
  );
  assert.equal(await workspaceSelector.inputValue(), "responsibility");
  assert.deepEqual(
    await workspaceSelector.locator("option").evaluateAll((opts) => opts.map((x) => x.value)),
    ["responsibility", "activity", "agents"],
  );
  assert.equal(
    await page.getByRole("button", { name: "Pause following", exact: true }).count(),
    0,
    "hidden log is excluded from accessibility",
  );
  assert.equal(
    await page.getByRole("heading", { name: "Agents & connections", exact: true }).count(),
    0,
    "hidden Agent view is excluded from accessibility",
  );
  assert.equal(
    await page.locator("[data-shipping-deviations]").evaluate((el) => el.open),
    false,
    "shipping blockers start collapsed",
  );
  assert.equal(
    await page.locator("[data-shipping-analysis] [data-operational-deviations]").count(),
    1,
    "shipping blockers belong to shipping analysis",
  );
  await workspaceSelector.focus();
  const beforeWorkspace = await workspaceSelector.evaluate((el) => ({
    top: el.closest("[data-operations-workspace]").getBoundingClientRect().top,
    history: history.length,
  }));
  await workspaceSelector.press("l");
  assert.equal(
    await workspaceSelector.inputValue(),
    "activity",
    "native keyboard changes workspace view",
  );
  assert.equal(await page.locator("[data-case-register]").isVisible(), false);
  const afterWorkspace = await workspaceSelector.evaluate((el) => ({
    top: el.closest("[data-operations-workspace]").getBoundingClientRect().top,
    history: history.length,
    focus: document.activeElement === el,
  }));
  assert(
    Math.abs(beforeWorkspace.top - afterWorkspace.top) < 2 &&
      beforeWorkspace.history === afterWorkspace.history &&
      afterWorkspace.focus,
    "workspace switch retains viewport, history and focus",
  );
  await showWorkspace("agents");
  const accessToggle = page.getByRole("button", { name: "View all accesses", exact: true });
  assert.equal(await accessToggle.getAttribute("title"), "View all accesses");
  assert.equal(await accessToggle.locator("svg").count(), 1);
  assert.equal(await accessToggle.getAttribute("aria-expanded"), "false");
  await accessToggle.focus();
  await page.keyboard.press("Enter");
  await page.getByRole("combobox", { name: /Access state/ }).waitFor();
  const compactAccess = page.getByRole("button", { name: "Compact view", exact: true });
  assert.equal(await compactAccess.getAttribute("aria-expanded"), "true");
  await showWorkspace("responsibility");
  await showWorkspace("agents");
  assert.equal(
    await compactAccess.getAttribute("aria-expanded"),
    "true",
    "Agent expansion survives view switches",
  );
  await compactAccess.click();
  await showWorkspace("responsibility");
  await page.locator("[data-risk-legend]").waitFor();
  for (const area of ["orders", "messages", "supply", "stock", "returns"]) {
    const tile = page.locator(`[data-status-area="${area}"]`);
    for (const category of ["in_plan", "at_risk", "critical"]) {
      const count = flows[area].risk[category];
      assert.equal(
        await tile.locator(`[data-risk-count="${category}"] strong`).textContent(),
        count === null ? "—" : String(count),
      );
    }
    const total = flows[area].risk.total;
    if (total > 0) {
      for (const category of ["in_plan", "at_risk", "critical", "unclassified"]) {
        const count = flows[area].risk[category];
        if (typeof count === "number" && count > 0) {
          const width = await tile
            .locator(`[data-risk-segment="${category}"]`)
            .evaluate((node) => Number.parseFloat(node.style.width));
          assert(
            Math.abs(width - (100 * count) / total) < 0.001,
            `${area}/${category}: meter preserves the exact share, including small categories`,
          );
        }
      }
      const widths = await tile
        .locator("[data-risk-segment]")
        .evaluateAll((nodes) => nodes.map((node) => Number.parseFloat(node.style.width)));
      assert(
        Math.abs(widths.reduce((a, b) => a + b, 0) - 100) < 0.001,
        `${area}: exact proportional meter`,
      );
    }
  }
  assert.equal(await page.locator("[data-risk-legend] [data-risk-key]").count(), 4);
  assert.equal(await page.locator("[data-case-workspace]").isVisible(), false);
  const selectCase = page.getByRole("button", { name: "Select a case", exact: true });
  await selectCase.focus();
  await selectCase.press("Enter");
  assert(await page.locator("[data-case-workspace]").isVisible());
  await page.getByRole("button", { name: "Hide case list", exact: true }).click();
  await page.locator('[data-case-count="human"]').click();
  assert.equal(
    await page
      .getByRole("button", { name: "Manually taken over", exact: true })
      .getAttribute("aria-pressed"),
    "true",
  );
  await page.locator('[data-case-count="automation"]').click();
  assert.equal(
    await page
      .getByRole("button", { name: "Still open", exact: true })
      .getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(writes.length, 0, "ownership shortcuts never stop work");
  await page.getByRole("button", { name: "Hide case list", exact: true }).click();
  await page.evaluate(() => window.__cockpitNavigate({ cockpitCase: "case_d" }));
  await page.locator("[data-case-inspection]").waitFor();
  assert(
    await page.locator("[data-case-workspace]").isVisible(),
    "case context opens the register",
  );
  await page.getByRole("button", { name: "Close case inspection", exact: true }).click();
  await page.evaluate(() => window.__cockpitNavigate({ cockpitCase: "" }));
  assert.equal(await page.locator("[data-flow-area]").count(), 5);
  const summary = page.locator("[data-operating-status]");
  assert.equal(await summary.count(), 1, "a central status overview is present");
  assert.equal(await summary.locator("[data-status-area]").count(), 5);
  assert.equal(await summary.locator("[data-instrument-strip]").count(), 6);
  assert.match(
    await summary.locator('[data-instrument-area="finance"]').textContent(),
    /Not available/,
  );
  assert(
    await summary.evaluate(
      (element) =>
        element.getBoundingClientRect().bottom <
        document.querySelector(".cockpit-shipping").getBoundingClientRect().top,
    ),
    "status precedes shipping",
  );
  for (const area of ["orders", "messages", "supply", "stock", "returns"]) {
    const tile = summary.locator(`[data-status-area="${area}"]`);
    assert.equal(await tile.getAttribute("data-signal"), flows[area].signal);
    assert.equal(
      await tile.locator("[data-status-metric]").textContent(),
      await page.locator(`[data-flow-area="${area}"] dd`).first().textContent(),
    );
    assert.equal(
      await tile.locator("select").count(),
      0,
      "summary does not duplicate the chart selector",
    );
    assert((await tile.locator("button").count()) >= 4, "counts open compact inspection");
  }
  const areaSelector = page.getByRole("combobox", { name: "Analysis area", exact: true });
  assert.equal(await areaSelector.count(), 1, "analysis owns exactly one selector");
  assert.equal(await page.locator(".cockpit-analysis-selector button").count(), 0);
  await areaSelector.focus();
  const stablePosition = () =>
    page.locator("[data-operating-flows]").evaluate((el) => ({
      top: el.getBoundingClientRect().top,
      focused: document.activeElement === el.querySelector("select"),
      historyLength: history.length,
    }));
  const beforeInspectionUrl = page.url();
  const stockTrigger = summary.locator('[data-status-area="stock"] [data-risk-count="critical"]');
  await stockTrigger.focus();
  const beforeInspection = await stablePosition();
  await stockTrigger.click();
  const inspection = page.getByRole("dialog", { name: "Quick inspection", exact: true });
  await inspection.waitFor();
  assert.equal(await inspection.locator("tbody tr").count(), 2, "both uncovered items appear");
  assert.match(await inspection.textContent(), /Inspection mug/);
  assert.match(await inspection.textContent(), /Inspection bowl/);
  assert.equal(page.url(), beforeInspectionUrl, "inspection preserves URL");
  assert(
    Math.abs((await stablePosition()).top - beforeInspection.top) < 2,
    "inspection does not scroll",
  );
  await inspection
    .getByRole("combobox", { name: "Risk group", exact: true })
    .selectOption("in_plan");
  await inspection.getByText("No records in this group", { exact: true }).waitFor();
  await inspection.press("Escape");
  assert.equal(
    await stockTrigger.evaluate((el) => document.activeElement === el),
    true,
    "Escape restores risk trigger focus",
  );
  await summary.locator('[data-status-area="orders"] [data-status-metric]').click();
  await inspection.waitFor();
  assert.equal(await inspection.locator("tbody tr").count(), 8, "order preview stays bounded");
  await inspection.getByRole("button", { name: "Close", exact: true }).click();
  await areaSelector.focus();
  const beforeSelection = await stablePosition();
  await areaSelector.selectOption("messages");
  const afterSelection = await stablePosition();
  assert(
    Math.abs(afterSelection.top - beforeSelection.top) < 2,
    "selection does not scroll the analysis",
  );
  assert(afterSelection.focused, "selection retains keyboard focus");
  assert.equal(
    afterSelection.historyLength,
    beforeSelection.historyLength,
    "switching areas adds no history entry",
  );
  assert.equal(await page.evaluate(() => location.hash), "#cockpit-flow-messages");
  const bookmarkedHash = await page.evaluate(() => location.hash);
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html" +
      bookmarkedHash,
  );
  await page.locator('[data-flow-area="messages"]:visible').waitFor();
  assert.equal(await areaSelector.inputValue(), "messages", "bookmark reload restores area");
  await areaSelector.focus();
  await areaSelector.press("Tab");
  await page.keyboard.press("Shift+Tab");
  assert(
    await areaSelector.evaluate((el) => document.activeElement === el),
    "native selector stays in the keyboard tab order",
  );
  await areaSelector.selectOption("orders");
  await areaSelector.selectOption("messages");
  await showWorkspace("agents");
  await page.evaluate(() => window.__cockpitNavigate({ tenant: "other-company" }));
  assert.equal(
    await workspaceSelector.inputValue(),
    "responsibility",
    "company change resets the operations workspace",
  );
  await page.waitForFunction(
    () => document.querySelector(".cockpit-analysis-selector select")?.value === "shipping",
  );
  assert.equal(await areaSelector.inputValue(), "shipping", "company switch resets analysis");
  summaryVariants = true;
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
  await page.locator('[data-status-area="orders"][data-signal="attention"]').waitFor();
  for (const signal of ["attention", "progress", "unknown", "critical", "clear"]) {
    assert.equal(
      await summary.locator(`[data-signal="${signal}"]`).count(),
      1,
      `canonical ${signal} is distinct`,
    );
  }
  await assertTrafficPalette("all five canonical signals");
  summaryVariants = false;
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
  await page.locator('[data-status-area="orders"][data-signal="progress"]').waitFor();
  assert.equal(
    await page.locator("[data-operations-workspace]").count(),
    1,
    "one compact operations workspace",
  );
  await assertFlowAlignment("initial desktop");
  await showWorkspace("activity");
  await page.getByText("Recording rate & period", { exact: true }).click();
  const timeSelection = page.getByRole("group", { name: "Activity period", exact: true });
  assert.equal(await timeSelection.locator(".br-btn").count(), 3);
  assert.equal(await timeSelection.getByRole("button").nth(1).getAttribute("aria-pressed"), "true");
  await timeSelection.getByRole("button").nth(0).focus();
  await timeSelection.getByRole("button").nth(0).press("Space");
  await timeSelection
    .getByRole("button")
    .nth(0)
    .evaluate((button) => {
      if (button.getAttribute("aria-pressed") !== "true")
        throw new Error("Keyboard time selection did not update");
    });
  await timeSelection.getByRole("button").nth(1).click();
  await openCaseWorkspace();
  await areaSelector.selectOption("orders");
  assert.equal(await page.locator("[data-case-register] .cockpit-selection").count(), 1);
  await page.locator(".operations-cockpit").evaluate((element) => {
    element.style.maxWidth = "720px";
  });
  assert.equal(
    await page.locator("[data-flow-area]:visible").count(),
    1,
    "narrow analysis shows one selected area",
  );
  await page.locator(".operations-cockpit").evaluate((element) => {
    element.style.maxWidth = "440px";
  });
  const single = await page.locator("[data-flow-area]").evaluateAll((elements) =>
    elements
      .filter((element) => !element.hidden)
      .map((element) => ({
        top: element.getBoundingClientRect().top,
        display: getComputedStyle(element).display,
        overflow: element.scrollWidth > element.clientWidth,
      })),
  );
  assert(
    single.every((card) => card.display === "block" && !card.overflow),
    "single-column content releases comparison spacing without clipping",
  );
  assert.equal(single.length, 1, "only the selected analysis occupies space");
  await page.locator(".operations-cockpit").evaluate((element) => {
    element.style.maxWidth = "";
  });
  await page.locator(".cockpit-analysis-selector select").selectOption("messages");
  const mailbox = page.locator('[data-flow-area="messages"]');
  assert.equal(await mailbox.locator('[data-analysis-kind="flow"] [data-flow-series]').count(), 2);
  assert.equal(
    await mailbox.locator('[data-analysis-kind="backlog"] [data-flow-series]').count(),
    1,
  );
  await mailbox.getByText("Definition & evidence", { exact: true }).click();
  await page.waitForTimeout(5500);
  assert(await mailbox.isVisible(), "live refresh retains the selected analysis");
  assert(
    await mailbox.locator("details").evaluate((el) => el.open),
    "live refresh retains evidence disclosure",
  );
  await mailbox.getByText("Definition & evidence", { exact: true }).click();
  assert.equal(await mailbox.locator("dd").first().textContent(), "8");
  assert.equal(
    await mailbox.locator("dd").nth(2).textContent(),
    "3",
    "Unread is independent of reply backlog",
  );
  await mailbox.getByText("Definition & evidence", { exact: true }).click();
  const mailEvidence = await mailbox
    .getByRole("link", { name: "Delivery question", exact: true })
    .getAttribute("href");
  assert(
    mailEvidence.includes("inspector_target_kind=source_record") &&
      mailEvidence.includes("src_mail_flow") &&
      mailEvidence.includes("tenant=cockpit"),
  );
  await mailbox.getByText("Definition & evidence", { exact: true }).click();
  assert.equal(
    await page.locator('[data-flow-area="stock"] .cockpit-flow-signal.critical').count(),
    1,
  );
  assert.equal(
    await page.locator('[data-flow-area="supply"] .cockpit-flow-signal.unknown').count(),
    1,
  );
  assert.equal(await page.locator('[data-flow-area="returns"] dd').first().textContent(), "2");
  await showWorkspace("activity");
  await page.getByText("Business document recorded", { exact: true }).waitFor();
  await areaSelector.selectOption("shipping");
  const shippingDeviations = page.locator("[data-shipping-deviations]");
  await shippingDeviations.locator(":scope > summary").click();
  assert.equal(await page.locator("[data-shipping-series]").count(), 3);
  assert.equal(
    await page.locator("[data-cutoff-preview]").first().locator(":scope > div").count(),
    2,
    "Only two exact cutoff entries initially occupy the site row",
  );
  assert.equal(
    await page.locator("[data-deviation-preview]").count(),
    4,
    "Deviation preview remains bounded",
  );
  await page
    .locator("[data-deviation-preview]")
    .nth(1)
    .locator(":scope > .cockpit-blocker")
    .getByText("Required evidence is incomplete", { exact: true })
    .waitFor();
  await page
    .locator("[data-deviation-preview]")
    .nth(2)
    .getByText("No linked operational case", { exact: true })
    .waitFor();
  await areaSelector.selectOption("shipping");
  const cutoff = page.locator("[data-cutoff-details]");
  assert.equal(
    await cutoff.locator("[data-cutoff-entry]").count(),
    320,
    "Every returned cutoff remains available",
  );
  assert.equal(await cutoff.locator("[data-cutoff-entry]").first().isVisible(), false);
  await cutoff.locator("summary").click();
  assert.equal(await cutoff.locator("[data-cutoff-entry]").last().isVisible(), true);
  await cutoff.locator("summary").click();
  assert(await shippingDeviations.evaluate((el) => el.open));
  const deviation = page.locator("[data-deviation-preview]").first();
  assert.equal(
    await deviation.getByRole("link", { name: "Recorded action 39", exact: true }).isVisible(),
    false,
  );
  await deviation.locator("summary").click();
  await deviation.getByRole("link", { name: "Recorded action 39", exact: true }).waitFor();
  await deviation.locator("summary").click();
  await page.getByRole("button", { name: "Show more deviations", exact: true }).click();
  assert.equal(await page.locator("[data-deviation-preview]").count(), 8);
  await areaSelector.selectOption("messages");
  assert.equal(
    await shippingDeviations.isVisible(),
    false,
    "shipping blockers are scoped to the selected shipping view",
  );
  await areaSelector.selectOption("shipping");
  assert(
    await shippingDeviations.evaluate((el) => el.open),
    "blocker disclosure survives chart switches",
  );
  await page.getByRole("button", { name: "Inspect all affected orders", exact: true }).click();
  assert.equal(
    await areaSelector.inputValue(),
    "shipping",
    "shipping investigation retains shipping",
  );
  await page.locator("[data-shipping-inspection]").waitFor();
  assert.equal(
    await page
      .locator("[data-shipping-inspection]")
      .evaluate((el) => el === document.activeElement),
    true,
    "Shipping inspection receives focus",
  );
  assert.equal(
    await page
      .locator(".cockpit-shipping")
      .evaluate((el) =>
        Boolean(
          el
            .closest("[data-operating-flows]")
            .nextElementSibling?.querySelector("[data-shipping-inspection]"),
        ),
      ),
    true,
    "Inspection stays beside the originating shipping panel",
  );
  assert(
    reads.some(
      (url) => url.searchParams.get("limit") === "10" && url.searchParams.get("measure") === "risk",
    ),
  );
  await page
    .locator("[data-shipping-inspection]")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  assert.equal(
    await page
      .getByRole("button", { name: "Inspect all affected orders", exact: true })
      .evaluate((el) => el === document.activeElement),
    true,
    "Closing restores the triggering control",
  );
  await showWorkspace("responsibility");
  assert.equal(
    await page
      .locator("[data-case-register]")
      .getByRole("button", { name: "Back to beginning", exact: true })
      .count(),
    0,
    "Initial page omits reset navigation",
  );
  await page.getByRole("button", { name: "Hide case list", exact: true }).click();
  assert(
    await page
      .locator(".operations-cockpit")
      .evaluate(
        (el) =>
          el.getBoundingClientRect().height -
            el.querySelector(".cockpit-flow-board").getBoundingClientRect().height <
          3000,
      ),
    "Hundreds of cutoffs and actions do not enlarge the default page",
  );
  await page.getByRole("button", { name: "Show fewer deviations", exact: true }).click();
  assert.equal(await page.locator("[data-deviation-preview]").count(), 4);
  await page.setViewportSize({ width: 390, height: 844 });
  assert(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    "Dense-evidence mobile stays bounded",
  );
  await page.screenshot({ path: "/private/tmp/reality-378-ux-dense-390.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.screenshot({ path: "/private/tmp/reality-378-ux-dense-1440.png", fullPage: true });
  denseEvidence = false;
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
  await page.getByRole("heading", { name: "Shipping by end of day" }).waitFor();
  await page.evaluate(() => window.__cockpitNavigate({ cockpitDay: "2026-10-06" }));
  await page.getByRole("button", { name: "Due on selected day: 4", exact: true }).waitFor();
  await page.getByRole("columnheader", { name: "Due on selected day", exact: true }).waitFor();
  await page.evaluate(() => window.__cockpitNavigate({ cockpitDay: "today" }));
  await page.getByRole("button", { name: "Due today: 4", exact: true }).waitFor();
  await page.getByRole("heading", { name: "Cases & takeover" }).waitFor();
  await openCaseWorkspace();
  for (const panel of ["[data-agent-access]", "[data-case-register]"]) {
    await showWorkspace(panel === "[data-agent-access]" ? "agents" : "responsibility");
    const observation = page.locator(`${panel} time[data-observed-at]`);
    await observation.waitFor();
    assert.equal(await observation.getAttribute("datetime"), at("12:30"));
    assert.match(
      await observation.textContent(),
      panel === "[data-agent-access]" ? /12:30.*GMT/ : /14:30.*GMT\+2/,
    );
  }
  await showWorkspace("responsibility");
  await page
    .locator('[data-case-id="case_d"]')
    .getByRole("button", { name: "Case details", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Take over manually / stop automation", exact: true })
    .click();
  await page.getByLabel("Takeover reason").fill("Customer appointment");
  await page.getByRole("button", { name: "Hide case list", exact: true }).click();
  await openCaseWorkspace();
  assert.equal(await page.getByLabel("Takeover reason").inputValue(), "Customer appointment");
  await showWorkspace("activity");
  await showWorkspace("agents");
  await showWorkspace("responsibility");
  assert.equal(
    await page.getByLabel("Takeover reason").inputValue(),
    "Customer appointment",
    "exact manual review survives workspace switches",
  );
  assert.equal(writes.length, 0, "Observation and review preparation never mutate business work");
  await page.getByRole("button", { name: "Confirm manual takeover", exact: true }).click();
  await page.getByText("Alex Operations", { exact: true }).waitFor();
  const controlTime = page.locator("[data-case-inspection] time[data-control-time]");
  assert.equal(await controlTime.getAttribute("datetime"), "2026-10-06T12:31:00Z");
  assert.match(await controlTime.textContent(), /06 Oct 2026/);
  await page.getByRole("button", { name: "Manually taken over", exact: true }).click();
  await page.locator('[data-case-id="case_d"]').waitFor();
  await page
    .getByRole("button", { name: "Review before returning to automation", exact: true })
    .click();
  await page.getByRole("button", { name: "Return to automation", exact: true }).click();
  await page.getByText("Automation owns this work", { exact: true }).first().waitFor();
  assert.equal(controlRevision, 3);
  assert.equal(writes.length, 2);
  await showWorkspace("agents");
  await page.getByText("Shipping <Agent>", { exact: true }).waitFor();
  await page.locator("[data-agent-access] .cockpit-agent-list button").first().click();
  await showWorkspace("responsibility");
  await showWorkspace("activity");
  await showWorkspace("agents");
  assert(
    await page
      .locator("[data-agent-access]")
      .getByRole("heading", { name: "Shipping <Agent>", exact: true })
      .isVisible(),
    "selected Agent inspection survives switches",
  );
  await page
    .locator("[data-agent-access]")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await showWorkspace("activity");
  await page.getByRole("heading", { name: "Recorded business activity" }).waitFor();
  assert.equal(await page.locator("[data-agent-access] script").count(), 0);
  const pause = page.getByRole("button", { name: "Pause following", exact: true });
  assert.equal(await pause.getAttribute("title"), "Pause following");
  assert.equal(await pause.locator("svg").count(), 1);
  assert.equal(
    await page
      .locator(".cockpit-activity .cockpit-card-heading")
      .getByRole("button", { name: "Pause following" })
      .count(),
    1,
  );
  await pause.focus();
  await page.keyboard.press("Space");
  assert.equal(
    await page.getByRole("button", { name: "Resume following" }).getAttribute("aria-pressed"),
    "true",
  );
  await showWorkspace("responsibility");
  await showWorkspace("agents");
  await showWorkspace("activity");
  assert.equal(
    await page.getByRole("button", { name: "Resume following" }).getAttribute("aria-pressed"),
    "true",
    "paused log survives workspace switches",
  );
  eventIndex = 2;
  await page.getByText("New activity available", { exact: true }).waitFor({ timeout: 12000 });
  assert.equal(await page.locator('[data-activity-event="event_1"]').count(), 1);
  await page.getByRole("button", { name: "Resume following" }).click();
  await page.locator('[data-activity-event="event_2"]').waitFor();
  await page.screenshot({ path: "/private/tmp/reality-378-cockpit-1440.png", fullPage: true });
  await areaSelector.selectOption("shipping");
  await page.getByRole("rowheader", { name: /^Venlo/ }).waitFor();
  await page.getByRole("rowheader", { name: /^Leipzig/ }).waitFor();
  await page.getByRole("button", { name: "At risk: 1", exact: true }).click();
  await page.getByRole("link", { name: "SO-104", exact: true }).waitFor();
  await page
    .getByText("The delivery commitment has an active hold.", { exact: true })
    .first()
    .waitFor();
  const target = await page.getByRole("link", { name: "SO-104", exact: true }).getAttribute("href");
  assert(target.includes("entry=order_d") && target.includes("cockpit_origin="));
  assert(reads.some((url) => url.searchParams.get("measure") === "risk"));
  const basis = page.getByRole("button", { name: "Show calculation basis", exact: true });
  assert.equal(await basis.getAttribute("title"), "Show calculation basis");
  assert.equal(await basis.locator("svg").count(), 1);
  await basis.focus();
  await page.keyboard.press("Enter");
  assert.equal(
    await page
      .getByRole("button", { name: "Hide calculation basis" })
      .getAttribute("aria-expanded"),
    "true",
  );
  await assertWorkspaceSurfaces("expanded calculation basis");
  await page.getByText("completion-slot-v1", { exact: true }).waitFor();
  await areaSelector.focus();
  const beforeShippingSwitch = await stablePosition();
  await areaSelector.selectOption("messages");
  assert.equal(
    await page.locator(".cockpit-shipping:visible").count(),
    0,
    "shipping hides in the same analysis location",
  );
  assert.equal(await mailbox.locator("svg").count(), 2, "both mail diagrams remain available");
  assert.equal(
    await page.locator("[data-shipping-investigation]").isVisible(),
    false,
    "supporting investigation follows shipping visibility",
  );
  await areaSelector.selectOption("shipping");
  assert.equal(
    await page
      .getByRole("button", { name: "Hide calculation basis" })
      .getAttribute("aria-expanded"),
    "true",
    "switching retains the opened source basis",
  );
  await page.getByRole("link", { name: "SO-104", exact: true }).waitFor();
  const afterShippingSwitch = await stablePosition();
  assert(
    Math.abs(afterShippingSwitch.top - beforeShippingSwitch.top) < 2,
    "shipping switch remains stationary",
  );
  assert(afterShippingSwitch.focused, "shipping switch retains selector focus");
  assert.equal(
    afterShippingSwitch.historyLength,
    beforeShippingSwitch.historyLength,
    "shipping switch adds no history entry",
  );
  const curve = page.locator('[data-shipping-series="plan"]');
  await curve.focus();
  await page.keyboard.press("Enter");
  await page.getByRole("link", { name: "SO-104", exact: true }).waitFor();
  assert(
    reads.some((url) => url.searchParams.get("at")),
    "Keyboard curve inspection sends an exact returned instant",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "/private/tmp/reality-378-cockpit-390-populated.png",
    fullPage: true,
  });
  assert(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    "Populated mobile has no page overflow",
  );
  await page.setViewportSize({ width: 1440, height: 1050 });
  await showWorkspace("activity");
  failure = true;
  await page
    .locator(".cockpit-status")
    .getByText("Previous observation — refresh failed", { exact: true })
    .waitFor({ timeout: 15000 });
  await page
    .getByLabel("Recorded business activity")
    .getByText("Previous observation — refresh failed", { exact: true })
    .waitFor();
  assert.equal(
    await page.locator("[data-shipping-series]").count(),
    3,
    "refresh failure retains aged values",
  );
  assert.equal(
    await page.locator("[data-flow-area] .cockpit-flow-signal.unknown").count(),
    5,
    "Stale observations cannot retain positive status",
  );
  assert.equal(
    await summary.locator('[data-risk-segment="in_plan"]').count(),
    0,
    "stale instruments cannot retain a green assessment",
  );
  assert.equal(
    await summary.locator('[data-signal="unknown"]').count(),
    5,
    "stale summary is entirely unknown",
  );
  await summary.locator('[data-status-area="stock"] [data-risk-count="critical"]').click();
  await page
    .locator(".cockpit-instrument-dialog")
    .getByText("Previous observation — refresh failed", { exact: true })
    .waitFor();
  assert.equal(
    await page.locator(".cockpit-instrument-dialog tbody tr").count(),
    2,
    "stale preview retains explicitly aged members",
  );
  await page.locator(".cockpit-instrument-dialog").press("Escape");
  await assertTrafficPalette("stale evidence remains orange");
  failure = false;
  missing = true;
  restrictedAgents = true;
  await page.getByText("Shipping plan unavailable", { exact: true }).waitFor({ timeout: 15000 });
  await page.locator("[data-shipping-actuals]").waitFor();
  assert.equal(
    await page.locator("[data-daily-shipping-series]").count(),
    2,
    "Actual evidence remains visible without a plan",
  );
  assert.match(await page.locator("[data-shipping-actuals]").textContent(), /8/);
  const showActualBasis = page.getByRole("button", { name: "Show calculation basis", exact: true });
  if (await showActualBasis.isVisible()) await showActualBasis.click();
  assert.ok(
    (
      await page
        .getByRole("link", { name: "Movement · mov_actual", exact: true })
        .getAttribute("href")
    ).includes("inspector_target_id=mov_actual"),
    "Physical activity has a direct record trace without a plan",
  );
  assert.ok(
    (
      await page
        .getByRole("link", { name: "Source record · src_carrier_actual", exact: true })
        .getAttribute("href")
    ).includes("inspector_target_id=src_carrier_actual"),
    "Actual carrier evidence remains directly inspectable",
  );
  await page.getByRole("button", { name: "Hide calculation basis", exact: true }).click();
  assert.match(
    await page.locator("[data-shipping-deviations] summary").textContent(),
    /—/,
    "Missing cohort cannot imply zero affected orders",
  );
  assert.equal(
    await mailbox.locator("dd").first().textContent(),
    "—",
    "Unknown mailbox is not a green zero",
  );
  assert.equal(
    await page.locator("[data-shipping-series]").count(),
    0,
    "missing inputs must not invent a curve",
  );
  assert.equal(writes.length, 2, "only the two explicit reviewed controls mutate work");
  assert.deepEqual(errors, []);
  await showWorkspace("agents");
  await page
    .getByText("Agent access overview is restricted to company owners", { exact: true })
    .waitFor({ timeout: 12000 });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "/private/tmp/reality-378-cockpit-390.png", fullPage: true });
  assert(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    "mobile has no page overflow",
  );
  absentFlows = true;
  missing = false;
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
  await page.locator('[data-shipping-series="plan"]').waitFor();
  assert.equal(
    await areaSelector.inputValue(),
    "shipping",
    "missing flow evidence does not remove shipping",
  );
  await areaSelector.selectOption("messages");
  await page.getByText("Operating flow evidence is unavailable", { exact: true }).waitFor();
  assert.equal(await summary.locator('[data-signal="unknown"]').count(), 5);
  assert.equal(
    await summary.locator("[data-status-area] a").count(),
    0,
    "missing cards have no dead navigation",
  );
  assert.deepEqual(await summary.locator("[data-status-metric]").allTextContents(), [
    "—",
    "—",
    "—",
    "—",
    "—",
  ]);
  absentFlows = false;
  missing = false;
  restrictedAgents = false;
  summaryVariants = true;
  for (const language of ["en", "de", "nl", "es"]) {
    for (const theme of ["light", "dark"]) {
      await page.goto(
        (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
          "/scripts/fixtures/operations-cockpit-harness.html?language=" +
          language +
          "&theme=" +
          theme,
      );
      await page.locator('[data-shipping-series="plan"]').waitFor();
      assert.equal(await page.locator("[data-shipping-series]").count(), 3);
      assert(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
        `${language}/${theme} mobile is bounded`,
      );
      await page.screenshot({
        path: `/private/tmp/reality-378-cockpit-${language}-${theme}-390.png`,
        fullPage: true,
      });
      for (const width of [320, 390, 1440, 1920]) {
        await page.setViewportSize({ width, height: 1050 });
        await page.locator(".cockpit-analysis-selector select").selectOption("shipping");
        await assertFlowAlignment(`${language}/${theme}/${width}/shipping`);
        await page.locator(".cockpit-analysis-selector select").selectOption("messages");
        await assertFlowAlignment(`${language}/${theme}/${width}/messages`);
        const riskTrigger = page.locator('[data-status-area="stock"] [data-risk-count="critical"]');
        await riskTrigger.click();
        const preview = page.locator(".cockpit-instrument-dialog");
        await preview.waitFor();
        assert.equal(
          await preview.locator("tbody tr").count(),
          2,
          `${language}/${theme}/${width}: exact stock preview`,
        );
        assert(
          await preview.evaluate((el) => {
            const r = el.getBoundingClientRect();
            return r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight;
          }),
          `${language}/${theme}/${width}: dialog stays within viewport`,
        );
        await preview.press("Escape");
        for (const view of ["responsibility", "activity", "agents"]) {
          await showWorkspace(view);
          await assertCaseEntry(`${language}/${theme}/${width}/${view}`);
        }
        assert(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          `${language}/${theme}/${width}: viewport remains bounded; ${JSON.stringify(
            await page.evaluate(() =>
              [...document.querySelectorAll("body *")]
                .filter((el) => el.getBoundingClientRect().right > innerWidth + 0.1)
                .map((el) => ({
                  tag: el.tagName,
                  cls: el.className,
                  right: el.getBoundingClientRect().right,
                  text: el.textContent?.slice(0, 60),
                }))
                .slice(0, 12),
            ),
          )}`,
        );
      }
      await page.setViewportSize({ width: 390, height: 844 });

      if (language === "de" && theme === "light") {
        await page.setViewportSize({ width: 1440, height: 1050 });
        const layout = await page.locator("[data-flow-area]").evaluateAll((elements) =>
          elements
            .filter((element) => !element.hidden)
            .map((element) => {
              const rect = element.getBoundingClientRect();
              return { top: rect.top, width: rect.width };
            }),
        );
        assert.equal(layout.length, 1, "desktop retains one focused analysis");
        await page.locator(".cockpit-analysis-selector select").selectOption("messages");
        assert.equal(await page.locator('[data-flow-area="messages"] svg').count(), 2);

        await page.screenshot({
          path: "/private/tmp/reality-378-cockpit-de-light-1440.png",
          fullPage: true,
        });
        await page.setViewportSize({ width: 390, height: 844 });
      }
    }
  }
  nextDayCollection = true;
  largeCaseCounts = true;
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html?language=en&locale=de-DE&timezone=Asia/Tokyo",
  );
  await page.locator('[data-shipping-series="plan"]').waitFor();
  await page.getByText("With automation: 12.345", { exact: true }).waitFor();
  await page.getByText("Manually taken over: 3.456", { exact: true }).waitFor();
  await openCaseWorkspace();
  assert.match(
    await page.locator(".cockpit-table-scroll").first().textContent(),
    /07\. Okt\. 2026.*03:00.*GMT\+2/s,
    "A next-day collection retains its date and site offset in the chosen display locale",
  );
  assert.equal(
    await page.locator(".cockpit-event-list time").first().textContent(),
    "21:29:00",
    "Activity respects the independently chosen display timezone and locale",
  );
  assert.match(
    await page.locator("[data-agent-access] time[data-observed-at]").textContent(),
    /21:30.*GMT\+9/,
  );
  assert.match(await page.locator(".cockpit-status").textContent(), /14:30/);
  await page
    .locator("[data-case-register]")
    .getByRole("button", { name: "Next cases", exact: true })
    .click();
  await page
    .locator("[data-case-register]")
    .getByRole("button", { name: "Back to beginning", exact: true })
    .waitFor();
  assert(
    reads.some(
      (url) =>
        url.pathname.endsWith("/operational-cases/register") &&
        url.searchParams.get("after") === "remaining-cases",
    ),
  );
  await page
    .locator("[data-case-register]")
    .getByRole("button", { name: "Back to beginning", exact: true })
    .click();
  reconcilingCases = true;
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
  await page.getByText("Operational case upgrade is still reconciling existing work.").waitFor();
  await page.getByText("With automation: 0", { exact: true }).waitFor();
  await page.getByText("Manually taken over: 0", { exact: true }).waitFor();
  staleAccess = staleCases = true;
  for (const panel of ["[data-agent-access]", "[data-case-register]"]) {
    await showWorkspace(panel === "[data-agent-access]" ? "agents" : "responsibility");
    await page
      .locator(panel)
      .getByText("Previous observation — refresh failed", { exact: true })
      .waitFor();
    assert.equal(
      await page.locator(`${panel} time[data-observed-at]`).getAttribute("datetime"),
      at("12:30"),
      "Each failed panel retains its own successful observation time",
    );
  }
  assert.deepEqual(errors, []);
  console.log(
    "Operations cockpit shipping, source basis, contextual links, stale and missing-input proof passed",
  );
} catch (error) {
  console.error("Cockpit browser failure diagnostics:", {
    errors,
    lastReads: reads.slice(-5).map((url) => url.pathname),
  });
  await page.screenshot({
    path: "/private/tmp/reality-status-browser-failure.png",
    fullPage: true,
  });
  console.error((await page.locator("body").innerText()).slice(0, 3000));
  throw error;
} finally {
  await browser.close();
}
