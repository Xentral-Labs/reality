import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { reference } from "./action-discovery-fixture.mjs";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
  headless: true,
});
const page = await browser.newPage();
page.setDefaultTimeout(10000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
let total = 37;
let language = "en";
await page.route("**/api/**", (route) => {
  const url = new URL(route.request().url()),
    path = url.pathname;
  const reply = (value) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(value) });
  if (path === "/api/auth/me")
    return reply({
      id: "u",
      email: "u@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: "t", name: "Count fixture", role: "owner" }],
      default_tenant_id: "t",
    });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
      active_session_id: null,
    });
  if (path.endsWith("/finance/accounts"))
    return reply({ revision: 1, accounts: [], roles: {}, defaults: {} });
  if (path.includes("application-reference")) return reply(reference);
  if (path.endsWith("/explorer")) return reply({ sections: [], limit_per_collection: 20 });
  if (url.searchParams.get("q") === "failed")
    return route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Fixture failure" }),
    });
  const count = url.searchParams.get("q") === "nothing" ? 0 : total;
  return reply({
    scope: { view: path.split("/").at(-1), item_id: null, item: null },
    classes: [],
    items: [],
    total: count,
    totals: [],
    subject_types: [],
    page: { total: count, number: 1, size: 50, pages: 1, has_next: false, has_previous: false },
  });
});
const base = process.env.BASE_URL || "http://localhost:8096";
const paths = [
  "/orders-deliveries?orders_view=customer-orders",
  "/orders-deliveries?orders_view=supplier-orders",
  ...["stock", "reservations", "movements"].map((v) => `/warehouse?warehouse_view=${v}`),
  ...["open-items", "payments", "journal"].map((v) => `/finance?finance_view=${v}`),
  ...["customer", "supplier", "item", "location"].map((v) => `/master-data?family=${v}`),
  ...["systems", "records", "documents"].map((v) => `/data-sources?data_view=${v}`),
  "/facts",
  "/inspector?inspector_view=facts",
  "/inspector?inspector_view=rules",
];
const badge = page.locator(".page-introduction-count [data-page-record-count]");
try {
  for (const path of paths) {
    await page.goto(base + "/app" + path);
    await badge.waitFor();
    assert.equal((await badge.evaluate((el) => el.firstChild.textContent)).trim(), "37", path);
    assert.equal(await badge.count(), 1, path);
    const header = page.locator("[data-shell-header]");
    if (await header.locator(".register-tabs").count()) {
      assert.equal(
        await header.locator(".shell-tab-count [data-page-record-count]").count(),
        1,
        path,
      );
      assert.equal(
        await header
          .locator(".shell-tab-count")
          .evaluate((node) => node.previousElementSibling?.getAttribute("aria-pressed")),
        "true",
        path,
      );
    }
    assert.equal(await page.locator("main [data-page-tabs]").count(), 0, path);
    assert.equal((await page.locator("[data-shell-header]").boundingBox()).height, 48, path);
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
      path,
    );
    if (path.includes("supplier-orders"))
      await page.screenshot({ path: "/private/tmp/compact-purchasing.png" });
    assert.equal(await page.locator(".register-toolbar-block .register-count").count(), 0, path);
    const actions = header.locator(".register-actions");
    if (await actions.count()) {
      await actions.locator("summary").click();
      const menu = await actions.locator(".register-action-menu").boundingBox();
      assert.ok(menu.x >= 0 && menu.x + menu.width <= page.viewportSize().width + 1, path);
      await actions.locator("summary").press("Escape");
    }
  }
  await page.goto(base + "/app/finance?finance_view=open-items");
  await badge.waitFor();
  await page
    .locator(".register-tabs")
    .getByRole("button", { name: "Settings", exact: true })
    .click();
  await page.getByRole("region", { name: "Finance settings", exact: true }).waitFor();
  await badge.waitFor({ state: "detached" });
  await page
    .locator(".register-tabs")
    .getByRole("button", { name: "Open items", exact: true })
    .click();
  await badge.waitFor();
  assert.equal((await badge.evaluate((el) => el.firstChild.textContent)).trim(), "37");
  const badgeWidths = [];
  for (const value of [8, 35, 705]) {
    total = value;
    await page.goto(`${base}/app/warehouse?warehouse_view=stock&q=badge-${value}`);
    await badge.waitFor();
    assert.equal((await badge.evaluate((el) => el.firstChild.textContent)).trim(), String(value));
    const box = await badge.boundingBox();
    assert.equal(box.height, 18);
    badgeWidths.push(box.width);
    await page.screenshot({ path: `/private/tmp/page-count-badge-${value}.png` });
  }
  assert.ok(badgeWidths[0] <= badgeWidths[1]);
  assert.ok(badgeWidths[1] < badgeWidths[2]);
  total = 37;
  await page.goto(base + "/app/inspector?inspector_view=facts");
  await badge.waitFor();
  // The disclosure is keyboard-accessible even beside the fixed register footer.
  await page.getByText("Technical record overview", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await page.locator(".register-count").waitFor();
  assert.equal((await badge.evaluate((el) => el.firstChild.textContent)).trim(), "37");
  assert.equal(await badge.count(), 1);
  assert.match(await page.locator(".register-count").innerText(), /0 records/);
  for (const tab of ["commands", "views", "exceptions"]) {
    await page.goto(base + "/app/inspector?inspector_view=" + tab);
    await badge.waitFor();
    assert.equal(await badge.count(), 1, tab);
    assert.equal(await page.locator(".register-toolbar-block .register-count").count(), 0, tab);
    if (tab === "commands") {
      await page
        .getByRole("searchbox", { name: "Search action catalog" })
        .fill("no-such-command-xyz");
      await page.waitForFunction(() =>
        document.querySelector("[data-page-record-count]")?.textContent.startsWith("0"),
      );
    }
  }
  total = 0;
  await page.goto(base + "/app/warehouse");
  await badge.waitFor();
  assert.equal((await badge.evaluate((el) => el.firstChild.textContent)).trim(), "0");
  total = 12;
  await page.getByRole("button", { name: "Movements", exact: true }).click();
  await page.waitForFunction(() =>
    document.querySelector("[data-page-record-count]")?.textContent.startsWith("12"),
  );
  await page.locator(".register-search input").fill("nothing");
  await page.waitForFunction(() =>
    document.querySelector("[data-page-record-count]")?.textContent.startsWith("0"),
  );
  await page.locator(".register-search input").fill("failed");
  await badge.waitFor({ state: "detached" });
  await page.locator(".register-search input").fill("");
  await badge.waitFor();
  assert.equal((await badge.evaluate((el) => el.firstChild.textContent)).trim(), "12");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await badge.waitFor();
  await page.evaluate(() => window.scrollTo(0, 0));
  const bounds = await badge.boundingBox();
  assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= 390);
  assert.ok(bounds.y >= 0 && bounds.y + bounds.height <= 844);
  await page.screenshot({ path: "/private/tmp/page-title-counts-mobile.png" });
  await page.locator(".page-introduction-actions").waitFor();
  assert.ok(
    await page
      .locator(".page-introduction-actions button, .page-introduction-actions summary")
      .count(),
  );
  await page.screenshot({ path: "/private/tmp/compact-page-actions-mobile.png" });
  await page.keyboard.press("Escape");
  await page.goto(base + "/app/inspector?inspector_view=graph");
  await page.locator("[data-page-introduction]").waitFor();
  assert.equal(await badge.count(), 0);
  language = "de";
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(base + "/app/orders-deliveries?orders_view=customer-orders&tenant=t");
    await badge.waitFor();
    const actions = page.locator("[data-shell-header] .register-actions");
    await actions.locator("summary").click();
    const menu = await actions.locator(".register-action-menu").boundingBox();
    assert.ok(menu.x >= 0 && menu.x + menu.width <= width + 1);
    await page.screenshot({
      path: `/private/tmp/reality-225-tabs-de-${width}.png`,
      animations: "disabled",
    });
    await actions.locator("summary").press("Escape");
  }
  assert.deepEqual(errors, []);
  console.log(
    `PASS ${paths.length} main registers, zero, tab changes, nested catalog, navigation and mobile title counts`,
  );
} catch (error) {
  console.error(page.url(), errors);
  console.error((await page.locator("body").innerText()).slice(0, 4000));
  throw error;
} finally {
  await browser.close();
}
