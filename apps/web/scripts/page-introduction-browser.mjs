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
page.setDefaultTimeout(10000);
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
const paths = [
  "",
  "/orders-deliveries?orders_view=customer-orders",
  "/orders-deliveries?orders_view=supplier-orders",
  "/inspector?inspector_view=rules",
  "/inspector?inspector_view=exceptions",
  "/inspector?inspector_view=commands",
  "/inspector?inspector_view=graph",
  "/attention",
  "/decisions",
  "/orders-deliveries",
  "/warehouse",
  "/finance",
  "/finance?finance_view=settings",
  "/facts",
  "/analytics",
  "/master-data",
  "/data-sources",
  "/settings",
  "/demo-data",
  "/inspector?inspector_view=overview",
  "/inspector?inspector_view=facts",
  "/inspector?inspector_view=views",
  "/inspector?inspector_view=history",
];
await mkdir("/private/tmp/page-introduction-screens", { recursive: true });
for (const width of [1440, 390]) {
  await page.setViewportSize({ width, height: 950 });
  for (const path of paths) {
    await page.goto(
      origin + "/app" + path + (path.includes("?") ? "&" : "?") + "tenant=intro_company",
    );
    const description = page.locator("[data-page-description]");
    await page
      .locator("[data-page-description-trigger]")
      .click()
      .catch(async (error) => {
        console.error({ path, width, url: page.url(), errors });
        await page.screenshot({ path: "/private/tmp/reality-225-introduction-failure.png" });
        throw error;
      });
    await description.waitFor();
    assert.equal(await page.locator("h1:visible").count(), 1, path);
    assert.equal(await page.locator("main [data-page-introduction]").count(), 0, path);
    const header = await page.locator("[data-shell-header]").boundingBox();
    assert.equal(header.height, 48, path);
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
      path,
    );
    assert.equal(await page.locator("[data-page-description]:visible").count(), 1, path);
    assert.ok((await description.innerText()).length > 20, path);
    const descriptionBox = await description.boundingBox();
    assert.ok(descriptionBox.y >= header.y, path);
    assert.ok(descriptionBox.y + descriptionBox.height <= 950, path);
    await page.keyboard.press("Escape");
    const badge = page.locator("[data-page-record-count]");
    if (await badge.count()) {
      const badgeBox = await badge.boundingBox();
      const titleBox = await page.locator("[data-page-introduction] h1").boundingBox();
      assert.ok(badgeBox.width >= 18, path);
      assert.equal(badgeBox.height, 18, path);
      assert.ok(
        Math.abs(badgeBox.y + badgeBox.height / 2 - titleBox.y - titleBox.height / 2) <= 1,
        path,
      );
    }
    const tabs = page.locator("[data-page-tabs] .register-tabs");
    assert.equal(await page.locator("[data-shell-header] .register-tabs").count(), 0, path);
    if (await tabs.count()) {
      const box = await tabs.boundingBox();
      assert.ok(box.y >= header.y + header.height, path);
      if (width === 390) await tabs.locator("button,a").last().click();
      const selected = tabs.locator('[aria-pressed="true"], [aria-current="page"]');
      assert.equal(await selected.count(), 1, path);
      const style = await selected.evaluate((el) => ({
        border: getComputedStyle(el).borderBottomWidth,
        radius: getComputedStyle(el).borderRadius,
      }));
      assert.equal(style.border, "2px", path);
      assert.equal(style.radius, "0px", path);
    }
    if (width === 390) {
      await page.locator("[data-navigation-opener]").click();
      await page.getByRole("button", { name: "Switch company", exact: true }).waitFor();
      await page.getByRole("button", { name: "Switch company", exact: true }).click();
      await page.getByRole("dialog", { name: "Switch company", exact: true }).waitFor();
      await page.keyboard.press("Escape");
      await page.keyboard.press("Escape");
      if (path.includes("orders_view=customer-orders")) {
        await page.locator("[data-navigation-opener]").click();
        await page.locator("[data-action-launcher] > button").click();
        await page.getByRole("searchbox", { name: "Search actions", exact: true }).waitFor();
        await page.keyboard.press("Escape");
        await page.locator("[data-navigation-close]").click();
      }
      assert.equal((await page.locator("[data-shell-header]").boundingBox()).height, 48, path);
    }
  }
  await page.screenshot({
    path: `/private/tmp/page-introduction-screens/${width}.png`,
    fullPage: true,
  });
}
for (language of ["de", "nl", "es"]) {
  await page.goto(origin + "/app/warehouse?tenant=intro_company");
  await page.locator("[data-page-description-trigger]").click();
  await page.locator("[data-page-description]").waitFor();
  assert.notEqual(
    await page.locator("[data-page-description]").textContent(),
    "See physical, reserved and available stock for each item.",
  );
}
assert.deepEqual(errors, []);
await browser.close();
console.log(
  `${paths.length * 2} desktop/mobile page layouts and 3 translations passed with unavailable reads.`,
);
