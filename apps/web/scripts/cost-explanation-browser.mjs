import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

if (!process.env.PLAYWRIGHT_MODULE || !process.env.PLAYWRIGHT_EXECUTABLE)
  throw new Error("Set PLAYWRIGHT_MODULE and PLAYWRIGHT_EXECUTABLE.");
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const visible = process.env.PLAYWRIGHT_VISIBLE === "1";
const browser = await chromium.launch({
  headless: !visible,
  slowMo: visible ? 650 : 0,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const requests = [],
  errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenant = "cost_ui_company",
  other = "cost_ui_other",
  item = "cost_ui_item";
let costState = "ready";
// Spec 279: which resolution guidance the cost query returns in this step.
let scenario = "none";
let role = "member";
let language = "en";
const guidanceCatalog = JSON.parse(
  await readFile(
    new URL("../../../packages/reality-core/config/resolution_guidance.json", import.meta.url),
    "utf8",
  ),
);
const step = (code, state, extra = {}) => ({
  code,
  state,
  role: guidanceCatalog.steps[code].role,
  path: guidanceCatalog.steps[code].path,
  targets: [],
  target_count: 0,
  ...extra,
});
const scenarios = {
  none: { reason_code: "cost_complete", steps: [], writable: true },
  stale: {
    reason_code: "inventory_review_stale",
    steps: [
      step("receipt_cost_evidence", "open", { targets: ["mov_late"], target_count: 1 }),
      step("inventory_review_renew", "blocked"),
      step("owner_confirmation", "blocked"),
    ],
    writable: true,
  },
  receipts: {
    reason_code: "inventory_scope_not_reviewed",
    steps: [
      step("receipt_cost_evidence", "open", { targets: ["mov_a", "mov_b"], target_count: 2 }),
      step("inventory_review", "blocked"),
      step("owner_confirmation", "blocked"),
    ],
    writable: true,
  },
  owner: {
    reason_code: "inventory_scope_not_reviewed",
    steps: [
      step("receipt_cost_evidence", "done"),
      step("inventory_review", "done"),
      step("owner_confirmation", "open", { proposal_id: "act_cost_fixture" }),
    ],
    writable: true,
  },
};
scenarios.readonly = { ...scenarios.receipts, writable: false };
const pager = { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false };
const reply = (route, body, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

await page.route("**/api/**", async (route) => {
  const request = route.request(),
    url = new URL(request.url()),
    path = url.pathname;
  requests.push({ path, method: request.method(), query: url.search });
  if (path === "/api/auth/me")
    return reply(route, {
      id: "cost_operator",
      email: "operator@example.test",
      display_name: "Operator",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
      language,
    });
  if (path === "/api/v1/bootstrap")
    return reply(route, {
      tenants: [
        { id: tenant, name: "Northstar Commerce", role },
        { id: other, name: "Other company" },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference"))
    return reply(route, {
      command_count: 0,
      event_count: 0,
      projection_count: 0,
      fact_predicate_count: 0,
      projections: [],
      workspaces: [],
      resolution_guidance: guidanceCatalog,
    });
  if (path.endsWith("/copilot"))
    return reply(route, {
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path.endsWith("/warehouse/stock"))
    return reply(route, {
      items: [
        {
          id: item,
          name: "Desk lamp",
          sku: "LAMP",
          unit: "pcs",
          physical: "40",
          reserved: "0",
          available: "40",
          incoming: "0",
          projected: "40",
        },
      ],
      page: pager,
      scope: { view: "stock", item_id: item, item: "Desk lamp" },
      observed_at: "2026-09-20T12:00:00Z",
    });
  if (path.endsWith("/cost-query")) {
    assert.equal(url.searchParams.get("kind"), "inventory");
    assert.equal(url.searchParams.get("scope_id"), item);
    const initialized = costState !== "uninitialized";
    const stage = costState === "ready" ? "complete" : costState;
    const basis = {
      item_id: item,
      review_id: initialized ? "inventory_review_fixture" : null,
      currency: "EUR",
      base_unit: "pcs",
      acquisition_value: costState === "ready" ? "420.0000" : null,
      basis_acquisition_value: initialized ? "420.0000" : null,
      carrying_value: null,
      carrying_value_state: "assessment_missing",
      missing_basis: costState === "ready" ? [] : [scenarios[scenario].reason_code],
    };
    return reply(route, {
      requested: { kind: "inventory", scope_id: item, review_id: null },
      resolved: initialized
        ? {
            currency: "EUR",
            base_unit: "pcs",
            effective_at: "2026-09-20T10:00:00Z",
            knowledge_at: "2026-09-20T12:00:00Z",
            review_id: "inventory_review_fixture",
          }
        : null,
      context_id: initialized ? "cost_context_fixture" : null,
      freshness: {
        state: costState,
        processed_event_sequence: initialized ? 7 : null,
        target_event_sequence: costState === "ready" ? 7 : initialized ? 8 : null,
      },
      result: costState === "ready" ? basis : null,
      basis_result: basis,
      guidance: {
        stage,
        scope: { kind: "inventory", id: item },
        review_state: stage,
        missing_basis: basis.missing_basis,
        reason:
          stage === "complete"
            ? "The retained cost basis is current for this bounded scope."
            : stage === "stale"
              ? "Newer relevant business evidence exists after the retained review."
              : "No retained owner-reviewed cost basis exists for this scope.",
        next_action:
          stage === "complete"
            ? null
            : {
                tool: "cost_change_propose",
                operation: "inventory_review",
                required_principal: "authenticated_active_owner",
              },
        explanation_links: initialized
          ? [{ kind: "cost_inventory_review", id: "inventory_review_fixture" }]
          : [],
        value_reasons: { carrying_value: "assessment_missing" },
        ...scenarios[scenario],
      },
      persistence: { business_writes: false, projection_writes: false },
    });
  }
  if (path.includes("/inspector/"))
    return reply(route, {
      kind: "item",
      id: item,
      eyebrow: "Master data",
      title: "Desk lamp",
      subtitle: "LAMP",
      status: "Active",
      meaning: "Inventory item",
      business_reference: null,
      guidance: null,
      technical_rows: [],
      metrics: [],
      trail: [],
      sections: [],
    });
  return reply(route, { detail: "Fixture endpoint unavailable" }, 404);
});

const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const out = "/private/tmp/reality-234-cost-browser";
await mkdir(out, { recursive: true });
const url = (company = tenant) =>
  `${base}/app/warehouse?tenant=${company}&warehouse_view=stock&item=${item}&entry=${item}`;
try {
  await page.goto(url());
  const cost = page.getByRole("region", { name: "Cost explanation", exact: true });
  await cost.getByText("€420.00", { exact: true }).waitFor();
  await cost.getByText("Exact retained value: 420.0000", { exact: true }).waitFor();
  // FR-010: no unit cost field, and the missing carrying value names its reason.
  assert.equal(await cost.getByText("Unit cost", { exact: true }).count(), 0);
  await cost.getByText("No carrying value assessment exists", { exact: true }).waitFor();
  assert.equal(await cost.locator("[data-resolution-guidance]").count(), 0);
  const href = await cost.getByRole("link", { name: "Inspect cost basis" }).getAttribute("href");
  assert.ok(href?.includes("inspector_target_kind=cost_inventory_review"));

  costState = "stale";
  scenario = "stale";
  await page.reload();
  await cost.getByText("Retained basis — not current", { exact: false }).waitFor();
  await cost.getByText("The item's cost review is out of date", { exact: true }).waitFor();
  await cost.getByText("€420.00", { exact: true }).waitFor();
  assert.equal(
    await cost
      .locator('[data-guidance-step="inventory_review_renew"]')
      .getAttribute("data-guidance-state"),
    "blocked",
  );

  // FR-005 in German: plain sentences, no machine codes, no repeated reason.
  costState = "uninitialized";
  scenario = "receipts";
  language = "de";
  await page.evaluate(() => {
    document.cookie = "reality_language=de; path=/";
    localStorage.setItem("reality.language", "de");
  });
  await page.reload();
  const reason = "Für diesen Artikel hat noch niemand die Anschaffungskosten bestätigt";
  await page.getByText(reason, { exact: true }).waitFor();
  assert.equal(await page.getByText(reason, { exact: true }).count(), 1);
  const panel = page.locator("[data-resolution-guidance]");
  const shown = await panel.evaluate(
    (node) => node.closest("section")?.parentElement?.innerText || "",
  );
  for (const code of [
    "uninitialized",
    "cost_change_propose",
    "inventory_scope_not_reviewed",
    "inventory_review",
    "receipt_cost_evidence",
    "authenticated_active_owner",
  ])
    assert.ok(!shown.includes(code), `raw code visible: ${code}`);
  await page.getByText("Kosten jedes Wareneingangs bestätigen", { exact: false }).waitFor();
  assert.equal(await page.getByRole("link", { name: "Kostengrundlage prüfen" }).count(), 0);

  // FR-008: the chat step fills the composer and sends nothing.
  const writesBefore = requests.filter((row) => row.method !== "GET").length;
  await panel.getByRole("button", { name: "Mit Reality vorbereiten" }).click();
  const composer = page.locator("[data-global-chat] textarea").first();
  await composer.waitFor();
  const draft = await composer.inputValue();
  assert.match(draft, /Desk lamp \(cost_ui_item\)/);
  assert.match(draft, /Bereite die Kostenprüfung der Wareneingänge/);
  assert.ok(
    requests
      .slice(writesBefore)
      .every((row) => row.method === "GET" || row.path.endsWith("/search/resolve")),
    "the chat handoff must not send",
  );

  // FR-007: the alternative opens the existing supplier invoice form.
  await panel.getByRole("button", { name: "Zuerst die Lieferantenrechnung erfassen" }).click();
  await page.locator("dialog[open]").first().waitFor();
  await page.keyboard.press("Escape");

  // Re-read after any write instead of assuming success locally.
  const readsBefore = requests.filter((row) => row.path.endsWith("/cost-query")).length;
  const reread = page.waitForResponse((response) => response.url().includes("/cost-query"));
  await page.evaluate(() => window.dispatchEvent(new Event("reality:records-changed")));
  await reread;
  assert.ok(requests.filter((row) => row.path.endsWith("/cost-query")).length > readsBefore);

  // FR-009: a member sees who must act; an owner gets the decision review.
  scenario = "owner";
  await page.reload();
  await page.getByText("Ein Inhaber muss das bestätigen.", { exact: true }).waitFor();
  assert.equal(await page.getByRole("button", { name: "In Entscheidungen prüfen" }).count(), 0);
  role = "owner";
  await page.reload();
  await page.getByRole("button", { name: "In Entscheidungen prüfen" }).click();
  await page.waitForURL(/\/app\/decisions/);
  assert.match(page.url(), /proposal=act_cost_fixture/);

  // A read-only company shows no write path.
  scenario = "readonly";
  await page.goto(url());
  await page
    .getByText("In diesem Unternehmen lassen sich keine Kostenentscheidungen bestätigen.", {
      exact: true,
    })
    .waitFor();
  assert.equal(await page.getByRole("button", { name: "Mit Reality vorbereiten" }).count(), 0);
  await page.screenshot({ path: `${out}/inventory-cost-guidance-de.png`, fullPage: true });

  costState = "ready";
  scenario = "none";
  language = "en";
  role = "member";
  await page.evaluate(() => {
    document.cookie = "reality_language=en; path=/";
    localStorage.setItem("reality.language", "en");
  });
  await page.goto(url(other));
  await cost.getByText("€420.00", { exact: true }).waitFor();
  assert.ok(requests.some((row) => row.path === `/api/tenants/${other}/cost-query`));
  assert.ok(
    requests
      .filter((row) => row.method !== "GET")
      .every((row) => row.method === "POST" && row.path.endsWith("/search/resolve")),
  );
  assert.deepEqual(errors, []);
  await page.screenshot({ path: `${out}/inventory-cost-explanation.png`, fullPage: true });
  console.log(
    "PASS: cost explanation with resolution guidance (German wording, chat handoff without sending, form step, owner/member, read-only, re-read), Inspector trace and tenant scope.",
  );
} catch (error) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  console.log(errors, requests.slice(-30));
  throw error;
} finally {
  await browser.close();
}
