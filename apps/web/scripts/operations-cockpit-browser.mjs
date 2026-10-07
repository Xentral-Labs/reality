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
async function openCaseWorkspace() {
  const toggle = page.getByRole("button", { name: "Select a case", exact: true });
  if (await toggle.count()) await toggle.click();
}
async function assertCaseEntry(label) {
  const layout = await page.locator("[data-case-register]").evaluate((element) => ({
    top: element.getBoundingClientRect().top,
    bottom: element.getBoundingClientRect().bottom,
    width: element.getBoundingClientRect().width,
    hidden: element.querySelector("[data-case-workspace]")?.hidden,
    statusBottom: document.querySelector("[data-operating-status]").getBoundingClientRect().bottom,
    shippingTop: document.querySelector(".cockpit-shipping").getBoundingClientRect().top,
  }));
  assert(layout.top > layout.statusBottom, `${label}: takeover follows status`);
  assert(layout.bottom < layout.shippingTop, `${label}: takeover precedes shipping`);
  assert(layout.width <= 1120, `${label}: responsibility entry stays bounded`);
  if (layout.hidden && layout.width >= 900)
    assert(layout.bottom - layout.top <= 300, `${label}: routine entry stays compact`);
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
  const metricSpacing = await page
    .locator("[data-flow-area]:not([hidden]) dl")
    .evaluate((element) => getComputedStyle(element).rowGap);
  assert.equal(
    metricSpacing,
    "16px",
    `${label}: selected analysis keeps explicit metric-row spacing`,
  );
  const rhythm = await page.locator("[data-operating-flows]").evaluate((element) => ({
    margin: getComputedStyle(element).marginTop,
    outerGap:
      element.getBoundingClientRect().top -
      element.previousElementSibling.getBoundingClientRect().bottom,
    headingSize: getComputedStyle(element.querySelector("h2")).fontSize,
    sharedSize: getComputedStyle(document.querySelector(".cockpit-shipping h2")).fontSize,
    contentGap:
      element.querySelector(".cockpit-analysis-selector").getBoundingClientRect().top -
      element.querySelector("header").getBoundingClientRect().bottom,
  }));
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
    `${label}: heading is separated from cards`,
  );
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
      deviation_total: denseEvidence ? 321 : 0,
      deviations_has_more: denseEvidence,
      shipping: missing
        ? {
            ...shipping,
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
  await assertCaseEntry("initial desktop");
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
    assert.equal(await tile.getByRole("link").getAttribute("href"), `#cockpit-flow-${area}`);
  }
  await summary.locator('[data-status-area="orders"] a').focus();
  await summary.locator('[data-status-area="orders"] a').press("Enter");
  assert.equal(await page.evaluate(() => location.hash), "#cockpit-flow-orders");
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
  await assertFlowAlignment("initial desktop");
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
  await page.locator('[data-status-area="messages"] a').click();
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
  await page.getByText("Business document recorded", { exact: true }).waitFor();
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
  await page.getByRole("button", { name: "Inspect all affected orders", exact: true }).click();
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
      .evaluate((el) => el.nextElementSibling.hasAttribute("data-shipping-inspection")),
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
    const observation = page.locator(`${panel} time[data-observed-at]`);
    await observation.waitFor();
    assert.equal(await observation.getAttribute("datetime"), at("12:30"));
    assert.match(
      await observation.textContent(),
      panel === "[data-agent-access]" ? /12:30.*GMT/ : /14:30.*GMT\+2/,
    );
  }
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
  await page.getByRole("heading", { name: "Recorded business activity" }).waitFor();
  await page.getByText("Shipping <Agent>", { exact: true }).waitFor();
  assert.equal(await page.locator("[data-agent-access] script").count(), 0);
  await page.getByRole("button", { name: "Pause following" }).click();
  eventIndex = 2;
  await page.getByText("New activity available", { exact: true }).waitFor({ timeout: 12000 });
  assert.equal(await page.locator('[data-activity-event="event_1"]').count(), 1);
  await page.getByRole("button", { name: "Resume following" }).click();
  await page.locator('[data-activity-event="event_2"]').waitFor();
  await page.screenshot({ path: "/private/tmp/reality-378-cockpit-1440.png", fullPage: true });
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
  await page.getByRole("button", { name: "Show calculation basis" }).click();
  await assertWorkspaceSurfaces("expanded calculation basis");
  await page.getByText("completion-slot-v1", { exact: true }).waitFor();
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
    await summary.locator('[data-signal="unknown"]').count(),
    5,
    "stale summary is entirely unknown",
  );
  await assertTrafficPalette("stale evidence remains orange");
  failure = false;
  missing = true;
  restrictedAgents = true;
  await page.getByText("Shipping plan unavailable", { exact: true }).waitFor({ timeout: 15000 });
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
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177") +
      "/scripts/fixtures/operations-cockpit-harness.html",
  );
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
        await assertFlowAlignment(`${language}/${theme}/${width}`);
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
        await page.locator('[data-status-area="messages"] a').click();
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
