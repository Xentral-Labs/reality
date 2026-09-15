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
let fresh = true;
const sent = [];
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
      sessions: [
        { id: "chat_a", title: "Stock review" },
        { id: "chat_b", title: "Earlier conversation" },
      ],
      active_session_id: url.searchParams.get("session_id") || "chat_a",
      messages: fresh
        ? []
        : [
            {
              id: "answer",
              role: "assistant",
              created_at: "2026-09-08T10:00:00Z",
              content:
                "Here are the recorded quantities.\n\n| SKU | Product | Available |\n| --- | --- | ---: |\n| LAMP-01 | Desk lamp | 8 |\n| LAMP-02 | Reading lamp | 4 |\n\nOpen a delivery to review the next step.",
            },
            ...sent.flatMap((text, index) => [
              {
                id: `sent_${index}`,
                role: "user",
                created_at: "2026-09-08T10:01:00Z",
                content: text,
              },
              {
                id: `reply_${index}`,
                role: "assistant",
                created_at: "2026-09-08T10:01:05Z",
                content: `Recorded answer ${index + 1}.`,
              },
            ]),
          ],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (url.pathname.endsWith("/copilot/sessions"))
    return respond({ id: "chat_a", title: "New conversation" });
  if (url.pathname.endsWith("/messages")) {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    if (!sent.length && requests.filter((path) => path.endsWith("/messages")).length === 1)
      return respond({ detail: "Provider unavailable" }, 503);
    sent.push(request.postDataJSON().message);
    return respond({ id: `sent_${sent.length - 1}` });
  }
  if (url.pathname.endsWith("/change-proposals"))
    return respond({
      items: [],
      page: { number: 1, size: 50, total: 0, pages: 1, has_previous: false, has_next: false },
    });
  return respond({ detail: `Unexpected fixture request: ${url.pathname}` }, 404);
});
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
await page.addInitScript(() => {
  window.SpeechRecognition = window.webkitSpeechRecognition = class {
    start() {
      window.voice = this;
      this.onstart?.();
    }
    stop() {
      window.voiceStopped = true;
      this.onend?.();
    }
    abort() {
      window.voiceStopped = true;
      this.onend?.();
    }
  };
});
try {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/app?tenant=tenant_a&lang=en`);
  const nav = page.locator("[data-primary-navigation]");
  const collapse = page.getByRole("button", { name: "Collapse sidebar", exact: true });
  await collapse.waitFor();
  const heading = nav.locator(".shell-navigation-heading");
  assert.ok((await heading.boundingBox()).height <= 36);
  const links = nav.locator("a[data-navigation-item]");
  const names = await links.allTextContents();
  const width = async (locator) => (await locator.boundingBox()).width;
  assert.equal(await width(nav), 200);
  const content = page.locator("#main-content");
  const before = await width(content);
  const draft = page.locator("[data-global-chat] textarea");
  await draft.fill("Preserve my draft");
  await collapse.focus();
  await collapse.press("Enter");
  const expand = page.getByRole("button", { name: "Expand sidebar", exact: true });
  assert.equal(await expand.getAttribute("aria-expanded"), "false");
  assert.equal(await width(nav), 60);
  assert.equal(await width(content), before + 140);
  assert.equal(await draft.inputValue(), "Preserve my draft");
  assert.deepEqual(await links.allTextContents(), names);
  for (const link of await links.all()) {
    assert.equal(await link.getAttribute("title"), null);
    assert.ok(await link.getAttribute("aria-label"));
  }
  const chatLink = nav.getByRole("link", { name: "Chat", exact: true });
  await chatLink.hover();
  const tooltip = page.getByRole("tooltip");
  await tooltip.waitFor();
  assert.equal(await tooltip.textContent(), "Chat");
  assert.ok((await tooltip.boundingBox()).x >= (await nav.boundingBox()).width);
  assert.equal(await tooltip.evaluate((n) => getComputedStyle(n).color), "rgb(255, 255, 255)");
  await page.screenshot({ path: "/private/tmp/reality-203-tooltip.png" });
  await page.keyboard.press("Escape");
  await tooltip.waitFor({ state: "hidden" });
  await page.mouse.move(800, 400);
  await chatLink.focus();
  await tooltip.waitFor();
  await nav.evaluate((n) => n.dispatchEvent(new Event("scroll")));
  await tooltip.waitFor({ state: "hidden" });
  await nav.getByRole("button", { name: "Profile", exact: true }).click();
  await page.getByRole("dialog", { name: "Profile", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.getByRole("dialog", { name: "Switch company", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  await nav.getByRole("link", { name: "Chat", exact: true }).click();
  await page.waitForURL(/app\/chat/);
  assert.equal(await width(nav), 60);
  assert.equal(
    await nav.getByRole("link", { name: "Chat", exact: true }).getAttribute("aria-current"),
    "page",
  );
  await page.reload();
  await expand.waitFor();
  assert.equal(await width(nav), 60);
  await mkdir("/private/tmp/reality-203-browser", { recursive: true });
  await page.screenshot({ path: "/private/tmp/reality-203-browser/collapsed.png" });
  await expand.click();
  assert.equal(await width(nav), 200);
  await page.screenshot({ path: "/private/tmp/reality-203-browser/expanded.png" });
  await collapse.click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Navigation", exact: true }).click();
  await nav.waitFor({ state: "visible" });
  assert.equal(await width(nav), 240);
  assert.equal(
    await nav
      .locator("[data-navigation-label]")
      .first()
      .evaluate((n) => getComputedStyle(n).position),
    "static",
  );
  await page.screenshot({ path: "/private/tmp/reality-203-browser/mobile.png" });
  await nav.getByRole("button", { name: "Close", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  assert.equal(await width(nav), 60);
  for (const [language, label] of [
    ["de", "Seitenleiste öffnen"],
    ["nl", "Zijbalk openen"],
    ["es", "Abrir barra lateral"],
  ]) {
    user.language = language;
    await page.goto(`${base}/app/chat?tenant=tenant_a&lang=${language}`);
    await page.getByRole("button", { name: label, exact: true }).waitFor();
  }
  await page.addInitScript(() => {
    const read = Storage.prototype.getItem;
    const write = Storage.prototype.setItem;
    Storage.prototype.getItem = function (key) {
      if (key === "reality.navigation.collapsed") throw new Error("Storage blocked");
      return read.call(this, key);
    };
    Storage.prototype.setItem = function (key, value) {
      if (key === "reality.navigation.collapsed") throw new Error("Storage blocked");
      return write.call(this, key, value);
    };
  });
  user.language = "en";
  await page.goto(`${base}/app/chat?tenant=tenant_a&lang=en`);
  await collapse.waitFor();
  await collapse.click();
  assert.equal(await width(nav), 60);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: collapsible primary navigation, keyboard, profile, persistence, draft preservation, mobile and localization.",
  );
} finally {
  await browser.close();
}
