// HTTP fixtures test navigation; PostgreSQL tests prove canonical quantities and scope.
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
  out = "/private/tmp/reality-209-browser";
const requests = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  fail = false;
const delivery = {
  id: "customer1",
  type: "customer_delivery",
  tenant_id: "orders",
  counterparty: "Müller",
  party_id: "p1",
  item_id: "i1",
  item: "Desk lamp",
  location_id: "l1",
  location: "Main warehouse",
  unit: "pcs",
  promised: "12",
  reserved: "4",
  fulfilled: "2",
  open: "10",
  status: "open",
  due_at: "2026-09-12T12:00:00Z",
  document_id: "doc-c",
  document_line_id: "line1",
};
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    path = u.pathname;
  requests.push({ path, query: u.search, method: req.method() });
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
      tenants: [
        { id: "orders", name: "Northstar Commerce" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: "orders",
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.endsWith("/delivery-work") || path.endsWith("/evidence-documents")) {
    if (fail) return reply({ detail: "Register unavailable" }, 503);
    const empty = u.searchParams.get("q") === "missing",
      n = Number(u.searchParams.get("page") || 1);
    const supplier =
      u.searchParams.get("commitment_type") === "supplier_delivery" ||
      u.searchParams.get("document_type") === "purchase_order";
    const row = path.endsWith("/delivery-work")
      ? {
          ...delivery,
          id: supplier ? "supplier1" : "customer1",
          type: supplier ? "supplier_delivery" : "customer_delivery",
          counterparty: supplier ? "Weber Supplies" : "Müller",
          party_id: supplier ? "ps" : "pc",
        }
      : {
          id: supplier ? "doc-s" : "doc-c",
          date: "2026-09-07",
          number: supplier ? "PO-113" : "SO-113",
          type: supplier ? "purchase_order" : "sales_order",
          party: supplier ? "Weber Supplies" : "Müller",
          party_id: "p1",
          gross_amount: "720.00",
          currency: "EUR",
          line_count: 2,
          reality_link_count: 2,
          status: "recorded",
          source: { system: "sample", type: "order", external_id: "113" },
        };
    return reply({
      items: empty ? [] : [row],
      page: {
        number: n,
        size: 50,
        total: empty ? 0 : 51,
        pages: empty ? 1 : 2,
        has_next: !empty && n === 1,
        has_previous: n > 1,
      },
    });
  }
  if (path.endsWith("/delivery-work/customer1") || path.endsWith("/delivery-work/supplier1"))
    return reply({
      case: {
        ...delivery,
        type: path.endsWith("supplier1") ? "supplier_delivery" : "customer_delivery",
        blockers: [],
      },
      inventory: {
        item_id: "i1",
        location_id: "l1",
        unit: "pcs",
        physical: "20",
        reserved: "4",
        available: "16",
      },
      links: [],
      history: { items: [], has_more: false, next_cursor: null },
      observation: { observed_at: "2026-09-07T12:00:00Z", evidence_available: false },
    });
  const pager = { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false };
  if (path.endsWith("/master-data")) {
    const family = u.searchParams.get("family") || "customer";
    return reply({
      page: pager,
      items: [
        {
          id: "master1",
          family,
          name: "Master original name",
          is_active: true,
          accounting_code: "AR-209",
          payment_term_code: "NET30",
          default_currency: "EUR",
          sku: "SKU209",
          unit: "pcs",
          item_type: "stocked",
          default_location_name: "Named warehouse",
          type: "bin",
          parent_location_name: "Named warehouse",
          allows_stock: false,
        },
      ],
    });
  }
  if (path.includes("/master-data/")) {
    const family = path.split("/").at(-2);
    return reply({
      id: "master1",
      family,
      name: "Master original name",
      is_active: true,
      expected_revision: "rev209",
      source_system: "source209",
      external_id: "external209",
      source_record_id: "source1",
      preview_sections: [
        { title: "Identity", rows: [{ label: "Status", value: "Active", translate_value: true }] },
        {
          title:
            family === "item"
              ? "Inventory behaviour"
              : family === "location"
                ? "Hierarchy"
                : "Commercial defaults",
          rows: [
            {
              label:
                family === "item"
                  ? "Default location"
                  : family === "location"
                    ? "Parent location"
                    : "Accounting code",
              value: family === "item" || family === "location" ? "Named warehouse" : "AR-209",
            },
            {
              label: "Credit limit",
              value: "1250.50",
              display_parts: [{ type: "money", value: "1250.50", currency: "EUR" }],
            },
          ],
        },
      ],
    });
  }
  if (path.includes("/warehouse/"))
    return reply({
      scope: { view: path.split("/").at(-1) },
      page: pager,
      items: [
        {
          id: "warehouse1",
          item_id: "i1",
          name: "Lamp",
          item: "Lamp",
          sku: "P12",
          unit: "pcs",
          physical: "20",
          reserved: "3",
          available: "17",
          quantity: "3",
          status: "active",
          type: "receipt",
          location: "Main warehouse",
          from_location: null,
          to_location: "Main warehouse",
          at: "2026-09-16T12:00:00Z",
        },
      ],
    });
  if (path.includes("/finance/"))
    return reply({
      page: pager,
      totals: [],
      items: [
        {
          id: "payment1",
          document_id: "invoice1",
          number: "INV-209",
          document_type: "sales_invoice",
          document_date: "2026-09-16",
          party: "Müller",
          party_id: "p1",
          gross: "77.77",
          settled: "20",
          open: "57.77",
          currency: "EUR",
          status: "partial",
          amount: "20",
          allocated: "20",
          unallocated: "0",
          direction: "incoming",
          reference: "PAY-209",
          effective_at: "2026-09-16T12:00:00Z",
          posting_group_id: "group1",
          reversal_role: "normal",
          account: "cash",
          account_code: "1000",
          account_name: "Cash",
          debit_credit: "debit",
          inspect_id: "payment1",
        },
      ],
    });
  if (path.endsWith("/shipments"))
    return reply({
      page: pager,
      items: [
        {
          id: "shipment1",
          direction: "outbound",
          purpose: "customer_delivery",
          created_at: "2026-09-16T12:00:00Z",
          packages: [{ id: "package1", carrier: "DHL", tracking_number: "TRACK-209" }],
          movements: [],
          observations: {},
          events: [],
          quantities: { promised: null, dispatched: null, received: null },
          discrepancies: {},
        },
      ],
    });
  if (path.includes("/inspector/")) {
    const compact = u.searchParams.get("preview") === "true";
    return reply({
      kind: "document",
      id: "doc-c",
      title: "Sales Order SO-113",
      subtitle: "Müller",
      meaning: "Sales Order SO-113. Müller.",
      sections: [
        { title: "Correction", rows: [{ label: "Evidence", value: "Original source retained" }] },
      ],
      metrics: [],
      technical_rows: [],
      events: [],
      ...(compact
        ? {
            preview_sections: [
              {
                title: "Document",
                rows: [
                  { label: "Customer", value: "Müller" },
                  {
                    label: "Gross amount",
                    value: "77.77",
                    display_parts: [{ type: "money", value: "77.77", currency: "EUR" }],
                  },
                ],
              },
              {
                title: "Lines",
                has_more: true,
                rows: [
                  {
                    label:
                      "P12 · Original extra-long outdoor lamp description for accurate business identification",
                    original_label: true,
                    value: "2 pcs · EUR 30.17",
                    display_parts: [
                      { type: "number", value: "2" },
                      { type: "text", value: " pcs · " },
                      { type: "money", value: "30.17", currency: "EUR" },
                    ],
                    hint: "Current item name",
                    link: { kind: "document_line", id: "line1" },
                  },
                ],
              },
              {
                title: "Settlement",
                rows: [
                  {
                    label: "Open amount",
                    value: "0",
                    display_parts: [{ type: "money", value: "0", currency: "EUR" }],
                  },
                ],
              },
              { title: "Current tracking observations", rows: [] },
            ],
          }
        : {}),
    });
  }
  return reply({ detail: "Fixture unavailable" }, 404);
});

