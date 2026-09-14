import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
await mkdir("/private/tmp/reality-graph-browser", { recursive: true });
try {
  for (const language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const mobile of [false, true]) {
        const page = await browser.newPage({
          viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1100 },
        });
        await page.addInitScript((theme) => localStorage.setItem("reality.theme", theme), theme);
        let releaseDashboard;
        const dashboardGate = new Promise((resolve) => {
          releaseDashboard = resolve;
        });
        let failed = false,
          count = 1,
          writes = 0,
          reads = 0,
          lastDays = 30,
          userId = "owner",
          delayNext = false,
          release,
          started;
        const errors = [];
        page.on("pageerror", (e) => errors.push(e.message));
        await page.route("**/api/**", async (route) => {
          const req = route.request(),
            url = new URL(req.url()),
            p = url.pathname;
          const reply = (data, status = 200) =>
            route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
          if (req.method() !== "GET") {
            writes++;
            return reply({});
          }
          if (p === "/api/auth/me")
            return reply({
              id: userId,
              email: "owner@example.test",
              status: "active",
              language,
              locale: "en-GB",
              timezone: "UTC",
            });
          if (p === "/api/v1/bootstrap")
            return reply({
              tenants: [
                {
                  id: "demo",
                  name: "Northstar Demo",
                  role: "owner",
                  company_kind: "demo",
                  sandbox_run_id: "run",
                },
                { id: "other", name: "Other Company", role: "owner" },
              ],
              default_tenant_id: "demo",
            });
          if (p.endsWith("/dashboard")) {
            await dashboardGate;
            return reply({ totals: { open_deliveries: 39, exceptions: 66, pending_decisions: 0 } });
          }
          if (p.endsWith("/analytics"))
            return reply({ position: { fully_reserved: 2, needs_reservation: 37, overdue: 3 } });
          if (p.endsWith("/copilot"))
            return reply({
              sessions: [],
              messages: [],
              proposals: [],
              suggestions: [],
              has_archived: false,
            });
          if (p.endsWith("/readiness"))
            return failed
              ? reply({}, 503)
              : reply({
                  status: "ready",
                  components: { connection: "ready", scheduler: "ready", worker: "ready" },
                  observed_at: new Date().toISOString(),
                });
          if (p.endsWith("/activity-volume")) {
            reads++;
            lastDays = Number(url.searchParams.get("days"));
            assert.ok([1, 7, 30].includes(lastDays));
            const end = Date.now(),
              start = end - lastDays * 86400000,
              other = p.includes("/other/");
            const buckets = [];
            for (
              let at = Math.floor(start / 1800000) * 1800000, i = 0;
              at < end;
              at += 1800000, i++
            )
              buckets.push({
                start: new Date(at).toISOString(),
                end: new Date(Math.min(at + 1800000, end)).toISOString(),
                counts: {
                  orders: other
                    ? 0
                    : Math.round((Math.sin(i / 19) + 1) * 8) + (i % 50 === 0 ? 30 : 0) + count,
                  reservations: other ? 0 : i % 5,
                  movements: other ? 0 : i % 3,
                  documents: 0,
                },
              });
            if (delayNext && !other) {
              delayNext = false;
              await new Promise((resolve) => {
                release = resolve;
                started();
              });
            }
            return failed
              ? reply({}, 503)
              : reply({
                  start: new Date(start).toISOString(),
                  observed_at: new Date(end).toISOString(),
                  coverage_start: new Date(other ? end - 3600000 : start).toISOString(),
                  bucket_seconds: 1800,
                  total: other ? 0 : 123,
                  buckets,
                });
          }
          if (p.endsWith("/activity-volume/events")) {
            assert.ok(
              Date.parse(url.searchParams.get("end")) - Date.parse(url.searchParams.get("start")) <=
                86400000,
            );
            return reply({
              total: 1,
              has_more: false,
              events: [
                {
                  id: "event-one",
                  sequence: 1,
                  type: "document.recorded",
                  recorded_at: url.searchParams.get("start"),
                  subject_type: "document",
                  subject_id: "doc",
                },
              ],
            });
          }
          return reply({ items: [], workspaces: [], events: [], total: 0 });
        });
        await page.goto(
          `${process.env.UNIFIED_APP_URL || "http://127.0.0.1:5190"}/app?tenant=demo`,
        );
        const panel = page.locator("[data-home-pulse]"),
          bars = panel.locator("[data-activity-bucket]");
        await bars.first().waitFor();
        const beforeDashboard = await panel.evaluate((el) => el.getBoundingClientRect().top);
        assert.equal(await page.locator("main .read-line").count(), 3);
        releaseDashboard();
        await page.waitForFunction(() => document.querySelectorAll("main .read-line").length === 0);
        const afterDashboard = await panel.evaluate((el) => el.getBoundingClientRect().top);
        assert.ok(
          Math.abs(beforeDashboard - afterDashboard) < 2,
          `Dashboard shifted activity by ${afterDashboard - beforeDashboard}px`,
        );
        assert.equal(lastDays, 1, "New user should start with 24 hours");
        if (process.env.HOME_LOADING_ONLY) {
          assert.deepEqual(errors, []);
          assert.equal(writes, 0);
          await page.screenshot({
            path: `/private/tmp/reality-graph-browser/loading-${language}-${theme}-${mobile ? "mobile" : "desktop"}.png`,
          });
          console.log(`PASS stable loading ${language} ${theme} ${mobile ? "mobile" : "desktop"}`);
          await page.close();
          continue;
        }

        if (language === "en" && theme === "light" && !mobile) {
          const selected = () => panel.locator('button[aria-pressed="true"]');
          await panel.getByRole("button", { name: "7 days", exact: true }).click();
          await bars.first().waitFor();
          await page.reload();
          await bars.first().waitFor();
          assert.equal(await selected().innerText(), "7 days", "Reload lost preference");
          await page.goto(`${new URL(page.url()).origin}/app?tenant=other`);
          await bars.first().waitFor();
          assert.equal(lastDays, 7, "Company change lost preference");
          userId = "second-user";
          await page.reload();
          await bars.first().waitFor();
          assert.equal(lastDays, 1, "Another user inherited preference");
          userId = "owner";
          await page.reload();
          await bars.first().waitFor();
          assert.equal(lastDays, 7, "Returning user lost preference");
          await page.evaluate(() =>
            localStorage.setItem("reality.home.activity-days.owner", "999"),
          );
          await page.reload();
          await bars.first().waitFor();
          assert.equal(lastDays, 1, "Invalid preference did not fall back");
          await page.addInitScript(() => {
            const get = Storage.prototype.getItem,
              set = Storage.prototype.setItem;
            Storage.prototype.getItem = function (key) {
              if (key.startsWith("reality.home.activity-days.")) throw new Error("Storage blocked");
              return get.call(this, key);
            };
            Storage.prototype.setItem = function (key, value) {
              if (key.startsWith("reality.home.activity-days.")) throw new Error("Storage blocked");
              return set.call(this, key, value);
            };
          });
          await page.reload();
          await bars.first().waitFor();
          assert.equal(lastDays, 1, "Unavailable storage did not fall back");
          await panel.getByRole("button", { name: "30 days", exact: true }).click();
          await bars.first().waitFor();
          assert.equal(lastDays, 30, "Unavailable storage prevented selection");

          await page.goto(`${new URL(page.url()).origin}/app?tenant=demo`);
          await bars.first().waitFor();
        }
        const summary = panel.locator("[data-activity-summary]");
        await page.mouse.move(0, 0);
        const restingHeight = (await summary.boundingBox()).height;
        await bars.first().hover();
        assert.equal((await summary.boundingBox()).height, restingHeight, "Summary grows on hover");
        await bars.last().hover();
        assert.equal(
          (await summary.boundingBox()).height,
          restingHeight,
          "Summary changes between bars",
        );
        await page.mouse.move(0, 0);
        assert.equal(
          (await summary.boundingBox()).height,
          restingHeight,
          "Summary shrinks on leave",
        );
        if (language === "en" && theme === "light" && !mobile && !process.env.HOVER_ONLY) {
          await panel.getByRole("button", { name: "7 days", exact: true }).click();
          await bars.first().waitFor();
          assert.equal(lastDays, 7);
          await panel.getByRole("button", { name: "24 hours", exact: true }).click();
          await bars.first().waitFor();
          assert.equal(lastDays, 1);
          await bars.last().focus();
          await page.keyboard.press("Enter");
          await panel.getByText("Business document recorded", { exact: true }).waitFor();
          await panel.getByRole("button", { name: "Close", exact: true }).click();
          const old = await bars.last().getAttribute("aria-label");
          count = 90;
          await page.waitForTimeout(11000);
          assert.notEqual(await bars.last().getAttribute("aria-label"), old);
          failed = true;
          await panel
            .getByText("Updates paused. Showing the last available activity.", { exact: true })
            .waitFor({ timeout: 14000 });
          assert.ok(await bars.count());
          assert.equal(await panel.getByText("Everything is ready", { exact: true }).count(), 0);
          failed = false;
          await panel.getByText("Everything is ready", { exact: true }).waitFor({ timeout: 14000 });
          await page.evaluate(() => {
            Object.defineProperty(document, "hidden", { configurable: true, value: true });
            document.dispatchEvent(new Event("visibilitychange"));
          });
          const before = reads;
          await page.waitForTimeout(11000);
          assert.equal(reads, before);
          await page.evaluate(() => {
            Object.defineProperty(document, "hidden", { configurable: true, value: false });
            document.dispatchEvent(new Event("visibilitychange"));
          });
          await page.waitForTimeout(200);
          delayNext = true;
          const pending = new Promise((resolve) => {
            started = resolve;
          });
          await page.evaluate(() => document.dispatchEvent(new Event("visibilitychange")));
          await pending;
          await page.evaluate(() => {
            history.pushState(null, "", "/app?tenant=other");
            window.dispatchEvent(new PopStateEvent("popstate"));
          });
          await bars.first().waitFor();
          release();
          await page.waitForTimeout(200);
          assert.ok((await bars.first().getAttribute("aria-label")).includes(": 0 "));
          await page.goto(
            `${process.env.UNIFIED_APP_URL || "http://127.0.0.1:5190"}/app?tenant=demo`,
          );
          await bars.first().waitFor();
        }
        await panel.scrollIntoViewIfNeeded();
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
          false,
        );
        assert.deepEqual(errors, []);
        assert.equal(writes, 0);
        await page.screenshot({
          path: `/private/tmp/reality-graph-browser/${language}-${theme}-${mobile ? "mobile" : "desktop"}.png`,
        });
        console.log(`PASS ${language} ${theme} ${mobile ? "mobile" : "desktop"}`);
        await page.close();
      }
} finally {
  await browser.close();
}
