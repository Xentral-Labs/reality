// HTTP fixtures test what the workspace states about origin; PostgreSQL tests prove
// resolution, tenant scope and address validation (spec 211).
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177",
  out = "/private/tmp/reality-211-browser";
const requests = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en";

const imported = {
  kind: "source",
  system_code: "shopify_de",
  system_name: "Shopify Germany",
  source_type: "order",
  external_id: "1042",
  source_version: 1,
  received_at: "2026-09-16T08:00:00Z",
  source_record_id: "src1",
  superseded: false,
  url: "https://acme-de.myshopify.com/admin/orders/1042",
};
const unaddressed = {
  ...imported,
  system_code: "retired_shop",
  system_name: "retired_shop",
  external_id: "77",
  source_record_id: "src2",
  superseded: true,
  url: null,
};
const manual = { kind: "application", actor: "operator@example.test" };

await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    path = u.pathname;
  requests.push({ path, method: req.method() });
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      display_name: "Operator",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: "orders", name: "Northstar Commerce" }],
      default_tenant_id: "orders",
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  const pager = { number: 1, size: 50, total: 3, pages: 1, has_next: false, has_previous: false };
  if (path.endsWith("/evidence-documents"))
    return reply({
      page: pager,
      items: [
        {
          id: "doc1",
          date: "2026-09-16",
          number: "SO-1042",
          type: "sales_order",
          party: "Müller GmbH",
          party_id: "p1",
          gross_amount: "720.00",
          currency: "EUR",
          line_count: 2,
          reality_link_count: 2,
          status: "recorded",
          source: { system: "shopify_de", type: "order", external_id: "1042" },
          origin: imported,
        },
        {
          id: "doc2",
          date: "2026-09-15",
          number: "SO-0077",
          type: "sales_order",
          party: "Weber KG",
          party_id: "p2",
          gross_amount: "120.00",
          currency: "EUR",
          line_count: 1,
          reality_link_count: 0,
          status: "recorded",
          source: null,
          origin: unaddressed,
        },
        {
          id: "doc3",
          date: "2026-09-14",
          number: "SO-0001",
          type: "sales_order",
          party: "Hand entered",
          party_id: "p3",
          gross_amount: "10.00",
          currency: "EUR",
          line_count: 1,
          reality_link_count: 0,
          status: "recorded",
          source: null,
          origin: manual,
        },
      ],
    });
  if (path.endsWith("/delivery-work")) return reply({ page: pager, items: [] });
  if (path.endsWith("/master-data"))
    return reply({
      page: pager,
      items: [
        {
          id: "master1",
          family: u.searchParams.get("family") || "customer",
          name: "Imported customer",
          is_active: true,
          accounting_code: "AR-211",
          origin: imported,
        },
        {
          id: "master2",
          family: u.searchParams.get("family") || "customer",
          name: "Hand entered customer",
          is_active: true,
          accounting_code: "AR-000",
          origin: manual,
        },
      ],
    });
  if (path.includes("/master-data/"))
    return reply({
      id: "master1",
      family: path.split("/").at(-2),
      name: "Imported customer",
      is_active: true,
      expected_revision: "rev211",
      source_system: "shopify_de",
      external_id: "1042",
      source_record_id: "src1",
      origin: imported,
      contributing_systems: ["hubspot_main", "shopify_de"],
      preview_sections: [],
    });
  if (path.includes("/inspector/source_record/"))
    return reply({
      kind: "source_record",
      id: "src1",
      eyebrow: "",
      title: "Source Record",
      subtitle: "",
      status: "Recorded",
      meaning: "",
      metrics: [],
      trail: [],
      events: [],
      sections: [
        {
          title: "Recorded values",
          rows: [
            { label: "Source system", value: "Shopify Germany", tone: "", link: null },
            { label: "External reference", value: "1042", tone: "", link: null },
            { label: "Interpretation", value: "interpreted", tone: "", link: null },
            {
              label: "Open in source system",
              value: "https://acme-de.myshopify.com/admin/orders/1042",
              tone: "",
              link: null,
            },
          ],
        },
      ],
      technical_rows: [],
      source_payload: '{"id": "1042", "total": "720.00"}',
      source_payload_truncated: false,
    });
  return reply({ page: pager, items: [] });
});

