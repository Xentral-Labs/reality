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
  out = "/private/tmp/reality-113-browser";
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
  if (path.endsWith("/projection-views/fulfillment_queue"))
    return reply({
      metadata: {
        projection: "fulfillment_queue",
        calculation_mode: "stored",
        state: u.searchParams.get("q") === "stale" ? "pending" : "ready",
        processed_event_sequence: u.searchParams.get("q") === "stale" ? 40 : 42,
        target_event_sequence: 42,
        completed_at: "2026-09-25T10:00:00Z",
        projection_version: 1,
        upstream_freshness: "unknown",
        consistency: "completed_snapshot",
      },
      items: [
        {
          order_key: "doc-future",
          document_id: "doc-future",
          document_number: "SO-FUTURE",
          party_id: "customer-a",
          party: "Müller Maschinenbau",
          due_at: "2026-11-15T00:00:00Z",
          readiness: "blocked",
          ship_ready: false,
          blocking_reasons: ["insufficient_reservation", "insufficient_stock"],
          lines: [
            {
              commitment_id: "commitment-partial",
              item_id: "item-a",
              item: "Drive assembly",
              sku: "DRV-1",
              unit: "pcs",
              quantity: "10",
              open_quantity: "10",
              fulfilled_quantity: "0",
              reserved_quantity: "4",
              physical_quantity: "4",
              shippable_quantity: "4",
              shortage_quantity: "6",
              location_id: "warehouse-a",
              due_at: "2026-11-15T00:00:00Z",
              blocking_reasons: ["insufficient_reservation", "insufficient_stock"],
              fulfillment_readiness: null,
            },
          ],
        },
        {
          order_key: "doc-prepay",
          document_id: "doc-prepay",
          document_number: "SO-PREPAY",
          party_id: "customer-b",
          party: "Schmidt Handel",
          due_at: "2026-12-01T00:00:00Z",
          readiness: "blocked",
          ship_ready: false,
          blocking_reasons: ["prepayment_invoice_missing", "prepayment_required"],
          lines: [
            {
              commitment_id: "commitment-prepay",
              item_id: "item-b",
              item: "Control cabinet",
              sku: "CAB-1",
              unit: "pcs",
              quantity: "2",
              open_quantity: "2",
              fulfilled_quantity: "0",
              reserved_quantity: "2",
              physical_quantity: "2",
              shippable_quantity: "0",
              shortage_quantity: "0",
              location_id: "warehouse-a",
              due_at: "2026-12-01T00:00:00Z",
              blocking_reasons: ["prepayment_invoice_missing", "prepayment_required"],
              fulfillment_readiness: {
                currency: "EUR",
                required_amount: "2000.00",
                received_amount: "0.00",
                remaining_amount: "2000.00",
                requires_prepayment: true,
              },
            },
          ],
        },
      ],
      page: {
        number: 1,
        size: 50,
        total: 2,
        pages: 1,
        has_next: false,
        has_previous: false,
      },
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
  if (path.includes("/inspector/"))
    return path.endsWith("/foreign")
      ? reply({ detail: "Not found" }, 404)
      : reply({
          title: "Selected order or delivery",
          subtitle: "Exact record",
          meaning: "Held evidence and current reality",
          sections: [],
          metrics: [],
          technical_rows: [],
        });
  return reply({ detail: "Fixture unavailable" }, 404);
});
const go = async (view = "deliveries", extra = "") => {
  await page.goto(`${base}/app/orders-deliveries?tenant=orders&orders_view=${view}${extra}`);
  await page.locator("[data-orders-row]").first().waitFor();
};
if (process.env.READINESS_ONLY === "1") {
  try {
    await mkdir(out, { recursive: true });
    await go("readiness");
    if (process.env.READINESS_DEBUG === "1")
      console.log(page.url(), await page.locator("body").innerText());
    await page.getByText("SO-FUTURE", { exact: true }).waitFor();
    await page.getByText("SO-PREPAY", { exact: true }).waitFor();
    await page.getByText("4 pcs of 10 pcs reserved", { exact: true }).waitFor();
    await page.getByText("4 pcs of 10 pcs physically available", { exact: true }).waitFor();
    await page.getByText("Prepayment invoice evidence is missing", { exact: true }).waitFor();
    await page.getByText(/2,000.*prepayment remaining/).waitFor();
    await page.getByText(/Readiness observed at/).waitFor();
    await page
      .locator('[data-orders-row="doc-prepay"]')
      .getByRole("button", { name: /SO-PREPAY/ })
      .click();
    await page.getByText("€0.00 / €2,000.00", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Prepare prepayment invoice", exact: true }).click();
    await page.getByRole("dialog").getByRole("heading", { name: "New invoice" }).waitFor();
    assert.equal(
      await page.getByRole("combobox", { name: "Order", exact: true }).inputValue(),
      "doc-prepay",
    );
    await page.getByRole("dialog").getByRole("button", { name: "Close" }).click();
    await page.getByRole("button", { name: "Inspect commitment", exact: true }).last().click();
    await page.getByRole("dialog").waitFor();
    assert.ok(requests.some((r) => r.path.endsWith("/inspector/commitment/commitment-prepay")));
    await page.keyboard.press("Escape");
    await page
      .locator('[data-orders-row="doc-future"]')
      .getByRole("button", { name: /SO-FUTURE/ })
      .click();
    await page.getByRole("button", { name: "Prepare available shipment", exact: true }).click();
    const shipmentDialog = page.getByRole("dialog");
    assert.equal(
      await shipmentDialog.getByRole("textbox", { name: "Counterparty ID" }).inputValue(),
      "customer-a",
    );
    assert.match(
      await shipmentDialog.getByRole("textbox", { name: "Movement inputs (JSON)" }).inputValue(),
      /"commitment_id":"commitment-partial".*"quantity":"4"/,
    );
    await shipmentDialog.getByRole("button", { name: "Close" }).click();
    await go("readiness", "&q=stale");
    if (process.env.READINESS_DEBUG === "1")
      console.log(
        requests.filter((r) => r.path.endsWith("/projection-views/fulfillment_queue")),
        await page.locator("body").innerText(),
      );
    await page
      .locator('[data-orders-row="doc-future"]')
      .getByRole("button", { name: /SO-FUTURE/ })
      .click();
    await page
      .getByText("Actions are unavailable until the readiness projection is current.", {
        exact: true,
      })
      .first()
      .waitFor();
    assert.equal(
      await page.getByRole("button", { name: "Prepare available shipment", exact: true }).count(),
      0,
    );
    assert.equal(
      await page.getByRole("button", { name: "Prepare prepayment invoice", exact: true }).count(),
      0,
    );
    await go("readiness");
    const reloaded = page.waitForResponse((response) =>
      response.url().includes("/projection-views/fulfillment_queue"),
    );
    await page.evaluate(() => window.dispatchEvent(new Event("reality:delivery-settled")));
    await reloaded;
    await page
      .getByRole("status")
      .getByText(/Readiness was reloaded/)
      .waitFor();
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await go("readiness");
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: `${out}/readiness-${width}.png`, fullPage: true });
    }
    const mutations = requests.filter(
      (r) => r.method !== "GET" && !r.path.endsWith("/search/resolve"),
    );
    assert.equal(mutations.length, 0, JSON.stringify(mutations));
    assert.deepEqual(errors, []);
    console.log(
      "PASS: multi-customer readiness, exact invoice/shipment handoffs, future dates, partial stock, prepayment evidence, Inspector trace, responsive layout and no writes.",
    );
  } finally {
    await browser.close();
  }
  process.exit(0);
}
try {
  await mkdir(out, { recursive: true });
  await go("deliveries", "&q=Muller&page=2");
  assert.equal(await page.getByRole("link", { name: "Your work", exact: true }).count(), 0);
  let listUrl = page.url();
  await page.locator("[data-orders-row]").first().focus();
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: "Reserve stock", exact: true }).waitFor();
  assert.equal(new URL(page.url()).pathname, "/app/orders-deliveries");
  assert.equal(new URL(page.url()).searchParams.get("q"), "Muller");
  assert.equal(new URL(page.url()).searchParams.get("page"), "2");
  await page.getByRole("button", { name: "Back to commitments", exact: true }).click();
  assert.equal(new URL(page.url()).searchParams.get("q"), "Muller");
  assert.equal(new URL(page.url()).searchParams.get("page"), "2");
  assert.equal(new URL(page.url()).searchParams.has("commitment"), false);
  listUrl = page.url();
  await page.locator("[data-orders-row]").first().getByText("Müller", { exact: true }).click();
  await page.getByRole("button", { name: "Reserve stock", exact: true }).waitFor();
  await page.goBack();
  await page.locator("[data-orders-row]").first().waitFor();
  assert.equal(page.url(), listUrl);
  await page.goto(base + "/app/work?tenant=orders&commitment=foreign");
  await page.getByRole("alert").first().waitFor();
  assert.equal(new URL(page.url()).pathname, "/app/orders-deliveries");
  assert.equal(new URL(page.url()).searchParams.get("commitment"), "foreign");
  await page.getByRole("button", { name: "Back to commitments", exact: true }).click();
  await page.goto(base + "/app/work?tenant=orders&q=missing");
  await page.getByText("No matching records", { exact: true }).waitFor();
  assert.equal(new URL(page.url()).pathname, "/app/orders-deliveries");
  await go("customer-orders");
  assert.ok(
    requests.some(
      (r) =>
        r.path.endsWith("/evidence-documents") && r.query.includes("document_type=sales_order"),
    ),
  );
  await go("readiness");
  await page.getByText("SO-FUTURE", { exact: true }).waitFor();
  await page.getByText("SO-PREPAY", { exact: true }).waitFor();
  await page.getByText(/2.*40.*42/).waitFor();
  await page
    .locator('[data-orders-row="doc-prepay"]')
    .getByRole("button", { name: /SO-PREPAY/ })
    .click();
  await page.getByText(/€500.00.*€2,000.00/).waitFor();
  await page.getByRole("button", { name: "Inspect commitment", exact: true }).last().click();
  await page.getByRole("dialog").waitFor();
  assert.ok(requests.some((r) => r.path.endsWith("/inspector/commitment/commitment-prepay")));
  await page.keyboard.press("Escape");
  const inspect = page.locator("tbody").getByRole("button", { name: "Explain", exact: true });
  await inspect.focus();
  await page.keyboard.press("Enter");
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Selected order or delivery", exact: true })
    .waitFor();
  await page.keyboard.press("Escape");
  assert.equal(await inspect.evaluate((n) => n === document.activeElement), true);
  await inspect.click();
  await page.reload();
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Selected order or delivery", exact: true })
    .waitFor();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "View commitments", exact: true }).click();
  await page.waitForURL(/order=doc-c/);
  await page.locator("[data-orders-row]").first().waitFor();
  assert.ok(
    requests.some(
      (r) =>
        r.path.endsWith("/delivery-work") &&
        r.query.includes("document_id=doc-c") &&
        r.query.includes("status=all") &&
        r.query.includes("commitment_type=customer_delivery"),
    ),
  );
  await page.getByRole("button", { name: "Open commitment", exact: true }).click();
  await page.waitForURL(/commitment=customer1/);
  await page.getByRole("button", { name: "Reserve stock", exact: true }).waitFor();
  assert.ok(page.url().includes("commitment=customer1"));
  await go("supplier-orders");
  await page.getByRole("button", { name: "View commitments", exact: true }).click();
  await page.waitForURL(/order=doc-s/);
  await page.locator("[data-orders-row]").first().waitFor();
  await page.getByRole("button", { name: "Open commitment", exact: true }).click();
  await page.getByRole("button", { name: "Receive goods", exact: true }).waitFor();
  assert.equal(await page.getByRole("button", { name: "Reserve stock", exact: true }).count(), 0);
  await page.getByRole("button", { name: "Back to commitments", exact: true }).click();
  assert.ok(
    requests.some(
      (r) =>
        r.query.includes("document_id=doc-s") &&
        r.query.includes("commitment_type=supplier_delivery"),
    ),
  );
  await page.locator("tbody").getByRole("button", { name: "Explain", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Selected order or delivery", exact: true })
    .waitFor();
  assert.ok(requests.some((r) => r.path.endsWith("/inspector/commitment/supplier1")));
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Clear order filter", exact: true }).click();
  assert.equal(new URL(page.url()).searchParams.has("order"), false);
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.waitForURL(/page=2/);
  await page.getByRole("combobox", { name: "Delivery scope", exact: true }).selectOption("open");
  assert.equal(new URL(page.url()).searchParams.has("page"), false);
  await page
    .getByRole("textbox", { name: "Search orders and deliveries", exact: true })
    .fill("missing");
  await page.getByText("No matching records", { exact: true }).waitFor();
  fail = true;
  await page.reload();
  await page.getByRole("alert").waitFor();
  fail = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.getByText("No matching records", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="other"]').click();
  for (const key of ["order", "entry", "q"])
    assert.equal(new URL(page.url()).searchParams.has(key), false);
  await page.goto(`${base}/app/orders-deliveries?tenant=orders&entry=foreign`);
  await page.getByRole("dialog").getByRole("alert").waitFor();
  await page.keyboard.press("Escape");
  for (language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        for (const view of ["deliveries", "customer-orders", "supplier-orders", "readiness"]) {
          await go(view);
          assert.ok(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            `${language}/${theme}/${width}/${view}`,
          );
          await page.screenshot({
            path: `${out}/${language}-${theme}-${width}-${view}.png`,
            fullPage: true,
          });
        }
      }
  assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: exact customer/supplier order drilldown, multi-customer readiness with future dates, partial stock and prepayment evidence, Inspector, keyboard/reload, filters/paging, empty/retry/foreign/company reset, no writes and 64 localized screenshots.",
  );
} finally {
  await browser.close();
}
