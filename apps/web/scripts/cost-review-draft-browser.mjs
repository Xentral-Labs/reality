// Spec 282: the "Prepare the item's cost review" step opens the drafted review. The
// dialog shows the draft in German without identifiers, preselects FIFO, re-drafts when
// the records changed, and proposes; the panel then shows the owner's step.
import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177",
  out = "/private/tmp/reality-282-draft-browser";
const errors = [],
  posts = [],
  draftReads = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenant = "draft_company",
  item = "draft_item";
const catalog = JSON.parse(
  await readFile(
    new URL("../../../packages/reality-core/config/resolution_guidance.json", import.meta.url),
    "utf8",
  ),
);
let proposed = false,
  sequence = 41,
  refuseOnce = true;
const step = (code, state, extra = {}) => ({
  code,
  state,
  role: catalog.steps[code].role,
  path: catalog.steps[code].path,
  targets: [],
  target_count: 0,
  ...extra,
});
const reply = (route, body, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

await page.route("**/api/**", async (route) => {
  const request = route.request(),
    url = new URL(request.url()),
    path = url.pathname;
  if (path === "/api/auth/me")
    return reply(route, {
      id: "clerk",
      email: "clerk@example.test",
      display_name: "Clerk",
      status: "active",
      language: "de",
      locale: "de-DE",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply(route, {
      tenants: [{ id: tenant, name: "Nordlicht Handel", role: "member" }],
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
      resolution_guidance: catalog,
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
          name: "Schreibtischlampe",
          sku: "LAMP",
          unit: "pcs",
          physical: "40",
          reserved: "0",
          available: "40",
          incoming: "0",
          projected: "40",
        },
      ],
      page: { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false },
      scope: { view: "stock", item_id: item, item: "Schreibtischlampe" },
      observed_at: "2026-09-26T12:00:00Z",
    });
  if (path.endsWith("/cost-query"))
    return reply(route, {
      requested: { kind: "inventory", scope_id: item, review_id: null },
      resolved: null,
      context_id: null,
      freshness: {
        state: "uninitialized",
        processed_event_sequence: null,
        target_event_sequence: null,
      },
      result: null,
      basis_result: {
        item_id: item,
        review_id: null,
        missing_basis: ["inventory_scope_not_reviewed"],
      },
      guidance: {
        stage: "uninitialized",
        scope: { kind: "inventory", id: item },
        review_state: "unreviewed",
        missing_basis: ["inventory_scope_not_reviewed"],
        reason: "",
        next_action: null,
        explanation_links: [],
        reason_code: "inventory_scope_not_reviewed",
        writable: true,
        value_reasons: {},
        steps: proposed
          ? [
              step("inventory_review", "done"),
              step("owner_confirmation", "open", { proposal_id: "act_draft" }),
            ]
          : [step("inventory_review", "open"), step("owner_confirmation", "blocked")],
      },
      persistence: { business_writes: false, projection_writes: false },
    });
  if (path.endsWith("/cost-review-draft")) {
    draftReads.push(Object.fromEntries(url.searchParams));
    const method = url.searchParams.get("method");
    return reply(route, {
      kind: "inventory",
      scope_id: item,
      event_sequence: sequence,
      arguments: method ? { operation: "inventory_review", item_id: item, method } : null,
      partial_arguments: method ? null : { operation: "inventory_review", item_id: item },
      open_inputs: method ? [] : [{ code: "valuation_method", choices: ["fifo"], default: "fifo" }],
      basis: [{ kind: "item", id: item, role: "scope" }],
      summary: {
        item_name: "Schreibtischlampe",
        item_sku: "LAMP",
        base_unit: "pcs",
        owner_name: "Nordlicht Handel GmbH",
        party_names: {},
        currency: "EUR",
        movement_counts: { opening_stock: 1, shipment: 2 },
        openings: [{ amount: "480.00", currency: "EUR", movement_id: "mov_open" }],
      },
    });
  }
  if (path.endsWith("/cost-review-proposals")) {
    posts.push(JSON.parse(request.postData() || "{}"));
    if (refuseOnce) {
      refuseOnce = false;
      sequence = 42;
      return reply(route, { detail: { code: "draft_changed", message: "Draft changed." } }, 409);
    }
    proposed = true;
    return reply(route, { id: "act_draft", status: "proposed" }, 201);
  }
  if (path.includes("/inspector/"))
    return reply(route, {
      kind: "item",
      id: item,
      eyebrow: "",
      title: "Schreibtischlampe",
      subtitle: "LAMP",
      status: "",
      meaning: "",
      business_reference: null,
      guidance: null,
      technical_rows: [],
      metrics: [],
      trail: [],
      sections: [],
    });
  return reply(route, { detail: "Fixture endpoint unavailable" }, 404);
});

await mkdir(out, { recursive: true });
try {
  await page.goto(
    `${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&item=${item}&entry=${item}`,
  );
  const panel = page.locator("[data-resolution-guidance]").first();
  await panel.getByRole("button", { name: "Prüfung vorbereiten" }).click();
  const dialog = page.locator("dialog[data-cost-review-draft=inventory]");
  await dialog
    .getByText("Reality hat diese Prüfung aus deinen Daten entworfen.", { exact: false })
    .waitFor();
  await dialog.getByText("Nordlicht Handel GmbH", { exact: true }).waitFor();
  await dialog.getByText("1 × Anfangsbestand, 2 × Warenausgänge", { exact: true }).waitFor();
  await dialog.getByText("480,00 €", { exact: false }).waitFor();
  // FIFO is preselected; the answer is re-drafted on the server, which completes it.
  await page.waitForFunction(
    () => document.querySelector("[data-draft-submit]")?.hasAttribute("disabled") === false,
  );
  assert.equal(draftReads.at(-1).method, "fifo");
  // No identifier outside the collapsed system details.
  const visible = await dialog.evaluate((node) => {
    const clone = node.cloneNode(true);
    clone.querySelector("[data-draft-system-details]")?.remove();
    return clone.textContent;
  });
  assert.ok(!/draft_item|mov_open|inventory_review|valuation_method/.test(visible), visible);

  // First submit: the records changed; the dialog says so and re-drafts.
  await dialog.locator("[data-draft-submit]").click();
  await dialog.getByText("Deine Daten haben sich inzwischen geändert.", { exact: false }).waitFor();
  await page.waitForFunction(
    () => document.querySelector("[data-draft-submit]")?.hasAttribute("disabled") === false,
  );
  assert.deepEqual(posts[0], {
    kind: "inventory",
    scope_id: item,
    event_sequence: 41,
    answers: { method: "fifo" },
  });
  await page.screenshot({ path: `${out}/draft-dialog-de.png`, fullPage: true });

  // Second submit proposes; the dialog closes and the panel shows the owner's step.
  await dialog.locator("[data-draft-submit]").click();
  await dialog.waitFor({ state: "detached" });
  assert.equal(posts[1].event_sequence, 42);
  await page.getByText("Ein Inhaber muss das bestätigen.", { exact: true }).waitFor();
  assert.deepEqual(errors, []);
  console.log(
    "PASS: drafted review dialog (German summary, FIFO preselected, re-draft on change, proposal).",
  );
} catch (error) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  console.log(errors, posts, draftReads);
  throw error;
} finally {
  await browser.close();
}
