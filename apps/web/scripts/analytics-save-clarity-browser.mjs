import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { reference as discoveryReference } from "./action-discovery-fixture.mjs";

/** The moment a question becomes a report of your own.
 *
 * Every assertion here is something a reader could not previously see: that
 * there is a save control at all without opening a menu, what the analysis is
 * called before anybody types, whether it is saved yet, and that confirming a
 * proposal in chat leads to the report it wrote rather than to a copy of it.
 */

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";

const order = {
  key: "order",
  label: "Customer order",
  grain: "One customer order",
  backed_by: "documents",
  corrections: "revise",
  coverage: [],
  category: "Sales",
  evidence: null,
  properties: [
    { key: "id", label: "ID", kind: "text", identity: true },
    { key: "currency", label: "Currency", kind: "text" },
  ],
  measures: [
    {
      key: "stated_order_amount",
      label: "Order value",
      unit: "currency",
      additive_over: [],
      never_across: [],
      note: null,
    },
  ],
  edges: [],
  edges_in: [],
};
const catalog = { nodes: [order], limits: { result_rows: 500 } };
const templateQuestion = {
  from: "order",
  as: "o",
  measures: ["stated_order_amount"],
  group_by: [{ field: "o.currency" }],
  limit: 200,
};
const templates = {
  templates: [
    {
      key: "revenue_by_currency",
      label: "Revenue by currency",
      about: "What each currency contributed.",
      question: templateQuestion,
      period: null,
    },
    {
      key: "revenue_this_month",
      label: "Revenue this month",
      about: "The current month only.",
      question: templateQuestion,
      period: { field: "o.ordered_at", window: "this_month" },
    },
  ],
};

/** One saved report store, so what the library lists is what saving wrote. */
function server() {
  const reports = new Map();
  const proposals = new Map();
  let writes = 0;
  return { reports, proposals, writes: () => writes, bump: () => writes++ };
}

async function open(language = "en") {
  const state = server();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    locale: language === "de" ? "de-DE" : "en-GB",
  });
  const page = await context.newPage();
  const errors = [];
  const unmatched = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const reply = (body, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/auth/me")
      return reply({
        id: "operator",
        email: "operator@example.test",
        status: "active",
        language,
        locale: language === "de" ? "de-DE" : "en-GB",
        timezone: "UTC",
      });
    if (path === "/api/v1/bootstrap")
      return reply({
        tenants: [{ id: "company", name: "Northstar" }],
        default_tenant_id: "company",
      });
    if (path.endsWith("/copilot"))
      return reply({
        sessions: [],
        active_session_id: null,
        messages: [],
        proposals: [...state.proposals.values()].map((proposal) => ({
          id: proposal.proposal_id,
          tool: "graph.reports.change",
          review_kind: "common",
          review_label: "Report",
        })),
        suggestions: [],
        has_archived: false,
      });
    if (path.endsWith("/analytics/graph/catalog")) return reply(catalog);
    if (path.endsWith("/analytics/graph/templates")) return reply(templates);
    if (path.endsWith("/analytics/graph/ask"))
      return reply({
        question: request.postDataJSON().question ?? templateQuestion,
        rows: [{ "o.currency": "EUR", stated_order_amount: "1000" }],
        path: [],
        model_version: "1",
        statements: 1,
        sql: "SELECT 1",
        editor: { path: "MATCH (o:order) RETURN o.currency", parameters: {} },
      });
    if (path.endsWith("/analytics/graph/reports/changes")) {
      const body = request.postDataJSON();
      state.bump();
      if (body.operation === "create") {
        const stored = {
          id: `anr-${state.reports.size + 1}`,
          name: body.name,
          kind: "graph",
          definition: body.question,
          model_version: "1",
          revision: 1,
          created_at: "2026-09-23T08:00:00Z",
          updated_at: "2026-09-23T08:00:00Z",
          deleted: false,
        };
        state.reports.set(stored.id, stored);
        return reply(stored);
      }
      const stored = state.reports.get(body.report_id);
      Object.assign(stored, {
        revision: stored.revision + 1,
        ...(body.name ? { name: body.name } : {}),
        ...(body.question ? { definition: body.question } : {}),
        updated_at: "2026-09-23T09:00:00Z",
      });
      return reply(stored);
    }
    const single = path.match(/\/analytics\/graph\/reports\/(anr-[^/]+)$/);
    if (single) return reply(state.reports.get(single[1]));
    if (path.endsWith("/analytics/graph/reports"))
      return reply({
        records: [...state.reports.values()],
        has_more: false,
        next_cursor: null,
      });
    const proposal = path.match(/\/analytics\/reports\/proposals\/([^/]+)$/);
    if (proposal) return reply(state.proposals.get(proposal[1]));
    if (path.includes("/change-proposals/") && path.endsWith("/approve")) {
      const id = path.split("/change-proposals/")[1].replace("/approve", "");
      const pending = state.proposals.get(id);
      // Confirming is what writes the report, and from here on the proposal can
      // name it. That is the whole point of the change under test.
      const stored = {
        id: "anr-from-chat",
        name: pending.name,
        kind: "graph",
        definition: pending.definition,
        model_version: "1",
        revision: 1,
        created_at: "2026-09-23T08:00:00Z",
        updated_at: "2026-09-23T08:00:00Z",
        deleted: false,
      };
      state.reports.set(stored.id, stored);
      Object.assign(pending, { status: "executed", report_id: stored.id });
      return reply({ id, status: "executed" });
    }
    if (path.endsWith("/application-reference")) return reply(discoveryReference);
    if (path.endsWith("/change-proposals"))
      return reply({
        items: [],
        page: { number: 1, size: 50, total: 0, pages: 1, has_next: false, has_previous: false },
      });
    unmatched.push(path);
    return reply({ items: [] });
  });
  return { page, context, state, errors, unmatched };
}

