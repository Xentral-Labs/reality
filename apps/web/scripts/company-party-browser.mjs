// Spec 289: a company without its own business partner is offered to record it from the
// cost review draft, prefilled with the company name and without sending a name; the
// draft then names the waiting proposal. Intercepted fixture; the service side is proven
// in test_company_party.py.
import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";

import { parseCatalogs } from "./i18n-audit-lib.mjs";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177",
  out = "/private/tmp/reality-289-company-party-browser";
const errors = [],
  prepares = [];
let language = "de",
  waiting = null;
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
      language,
      locale: { de: "de-DE", nl: "nl-NL", es: "es-ES" }[language],
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
  if (path.endsWith("/cost-review-draft"))
    return reply(route, {
      kind: "inventory",
      scope_id: item,
      event_sequence: 41,
      arguments: null,
      partial_arguments: { operation: "inventory_review", item_id: item },
      open_inputs: [
        waiting
          ? { code: "company_party_missing", proposal_id: waiting }
          : {
              code: "company_party_missing",
              action: "company_party_record",
              name: "Nordlicht Handel",
            },
      ],
      basis: [{ kind: "item", id: item, role: "scope" }],
      summary: {
        item_name: "Schreibtischlampe",
        item_sku: "LAMP",
        base_unit: "pcs",
        party_names: {},
        currency: "EUR",
        movement_counts: { opening_stock: 1 },
        openings: [],
      },
    });
  if (path.endsWith("/company-party/prepare")) {
    prepares.push({ method: request.method(), body: request.postData() });
    waiting = "act_company";
    return reply(route, { id: waiting, status: "proposed", name: "Nordlicht Handel" }, 201);
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

const catalogs = parseCatalogs(fileURLToPath(new URL("../src/localization.tsx", import.meta.url)));
const t = (lang, source) => catalogs[lang].get(source) || source;

await mkdir(out, { recursive: true });
try {
  for (const lang of ["de", "nl", "es"]) {
    language = lang;
    waiting = null;
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(
        `${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&item=${item}&entry=${item}&lang=${lang}`,
      );
      const panel = page.locator("[data-resolution-guidance]").first();
      await panel.getByRole("button", { name: t(lang, "Prepare review") }).click();
      const dialog = page.locator("dialog[data-cost-review-draft=inventory]");
      const offer = dialog.locator("[data-company-party-action=offer]");
      await offer.waitFor();
      // FR-004: the prefilled name, in the person's language.
      await offer
        .getByText(
          t(lang, "{name} will be recorded as your company.").replace("{name}", "Nordlicht Handel"),
          { exact: true },
        )
        .waitFor();
      await page.screenshot({ path: `${out}/offer-${lang}-${width}.png`, fullPage: true });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await dialog.getByRole("button", { name: t(lang, "Close") }).click();
    }
  }
  // Propose from the draft: nothing is sent but the request itself (DR-003).
  language = "de";
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(
    `${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&item=${item}&entry=${item}&lang=de`,
  );
  await page
    .locator("[data-resolution-guidance]")
    .first()
    .getByRole("button", { name: "Prüfung vorbereiten" })
    .click();
  const dialog = page.locator("dialog[data-cost-review-draft=inventory]");
  await dialog
    .getByRole("button", { name: "Mein Unternehmen als Geschäftspartner erfassen", exact: true })
    .click();
  // FR-006: the draft now names the waiting proposal instead of offering another.
  const pending = dialog.locator("[data-company-party-action=waiting]");
  await pending.waitFor();
  await pending
    .getByText("Wartet auf die Bestätigung durch einen Inhaber.", { exact: false })
    .waitFor();
  assert.equal(await dialog.locator("[data-company-party-action=offer]").count(), 0);
  const link = await pending.getByRole("link").getAttribute("href");
  assert.equal(link, `/app/decisions?tenant=${tenant}&proposal=act_company`);
  assert.deepEqual(prepares, [{ method: "POST", body: null }]);
  await page.screenshot({ path: `${out}/waiting-de-1440.png`, fullPage: true });
  assert.deepEqual(errors, []);
  console.log(
    "PASS the draft offers recording the company, prefilled, and then names the waiting proposal",
  );
} catch (error) {
  console.error(errors);
  console.error("Failure URL:", page.url());
  console.error("Failure body:", (await page.locator("body").innerText()).slice(0, 3000));
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  throw error;
} finally {
  await browser.close();
}
