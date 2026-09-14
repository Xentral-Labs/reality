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
  { id: "tenant_a", name: "Northstar Commerce" },
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
const requests = [];
await page.route("**/api/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  requests.push(url.pathname);
  const respond = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (url.pathname.endsWith("/application-reference"))
    return respond({
      workspaces: [{ actions: [{ command: "reserve" }, { command: "record_movement" }] }],
    });
  if (url.pathname === "/api/auth/me") return respond(user);
  if (url.pathname === "/api/v1/bootstrap")
    return respond({ tenants, default_tenant_id: "tenant_a" });
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
});
const base = "http://localhost:5177";
try {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${base}/app?tenant=tenant_a`);
  const panel = page.locator("[data-global-chat]");
  await panel.waitFor();
  assert.equal(
    await page.locator("[data-shell-header]").evaluate((n) => n.getBoundingClientRect().height),
    56,
  );
  const input = panel.getByRole("textbox", { name: "Ask about your company", exact: true });
  await input.fill("Keep this draft");
  await page.getByRole("button", { name: "Hide chat", exact: true }).first().click();
  assert.equal(await panel.isVisible(), false);
  await page.getByRole("button", { name: "Show chat", exact: true }).click();
  assert.equal(await input.inputValue(), "Keep this draft");
  await page.getByRole("link", { name: "Orders & deliveries", exact: true }).click();
  assert.equal(await input.inputValue(), "Keep this draft");
  const companyToggle = page.getByRole("button", { name: "Switch company", exact: true });
  await companyToggle.click();
  await page.getByRole("dialog", { name: "Switch company", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  assert.equal(await companyToggle.evaluate((n) => n === document.activeElement), true);
  assert.equal(
    await page
      .locator("[data-shell-header]")
      .getByRole("button", { name: "Company settings", exact: true })
      .count(),
    0,
  );
  const nav = page.locator("[data-primary-navigation]");
  assert.equal(await nav.getByRole("link", { name: "Playground", exact: true }).count(), 0);
  assert.equal(await nav.getByRole("link", { name: "More workspaces", exact: true }).count(), 0);
  assert.deepEqual(
    await nav
      .getByRole("navigation", { name: "Daily work", exact: true })
      .getByRole("link")
      .allTextContents(),
    ["Home", "Exceptions", "Decisions"],
  );
  const primary = await nav.locator("a[data-navigation-item]").allTextContents();
  assert.deepEqual(
    await nav
      .locator("nav")
      .evaluateAll((nodes) =>
        nodes.map(
          (n) =>
            n.getAttribute("aria-label") ||
            document.getElementById(n.getAttribute("aria-labelledby"))?.textContent.trim(),
        ),
      ),
    ["Daily work", "Workspaces", "Analytics", "Reality Inspector", "Company"],
  );
  const analytics = nav.getByRole("navigation", { name: "Analytics", exact: true });
  assert.deepEqual(await analytics.getByRole("link").allTextContents(), ["Reports"]);
  assert.equal(await nav.getByRole("link", { name: "Analytics", exact: true }).count(), 0);
  assert.equal(primary.at(-1).trim(), "Settings");
  assert.ok(
    await nav
      .locator("a[data-navigation-item]")
      .first()
      .evaluate((n) => n.getBoundingClientRect().height <= 38),
  );
  await page.getByRole("link", { name: "Reports", exact: true }).click();
  await page.waitForURL(/app\/analytics/);
  assert.equal(await input.inputValue(), "Keep this draft");
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="tenant_b"]').click();
  assert.equal(
    await panel.getByRole("textbox", { name: "Ask about your company", exact: true }).inputValue(),
    "",
  );
  assert.equal(
    await page.getByRole("textbox", { name: "Ask about your company", exact: true }).count(),
    1,
  );
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="tenant_practice"]').click();
  await page
    .getByText("Practice companies are not available in this interface. Choose another company.", {
      exact: true,
    })
    .waitFor();
  assert.equal(await page.locator('a[href^="/playground"], a[href^="/app/orders?"]').count(), 0);
  await page.getByRole("button", { name: "Northstar Commerce", exact: true }).click();
  await page.locator("[data-shell-header]").waitFor();
  await mkdir("/private/tmp/reality-135-browser", { recursive: true });
  for (const language of ["en", "de", "nl", "es"])
    for (const width of [390, 1440, 1920])
      for (const theme of ["light", "dark"]) {
        user.language = language;
        const show = {
          en: "Show chat",
          de: "Chat einblenden",
          nl: "Chat tonen",
          es: "Mostrar chat",
        }[language];
        const hide = {
          en: "Hide chat",
          de: "Chat ausblenden",
          nl: "Chat verbergen",
          es: "Ocultar chat",
        }[language];
        await page.setViewportSize({ width, height: 900 });
        await page.goto(`${base}/app?tenant=tenant_a`);
        await page.locator("h1").waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        if (width < 1024) await page.getByRole("button", { name: show, exact: true }).click();
        await panel.locator("textarea").waitFor();
        const brand = await page.locator("[data-shell-header] .shell-brand").boundingBox();
        const companyTrigger = await page.locator("[data-company-id]").boundingBox();
        assert.ok(brand && companyTrigger);
        assert.ok(
          companyTrigger.x >= brand.x &&
            companyTrigger.x + companyTrigger.width <= brand.x + brand.width + 1,
        );
        assert.equal(await page.locator("[data-company-id]").count(), 1);
        if (width >= 1024) {
          const [headerCenter, headerControls, chat] = await Promise.all([
            page.locator(".shell-header-center").boundingBox(),
            page.locator("[data-shell-header] > .shell-controls").boundingBox(),
            panel.boundingBox(),
          ]);
          assert.ok(headerCenter && headerControls && chat);
          assert.ok(Math.abs(headerCenter.x + headerCenter.width - chat.x) <= 1);
          assert.ok(headerControls.x >= chat.x);
        }
        assert.equal(
          (await page.locator("#analytics-navigation-label").textContent()).trim(),
          "Analytics",
        );
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
        );
        await page.evaluate(() => window.scrollTo(0, 500));
        assert.equal(
          await page.locator("[data-shell-header]").evaluate((n) => n.getBoundingClientRect().top),
          0,
        );
        await page.screenshot({
          path: `/private/tmp/reality-135-browser/${language}-${width}-${theme}.png`,
        });
        await page.getByRole("button", { name: hide, exact: true }).first().click();
        await page.screenshot({
          path: `/private/tmp/reality-135-browser/${language}-${width}-${theme}-closed.png`,
        });
        await page.locator("[data-company-id]").click();
        const menu = page.locator("[popover]:popover-open");
        await menu.waitFor();
        const bounds = await menu.boundingBox();
        assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= width);
        assert.equal(await menu.locator('[aria-pressed="true"]').count(), 1);
        await page.screenshot({
          path: `/private/tmp/reality-135-browser/${language}-${width}-${theme}-company.png`,
          animations: "disabled",
        });
        await page.mouse.click(width - 4, 890);
        assert.equal(await menu.count(), 0);
      }
  assert.deepEqual(errors, []);
  console.log(
    "PASS: compact sticky shell, Analytics order, persistent isolated chat and 48 localized layouts.",
  );
} catch (error) {
  await page.screenshot({ path: "/private/tmp/reality-135-failure.png" });
  throw error;
} finally {
  await browser.close();
}
