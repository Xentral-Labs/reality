import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
// Spec 286: coded service refusals are shown in the account language, in the forms and
// in the chat panel. Intercepted fixture; the service side is proven in
// test_service_refusals.py and the translations in service-refusals-localization.test.mjs.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { parseCatalogs } from "./i18n-audit-lib.mjs";
import { localizeRefusal } from "../src/refusals.ts";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
const shots = "/private/tmp/reality-286-refusals-browser";
await mkdir(shots, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  prepared,
  refusal;
const pager = { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false };
const billing = (id) => ({
  order_line_id: id,
  order_id: "order",
  label: id === "line" ? "Desk lamp" : "Office chair",
  unit: "pcs",
  ordered: "4",
  invoiced: "0",
  remaining: "4",
  can_invoice: true,
  evidence: [],
});
const review = (tool, a) => ({
  id: "invoice",
  tool,
  status: "proposed",
  verification: "pending",
  links: [],
  observation: null,
  review: {
    token: "exact",
    intent: a,
    effect: { debit: "accounts_receivable", credit: "sales_revenue" },
    state: {
      billing: a.lines.map((row) => ({
        ...billing(row.order_line_id),
        requested: row.quantity,
        remaining_after: "2",
      })),
      // As the service does: each position spreads its selection, stated detail included.
      positions: a.lines.map((row) => ({
        ...row,
        item: { name: row.order_line_id === "line" ? "Desk lamp" : "Office chair" },
        line: { unit: "pcs" },
      })),
      creation: { ...a, direction: "sales", currency: "EUR", unit: "pcs" },
      order: { id: "order", number: "ORDER-284" },
      party: { name: "Müller" },
      item: { name: "Desk lamp" },
    },
  },
});
let proposal = review("sales_invoice_record", {
  lines: [
    {
      order_line_id: "line",
      quantity: "2",
      gross_amount: "59.50",
      reality_finance_v1: { net: "50.00", tax: "9.50" },
    },
    { order_line_id: "line2", quantity: "2", gross_amount: "60.00" },
  ],
  gross_amount: "119.50",
  number: "INV-284",
});
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    p = new URL(req.url()).pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (p === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
    });
  if (p === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "company", name: "Northstar" }], default_tenant_id: "company" });
  if (p.endsWith("/application-reference")) return reply(discoveryReference);
  if (p.endsWith("/evidence-documents"))
    return reply({
      items: [
        {
          id: "order",
          number: "ORDER-284",
          party: "Müller",
          currency: "EUR",
          gross_amount: "238",
          line_count: 2,
        },
      ],
      page: pager,
    });
  if (p.includes("/inspector/"))
    return reply({
      id: "order",
      evidence_lines: ["line", "line2"].map((id) => ({
        id,
        label: id === "line" ? "Desk lamp" : "Office chair",
        quantity: "4",
        gross_amount: "119",
        unit: "pcs",
        billing: billing(id),
      })),
    });
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    return reply(refusal, 400);
  }
  // The decision entry hands delivery-family proposals to their own card.
  if (p.endsWith("/change-proposals/invoice/review"))
    return reply({ id: "invoice", review_kind: "delivery", status: proposal.status });
  if (p.endsWith("/reject")) return reply({ ...proposal, status: "rejected" });
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (
    ["/dashboard", "/activity-volume", "/readiness", "/analytics"].some((path) => p.endsWith(path))
  )
    return reply({ detail: "Home reads are outside this invoice fixture" }, 503);
  return reply({ items: [], totals: [], page: pager });
});
const catalogs = parseCatalogs(fileURLToPath(new URL("../src/localization.tsx", import.meta.url)));
// What the page must show: the refusal translated with the web's own dictionaries.
const expected = (lang, body) =>
  localizeRefusal(body, {
    t: (source) => (lang === "en" ? source : catalogs[lang].get(source) || source),
    exact: (value) => value,
    date: (value) => value,
  });
