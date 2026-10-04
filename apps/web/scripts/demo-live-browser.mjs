// Stateful read-only HTTP fixtures prove polling without creating real business records.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5190";
const out = process.env.DEMO_LIVE_ARTIFACTS || "/tmp/reality-demo-live-browser";
await mkdir(out, { recursive: true });
try {
  for (const language of process.env.DEMO_VISUAL_ONLY
    ? ["de", "nl", "es"]
    : ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const mobile of [false, true]) {
        const page = await browser.newPage({
          viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1100 },
        });
        page.setDefaultTimeout(15000);
        await page.addInitScript((theme) => localStorage.setItem("reality.theme", theme), theme);
        let ordinary = false;
        const errors = [],
          writes = [];
        page.on("pageerror", (error) => errors.push(error.message));
        let count = 1,
          reads = 0,
          failed = false,
          state = "running",
          awaitingReview = false,
          reviewRequired = false,
          revision = 1;
        await page.route("**/api/**", async (route) => {
          const req = route.request(),
            url = new URL(req.url()),
            path = url.pathname;
          const reply = (data, status = 200) =>
            route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
          if (req.method() !== "GET") {
            writes.push({ path, body: req.postDataJSON() });
            assert.ok(path.endsWith("/demo-data/control"));
            assert.equal(req.postDataJSON().confirmed, true);
            state = req.postDataJSON().action === "pause" ? "paused" : "running";
            revision++;
            return reply({});
          }
          if (path === "/api/auth/me")
            return reply({
              id: "owner",
              email: "owner@example.test",
              status: "active",
              language,
              locale: "en-GB",
              timezone: "UTC",
            });
          if (path === "/api/v1/bootstrap")
            return reply({
              tenants: [
                {
                  id: "demo",
                  name: "Northstar Demo",
                  role: "owner",
                  sandbox_run_id: ordinary ? undefined : "run",
                  company_kind: ordinary ? "company" : "demo",
                },
              ],
              default_tenant_id: "demo",
            });
          if (path === "/api/v1/companies") return reply([]);
          if (path === "/api/playground/runs") return reply({ runs: [] });
          if (path.endsWith("/copilot"))
            return reply({
              sessions: [],
              active_session_id: null,
              messages: [],
              proposals: [],
              suggestions: [],
              has_archived: false,
            });
          if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
          if (path.endsWith("/demo-data")) {
            reads++;
            return failed
              ? reply({ detail: "Temporarily unavailable" }, 503)
              : reply({
                  id: "connection",
                  state,
                  derived_state: reviewRequired
                    ? "review_required"
                    : awaitingReview
                      ? "awaiting_reviewer"
                      : state,
                  revision,
                  rate: 60,
                  next_arrival: state === "running" ? "2026-09-09T09:00:00Z" : null,
                  last_success: awaitingReview ? null : "2026-09-09T08:59:00Z",
                  generated: count,
                  imported: awaitingReview ? 0 : count,
                  pending: awaitingReview ? count : 0,
                  awaiting_decision: awaitingReview && !reviewRequired ? count : 0,
                  review_required: reviewRequired ? count : 0,
                  failed: 0,
                });
          }
          if (path.endsWith("/demo-data/imports")) {
            assert.equal(url.searchParams.get("recent"), "true");
            return reply({
              items: Array.from({ length: count }, (_, i) => ({
                id: `imp-${count - i}`,
                source_record_id: `src-${count - i}`,
                status: reviewRequired
                  ? "review_required"
                  : awaitingReview
                    ? "awaiting_decision"
                    : "completed",
                document_id: awaitingReview ? null : `doc-${count - i}`,
                document_number: awaitingReview ? null : `DEMO-${count - i}`,
                created_at: "2026-09-09T08:58:00Z",
                completed_at: awaitingReview ? null : "2026-09-09T08:59:00Z",
              })),
              next_cursor: null,
              has_more: false,
            });
          }
          return reply({
            items: [],
            total: 0,
            page: { number: 1, size: 25, total: 0, pages: 1, has_previous: false, has_next: false },
          });
        });
        await page.goto(`${base}/app/settings?tenant=demo&settings_view=company`);
        await page.locator("[data-company-simulation=demo]").click();
        await page.waitForURL(/\/app\/demo-data\?tenant=demo/);
        const panel = page.locator(".demo-data-integration");
        await panel.getByText("DEMO-1", { exact: true }).waitFor();
        assert.equal(
          await page.locator('[data-navigation-item][href*="/demo-data"]').count(),
          0,
          "The simulation is company context, not a navigation destination",
        );
        if (language === "en") {
          assert.equal(
            await panel.getByText("More options", { exact: true }).count(),
            0,
            "Lifecycle actions must not be hidden behind a one-purpose disclosure",
          );
          await panel.getByRole("button", { name: "Stop", exact: true }).waitFor();
          await panel.getByRole("button", { name: "Disconnect", exact: true }).waitFor();
          const rate = panel.getByLabel("Orders per hour", { exact: true });
          await rate.selectOption("300");
          await panel.getByRole("button", { name: "Pause", exact: true }).click();
          count = 2;
          await panel.getByText("DEMO-2", { exact: true }).waitFor();
          assert.equal(await rate.inputValue(), "300");
          await panel.getByRole("button", { name: "Confirm", exact: true }).waitFor();
          assert.equal(writes.length, 0, "Polling and opening confirmation must not write");
          failed = true;
          await panel
            .getByText("Live updates are unavailable. Showing the last known information.")
            .waitFor();
          assert.equal(await panel.locator(".demo-live-event").count(), 2);
          assert.equal(await rate.inputValue(), "300");
          failed = false;
          await panel.getByRole("button", { name: "Refresh status", exact: true }).click();
          await page.waitForFunction(() => !document.querySelector(".demo-live-warning"));
          await panel.getByRole("button", { name: "Confirm", exact: true }).click();
          await panel.getByRole("button", { name: "Resume", exact: true }).waitFor();
          assert.equal(writes.length, 1);
          assert.equal(writes[0].body.action, "pause");
          assert.equal(await rate.inputValue(), "300");
          // The hidden-page guard is exercised through the same browser visibility event.
          await page.evaluate(() => {
            Object.defineProperty(document, "visibilityState", {
              configurable: true,
              get: () => "hidden",
            });
            document.dispatchEvent(new Event("visibilitychange"));
          });
          await page.waitForTimeout(100);
          const hiddenReads = reads;
          await page.waitForTimeout(5200);
          assert.equal(reads, hiddenReads, "Hidden page must not poll");
          await page.evaluate(() => {
            Object.defineProperty(document, "visibilityState", {
              configurable: true,
              get: () => "visible",
            });
            document.dispatchEvent(new Event("visibilitychange"));
          });
        } else {
          const activity = { de: "Live-Aktivität", nl: "Live-activiteit", es: "Actividad en vivo" }[
            language
          ];
          await panel.getByRole("heading", { name: activity, exact: true }).waitFor();
          assert.equal(writes.length, 0, "Localized activity must remain read-only");
        }
        awaitingReview = true;
        const writesBeforeReview = writes.length;
        await panel.locator(".demo-live-activity header button").click();
        await panel.locator("[data-awaiting-reviewer]").waitFor();
        await panel.locator('.demo-live-event[data-status="awaiting_decision"]').first().waitFor();
        assert.equal(await panel.locator('.demo-live-event[data-status="completed"]').count(), 0);
        const reviewLink = panel.locator("[data-awaiting-reviewer] a");
        assert.equal(await reviewLink.getAttribute("href"), "/app/decisions?tenant=demo");
        assert.equal(
          await panel.locator('.demo-live-badge[data-state="awaiting_reviewer"]').count(),
          1,
        );
        assert.equal(
          writes.length,
          writesBeforeReview,
          "Awaiting review must not enroll an agent or accept a source",
        );
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({
          path: `${out}/demo-live-${language === "en" ? "" : `${language}-`}${theme}-${mobile}.png`,
          fullPage: true,
        });
        const overflow = await page.evaluate(() =>
          [...document.querySelectorAll("body *")]
            .map((el) => ({
              tag: el.tagName,
              className: el.className,
              text: el.textContent?.slice(0, 80),
              right: el.getBoundingClientRect().right,
              width: innerWidth,
            }))
            .filter((el) => el.right > el.width + 1),
        );
        if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth))
          console.error(JSON.stringify(overflow.slice(0, 20)));
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
          false,
          "No horizontal overflow",
        );
        reviewRequired = true;
        await panel.locator(".demo-live-activity header button").click();
        await panel.locator('.demo-live-badge[data-state="review_required"]').waitFor();
        await panel.locator('.demo-live-event[data-status="review_required"]').first().waitFor();
        assert.equal(
          await panel.locator("[data-awaiting-reviewer] a").getAttribute("href"),
          "/app/data-sources?tenant=demo&data_view=records",
        );
        assert.equal(
          writes.length,
          writesBeforeReview,
          "Unsupported meaning cannot become approval",
        );
        if (language === "en") {
          await page.goto(`${base}/app/data-sources?tenant=demo`);
          // A connected simulation lives only in its registered source (252920bd); the
          // entry card is for companies where nothing is connected yet.
          await page.locator("[data-source-table-inset]").waitFor();
          assert.equal(await page.locator("[data-demo-data-source]").count(), 0);
          assert.equal(
            await page.locator(".demo-data-integration").count(),
            0,
            "Demo widget has its own page",
          );
          ordinary = true;
          await page.reload();
          await page.locator('[data-company-id="demo"]').first().waitFor({ state: "attached" });
          await page.locator("[data-source-table-inset]").waitFor();
          assert.equal(
            await page.locator("[data-demo-data-source]").count(),
            0,
            "An ordinary company has no simulation source",
          );
        }
        assert.deepEqual(errors, []);
        await page.close();
        console.log(
          language === "en"
            ? `PASS en ${theme} ${mobile ? "mobile" : "desktop"}: live arrivals, retained edits/confirmation, stale recovery, visible-only reads, confirmed control`
            : `PASS ${language} ${theme} ${mobile ? "mobile" : "desktop"}: localized live activity, no overflow, read-only`,
        );
      }
} finally {
  await browser.close();
}
