import { reference } from "./action-discovery-fixture.mjs";
// Synthetic HTTP fixtures exercise presentation only; PostgreSQL tests prove business effects.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
if (!process.env.PLAYWRIGHT_MODULE)
  throw new Error("Set PLAYWRIGHT_MODULE; browser acceptance must not be silently skipped.");
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const context = await browser.newContext();
const page = await context.newPage();
page.setDefaultTimeout(10000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenants = [
  { id: "tenant_a", name: "Northstar Commerce", role: "owner", purpose: "playground" },
  { id: "tenant_b", name: "Second company" },
  { id: "tenant_practice", name: "Practice company", sandbox_run_id: "run_fixture" },
];
const user = {
  id: "user_test",
  email: "test@example.test",
  display_name: "Operator",
  status: "active",
  language: "en",
  locale: "en-GB",
  timezone: "UTC",
  is_platform_admin: false,
};
let rejectQuestion = false;
let simulation = "running";
let derivedState;
let failStatus = false;
let delayStatus = 0;
let statusReads = 0;
const requests = [];
const fixture = async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  requests.push(url.pathname);
  const respond = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (url.pathname.endsWith("/application-reference")) return respond(reference);
  if (url.pathname === "/api/auth/me") return respond(user);
  if (url.pathname === "/api/v1/bootstrap")
    return respond({ tenants, default_tenant_id: "tenant_a" });
  if (url.pathname.endsWith("/timeline"))
    return respond({ events: [], activities: [], has_more: false });
  if (url.pathname.endsWith("/demo-data")) {
    statusReads++;
    const captured = simulation;
    if (delayStatus) await new Promise((resolve) => setTimeout(resolve, delayStatus));
    return respond(
      {
        state: captured,
        derived_state: derivedState || captured,
        revision: 1,
        rate: 60,
        imported: 3,
        generated: 3,
        pending: 0,
        failed: 0,
        next_arrival: null,
      },
      failStatus ? 503 : 200,
    );
  }
  if (url.pathname.endsWith("/demo-data/imports"))
    return respond({ items: [], has_more: false, next_cursor: null });
  const tenant = tenants.find((row) => url.pathname.includes(row.id));
  if (url.pathname.endsWith("/analytics"))
    return respond({
      position: {
        open: 1,
        fully_reserved: 0,
        needs_reservation: 1,
        overdue: 0,
        unknown_due: 1,
        coverage_percent: "0",
      },
      series: [{ day: "2026-09-08", date: "2026-09-08", created: 1, shipped: 0 }],
    });
  if (url.pathname.endsWith("/dashboard")) {
    if (tenant?.id === "tenant_a") await new Promise((resolve) => setTimeout(resolve, 120));
    return respond({
      tenant,
      totals: {
        exceptions: 0,
        open_commitments: tenant?.id === "tenant_a" ? 12 : 0,
        open_deliveries: tenant?.id === "tenant_a" ? 12 : 0,
        pending_decisions: 0,
      },
      exceptions: [],
      inventory: [],
      facts: [],
      capabilities: {},
    });
  }
  if (url.pathname.endsWith("/copilot"))
    return respond({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (url.pathname.endsWith("/copilot/sessions"))
    return respond({ id: "chat_a", title: "New conversation" });
  if (url.pathname.endsWith("/messages")) {
    rejectQuestion = true;
    return respond({ detail: "Provider unavailable" }, 503);
  }
  if (url.pathname.endsWith("/change-proposals"))
    return respond({
      items: [],
      page: { number: 1, size: 50, total: 0, pages: 1, has_previous: false, has_next: false },
    });
  return respond({ detail: `Unexpected fixture request: ${url.pathname}` }, 404);
};
await page.route("**/api/**", fixture);
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5225";
const nav = page.locator("[data-primary-navigation]");
const header = page.locator("[data-shell-header]");
const chat = page.locator("[data-global-chat]");
const company = page.locator("[data-company-id]");
const box = (locator) => locator.boundingBox();
const bounded = async (locator, width) => {
  await locator.waitFor({ state: "visible" });
  const rect = await box(locator);
  assert.ok(rect && rect.x >= 0 && rect.x + rect.width <= width + 1);
  assert.ok(rect.y >= 0 && rect.y + rect.height <= 901);
};
try {
  await mkdir("/private/tmp/reality-225-browser", { recursive: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${base}/app?tenant=tenant_a&lang=en`);
  await company.waitFor();
  assert.equal((await box(header)).height, 48, "content header is 48px");
  assert.equal(await nav.locator("[data-company-id]").count(), 1);
  assert.equal((await box(nav)).y, 0);
  assert.equal((await box(chat)).y, 0);
  assert.equal((await box(chat.locator("header").first())).height, 48);
  assert.equal(await header.getByRole("button", { name: "Activity", exact: true }).count(), 0);
  await header.locator("[data-page-description-trigger]").click();
  const description = page.locator("[data-page-description]:popover-open");
  await description.waitFor();
  await page.keyboard.press("Escape");
  assert.equal(
    await header
      .locator("[data-page-description-trigger]")
      .evaluate((n) => n === document.activeElement),
    true,
  );
  const draft = chat.locator("textarea");
  await draft.fill("Preserve the current company draft");
  await header.getByRole("button", { name: "Hide chat", exact: true }).click();
  await header.getByRole("button", { name: "Show chat", exact: true }).click();
  assert.equal(await draft.inputValue(), "Preserve the current company draft");
  await nav.getByRole("button", { name: "Collapse sidebar", exact: true }).click();
  assert.equal((await box(nav)).width, 60);
  await company.click();
  await bounded(page.getByRole("dialog", { name: "Switch company", exact: true }), 1440);
  await page.keyboard.press("Escape");
  assert.equal(await nav.getByRole("button", { name: "Activity", exact: true }).count(), 0);
  await nav.getByRole("link", { name: "Activities", exact: true }).click();
  await page.locator("[data-inline-activity]").waitFor();
  assert.equal(new URL(page.url()).searchParams.get("inspector_view"), "history");
  assert.equal(await page.getByRole("dialog", { name: "Activity", exact: true }).count(), 0);
  assert.ok((await header.innerText()).includes("Activities"));
  const launcher = nav.locator("[data-action-launcher]");
  assert.equal(await nav.locator(".shell-navigation-utilities [data-action-launcher]").count(), 0);
  await draft.focus();
  await page.keyboard.press("Control+k");
  const palette = page.locator("[data-action-menu]:popover-open");
  await palette.waitFor();
  assert.equal(
    await palette.getByRole("searchbox").evaluate((n) => n === document.activeElement),
    true,
  );
  const paletteBox = await box(palette);
  assert.ok(Math.abs(paletteBox.x + paletteBox.width / 2 - 720) <= 1);
  await palette.getByRole("searchbox").fill("no-such-action");
  await page.keyboard.press("Escape");
  assert.equal(await draft.evaluate((n) => n === document.activeElement), true);
  await page.keyboard.press("Meta+k");
  await palette.waitFor();
  assert.equal(await palette.getByRole("searchbox").inputValue(), "");
  await page.keyboard.press("Escape");
  await launcher.getByRole("button", { name: "Search actions", exact: true }).click();
  await bounded(page.getByRole("dialog", { name: "Actions", exact: true }), 1440);
  assert.ok(
    (await page.getByRole("dialog", { name: "Actions", exact: true }).getByRole("button").count()) >
      1,
  );
  await page.keyboard.press("Escape");
  assert.equal(
    await launcher
      .getByRole("button", { name: "Search actions", exact: true })
      .evaluate((n) => n === document.activeElement),
    true,
  );
  await nav.getByRole("button", { name: "My account", exact: true }).click();
  const profile = page.getByRole("dialog", { name: "My account", exact: true });
  const oldTheme = await page.locator("html").getAttribute("data-theme");
  await profile.getByRole("button", { name: "Appearance", exact: true }).click();
  assert.notEqual(await page.locator("html").getAttribute("data-theme"), oldTheme);
  await page.keyboard.press("Escape");
  assert.equal(await draft.inputValue(), "Preserve the current company draft");
  await company.click();
  await page.locator('[data-company-option="tenant_b"]').click();
  await page.waitForURL(/tenant_b/);
  assert.equal(await draft.inputValue(), "");
  assert.equal(await page.locator("[data-live-simulation]").count(), 0);
  await nav.getByRole("button", { name: "Expand sidebar", exact: true }).click();
  await nav.getByRole("link", { name: "Chat", exact: true }).click();
  await page.waitForURL(/app\/chat/);
  assert.equal(await chat.isVisible(), false);
  assert.equal((await box(page.locator("#main-content"))).height, 852);
  await page.setViewportSize({ width: 1440, height: 500 });
  await nav.getByRole("button", { name: "My account", exact: true }).click();
  const shortProfile = await box(page.getByRole("dialog", { name: "My account", exact: true }));
  assert.ok(shortProfile.y >= 0 && shortProfile.y + shortProfile.height <= 500);
  await page.keyboard.press("Escape");

  tenants[0].name = "Northstar Commerce International Operations";
  for (const language of ["en", "de", "nl", "es"]) {
    user.language = language;
    for (const width of [320, 390, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`${base}/app?tenant=tenant_a&lang=${language}`);
      await header.waitFor();
      if (width < 1024) await page.locator("[data-navigation-opener]").click();
      await nav.waitFor({ state: "visible" });
      const activityLabel = {
        en: "Activities",
        de: "Aktivitäten",
        nl: "Activiteiten",
        es: "Actividades",
      }[language];
      assert.equal(await nav.getByRole("link", { name: activityLabel, exact: true }).count(), 1);
      assert.equal(
        await nav
          .locator(".shell-navigation-utilities")
          .getByText(activityLabel, { exact: true })
          .count(),
        0,
      );
      assert.equal(await nav.locator("[data-live-simulation]").count(), 0);
      await company.click();
      await bounded(page.locator('[role="dialog"]:popover-open'), width);
      await page.keyboard.press("Escape");
      await nav.locator("[data-action-launcher] > button").click();
      await bounded(page.locator("[data-action-menu]:popover-open"), width);
      if (language === "de") {
        const menu = page.locator("[data-action-menu]:popover-open");
        for (const label of [
          "Versandmeldung erfassen",
          "Paket versenden",
          "Paket empfangen",
          "Tracking-Ereignis erfassen",
          "Tracking-Ereignis korrigieren",
        ])
          assert.equal(await menu.getByRole("button", { name: label, exact: true }).count(), 1);
        if (width === 1440)
          await page.screenshot({
            path: "/private/tmp/reality-225-browser/command-palette-de.png",
            animations: "disabled",
          });
        await menu.getByRole("searchbox").fill("Paket");
        assert.deepEqual(await menu.locator("section button").allTextContents(), [
          "Paket versenden",
          "Paket empfangen",
        ]);
        await menu.getByRole("searchbox").fill("");
      }
      await page.keyboard.press("Escape");
      if (width < 1024) await nav.locator("[data-navigation-close]").click();
      for (const theme of ["light", "dark"]) {
        await page.evaluate((value) => {
          localStorage.setItem("reality.theme", value);
          window.dispatchEvent(new Event("reality:theme-changed"));
        }, theme);
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
        );
        await page.screenshot({
          path: `/private/tmp/reality-225-browser/${language}-${width}-${theme}.png`,
          animations: "disabled",
        });
      }
    }
  }
  user.language = "en";
  const touchContext = await browser.newContext({
    hasTouch: true,
    viewport: { width: 1024, height: 900 },
  });
  const touchPage = await touchContext.newPage();
  await touchPage.route("**/api/**", fixture);
  await touchPage.goto(`${base}/app?tenant=tenant_a&lang=en`);
  await touchPage.getByRole("button", { name: "Collapse sidebar", exact: true }).click();
  for (const selector of [
    "[data-company-id]",
    "[data-navigation-toggle]",
    ".shell-utility",
    "[data-navigation-item]",
    ".shell-chat-header .reality-chat-icon",
  ]) {
    await touchPage.locator(selector).first().waitFor();
    for (const element of await touchPage.locator(selector).all()) {
      const rect = await element.boundingBox();
      assert.ok(rect.width >= 44 && rect.height >= 44, selector);
    }
  }
  await touchPage.locator("[data-action-launcher] > button").click();
  for (const element of await touchPage.locator("[data-action-menu] button").all())
    assert.ok((await element.boundingBox()).height >= 44);
  await touchPage.setViewportSize({ width: 390, height: 900 });
  await touchPage.locator("[data-navigation-opener]").click();
  await touchPage.locator("[data-action-launcher] > button").click();
  await touchPage
    .getByRole("dialog", { name: "Actions", exact: true })
    .getByRole("button", { name: "Available actions", exact: true })
    .click();
  assert.equal(await touchPage.locator("[data-primary-navigation]").isVisible(), false);
  await touchPage.keyboard.press("Control+k");
  await touchPage.locator("[data-action-menu]:popover-open").waitFor();
  await bounded(touchPage.locator("[data-action-menu]:popover-open"), 390);
  await touchPage.keyboard.press("Escape");
  await touchContext.close();
  assert.deepEqual(errors, []);
  console.log(
    "PASS: refined shell placement, menus, drafts, company isolation and 32 localized layouts.",
  );
} catch (error) {
  await page.screenshot({ path: "/private/tmp/reality-225-browser/failure.png" });
  throw error;
} finally {
  await browser.close();
}
