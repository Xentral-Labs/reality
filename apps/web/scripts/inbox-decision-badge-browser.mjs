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
try {
  for (const language of ["en", "de"])
    for (const collapsed of [false, true]) {
      const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
      await page.addInitScript(
        (collapsed) => localStorage.setItem("reality.navigation.collapsed", String(collapsed)),
        collapsed,
      );
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      const pending = { demo: 3, other: 120, empty: 0 };
      const reads = [];
      await page.route("**/api/**", async (route) => {
        const u = new URL(route.request().url()),
          p = u.pathname;
        const reply = (data) =>
          route.fulfill({ contentType: "application/json", body: JSON.stringify(data) });
        const rejected = p.match(/^\/api\/tenants\/([^/]+)\/change-proposals\/[^/]+\/reject$/);
        if (rejected && route.request().method() === "POST") {
          pending[rejected[1]] -= 1;
          return reply({ status: "rejected" });
        }
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
            tenants: [
              { id: "demo", name: "Northstar Demo", role: "owner" },
              { id: "other", name: "Other Company", role: "owner" },
              { id: "empty", name: "Quiet Company", role: "owner" },
            ],
            default_tenant_id: "demo",
          });
        const queue = p.match(/^\/api\/tenants\/([^/]+)\/change-proposals$/);
        if (queue) {
          const size = Number(u.searchParams.get("size") || 50);
          reads.push({ tenant: queue[1], size, status: u.searchParams.get("status") });
          return reply({ items: [], page: pager(size, pending[queue[1]]) });
        }
        if (p.endsWith("/dashboard"))
          return reply({ totals: { open_deliveries: 0, exceptions: 0, pending_decisions: 0 } });
        if (p.endsWith("/activity-volume") || p.endsWith("/readiness"))
          return route.fulfill({ status: 503, body: "Unavailable in badge fixture" });
        if (p.endsWith("/copilot"))
          return reply({
            sessions: [],
            active_session_id: null,
            messages: [],
            proposals: [],
            suggestions: [],
            has_archived: false,
          });
        return reply({ items: [], workspaces: [], commands: [], page: pager(50, 0) });
      });
      const inbox = page.locator('[data-primary-navigation] a[aria-label="Inbox"]');
      const badge = inbox.locator("[data-navigation-count]");
      const open = async (tenant) => {
        await page.goto(`${base}/app/facts?tenant=${tenant}`);
        await inbox.waitFor({ timeout: 12000 });
      };

      await open("demo");
      await badge.waitFor({ timeout: 5000 });
      assert.equal(await badge.innerText(), "3");
      assert.ok(await badge.isVisible(), "the count stays visible on the collapsed rail");
      assert.equal(await badge.getAttribute("aria-hidden"), "true");
      const described = await inbox.evaluate(
        (a) => document.getElementById(a.getAttribute("aria-describedby"))?.textContent,
      );
      assert.equal(
        described,
        `${language === "de" ? "Ausstehende Entscheidungen" : "Pending decisions"}: 3`,
      );
      assert.ok(reads.length >= 1);
      for (const read of reads) {
        assert.equal(read.size, 1, "the badge reads one row, never a page");
        assert.equal(read.status, "pending");
      }
      if (!collapsed) {
        const [label, count] = await Promise.all([
          inbox.locator("[data-navigation-label]").boundingBox(),
          badge.boundingBox(),
        ]);
        assert.ok(count.x > label.x + label.width, "the count sits after the label");
      }

      // A decision settled anywhere in this browser moves the count without reload.
      await page.evaluate(async () => {
        const { api } = await import("/src/api.ts");
        await api.rejectProposal("demo", "p0", null);
      });
      await page.waitForFunction(
        () =>
          document.querySelector(
            '[data-primary-navigation] a[aria-label="Inbox"] [data-navigation-count]',
          )?.textContent === "2",
        null,
        { timeout: 5000 },
      );

      // The Decisions tab keeps the waiting count visible from the other Inbox tabs.
      await page.goto(`${base}/app/attention?tenant=demo`);
      const tabCount = page.locator("[data-shell-header] [data-tab-work-count]");
      await tabCount.waitFor({ timeout: 5000 });
      assert.equal(await tabCount.innerText(), "2");
      const [decisionsTab, tabBadge] = await Promise.all([
        page
          .locator("[data-shell-header] .register-tabs button")
          .filter({ hasText: language === "de" ? "Entscheidungen" : "Decisions" })
          .boundingBox(),
        tabCount.boundingBox(),
      ]);
      assert.ok(tabBadge.x >= decisionsTab.x, "the count follows the Decisions tab");
      await page.goto(`${base}/app/decisions?tenant=demo`);
      await page.locator("[data-shell-header] .register-tabs").waitFor();
      await page.waitForTimeout(300);
      assert.equal(await tabCount.count(), 0, "the open tab shows the register count instead");

      // Each company states its own count; a large queue reads 99+; none reads nothing.
      await open("other");
      await page.waitForFunction(
        () =>
          document.querySelector("[data-primary-navigation] [data-navigation-count]")
            ?.textContent === "99+",
        null,
        { timeout: 5000 },
      );
      assert.ok(reads.some((read) => read.tenant === "other"));
      const quiet = page.waitForResponse((r) =>
        r.url().includes("/tenants/empty/change-proposals"),
      );
      await open("empty");
      await quiet;
      await page.waitForTimeout(300);
      assert.equal(await badge.count(), 0, "no badge when nothing waits");
      assert.equal(await inbox.getAttribute("aria-describedby"), null);

      assert.deepEqual(errors, []);
      await page.close();
    }
  console.log("inbox decision badge: ok");
} finally {
  await browser.close();
}
