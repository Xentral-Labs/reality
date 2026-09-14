// Read-only HTTP fixtures; canonical financial semantics remain covered by PostgreSQL tests.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const requests = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  fail = false;
const tenant = "finance_fixture";
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  requests.push({ path, method: req.method(), query: url.search });
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
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: tenant, name: "Northstar Commerce" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.includes("/finance/")) {
    if (fail) return reply({ detail: "Finance unavailable" }, 503);
    const view = path.split("/finance/")[1],
      n = Number(url.searchParams.get("page") || 1),
      empty = url.searchParams.get("q") === "missing";
    const pager = {
      number: n,
      size: 50,
      total: empty ? 0 : 51,
      pages: empty ? 1 : 2,
      has_previous: n > 1,
      has_next: !empty && n === 1,
    };
    const item = {
      document_id: `invoice_${n}`,
      number: `INV-${n}`,
      document_type:
        url.searchParams.get("flow") === "payable" ? "supplier_invoice" : "sales_invoice",
      document_date: "2026-09-07",
      party: "Schneider",
      party_id: "party_1",
      gross: "600",
      settled: "200",
      open: "400",
      currency: "EUR",
      status: "partial",
    };
    const payment = {
      id: `payment_${n}`,
      effective_at: "2026-09-07T10:00:00Z",
      direction: "incoming",
      document_id: "payment_doc",
      reference: "PAY-1",
      party: "Schneider",
      currency: "EUR",
      amount: "200",
      allocated: "0",
      unallocated: "0",
      posting_group_id: "posting_1",
      reversal_role: "reversed_original",
    };
    const journal = {
      id: `ledger_${n}`,
      effective_at: "2026-09-07T10:00:00Z",
      account: "cash",
      debit_credit: "debit",
      amount: "200",
      currency: "EUR",
      posting_group_id: "posting_1",
      document_id: "payment_doc",
      inspect_kind: "ledger_entry",
      inspect_id: `ledger_${n}`,
    };
    return reply({
      items: empty
        ? []
        : Array.from({ length: 50 }, (_, index) => ({
            ...(view === "open-items" ? item : view === "payments" ? payment : journal),
            id: `fixture-${index}`,
          })),
      page: pager,
      totals: empty
        ? []
        : view === "open-items"
          ? [
              { currency: "EUR", gross: "30600", settled: "10200", open: "20400" },
              { currency: "USD", gross: "100", settled: "0", open: "100" },
            ]
          : view === "journal"
            ? [
                { currency: "EUR", debit: "10200", credit: "0", balance: "10200" },
                { currency: "USD", debit: "100", credit: "100", balance: "0" },
              ]
            : [{ currency: "EUR", amount: "999999", allocated: "0", unallocated: "999999" }],
    });
  }
  if (path.includes("/inspector/"))
    return reply({
      title: "Financial evidence",
      subtitle: "Schneider",
      meaning: "Recorded values",
      sections: [],
      technical_rows: [],
      source_payload: '{"untrusted":"<script>alert(1)</script>"}',
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});

await mkdir("/private/tmp/content-heading-screens", { recursive: true });
const checkPaths = [
  "/app/finance?tenant=finance_fixture",
  "/app/finance?tenant=finance_fixture&finance_view=payments",
  "/app/finance?tenant=finance_fixture&finance_view=journal",
];
for (const width of [1440, 390]) {
  await page.setViewportSize({ width, height: 1000 });
  for (let index = 0; index < checkPaths.length; index++) {
    await page.goto((process.env.UNIFIED_APP_URL || "http://localhost:8087") + checkPaths[index], {
      waitUntil: "domcontentloaded",
    });
    await page.locator("[data-shell-header]").waitFor();
    await page.locator("tbody tr").first().waitFor();
    assert.equal(await page.locator("[data-page-introduction] h1:visible").count(), 1);
    assert.equal(await page.locator("[data-page-description]:visible").count(), 1);
    await page.waitForTimeout(150);
    const footer = page.locator(".erp-register-footer");
    const scroll = page.locator(".erp-table-scroll");
    if (width < 700) {
      await footer.scrollIntoViewIfNeeded();
      await page.waitForTimeout(150);
    }
    const checkEdges = async () => {
      const edges = await footer.evaluate((el) => {
        const f = el.getBoundingClientRect(),
          m = document.querySelector("main").getBoundingClientRect();
        return { left: f.left - m.left, right: f.right - m.right, bottom: f.bottom - innerHeight };
      });
      assert.ok(
        Math.abs(edges.left) < 2 && Math.abs(edges.right) < 2 && Math.abs(edges.bottom) < 2,
        JSON.stringify(edges),
      );
    };
    await checkEdges();
    if (width >= 1024) {
      await page.getByRole("button", { name: "Hide chat", exact: true }).click();
      await page.waitForTimeout(150);
      await checkEdges();
      assert.ok(
        Math.abs(await footer.evaluate((el) => el.getBoundingClientRect().right - innerWidth)) < 2,
      );
      await page.getByRole("button", { name: "Show chat", exact: true }).click();
      await page.waitForTimeout(150);
      await checkEdges();
    }
    const bottom = await footer.evaluate((el) => el.getBoundingClientRect().bottom);
    assert.ok(bottom <= 1000 && bottom >= 960, `footer bottom ${bottom} at ${width}`);
    await scroll.evaluate((el) => (el.scrollTop = 100));
    await page.waitForTimeout(50);
    assert.ok(await scroll.evaluate((el) => el.scrollTop > 0), "Rows must scroll independently");
    assert.ok(
      Math.abs((await footer.evaluate((el) => el.getBoundingClientRect().bottom)) - bottom) < 2,
    );

    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
      checkPaths[index],
    );
    await page.screenshot({
      path: `/private/tmp/content-heading-screens/finance-${index}-${width}.png`,
      fullPage: true,
    });
  }
}
await browser.close();
console.log("finance populated layout checks passed");
