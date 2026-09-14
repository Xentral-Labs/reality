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
      await page.goto(`${base}/app/settings?tenant=ordinary&settings_view=company`);
      await page.locator("[data-company-simulation=story]").click();
      const name = {
        en: "Create demo Sandbox",
        de: "Demo-Sandbox erstellen",
        nl: "Demo-Sandbox maken",
        es: "Crear Sandbox de demostración",
      }[language];
      await page.getByRole("button", { name, exact: true }).click();
      const dialog = page.locator(".company-setup-dialog");
      await dialog.locator("input[value=demo]").waitFor();
      assert(await dialog.locator("input[value=demo]").isChecked());
      assert(await dialog.locator("input[type=checkbox]").isChecked());
      assert.equal(writes.length, 0);
      assert.equal(new URL(page.url()).searchParams.get("tenant"), "story");
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: `/private/tmp/simulation-entry-${language}-${width}.png` });
      await dialog.locator("button.secondary-button").click();
      await dialog.waitFor({ state: "detached" });
      assert.equal(writes.length, 0);
      if (language === "en" && width === 1440) {
        await page.getByRole("button", { name, exact: true }).click();
        await page.locator("#setup-company-name").fill("Separate demo");
        await page.getByRole("button", { name: "Create company", exact: true }).click();
        await page
          .getByText("Creation could not be confirmed. Retry the same request to recover safely.")
          .waitFor();
        assert.equal(writes.length, 1);
        assert.equal(writes[0].path, "/api/company-setup");
        assert.equal(writes[0].body.environment, "sandbox");
        assert.equal(writes[0].body.content, "international_demo");
        assert.equal(writes[0].body.live_simulation, true);
        assert.equal(writes[0].body.confirmed, true);
      }
      assert.deepEqual(errors, []);
      await page.close();
      console.log(
        `PASS ${language}/${width}: scoped owner entry, compatibility fallback, separate confirmed setup and cancel`,
      );
    }
} finally {
  await browser.close();
}
