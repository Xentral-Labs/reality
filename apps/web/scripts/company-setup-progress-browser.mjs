import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
try {
  for (const language of ["en", "de", "nl", "es"])
    for (const width of [1440, 390]) {
      const page = await browser.newPage({
        viewport: { width, height: 950 },
        colorScheme: width === 390 ? "dark" : "light",
      });
      page.setDefaultTimeout(10000);
      const saved = {
        request_key: "same-request",
        confirmed: true,
        name: "Bene Firma 4",
        environment: "sandbox",
        content: "international_demo",
        live_simulation: true,
      };
      let writes = 0;
      await page.addInitScript(
        (saved) => sessionStorage.setItem("reality.company-setup.owner", JSON.stringify(saved)),
        saved,
      );
      await page.route("**/api/**", async (route) => {
        const path = new URL(route.request().url()).pathname;
        const reply = (data, status = 200) =>
          route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
        if (path === "/api/auth/me")
          return reply({
            id: "owner",
            email: "owner@example.test",
            status: "active",
            language,
            locale: "en-GB",
            timezone: "UTC",
          });
        if (path === "/api/v1/bootstrap") return reply({ tenants: [], default_tenant_id: null });
        if (path === "/api/company-setup/playground")
          return reply({
            requested: false,
            enabled: true,
            eligible: true,
            archived: false,
            receipt: null,
          });
        if (path === "/api/company-setup/options")
          return reply({
            actor_id: "owner",
            environments: ["business", "sandbox"],
            practice_enabled: true,
            suggested_name: "Bene",
          });
        if (path.startsWith("/api/company-setup/requests/")) {
          await new Promise((r) => setTimeout(r, 1200));
          return reply({ status: "initialization_failed" });
        }
        if (path === "/api/company-setup") {
          writes++;
          assert.deepEqual(route.request().postDataJSON(), saved);
          await new Promise((r) => setTimeout(r, 1500));
          return reply({ detail: "fixture failure" }, 503);
        }
        return reply({});
      });
      await page.goto(
        `${process.env.UNIFIED_APP_URL || "http://127.0.0.1:5195"}/app?lang=${language}`,
      );
      const card = page.locator(".company-setup-card");
      await card.locator("[role=status]").waitFor();
      assert.equal(await card.locator("button").count(), 0);
      await card.locator("button").waitFor();
      await card.locator("button").click();
      await card.locator("[role=status]").waitFor();
      assert.equal(await card.locator("button").count(), 0);
      assert.equal(await card.locator("svg.animate-spin").count(), 1);
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
        false,
      );
      if (language === "de")
        await page.screenshot({ path: `/private/tmp/company-progress-${width}.png` });
      await card.locator("[role=alert]").waitFor();
      assert.equal(await card.locator("button").isEnabled(), true);
      assert.equal(writes, 1);
      await page.close();
      console.log("PASS", language, width);
    }
} finally {
  await browser.close();
}