const analytics = (view = "reports", extra = "") =>
  `${base}/app/analytics?tenant=company&analytics_view=${view}${extra}`;

// --- US1, US2, US3, US4: a template becomes a report -----------------------------

{
  const { page, context, state, errors, unmatched } = await open();
  try {
    await page.goto(analytics("reports"));
    // US1.3: the way in is on the page, not folded into "More actions".
    await page
      .locator('[data-page-action="inline"]', { hasText: "New analysis" })
      .first()
      .waitFor();

    await page.goto(analytics("graph"));
    await page.getByRole("button", { name: "Use a template", exact: true }).click();
    await page.getByRole("button", { name: "Use template", exact: true }).first().click();

    // US3.1: the adopted template says what it is and that it is not saved yet.
    await page.getByRole("heading", { name: "Revenue by currency" }).waitFor();
    await page.getByText("Draft · not saved yet", { exact: true }).waitFor();

    // US1.1: a visible save control, with no menu opened anywhere.
    const save = page.getByRole("button", { name: "Save analysis", exact: true });
    await save.waitFor();
    assert.equal(
      await page.locator(".register-actions[open]").count(),
      0,
      "nothing had to be unfolded to find it",
    );
    await save.click();

    // US2.1: the template's own label is the suggestion, and it is selected.
    const field = page.getByLabel("Report name");
    await field.waitFor();
    assert.equal(await field.inputValue(), "Revenue by currency");
    assert.equal(
      await field.evaluate(
        (input) => input.selectionEnd - input.selectionStart === input.value.length,
      ),
      true,
      "one keystroke has to replace the whole suggestion",
    );

    await page.getByRole("button", { name: "Save", exact: true }).click();

    // US4.1: it is the saved report now, it says so, and the library is reachable.
    const identity = page.locator(".analysis-identity");
    await identity.getByText("Saved", { exact: true }).waitFor();
    // Scoped: "My reports" is also the name of the tab this links to.
    await identity.getByRole("button", { name: "My reports", exact: true }).waitFor();
    await page.waitForURL(/analytics_report=anr-1/);

    // A second press of the remaining save control must not write a second report:
    // before this change the builder never learned it had been saved.
    assert.equal(state.reports.size, 1);
    const changes = page.getByRole("button", { name: "Save changes", exact: true });
    await changes.waitFor();
    assert.equal(await changes.isDisabled(), true, "nothing changed, so there is nothing to save");

    // US4.2: reloading reopens the same saved report rather than an empty builder.
    await page.reload();
    await page.getByRole("heading", { name: "Revenue by currency" }).waitFor();
    await page.getByText("Saved report", { exact: true }).waitFor();
    assert.equal(state.reports.size, 1);

    assert.deepEqual(errors, []);
    assert.deepEqual(unmatched, []);
  } finally {
    await context.close();
  }
}

