// Mock transport only; no real company is created.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5198";
try {
  for (const language of ["en", "de", "nl", "es"])
    for (const width of [1440, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 950 } });
      page.setDefaultTimeout(10000);
      const writes = [],
        errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.route("**/api/**", async (route) => {
        const req = route.request(),
          path = new URL(req.url()).pathname;
        const reply = (data, status = 200) =>
          route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
        if (req.method() !== "GET") {
          writes.push({ path, body: req.postDataJSON() });
          return reply({ detail: "Fixture failure" }, 503);
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
              { id: "ordinary", name: "Business", role: "owner", company_kind: "company" },
              {
                id: "story",
                name: "Order to close",
                role: "owner",
                company_kind: "sandbox",
                sandbox_run_id: "story-run",
              },
              {
                id: "member",
                name: "Member Sandbox",
                role: "member",
                company_kind: "sandbox",
                sandbox_run_id: "member-run",
              },
              {
                id: "supported",
                name: "Demo Sandbox",
                role: "owner",
                company_kind: "sandbox",
                sandbox_run_id: "demo-run",
              },
            ],
            default_tenant_id: "ordinary",
          });
        if (path === "/api/tenants/story/demo-data")
          return reply({ detail: "Demo Data requires a ready compatible practice company." }, 403);
        if (path === "/api/tenants/supported/demo-data/preview")
          return reply({
            fingerprint: "fixture-preview",
            add: {
              items: [
                { key: "bottle", name: "Summit Bottle" },
                { key: "lantern", name: "Trail Lantern" },
              ],
              parties: Array.from({ length: 21 }, (_, i) => ({
                key: `party-${i}`,
                name: `Demo customer ${i + 1}`,
              })),
              locations: [{ key: "A", name: "Rotterdam Warehouse" }],
              payment_terms: [{ key: "term", name: "14 days net, 2 % within 7 days" }],
            },
          });
        if (path === "/api/tenants/supported/demo-data")
          return reply({ state: "not_connected", rate: 60 });
        if (path === "/api/company-setup/options")
          return reply({
            actor_id: "owner",
            environments: ["business", "sandbox"],
            practice_enabled: true,
            suggested_name: "",
          });
        if (path === "/api/v1/companies") return reply([]);
        if (path === "/api/playground/runs") return reply({ runs: [] });
        if (path.endsWith("/copilot"))
          return reply({
            sessions: [],
            messages: [],
            proposals: [],
            suggestions: [],
            active_session_id: null,
          });
        if (path.endsWith("/application-reference")) return reply({ workspaces: [], commands: [] });
        return reply({ items: [], total: 0 });
      });
      await page.goto(`${base}/app/settings?tenant=ordinary&settings_view=company`);
      await page
        .locator("[data-company-simulation=story]")
        .waitFor()
        .catch(async (error) => {
          console.error(errors, await page.locator("body").innerText());
          throw error;
        });
      for (const id of ["ordinary", "member"])
        assert.equal(await page.locator(`[data-company-simulation=${id}]`).count(), 0);
      await page.locator("[data-company-simulation=supported]").click();
      await page.locator(".demo-data-integration .secondary-button").first().waitFor();
      assert.equal(new URL(page.url()).searchParams.get("tenant"), "supported");
      assert.equal(writes.length, 0);
      await page.locator(".demo-data-integration .secondary-button").first().click();
      const preview = page.locator("[data-demo-connection-preview]");
      await preview.waitFor();
      assert.equal(await preview.locator("details").count(), 4);
      const parties = preview.locator("[data-demo-reference-group=parties]");
      assert.match(await parties.locator("summary").innerText(), /21/);
      assert.equal(await parties.getAttribute("open"), null);
      await parties.locator("summary").focus();
      await page.keyboard.press("Enter");
      assert.notEqual(await parties.getAttribute("open"), null);
      assert.equal(await parties.locator("li").count(), 21);
      await parties.locator("summary").click();
      assert.equal(writes.length, 0);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({
        path: `/private/tmp/demo-connection-preview-${language}-${width}.png`,
      });
      await preview.locator("button").last().click();
      await preview.waitFor({ state: "detached" });
      assert.equal(writes.length, 0);
      if (language === "en" && width === 1440) {
        await page.locator(".demo-data-integration .secondary-button").first().click();
        await preview.locator("button").first().click();
        await page.getByRole("alert").waitFor();
        assert.equal(writes.length, 1);
        assert.equal(writes[0].path, "/api/tenants/supported/demo-data/connect");
        assert.equal(writes[0].body.preview_fingerprint, "fixture-preview");
        assert.equal(writes[0].body.confirmed, true);
        assert.ok(writes[0].body.request_key);
        writes.length = 0;
      }

      await page.goto(`${base}/app/settings?tenant=ordinary&settings_view=company`);
      await page.locator("[data-company-simulation=story]").click();
      const unavailable = page.locator("[data-simulation-unavailable]");
      await unavailable.waitFor();
      if (language === "en")
        await unavailable
          .getByText(
            "Live simulation supports empty and standard demo Sandbox setups. Storyline Sandboxes use a different data setup that is not yet supported.",
          )
          .waitFor();
      const spacing = await unavailable.evaluate((node) => {
        const heading = node.querySelector("h2");
        return {
          padding: parseFloat(getComputedStyle(node).paddingLeft),
          heading: parseFloat(getComputedStyle(heading).fontSize),
        };
      });
      assert.ok(spacing.padding >= 24 && spacing.heading >= 20, "padded card and clear heading");
      await page.screenshot({
        path: `/private/tmp/simulation-unavailable-${language}-${width}.png`,
      });
      assert.equal(await page.locator(".company-setup-dialog").count(), 0);
      assert.equal(await unavailable.getByRole("button").count(), 0);
      assert.equal(writes.length, 0);
      await unavailable.getByRole("link").click();
      await page.waitForURL(/settings_view=company/);
      await page.locator("[data-company-simulation=story]").waitFor();
      assert.equal(new URL(page.url()).searchParams.get("tenant"), "story");
      assert.equal(await page.locator(".company-setup-dialog").count(), 0);
      assert.equal(
        writes.length,
        0,
        "unsupported entry and Companies navigation do not create anything",
      );
      assert.deepEqual(errors, []);
      await page.close();
      console.log(
        `PASS ${language}/${width}: scoped owner entry, explicit unavailable state, Companies navigation without creation`,
      );
    }
} finally {
  await browser.close();
}
