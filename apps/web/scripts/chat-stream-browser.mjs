// Synthetic HTTP fixtures exercise presentation only; PostgreSQL tests prove business effects.
import assert from "node:assert/strict";

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
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5186";
await page.addInitScript(() => {
  const original = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    if (String(input).includes("/messages?stream=true")) {
      window.chatSends = (window.chatSends || 0) + 1;
      const body = new ReadableStream({
        start(controller) {
          window.chatController = controller;
        },
      });
      return new Response(body, { headers: { "Content-Type": "application/x-ndjson" } });
    }
    return original(input, init);
  };
  window.chatEmit = (event) =>
    window.chatController.enqueue(new TextEncoder().encode(JSON.stringify(event) + "\n"));
});
try {
  await page.goto(`${base}/app/chat?tenant=tenant_a&session=chat_a`);
  const input = page.locator("textarea").first();
  await input.waitFor();
  await input.fill("Which customer orders are still open?");
  await input.press("Enter");
  await page.waitForFunction(() => !!window.chatController);
  await page.evaluate(() => window.chatEmit({ type: "delta", text: "Early answer" }));
  await page.getByText("Early answer", { exact: true }).waitFor();
  // The working indicator stays put while the stream runs, so tool rounds never make it blink.
  assert.equal(await page.locator("[data-chat-working]").count(), 1);
  assert.equal(await page.evaluate(() => window.chatSends), 1);
  await page.evaluate(() => window.chatEmit({ type: "reset" }));
  await page.getByText("Early answer", { exact: true }).waitFor({ state: "hidden" });
  await page.evaluate(() => window.chatEmit({ type: "delta", text: "Final Grüße" }));
  await page.getByText("Final Grüße", { exact: true }).waitFor();
  await page.evaluate(() => {
    window.chatEmit({
      type: "done",
      user: { id: "u1", content: "Which customer orders are still open?" },
      assistant: { id: "a1", content: "Final Grüße" },
    });
    window.chatController.close();
  });
  await page.waitForTimeout(250);
  assert.equal(await page.locator("[data-chat-working]").count(), 0);
  assert.equal(await page.getByText("Final Grüße", { exact: true }).count(), 1);
  assert.equal(
    await page
      .locator(".reality-chat-message")
      .getByText("Which customer orders are still open?", { exact: true })
      .count(),
    1,
  );
  assert.equal(await page.evaluate(() => window.chatSends), 1);
  // A metadata reload with stale rows must not erase the completed answer.
  await page.waitForTimeout(250);
  assert.equal(await page.getByText("Final Grüße", { exact: true }).count(), 1);
  await page.screenshot({ path: "/tmp/reality-chat-perf/stream-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: "/tmp/reality-chat-perf/stream-mobile.png" });
  // A truncated second request restores the draft, discards provisional output and never resends.
  await page.setViewportSize({ width: 1440, height: 900 });
  await input.fill("Check unpaid invoices");
  await input.press("Enter");
  await page.waitForFunction(() => window.chatSends === 2);
  await page.evaluate(() => {
    window.chatEmit({ type: "delta", text: "Incomplete answer" });
    window.chatController.close();
  });
  await page
    .getByText("Chat response is incomplete. Reload to check its status.", { exact: true })
    .waitFor();
  assert.equal(await input.inputValue(), "Check unpaid invoices");
  assert.equal(await page.getByText("Incomplete answer", { exact: true }).count(), 0);
  assert.equal(await page.evaluate(() => window.chatSends), 2);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: early text, reset, completion, stale reload, no duplicate send and narrow viewport",
  );
} finally {
  await browser.close();
}
