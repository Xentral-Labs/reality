import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const pager = (size, total) => ({
  number: 1,
  size,
  total,
  pages: Math.ceil(total / size),
  has_previous: false,
  has_next: size < total,
});
// The work behind each tab, keyed by the read its register pages.
const work = {
  customerCommitments: 7,
  supplierCommitments: 4,
  findings: 14,
  decisions: 3,
  shortages: 2,
  outstanding: 5,
};
try {
  for (const [language, theme] of [
    ["en", "light"],
    ["de", "dark"],
  ]) {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.addInitScript((theme) => localStorage.setItem("reality.theme", theme), theme);
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const counted = [];
    await page.route("**/api/**", async (route) => {
      const u = new URL(route.request().url()),
        p = u.pathname,
        q = u.searchParams;
      const size = Number(q.get("size") || 50);
      const reply = (data) =>
        route.fulfill({ contentType: "application/json", body: JSON.stringify(data) });
      const list = (total, extra = {}) => {
        if (size === 1) counted.push(`${p}?${q}`);
        return reply({ items: [], totals: [], page: pager(size, total), ...extra });
      };
      if (p === "/api/auth/me")
        return reply({
          id: "owner",
          email: "owner@example.test",
          status: "active",
          language,
          locale: language === "de" ? "de-DE" : "en-GB",
          timezone: "UTC",
        });
      if (p === "/api/v1/bootstrap")
        return reply({
          tenants: [{ id: "demo", name: "Northstar Demo", role: "owner" }],
          default_tenant_id: "demo",
        });
      if (p.endsWith("/copilot"))
        return reply({
          sessions: [],
          active_session_id: null,
          messages: [],
          proposals: [],
          suggestions: [],
          has_archived: false,
        });
      if (p.endsWith("/dashboard"))
        return reply({
          totals: { open_deliveries: 7, exceptions: 14, pending_decisions: work.decisions },
        });
      if (p.endsWith("/activity-volume") || p.endsWith("/readiness"))
        return route.fulfill({ status: 503, body: "Unavailable in tab count fixture" });
      if (p.endsWith("/change-proposals")) return list(work.decisions);
      if (p.endsWith("/delivery-work"))
        return list(
          q.get("status") !== "open"
            ? 99
            : q.get("commitment_type") === "supplier_delivery"
              ? work.supplierCommitments
              : work.customerCommitments,
        );
      if (p.endsWith("/attention")) return list(work.findings, { observed_at: null });
      if (p.endsWith("/warehouse/stock"))
        return list(q.get("state") === "shortage" ? work.shortages : 40, {
          scope: { view: "stock" },
        });
      if (/\/warehouse\/(reservations|movements)$/.test(p))
        return list(11, { scope: { view: p.split("/").pop() } });
      if (p.endsWith("/finance/open-items"))
        return list(
          q.get("item_status") === "outstanding" && q.get("flow") === "receivable"
            ? work.outstanding
            : 60,
        );
      return list(0, { workspaces: [], commands: [] });
    });

    const tabs = page.locator("[data-shell-header] .register-tabs");
    const countAfter = (label) =>
      tabs.locator(`button:has-text("${label}") + .shell-tab-work-count [data-tab-work-count]`);
    const visit = async (path, expected, absent = []) => {
      await page.goto(`${base}/app/${path}${path.includes("?") ? "&" : "?"}tenant=demo`);
      await tabs.waitFor({ timeout: 12000 });
      for (const [label, value, tone] of expected) {
        const badge = countAfter(label);
        await badge.waitFor({ timeout: 5000 }).catch(async (error) => {
          console.log(path, label, await tabs.innerHTML());
          throw error;
        });
        assert.equal(await badge.innerText(), value, `${path} ${label}`);
        assert.equal(await badge.getAttribute("data-tone"), tone ?? null, `${path} ${label} tone`);
        const described = await tabs
          .locator(`button:has-text("${label}")`)
          .evaluate(
            (b) => document.getElementById(b.getAttribute("aria-describedby"))?.textContent,
          );
        assert.ok(described?.endsWith(`: ${value}`), `${path} ${label} description ${described}`);
      }
      await page.waitForTimeout(400);
      for (const label of absent)
        assert.equal(await countAfter(label).count(), 0, `${path} ${label} has no work count`);
    };
    const de = language === "de";
    const L = (en, german) => (de ? german : en);

    // Inbox: every queue states its open work while another tab is open.
    await visit(
      "decisions",
      [
        [L("Commitments", "Commitments"), "7"],
        [L("Exceptions", "Ausnahmen"), "14"],
      ],
      [L("Decisions", "Entscheidungen")],
    );
    await visit("attention", [
      ["Commitments", "7"],
      [L("Decisions", "Entscheidungen"), "3", "accent"],
    ]);
    // Who must act comes first: Welcome, Decisions, Exceptions, Commitments.
    assert.deepEqual(
      await tabs.locator("button").allInnerTexts(),
      de
        ? ["Willkommen", "Entscheidungen", "Ausnahmen", "Commitments"]
        : ["Welcome", "Decisions", "Exceptions", "Commitments"],
    );
    // The open Decisions tab keeps the accent while decisions wait.
    await page.goto(`${base}/app/decisions?tenant=demo`);
    const accent = await page
      .locator(
        '[data-work-tone="accent"][aria-pressed="true"] + .shell-tab-count [data-page-record-count]',
      )
      .evaluate((node) => getComputedStyle(node).backgroundColor)
      .catch(() => "");
    assert.equal(accent, "rgb(99, 91, 255)", "open Decisions count carries the accent");

    // Welcome shows the same order; the decisions tile asks for attention while any wait.
    await page.goto(`${base}/app/?tenant=demo`);
    const tiles = page.locator("[data-home-work]");
    await tiles.first().waitFor({ timeout: 12000 });
    assert.deepEqual(await tiles.evaluateAll((nodes) => nodes.map((n) => n.dataset.homeWork)), [
      "pending_decisions",
      "exceptions",
      "open_deliveries",
    ]);
    const waiting = page.locator("[data-home-work][data-waiting]");
    await waiting.waitFor({ timeout: 5000 });
    assert.equal(await waiting.getAttribute("data-home-work"), "pending_decisions");
    assert.ok((await waiting.innerText()).includes(L("waiting for you", "warten auf dich")));

    // Sales and Purchasing: the Commitments tab of each direction; orders and shipments stay quiet.
    await visit(
      "orders-deliveries?orders_view=customer-orders",
      [["Commitments", "7"]],
      [L("Customer orders", "Kundenaufträge"), L("Shipments", "Sendungen")],
    );
    await visit(
      "orders-deliveries?orders_view=supplier-orders&delivery_type=supplier_delivery",
      [["Commitments", "4"]],
      [L("Shipments", "Sendungen")],
    );
    await visit("orders-deliveries?orders_view=deliveries", [], ["Commitments"]);

    // Warehouse: stock warns about overallocation; reservations and movements stay quiet.
    await visit(
      "warehouse?warehouse_view=movements",
      [[L("Stock", "Bestand"), "2", "warning"]],
      [L("Reservations", "Reservierungen")],
    );

    // Finance: open items states outstanding receivables; the other registers stay quiet.
    await visit(
      "finance?finance_view=payments",
      [[L("Open items", "Offene Posten"), "5"]],
      [L("Journal", "Journal"), L("Balances", "Salden")],
    );

    // Master data counts stock, not work: no tab states a count while inactive.
    await page.goto(`${base}/app/master-data?tenant=demo`);
    await tabs.waitFor({ timeout: 12000 });
    await page.waitForTimeout(400);
    assert.equal(await tabs.locator("[data-tab-work-count]").count(), 0);

    // Every work count read one row with the same filters its register opens with.
    const reads = new Set(
      counted.map((read) => read.replace(/[?&](size|sort|sort_direction)=[^&]*/g, "")),
    );
    for (const expected of [
      "/api/tenants/demo/delivery-work?q=&page=1&status=open&commitment_type=customer_delivery&document_id=",
      "/api/tenants/demo/delivery-work?q=&page=1&status=open&commitment_type=supplier_delivery&document_id=",
      "/api/tenants/demo/finance/open-items?q=&flow=receivable&item_status=outstanding&page=1",
    ])
      assert.ok(reads.has(expected), `missing ${expected} in ${[...reads].join("\n")}`);
    assert.ok(
      [...reads].some(
        (read) => read.includes("/warehouse/stock") && read.includes("state=shortage"),
      ),
    );
    assert.ok([...reads].some((read) => read.includes("/attention")));

    assert.deepEqual(errors, []);
    console.log(
      `PASS ${language} ${theme}: inbox, sales, purchasing, warehouse, finance, master data`,
    );
    await page.close();
  }
} finally {
  await browser.close();
}
