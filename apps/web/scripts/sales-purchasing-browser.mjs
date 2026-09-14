// Verify shared page chrome independently of business data loading.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const page = await browser.newPage();
let language = "en";
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
await page.route("**/api/**", (route) => {
  const path = new URL(route.request().url()).pathname;
  let body,
    status = 200;
  if (path === "/api/auth/me")
    body = {
      id: "intro_user",
      email: "intro@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
    };
  else if (path === "/api/v1/bootstrap")
    body = {
      tenants: [{ id: "intro_company", name: "Introduction test", role: "owner" }],
      default_tenant_id: "intro_company",
    };
  else if (path.endsWith("/copilot"))
    body = {
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
      active_session_id: null,
    };
  else {
    status = 503;
    body = { detail: "Fixture read unavailable" };
  }
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
});
const origin = process.env.BASE_URL || "http://localhost:8087";

try {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const [title, view, direction] of [
      ["Sales", "customer-orders", "customer_delivery"],
      ["Purchasing", "supplier-orders", "supplier_delivery"],
    ]) {
      await page.goto(origin + `/app/orders-deliveries?tenant=intro_company&orders_view=${view}`);
      await page.locator("[data-page-introduction] h1").waitFor();
      assert.equal((await page.locator("[data-page-introduction] h1").innerText()).trim(), title);
      const tabs = page.locator("[data-shell-header] .register-tabs");
      assert.equal(await tabs.getByRole("button").count(), 2);
      await tabs.getByRole("button", { name: "Deliveries", exact: true }).click();
      assert.equal(new URL(page.url()).searchParams.get("delivery_type"), direction);
      await page.reload();
      await page.locator("[data-page-introduction] h1").waitFor();
      assert.equal((await page.locator("[data-page-introduction] h1").innerText()).trim(), title);
      assert.equal(
        await page.getByRole("combobox", { name: "Delivery direction", exact: true }).count(),
        0,
      );
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
        false,
      );
      await page.screenshot({ path: `/private/tmp/${title}-${width}.png` });
    }
  }
  assert.deepEqual(errors, []);
  console.log("Sales/Purchasing desktop/mobile tab scope and reload passed");
} finally {
  await browser.close();
}
