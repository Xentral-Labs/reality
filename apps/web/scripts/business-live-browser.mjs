// Transport fixtures test presentation; PostgreSQL regressions prove business arithmetic.
import assert from "node:assert/strict";
import { isSearchRead } from "./shell-background-reads.mjs";
import { pathToFileURL, fileURLToPath } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const shots = fileURLToPath(
  new URL("../../../artifacts/company_simulator/screenshots/", import.meta.url),
);
const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || "/usr/bin/chromium",
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
let stale = false,
  calls = 0;
const errors = [],
  writes = [],
  inspections = [];
page.on("pageerror", (e) => errors.push(e.message));
const order = {
  document_id: "order-1",
  number: "S01",
  source_record_id: "source-1",
  party_name: "Retail North",
  received_at: "2026-10-05T10:00:00Z",
  due_at: "2026-10-05T15:00:00Z",
  open_units: "4",
  age_minutes: 30,
  flags: ["unshipped", "ready", "eligible", "received_last_hour"],
  first_dispatch_minutes: null,
  complete_dispatch_minutes: null,
  commitment_ids: ["commitment-1"],
};
const data = {
  observed_at: "2026-10-05T10:30:00Z",
  recent_documents: [
    {
      id: "order-1",
      number: "S01",
      type: "sales_order",
      party_name: "Retail North",
      amount: "40",
      currency: "EUR",
    },
  ],
  orders: [order],
  order_count: 112,
  eligible_orders: 112,
  complete_dispatch_orders: 0,
  ready_orders: 82,
  blocked_orders: 30,
  inventory: [
    {
      item_id: "item-1",
      name: "Mug",
      physical: "200",
      reserved: "200",
      available: "0",
      incoming: "0",
    },
  ],
  reservation_blocked_orders: 30,
  held_orders: 0,
  overdue_orders: 0,
  at_risk_orders: 10,
  partial_orders: 0,
  unshipped_orders: 112,
  orders_received_last_hour: 112,
  orders_completed_last_hour: 0,
  dispatch_rate_percent: 0,
  average_first_dispatch_minutes: null,
  average_complete_dispatch_minutes: null,
  complete_dispatch_sample_orders: 0,
  first_dispatch_sample_orders: 0,
  goods_flow_last_hour: [
    { item_id: "item-1", name: "Mug", sku: "MUG", received: "200", shipped: "0" },
  ],
  replenishment: [],
  open_replenishment_lines: 0,
  messages: [
    {
      source_record_id: "mail-1",
      subject: "Where is my order? <img onerror=window.injected=true>",
      body: "Please send tracking for S01.",
      direction: "incoming",
      reply_recorded: false,
      recorded_at: "2026-10-05T10:29:00Z",
    },
  ],
  local_unread_messages: 210,
  mailbox_counts: { incoming: 210, waiting: 210, outgoing: 1 },
  pending_decisions: 0,
  oldest_open_order_minutes: 30,
  bottleneck: "dispatch",
};
await page.route("**/api/**", async (route) => {
  const r = route.request(),
    u = new URL(r.url()),
    p = u.pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (r.method() !== "GET" && !isSearchRead(p)) {
    writes.push(p);
    return reply({}, 400);
  }
  if (p === "/api/auth/me")
    return reply({
      id: "owner",
      email: "owner@example.test",
      status: "active",
      language: "de",
      locale: "de-DE",
      timezone: "UTC",
    });
  if (p === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: "company", name: "Northstar Commerce", role: "owner" }],
      default_tenant_id: "company",
    });
  if (p.endsWith("/application-reference")) return reply({ workspaces: [], commands: [] });
  if (p.endsWith("/interactions/business")) {
    calls++;
    return stale
      ? reply({}, 503)
      : reply({
          ...data,
          orders: ["reservation_blocked", "complete_dispatch_sample"].includes(
            u.searchParams.get("order_filter"),
          )
            ? []
            : [order],
          messages:
            u.searchParams.get("mail_filter") === "outgoing"
              ? [
                  {
                    source_record_id: "reply-1",
                    subject: "Reply to S01",
                    body: "We will confirm the actual shipment.",
                    direction: "outgoing",
                    recorded_at: data.observed_at,
                    original: data.messages[0],
                  },
                ]
              : data.messages,
        });
  }
  if (p.includes("/inspector/")) {
    inspections.push(p);
    return reply({
      title: "Exact Reality record",
      subtitle: "Evidence",
      meaning: "Original business record",
      sections: p.includes("document/order-1")
        ? [
            {
              title: "Order progress",
              rows: [
                {
                  label: "Reserved",
                  value: "4 pieces",
                  tone: "default",
                  link: { kind: "commitment", id: "commitment-1" },
                },
              ],
            },
            {
              title: "Dispatch",
              rows: [
                {
                  label: "Shipment",
                  value: "SHIP-001",
                  tone: "default",
                  link: { kind: "shipment", id: "shipment-1" },
                },
              ],
            },
            {
              title: "Delivery note",
              rows: [{ label: "Delivery note", value: "DN-001", tone: "default", link: null }],
            },
            {
              title: "Tracking",
              rows: [
                {
                  label: "Tracking",
                  value: "TRACK-001",
                  tone: "default",
                  link: { kind: "shipment_package", id: "package-1" },
                },
              ],
            },
            {
              title: "Invoices",
              rows: [
                {
                  label: "Invoice",
                  value: "INV-001",
                  tone: "default",
                  link: { kind: "document", id: "invoice-1" },
                },
              ],
            },
          ]
        : [],
      technical_rows: [],
      metrics: [],
      source_payload: null,
    });
  }
  if (isSearchRead(p)) return reply({ items: [], hits: [], target: null });
  return reply({}, 404);
});
try {
  await page.goto(`${base}/app/inspector?tenant=company&inspector_view=business`);
  const dashboard = page.locator("[data-business-live]");
  await dashboard.waitFor();
  await mkdir(shots, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 2200 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page
    .locator("[data-reality-inspector]")
    .screenshot({ path: shots + "reality-business.png" });
  assert.match(await dashboard.innerText(), /82/);
  assert.match(await dashboard.innerText(), /30/);
  const summaryTop = await dashboard.getByText("Geschäftsfluss", { exact: true }).boundingBox();
  const mailTile = dashboard.getByRole("button", { name: /210.*Eingegangene Nachrichten/ });
  const mailTop = await mailTile.boundingBox();
  assert.ok(mailTop.y > summaryTop.y);
  await mailTile.click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: data.messages[0].subject, exact: true })
    .waitFor();
  assert.equal(
    await dashboard
      .getByRole("tab", { name: "Übersicht", exact: true })
      .getAttribute("aria-selected"),
    "true",
  );
  await page.keyboard.press("Escape");
  await dashboard.getByRole("button", { name: /210.*Noch ohne Antwort/ }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: data.messages[0].subject, exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByText("Antwort ausstehend (Simulator)", { exact: true })
    .waitFor();
  assert.equal(await page.getByRole("dialog").count(), 1);
  await page.keyboard.press("Escape");
  await dashboard.getByRole("button", { name: /1.*Gesendete Nachrichten/ }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Reply to S01", exact: true })
    .waitFor();
  await page.keyboard.press("Escape");
  await dashboard.getByRole("tab", { name: "Nachrichten", exact: true }).click();
  await dashboard.getByRole("button", { name: /Eingehend.*210/ }).click();
  assert.match(await dashboard.innerText(), /210/);
  await dashboard.getByRole("button", { name: data.messages[0].subject, exact: true }).click();
  await page
    .getByRole("dialog")
    .getByText("Antwort ausstehend (Simulator)", { exact: true })
    .waitFor();
  await page
    .getByRole("dialog")
    .getByText("Zugehörige eingehende Nachricht", { exact: true })
    .waitFor();
  await page.keyboard.press("Escape");
  await dashboard.getByRole("button", { name: /Ausgehend.*1/ }).click();
  await dashboard.getByRole("button", { name: "Reply to S01", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByText("Zugehörige eingehende Nachricht", { exact: true })
    .waitFor();
  assert.match(await page.getByRole("dialog").innerText(), /Please send tracking for S01/);
  await page.screenshot({ path: shots + "reality-business-mail-thread.png", fullPage: true });
  await page.keyboard.press("Escape");
  await dashboard.getByRole("tab", { name: "Übersicht", exact: true }).click();
  assert.equal(await page.locator("img[onerror]").count(), 0);
  await dashboard.getByRole("button", { name: /82.*Versandbereit/ }).click();
  await page.getByRole("dialog", { name: "Versandbereit", exact: true }).waitFor();
  await page.getByRole("dialog").getByRole("button", { name: "S01", exact: true }).click();
  await page.getByText("Exact Reality record", { exact: true }).waitFor();
  assert.ok(inspections.some((p) => p.includes("order-1")));
  await page.locator("[data-order-progress]").getByText("TRACK-001", { exact: true }).waitFor();
  await page.locator("[data-order-progress]").getByText("INV-001", { exact: true }).waitFor();
  await page.screenshot({ path: shots + "reality-order-progress.png", fullPage: true });
  await page.locator("[data-order-progress]").getByText("TRACK-001", { exact: true }).click();
  await page.waitForFunction(() => document.querySelector("[data-order-progress]") === null);
  assert.ok(inspections.some((p) => p.includes("package-1")));
  await page.keyboard.press("Escape");
  await page.goto(`${base}/app/inspector?tenant=company&inspector_view=business`);
  await dashboard.waitFor();
  await dashboard.getByRole("button", { name: /30.*Reservierungen fehlen/ }).click();
  const empty = page.getByRole("dialog", { name: "Reservierungen fehlen", exact: true });
  await empty.getByText("Keine passenden Aufträge.", { exact: true }).waitFor();
  await page.screenshot({ path: shots + "reality-business-orders-dialog.png", fullPage: true });
  await page.keyboard.press("Escape");
  await empty.waitFor({ state: "hidden" });
  assert.match(await page.locator(":focus").innerText(), /Reservierungen fehlen/);
  await dashboard.getByRole("tab", { name: "Aufträge & Bestellungen", exact: true }).click();
  await dashboard.getByRole("button", { name: "S01", exact: true }).waitFor();
  await dashboard.getByRole("tab", { name: "Bestand", exact: true }).click();
  assert.match(await dashboard.getByRole("tabpanel").innerText(), /Mug/);
  assert.equal(
    await dashboard.getByRole("tabpanel").getByText("Versandbereit", { exact: true }).count(),
    0,
  );
  await page.screenshot({ path: shots + "reality-business-stock-tab.png", fullPage: true });
  await dashboard.getByRole("tab", { name: "Übersicht", exact: true }).click();
  await dashboard.getByRole("button", { name: "Komplettversand", exact: true }).click();
  await page.getByRole("dialog").getByText("Keine passenden Aufträge.", { exact: true }).waitFor();
  await page.getByRole("dialog").getByRole("button", { name: "Schließen", exact: true }).click();
  stale = true;
  await dashboard
    .getByText("Aktualisierung fehlgeschlagen.", { exact: false })
    .waitFor({ timeout: 12000 });
  assert.match(await dashboard.innerText(), /82/);
  await mkdir(shots, { recursive: true });
  await page.screenshot({ path: shots + "reality-business-stale.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  assert.deepEqual(errors, []);
  assert.deepEqual(writes, []);
  assert.ok(calls >= 3);
  console.log(
    "PASS Business dashboard: counts, filtered drilldown, Inspector, inert mail, stale retention, mobile width, read-only requests",
  );
} finally {
  await browser.close();
}
