import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
await mkdir("/private/tmp/reality-work-lists", { recursive: true });
const pager = (n, size, total) => ({
  number: n,
  size,
  total,
  pages: Math.ceil(total / size),
  has_previous: n > 1,
  has_next: n * size < total,
});
try {
  for (const language of ["en", "de"])
    for (const mobile of [false, true])
      for (const theme of ["light", "dark"]) {
        const page = await browser.newPage({
          viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 },
        });
        await page.addInitScript((theme) => localStorage.setItem("reality.theme", theme), theme);
        let writes = 0;
        const errors = [];
        page.on("pageerror", (e) => errors.push(e.message));
        const delivery = (i, side = "customer_delivery") => ({
          id: `c${i}`,
          type: side,
          tenant_id: "demo",
          counterparty: `${side === "customer_delivery" ? "Northstar Retail" : "Supplier Studio"} ${i + 1}`,
          item: "Cotton shirt",
          unit: "pcs",
          open: "24",
          promised: "30",
          reserved: "6",
          fulfilled: "6",
          due_at: "2026-09-08T09:00:00Z",
          status: "open",
          item_id: "item",
          party_id: "party",
          location_id: "loc",
          location: "Main warehouse",
          document_id: null,
          document_line_id: null,
        });
        await page.route("**/api/**", async (route) => {
          const u = new URL(route.request().url()),
            p = u.pathname;
          const reply = (data) =>
            route.fulfill({ contentType: "application/json", body: JSON.stringify(data) });
          if (route.request().method() !== "GET") {
            writes++;
            return reply({});
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
              tenants: [{ id: "demo", name: "Northstar Demo", role: "owner" }],
              default_tenant_id: "demo",
            });
          if (p.endsWith("/copilot"))
            return reply({
              sessions: [],
              messages: [],
              proposals: [],
              suggestions: [],
              has_archived: false,
            });
          if (p.includes("/delivery-work/"))
            return reply({
              case: { ...delivery(0), blockers: [] },
              inventory: { physical: "100", reserved: "6", available: "94" },
              holds: [],
              links: [],
              history: { items: [], has_more: false },
              observation: { observed_at: new Date().toISOString(), evidence_available: false },
            });
          if (p.includes("/attention/"))
            return reply({
              id: p.split("/").pop(),
              severity: "high",
              title: "Stock shortage",
              context: "Northstar Retail · Cotton shirt",
              impact: "24 pieces missing",
              guidance: "Review the supporting records.",
              target: { kind: "commitment", id: "c0" },
              cause_ids: [],
              causal_values: {},
              trace: [],
            });
          if (p.includes("/inspector/"))
            return reply({
              title: "Commitment preview",
              subtitle: "Northstar Retail · Cotton shirt",
              meaning: "This commitment remains open.",
              sections: [{ title: "Position", rows: [{ label: "Open", value: "24 pcs" }] }],
              technical_rows: [],
              source_payload: null,
            });
          if (["/delivery-work", "/attention", "/change-proposals"].some((s) => p.endsWith(s))) {
            const n = Number(u.searchParams.get("page") || 1),
              size = Number(u.searchParams.get("size") || 50),
              total = u.searchParams.get("q") || u.searchParams.get("tool") ? 1 : 120;
            if (p.endsWith("/delivery-work")) assert.equal(u.searchParams.get("status"), "open");
            if (p.endsWith("/change-proposals"))
              assert.equal(u.searchParams.get("status"), "pending");
            const items = Array.from({ length: Math.min(size, total - (n - 1) * size) }, (_, j) => {
              const i = (n - 1) * size + j;
              return p.endsWith("/delivery-work")
                ? delivery(i, u.searchParams.get("commitment_type"))
                : p.endsWith("/attention")
                  ? {
                      id: `e${i}`,
                      severity: "high",
                      title: "Stock shortage",
                      context: "Northstar Retail · Cotton shirt",
                      impact: "24 pieces missing",
                      target: { kind: "commitment", id: "c0" },
                    }
                  : {
                      id: `p${i}`,
                      tool: "reserve",
                      status: "proposed",
                      input: { quantity: "24", unit: "pcs" },
                      actor_type: "human",
                      created_at: "2026-09-08T09:00:00Z",
                    };
            });
            return reply({
              items,
              page: pager(n, size, total),
              observed_at: new Date().toISOString(),
            });
          }
          return reply({ items: [], workspaces: [], commands: [], page: pager(1, 50, 0) });
        });
        for (const [path, kind] of [
          [
            "orders-deliveries?orders_view=commitments&delivery_type=customer_delivery",
            "commitments",
          ],
          ["attention", "exceptions"],
          ["decisions", "decisions"],
        ]) {
          await page.goto(
            `${process.env.UNIFIED_APP_URL || "http://127.0.0.1:5193"}/app/${path}${path.includes("?") ? "&" : "?"}tenant=demo`,
          );
          const list = page.locator(`[data-work-list="${kind}"]`),
            rows = list.locator("[data-work-row]");
          await rows
            .nth(49)
            .waitFor({ timeout: 12000 })
            .catch(async (error) => {
              console.log(await page.locator("body").innerText());
              console.log(errors);
              await page.screenshot({ path: "/private/tmp/worklist-error.png" });
              throw error;
            });
          assert.ok(
            await page.locator("[data-page-introduction] h1 .page-introduction-count").innerText(),
          );
          assert.equal(await list.locator(":scope > header").count(), 0);
          assert.equal(await rows.count(), 50);
          await list
            .getByRole("button", {
              name: language === "de" ? "Weitere laden" : "Load more",
              exact: true,
            })
            .click();
          await rows.nth(99).waitFor();
          assert.equal(await rows.count(), 100);
          await rows.first().click();
          const preview = list.getByRole("region").first();
          await preview.waitFor();
          assert.equal(await rows.first().getAttribute("aria-expanded"), "true");
          assert.equal(await page.getByRole("dialog").count(), 0);
          await page.screenshot({
            path: `/private/tmp/reality-work-lists/${kind}-${language}-${theme}-${mobile ? "mobile" : "desktop"}-open.png`,
            fullPage: true,
          });
          await rows.first().click();
          await preview.waitFor({ state: "hidden" });
          assert.equal(await rows.first().getAttribute("aria-expanded"), "false");
          if (kind === "commitments") {
            await list.getByRole("button", { name: /Supplier side|Lieferantenseite/ }).click();
            await rows.filter({ hasText: "Supplier Studio 1" }).first().waitFor();
            assert.equal(await rows.count(), 50);
            await page.reload();
            await rows.filter({ hasText: "Supplier Studio 1" }).first().waitFor();
            assert.equal(await list.locator("table").count(), 0);
          } else if (kind === "decisions") {
            await list.getByRole("combobox").selectOption("reserve");
            await page.waitForFunction(
              () => document.querySelectorAll("[data-work-row]").length === 1,
            );
          } else {
            await list.getByRole("textbox").fill("Northstar");
            await page.waitForFunction(
              () => document.querySelectorAll("[data-work-row]").length === 1,
            );
          }
          assert.equal(
            await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
            false,
          );
          await page.screenshot({
            path: `/private/tmp/reality-work-lists/${kind}-${language}-${theme}-${mobile ? "mobile" : "desktop"}.png`,
          });
        }
        assert.equal(writes, 0);
        assert.deepEqual(errors, []);
        console.log(
          `PASS ${language} ${theme} ${mobile ? "mobile" : "desktop"}: 3 queues, paging, inline previews, filters, no writes`,
        );
        await page.close();
      }
} finally {
  await browser.close();
}