const coded = (code, template, values = {}, detail) => ({
  detail: detail ?? template.replace(/\{([a-z_]+)\}/g, (_match, name) => values[name].value),
  code,
  template,
  values,
});
const REFUSALS = [
  coded("stated_invoice_net_tax_gross_mismatch", "Net plus tax differs from the invoice gross."),
  coded(
    "manual_line_amount_required",
    "Line {index} requires a stated amount; it is never calculated.",
    {
      index: { value: "3", kind: "number" },
    },
  ),
  coded("master_data_field_negative", "{field} cannot be negative.", {
    field: { value: "Lead time days", kind: "term" },
  }),
];
const LABELS = {
  en: ["Request changes", "Review change"],
  de: ["Änderungen anfordern", "Änderung prüfen"],
  nl: ["Wijzigingen aanvragen", "Wijziging beoordelen"],
  es: ["Solicitar cambios", "Revisar cambio"],
};
const submit = async (lang, body) => {
  refusal = body;
  language = lang;
  await page.goto(`${base}/app/finance?tenant=company&proposal=invoice&lang=${lang}`);
  await page.locator("#invoice-title").waitFor();
  await page.getByRole("button", { name: LABELS[lang][0], exact: true }).click();
  await page.getByRole("button", { name: LABELS[lang][1], exact: true }).click();
  const shown = page.getByText(expected(lang, body), { exact: true });
  await shown.waitFor();
  return shown;
};
try {
  // FR-005: every coded refusal is shown in the account language, values in place.
  for (const lang of ["de", "nl", "es"])
    for (const body of REFUSALS) {
      const text = expected(lang, body);
      assert.notEqual(text, body.detail, `${lang}: ${body.code} must not show English`);
      await submit(lang, body);
    }
  // The term value is translated with the sentence.
  assert.match(expected("de", REFUSALS[2]), /^Lieferzeit/);
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await submit("de", REFUSALS[1]);
    await page.screenshot({ path: `${shots}/invoice-de-${width}.png` });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  // English shows exactly the sentence the service sent.
  await submit("en", REFUSALS[0]);
  // An unknown code (a newer server) and an uncoded refusal fall back to English.
  const unknown = coded("refusal_from_the_future", "A future refusal {x}.", {
    x: { value: "7", kind: "number" },
  });
  refusal = unknown;
  language = "de";
  await page.goto(`${base}/app/finance?tenant=company&proposal=invoice&lang=de`);
  await page.getByRole("button", { name: LABELS.de[0], exact: true }).click();
  await page.getByRole("button", { name: LABELS.de[1], exact: true }).click();
  await page.getByText("A future refusal 7.", { exact: true }).waitFor();
  refusal = { detail: "A plain English refusal." };
  await page.getByRole("button", { name: LABELS.de[1], exact: true }).click();
  await page.getByText("A plain English refusal.", { exact: true }).waitFor();
  // US3: a coded refusal that ends a chat stream is shown in Spanish.
  const chat = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  chat.on("pageerror", (e) => errors.push(e.message));
  await chat.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const reply = (body, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/auth/me")
      return reply({
        id: "operator",
        email: "operator@example.test",
        status: "active",
        language: "es",
        locale: "es-ES",
        timezone: "UTC",
      });
    if (path === "/api/v1/bootstrap")
      return reply({
        tenants: [{ id: "company", name: "Northstar" }],
        default_tenant_id: "company",
      });
    if (path.endsWith("/application-reference")) return reply(discoveryReference);
    if (path.endsWith("/copilot"))
      return reply({
        sessions: [{ id: "chat_a", title: "Pagos" }],
        active_session_id: "chat_a",
        messages: [],
        proposals: [],
        suggestions: [],
        has_archived: false,
      });
    if (path.endsWith("/change-proposals")) return reply({ items: [], page: pager });
    if (
      ["/dashboard", "/activity-volume", "/readiness", "/analytics"].some((x) => path.endsWith(x))
    )
      return reply({ detail: "Outside this fixture" }, 503);
    return reply({ items: [], totals: [], page: pager });
  });
  await chat.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = async (input, init) => {
      if (String(input).includes("/messages?stream=true")) {
        const body = new ReadableStream({
          start(controller) {
            window.chatController = controller;
          },
        });
        return new Response(body, { headers: { "Content-Type": "application/x-ndjson" } });
      }
      return original(input, init);
    };
  });
  await chat.goto(`${base}/app/chat?tenant=company&session=chat_a&lang=es`);
  const input = chat.locator("textarea").first();
  await input.waitFor();
  await input.fill("Registra el pago");
  await input.press("Enter");
  await chat.waitForFunction(() => !!window.chatController);
  const streamed = REFUSALS[0];
  await chat.evaluate(
    (event) => {
      window.chatController.enqueue(new TextEncoder().encode(JSON.stringify(event) + "\n"));
      window.chatController.close();
    },
    {
      type: "error",
      message: streamed.detail,
      code: streamed.code,
      template: streamed.template,
      values: {},
    },
  );
  await chat.getByText(expected("es", streamed), { exact: true }).waitFor();
  await chat.screenshot({ path: `${shots}/chat-es-1440.png` });
  assert.deepEqual(errors, []);
  console.log(
    "PASS coded refusals are shown in de/nl/es with their values; unknown ones in English",
  );
} catch (error) {
  console.error(errors);
  console.error("Failure URL:", page.url());
  console.error("Failure body:", (await page.locator("body").innerText()).slice(0, 3000));
  await page.screenshot({ path: `${shots}/error.png` });
  throw error;
} finally {
  await browser.close();
}
