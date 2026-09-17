import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
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
      language: "en",
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
      sessions: exists ? [{ id: "first", title: "First conversation" }] : [],
      active_session_id: exists ? "first" : null,
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
const newChat = page.locator("[data-free-play-toolbar] [data-new-chat-action]");
try {
  await page.goto(`${base}/app/chat?tenant=one`);
  await newChat.waitFor();
  assert.equal(await history.isVisible(), false);
  await page.locator("[data-independent-free-play] textarea").fill("Keep this draft");
  await page.screenshot({ path: "/private/tmp/reality-empty-chat.png" });
  await newChat.click();
  const toggle = page
    .locator("[data-free-play-toolbar]")
    .getByRole("button", { name: "Conversation history", exact: true });
  await toggle.waitFor();
  assert.equal(await history.isVisible(), false, "first session must not expand history");
  await page
    .locator("[data-independent-free-play] textarea")
    .fill("Draft stays while opening history");
  await toggle.click();
  await history.waitFor({ state: "visible" });
  await page.keyboard.press("Escape");
  assert.equal(
    await page.locator("[data-independent-free-play] textarea").inputValue(),
    "Draft stays while opening history",
  );
  await history.waitFor({ state: "hidden" });
  await page.reload();
  await history.waitFor({ state: "visible" });
  await page.setViewportSize({ width: 390, height: 844 });
  await history.waitFor({ state: "hidden" });
  await toggle.click();
  await history.waitFor({ state: "visible" });
  await page.keyboard.press("Escape");
  await history.waitFor({ state: "hidden" });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.evaluate(() => {
    window.history.pushState({}, "", "/app/chat?tenant=two");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await newChat.waitFor();
  await history.waitFor({ state: "hidden" });
  archived = true;
  await page.reload();
  await history.waitFor({ state: "visible" });
  archived = false;
  unavailable = true;
  await page.goto(`${base}/app/chat?tenant=one`);
  await page.getByRole("button", { name: "Retry", exact: true }).first().waitFor();
  assert.equal(await history.isVisible(), false);
  unavailable = false;
  saved = true;
  await page.getByRole("button", { name: "Retry", exact: true }).first().click();
  await history.waitFor({ state: "visible" });
  assert.deepEqual(errors, []);
  console.log(
    "PASS empty history, first-session stability, explicit access, revisit, mobile, tenant isolation and archived access",
  );
} finally {
  await browser.close();
}
