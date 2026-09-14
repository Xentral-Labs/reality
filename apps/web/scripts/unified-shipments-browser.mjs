// Stateful browser proof for Spec 173; PostgreSQL tests prove the business effects.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const reference = JSON.parse(
  readFileSync(new URL("./fixtures/action-reference.json", import.meta.url), "utf8"),
);
reference.discovery = JSON.parse(
  readFileSync(
    new URL("../../../packages/reality-core/config/action_discovery.json", import.meta.url),
    "utf8",
  ),
);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const errors = [];
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.on("pageerror", (error) => errors.push(error.message));
page.setDefaultTimeout(10000);
let language = "en";
let executed = false;

const shipment = {
  id: "shp_out",
  direction: "outbound",
  purpose: "customer_delivery",
  counterparty_id: "customer",
  created_at: "2026-09-11T10:00:00Z",
  source_record_id: null,
  packages: [{ id: "pkg_1", carrier: "DHL", tracking_number: "TRACK-173", source_record_id: null }],
  movements: [
    {
      id: "mov_1",
      package_id: "pkg_1",
      type: "shipment",
      item_id: "LIGHT",
      quantity: "4",
      occurred_at: "2026-09-11T10:00:00Z",
    },
  ],
  events: [
    {
      id: "sev_1",
      package_id: "pkg_1",
      event_type: "in_transit",
      reporter_type: "carrier",
      occurred_at: "2026-09-11T11:00:00Z",
      location_text: "Bologna hub",
      source_record_id: null,
    },
  ],
  observations: {
    announced: true,
    dispatched: true,
    received: false,
    externally_delivered: false,
    has_exception: false,
  },
  quantities: {
    promised: "4",
    announced: null,
    dispatched: "4",
    externally_delivered: null,
    received: null,
  },
  discrepancies: {
    external_delivery_without_warehouse_receipt: false,
    warehouse_receipt_without_external_delivery: false,
  },
};
const pager = { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false };
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
      display_name: "Operator",
      status: "active",
      language,
      locale: language === "de" ? "de-DE" : "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: "company", name: "Northstar", role: "owner" }],
      default_tenant_id: "company",
    });
  if (path.endsWith("/application-reference")) return reply(reference);
  if (path.endsWith("/shipments")) return reply({ items: [shipment], page: pager });
  if (path.endsWith("/delivery-work")) return reply({ items: [], page: { ...pager, total: 0 } });
  if (path.includes("/inspector/"))
    return reply({
      title: "Shipment",
      subtitle: "TRACK-173",
      meaning: "Physical consignment",
      sections: [],
      metrics: [],
      technical_rows: [],
    });
  if (path.endsWith("/delivery-actions/prepare"))
    return reply({
      id: "act_173",
      tool: JSON.parse(request.postData()).tool,
      status: "proposed",
      review: {
        token: "token-173",
        intent: JSON.parse(request.postData()).arguments,
        effect: { shipment_action: "reviewed" },
        state: {},
      },
      receipt: null,
      verification: "pending",
      links: [],
    });
  if (path.endsWith("/change-proposals/act_173/approve")) {
    executed = true;
    return reply({
      id: "act_173",
      status: "executed",
      output: { shipment_id: "shp_new", package_id: "pkg_new", event_id: "sev_new" },
    });
  }
  if (
    path.endsWith("/delivery-actions/act_173") ||
    path.endsWith("/delivery-actions/act_173/review")
  )
    return reply({
      id: "act_173",
      tool: "shipment_notice_record",
      status: executed ? "executed" : "proposed",
      review: { token: "token-173", intent: {}, effect: {}, state: {} },
      receipt: executed ? { shipment_id: "shp_new" } : null,
      verification: executed ? "verified" : "pending",
      links: [],
    });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});

try {
  await page.goto(
    `${base}/app/orders-deliveries?tenant=company&orders_view=shipments&delivery_type=customer_delivery`,
  );
  await page.locator("[data-shipment-row=shp_out]").waitFor();
  assert.equal(await page.getByText("TRACK-173", { exact: true }).count(), 1);
  await page.getByRole("button", { name: /TRACK-173/ }).click();
  await page.getByText("Physical contents", { exact: true }).waitFor();
  await page.getByText("Tracking observations", { exact: true }).waitFor();

  await page.getByText("Actions", { exact: true }).first().click();
  await page.getByRole("button", { name: "Record shipment notice", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Counterparty ID").fill("supplier");
  await dialog.getByLabel("Tracking number").fill("IN-NEW");
  await dialog.getByRole("button", { name: "Review", exact: true }).click();
  await dialog.getByText("Review exact effect", { exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
  await dialog.getByText("Recorded", { exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Close", exact: true }).click();

  const forms = [
    ["Dispatch package", "Movement inputs (JSON)"],
    ["Receive package", "Movement inputs (JSON)"],
    ["Record tracking event", "Shipment ID"],
    ["Correct tracking event", "Event ID"],
  ];
  for (const [action, field] of forms) {
    await page.getByText("Actions", { exact: true }).first().click();
    await page.getByRole("button", { name: action, exact: true }).click();
    const fieldLocator =
      field === "Movement inputs (JSON)"
        ? page.getByRole("dialog").locator("textarea")
        : page.getByRole("dialog").getByLabel(field, { exact: true });
    await fieldLocator.waitFor();
    if (action === "Dispatch package") {
      await fieldLocator.fill("not-json");
      await page.getByRole("dialog").getByRole("button", { name: "Review", exact: true }).click();
      await page.getByRole("alert").waitFor();
    }
    await page.keyboard.press("Escape");
    await page.getByRole("dialog").waitFor({ state: "detached" });
  }

  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.locator("[data-shipment-row=shp_out]").count(), 1);
  for (const [locale, label] of [
    ["de", "Sendungen"],
    ["nl", "Zendingen"],
    ["es", "Envíos"],
    ["en", "Shipments"],
  ]) {
    language = locale;
    await page.reload();
    await page.getByRole("button", { name: label, exact: true }).waitFor();
  }
  await page.evaluate(() => localStorage.setItem("reality.theme", "light"));
  await page.reload();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "light");
  await page.evaluate(() => localStorage.setItem("reality.theme", "dark"));
  await page.reload();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "dark");
  assert.deepEqual(errors, []);
  console.log(
    "Shipments browser journey passed: five forms, confirmation/error, desktop/mobile, keyboard, four locales and light/dark media.",
  );
} finally {
  await browser.close();
}