// --- US2.2: an analysis built by hand names itself --------------------------------

{
  const { page, context, errors } = await open();
  try {
    await page.goto(analytics("graph"));
    await page.getByRole("button", { name: "Build it yourself", exact: true }).click();
    await page.getByText("Draft · not saved yet", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Save analysis", exact: true }).click();
    const field = page.getByLabel("Report name");
    const suggestion = await field.inputValue();
    assert.ok(suggestion.length > 0, "the field must never open blank");
    assert.ok(
      suggestion.startsWith("Customer order"),
      `expected the records being read, got ${suggestion}`,
    );
    assert.deepEqual(errors, []);
  } finally {
    await context.close();
  }
}

// --- US5: a confirmed proposal opens the report it wrote --------------------------

{
  const { page, context, state, errors } = await open();
  state.proposals.set("prop-1", {
    proposal_id: "prop-1",
    status: "proposed",
    operation: "create",
    name: "Revenue from chat",
    definition: templateQuestion,
    expected_revision: null,
    report_id: null,
    kind: "graph",
  });
  try {
    await page.goto(`${base}/app/chat?tenant=company`);
    // The same card also renders in the chat dock, so every look is scoped to
    // the page itself.
    const chat = page.locator("#main-content");
    // US5.3: while it waits, what it offers to open is stated to be unsaved.
    await chat.getByRole("button", { name: "Open in analysis", exact: true }).waitFor();
    await chat
      .getByText("An unsaved preview. Nothing is saved until you confirm here.", { exact: true })
      .waitFor();

    await chat.getByRole("button", { name: "Confirm", exact: true }).click();

    // US5.1 and US5.2: it says what happened and opens the saved report.
    await chat.getByText("Saved to your reports.", { exact: true }).waitFor();
    assert.equal(
      await chat.getByRole("button", { name: "Open in analysis", exact: true }).count(),
      0,
      "a copy of a report that now exists is never the thing to offer",
    );
    await chat.getByRole("button", { name: "Open the saved report", exact: true }).click();
    await page.waitForURL(/analytics_report=anr-from-chat/);
    await page.getByRole("heading", { name: "Revenue from chat" }).waitFor();
    await page.getByText("Saved report", { exact: true }).waitFor();
    assert.equal(state.reports.size, 1, "following the card must not write a second report");
    assert.deepEqual(errors, []);
  } finally {
    await context.close();
  }
}

// --- US6: the German words say different things -----------------------------------

{
  const { page, context, errors } = await open("de");
  try {
    await page.goto(analytics("graph"));
    const toggle = page.getByRole("button", { name: "Vorlage verwenden", exact: true });
    await toggle.click();
    const adopt = page.getByRole("button", { name: "Diese Vorlage übernehmen", exact: true });
    await adopt.first().waitFor();
    assert.equal(
      await toggle.count(),
      1,
      "the toggle and the row action must not be the same three words",
    );
    // US6.2: the card no longer advertises a window it does not keep.
    await page.getByText("Beim Übernehmen wird er auf feste Daten gesetzt.").first().waitFor();
    await adopt.first().click();
    await page.getByText("Entwurf · noch nicht gespeichert", { exact: true }).waitFor();
    assert.deepEqual(errors, []);
  } finally {
    await context.close();
  }
}

await browser.close();
console.log("analytics save clarity: ok");