await mkdir(out, { recursive: true });
try {
  for (language of ["en", "de", "nl", "es"]) {
    await page.goto(`${base}/app/orders-deliveries?tenant=orders&orders_view=customer-orders`);
    const origins = page.locator("[data-source-origin]");
    await origins.first().waitFor();
    assert.equal(await origins.count(), 3, `${language}: every row states an origin`);
    assert.equal(
      await page.locator('[data-source-origin="application"]').count(),
      1,
      `${language}: the hand-entered row says it was created here`,
    );
    for (const text of await origins.allInnerTexts())
      assert.notEqual(text.trim(), "", `${language}: no origin renders empty`);
  }
  language = "en";

  // The addressed row links out; the unaddressed one states origin without a link.
  await page.goto(`${base}/app/orders-deliveries?tenant=orders&orders_view=customer-orders`);
  const linked = page.locator('[data-source-system="shopify_de"] [data-source-link]');
  await linked.waitFor();
  assert.equal(
    await linked.getAttribute("href"),
    "https://acme-de.myshopify.com/admin/orders/1042",
  );
  assert.equal(await linked.getAttribute("target"), "_blank");
  assert.equal(await linked.getAttribute("rel"), "noopener noreferrer");
  assert.match(
    await linked.getAttribute("title"),
    /acme-de\.myshopify\.com/,
    "the target host is visible before activation",
  );
  assert.equal(
    await page.locator('[data-source-system="retired_shop"] [data-source-link]').count(),
    0,
    "an unconfigured system offers no link",
  );
  assert.equal(
    await page.locator('[data-source-system="retired_shop"] [data-source-superseded]').count(),
    1,
    "a superseded source version is disclosed",
  );
  await page.screenshot({ path: `${out}/orders-origin.png`, fullPage: true });

  // Activating the origin opens the source record with its payload.
  await page.locator('[data-source-system="shopify_de"] button').first().click();
  const dialog = page.getByRole("dialog");
  await dialog.waitFor();
  const inspection = await dialog.innerText();
  assert.match(inspection, /Shopify Germany/);
  assert.match(inspection, /interpreted/);
  // The retained payload sits behind its existing disclosure; opening it is the proof.
  await dialog.locator("[data-source-payload] summary").click();
  assert.match(
    await dialog.locator("[data-source-payload] pre").innerText(),
    /720\.00/,
    "the retained payload is readable",
  );
  await page.screenshot({ path: `${out}/source-inspection.png`, fullPage: true });
  await page.keyboard.press("Escape");

  // Master data carries the same statement, plus the contributing-system disclosure.
  await page.goto(`${base}/app/master-data?tenant=orders&family=customer`);
  await page.locator("[data-source-origin]").first().waitFor();
  assert.equal(await page.locator("[data-source-origin]").count(), 2);
  // Open the row the way a user does, rather than trusting a deep link.
  await page.locator('[aria-controls="master-preview-master1"]').click();
  const contributing = page.locator("[data-contributing-systems]");
  await contributing.waitFor();
  assert.match(await contributing.innerText(), /hubspot_main/);
  await page.screenshot({ path: `${out}/master-origin.png`, fullPage: true });

  // Narrow screens keep the statement and never scroll the page sideways.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${base}/app/orders-deliveries?tenant=orders&orders_view=customer-orders`);
  await page.locator("[data-source-origin]").first().waitFor();
  assert.ok(await page.locator("[data-source-origin]").first().isVisible());
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  assert.ok(overflow <= 0, `page scrolls sideways at 390px by ${overflow}px`);
  await page.screenshot({ path: `${out}/orders-origin-390.png`, fullPage: true });

  assert.deepEqual(errors, []);
  assert.equal(
    requests.filter((r) => r.method !== "GET").length,
    0,
    "reading origin writes nothing",
  );
  console.log(
    "Record provenance: four languages, origin on every row, link presence and absence, host visibility, source inspection, contributing systems and 390px checks passed.",
  );
} catch (error) {
  console.error(errors, page.url(), (await page.locator("body").innerText()).slice(-3000));
  throw error;
} finally {
  await browser.close();
}