try {
  await mkdir(out, { recursive: true });
  for (const width of process.env.PREVIEW_WORKSPACES_ONLY ? [] : [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const lang of ["en", "de", "nl", "es"]) {
      language = lang;
      await page.goto(`${base}/app/orders-deliveries?tenant=orders&orders_view=customer-orders`);
      const trigger = page.locator("tbody button[aria-expanded]").first();
      await trigger.focus();
      await page.keyboard.press("Enter");
      const preview = page.locator("[data-inline-inspector]");
      await preview.getByText(/P12 · Original extra-long/).waitFor();
      assert.equal(await preview.getByText("Correction", { exact: true }).count(), 0);
      assert.equal(await preview.locator("section").count(), 4);
      assert.ok(
        requests.some((r) => r.path.includes("/inspector/") && r.query === "?preview=true"),
      );
      const box = await preview.boundingBox();
      assert.ok(box.width <= width, `preview overflow at ${width}`);
      assert.ok(
        box.x >= 0 && box.x + box.width <= width,
        `preview outside viewport: ${JSON.stringify(box)}`,
      );
      const overflow = await preview.evaluate((el) => el.scrollWidth > el.clientWidth + 1);
      assert.equal(overflow, false);
      await page.screenshot({ path: `${out}/preview-${width}-${lang}.png`, fullPage: true });
      await preview.locator("div.mt-5 > button").first().click();
      await page.getByRole("dialog").waitFor();
      assert.ok(requests.some((r) => r.path.includes("/inspector/") && r.query === ""));
      await page.keyboard.press("Escape");
      await trigger.click();
      assert.equal(await preview.count(), 0);
    }
  }
  language = "en";
  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const [route, kind] of [
    ["/app/orders-deliveries?orders_view=supplier-orders", "document"],
    ["/app/orders-deliveries?orders_view=shipments", "shipment"],
    ["/app/warehouse?warehouse_view=stock", "item"],
    ["/app/warehouse?warehouse_view=reservations", "reservation"],
    ["/app/warehouse?warehouse_view=movements", "movement"],
    ["/app/finance?finance_view=open-items", "document"],
    ["/app/finance?finance_view=payments", "payment"],
    ["/app/finance?finance_view=journal", "ledger_entry"],
  ]) {
    console.log(`Checking ${route}`);
    const start = requests.length;
    await page.goto(`${base}${route}&tenant=orders`);
    await page.locator("tbody button[aria-expanded]").first().click();
    await page
      .locator("[data-inline-inspector]")
      .getByText(/P12 · Original extra-long/)
      .waitFor();
    assert.ok(
      requests
        .slice(start)
        .some((r) => r.path.includes(`/inspector/${kind}/`) && r.query === "?preview=true"),
      route,
    );
  }
  for (const family of ["customer", "supplier", "item", "location"]) {
    await page.goto(`${base}/app/master-data?tenant=orders&family=${family}`);
    await page.getByRole("navigation", { name: "Workspaces", exact: true }).waitFor();
    assert.equal(
      await page
        .getByRole("navigation", { name: "Workspaces", exact: true })
        .getByRole("link", { name: "Master data", exact: true })
        .count(),
      1,
    );
    assert.equal(
      await page
        .getByRole("navigation", { name: "Company", exact: true })
        .getByRole("link", { name: "Master data", exact: true })
        .count(),
      0,
    );
    assert.equal(await page.getByRole("columnheader", { name: /Record ID/ }).count(), 0);
    await page.locator("tbody button[aria-expanded]").first().click();
    const preview = page.locator("[data-master-preview]");
    await preview.getByRole("heading", { name: "Master original name" }).waitFor();
    await preview
      .getByText(family === "item" || family === "location" ? "Named warehouse" : "AR-209", {
        exact: true,
      })
      .waitFor();
    await preview.getByRole("button", { name: "Edit details", exact: true }).waitFor();
    const previewBounds = await preview.boundingBox();
    const scrollBounds = await page
      .getByRole("region", { name: "Scrollable register" })
      .boundingBox();
    assert.ok(previewBounds.x >= scrollBounds.x, "master preview left edge remains visible");
    assert.ok(
      previewBounds.x + previewBounds.width <= scrollBounds.x + scrollBounds.width,
      "master preview right edge remains visible",
    );
    await page.screenshot({ path: `${out}/master-${family}.png`, fullPage: true });
  }
  assert.deepEqual(errors, []);
  assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
  console.log(
    "Operational previews: four languages, desktop/mobile, keyboard, full explanation and read-only checks passed.",
  );
} catch (error) {
  console.error(errors, page.url(), (await page.locator("body").innerText()).slice(-3000));
  throw error;
} finally {
  await browser.close();
}
