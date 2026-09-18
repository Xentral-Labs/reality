import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en";
let many = false;
let saved = false,
  archived = false,
  unavailable = false;
await page.route("**/api/**", async (route) => {
  const path = new URL(route.request().url()).pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (path === "/api/auth/me")
    return reply({
      id: "user",
      email: "user@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "one", name: "One", purpose: "playground" },
        { id: "two", name: "Two", purpose: "playground" },
      ],
      default_tenant_id: "one",
    });
  if (path.endsWith("/copilot/sessions") && route.request().method() === "POST") {
    saved = true;
    return reply({ id: "first", title: "First conversation" });
  }
  if (path.endsWith("/copilot")) {
    if (unavailable) return reply({ detail: "Unavailable" }, 503);
    const exists = saved && path.includes("/one/");
    return reply({
      sessions: exists
        ? [
            { id: "first", title: "First conversation", message_count: 1 },
            ...(many
              ? Array.from({ length: 40 }, (_, i) => ({
                  id: `older-${i}`,
                  title: `Older conversation ${i}`,
                  message_count: 1,
                }))
              : []),
          ]
        : [],
      active_session_id: exists
        ? new URL(route.request().url()).searchParams.get("session_id") || "first"
        : null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: archived,
    });
  }
  return reply({ items: [], workspaces: [], commands: [] });
});
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5225";
const history = page.locator("[data-free-play-sessions]");
const newChat = page.getByRole("button", { name: "New chat", exact: true });
const actions = page.locator(".shell-workspace-header .page-inline-actions");
const toggle = actions.getByRole("button", { name: "History", exact: true });
const openActions = async () => {
  await newChat.waitFor();
  assert.equal(await page.locator(".shell-workspace-header .register-actions").count(), 0);
};
const openHistory = async () => {
  await openActions();
  await toggle.click();
  await history.waitFor({ state: "visible" });
  assert.equal(await toggle.getAttribute("aria-expanded"), "true");
};
try {
  await page.goto(`${base}/app/chat?tenant=one`);
  await openActions();
  assert.equal(await history.isVisible(), false);
  assert.equal(await toggle.count(), 0);
  assert.equal(await page.locator("[data-independent-free-play] header").count(), 0);
  await newChat.click();
  await openActions();
  await toggle.waitFor();
  assert.equal(await history.isVisible(), false);
  const composer = page.locator("[data-independent-free-play] textarea");
  await composer.fill("Keep this draft");
  const bounds = await page.locator("[data-independent-free-play]").boundingBox();
  assert.ok((await toggle.boundingBox()).x < (await newChat.boundingBox()).x);
  await openHistory();
  await toggle.click();
  await history.waitFor({ state: "hidden" });
  await openHistory();
  assert.deepEqual(await page.locator("[data-independent-free-play]").boundingBox(), bounds);
  assert.ok((await history.boundingBox()).x > bounds.x + bounds.width / 2);
  await page.screenshot({ path: "/private/tmp/reality-chat-history-desktop.png" });
  await history.locator("[data-chat-session-menu=first] summary").click();
  await history.locator("[data-chat-session-archive=first]").click();
  await page
    .locator("[data-chat-removal-dialog]")
    .getByRole("button", { name: "Cancel", exact: true })
    .click();
  await page.keyboard.press("Escape");
  await history.waitFor({ state: "hidden" });
  assert.equal(await toggle.evaluate((el) => el === document.activeElement), true);
  assert.equal(await composer.inputValue(), "Keep this draft");
  await openHistory();
  await composer.click({ position: { x: 12, y: 12 } });
  await history.waitFor({ state: "hidden" });
  await page.reload();
  await actions.waitFor();
  assert.equal(await history.isVisible(), false);
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await openHistory();
    assert.ok(await history.evaluate((el) => el.getBoundingClientRect().right <= innerWidth));
    assert.ok(await actions.evaluate((el) => el.getBoundingClientRect().right <= innerWidth));
    await page.screenshot({ path: `/private/tmp/reality-chat-history-mobile-${width}.png` });
    await page.keyboard.press("Escape");
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await openHistory();
  await page.evaluate(() => {
    window.history.pushState({}, "", "/app/chat?tenant=two");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await history.waitFor({ state: "hidden" });
  archived = true;
  await page.reload();
  await openHistory();
  archived = false;
  unavailable = true;
  await page.goto(`${base}/app/chat?tenant=one`);
  await page.getByRole("button", { name: "Retry", exact: true }).first().waitFor();
  assert.equal(await history.isVisible(), false);
  unavailable = false;
  saved = true;
  await page.getByRole("button", { name: "Retry", exact: true }).first().click();
  await openHistory();
  await page.keyboard.press("Escape");
  many = true;
  await page.reload();
  await openHistory();
  assert.ok((await history.boundingBox()).height <= 512);
  const last = history.locator("[data-chat-session]").last();
  await last.scrollIntoViewIfNeeded();
  await last.click();
  await history.waitFor({ state: "hidden" });
  await openHistory();
  await openActions();
  await newChat.click();
  await history.waitFor({ state: "hidden" });
  for (const code of ["de", "nl", "es"]) {
    language = code;
    await page.setViewportSize({ width: 320, height: 844 });
    await page.reload();
    await actions.getByRole("button").last().waitFor();
    assert.equal(await actions.getByRole("button").count(), 2);
    assert.ok((await page.locator(".shell-workspace-header h1").boundingBox()).width >= 24);
    assert.ok(await actions.evaluate((el) => el.getBoundingClientRect().right <= innerWidth));
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({ path: `/private/tmp/reality-chat-header-${code}.png` });
  }
  assert.deepEqual(errors, []);
  console.log(
    "PASS direct header actions, history, drafts, focus, archive, mobile, tenant isolation and scrolling",
  );
} finally {
  await browser.close();
}
