// Synthetic HTTP fixtures exercise presentation only; PostgreSQL tests prove business effects.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
if (!process.env.PLAYWRIGHT_MODULE)
  throw new Error("Set PLAYWRIGHT_MODULE; browser acceptance must not be silently skipped.");
const playwrightModule = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const chromium = playwrightModule.chromium ?? playwrightModule.default?.chromium;
if (!chromium) throw new Error("The configured Playwright module does not expose Chromium.");
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
        { id: "chat_a", title: "Stock review", message_count: 0 },
        { id: "chat_b", title: "Earlier conversation", message_count: 2 },
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
    return respond({
      user: { id: `sent_${sent.length - 1}`, content: request.postDataJSON().message },
      assistant: { id: `reply_${sent.length - 1}`, content: `Recorded answer ${sent.length}.` },
    });
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
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${base}/app?tenant=tenant_a`);
  const dock = page.locator("[data-global-chat]");
  await dock.getByRole("button", { name: "Conversation history", exact: true }).waitFor();
  const input = dock.getByRole("textbox", { name: "Ask about your company", exact: true });
  const starters = dock.locator("[data-chat-starters] button");
  await starters.first().waitFor();
  assert.equal(await starters.count(), 3);
  await mkdir("/private/tmp/reality-201-browser", { recursive: true });
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  }
  await page.screenshot({ path: "/private/tmp/reality-201-browser/desktop.png" });
  const firstQuestion = "Which customer orders are still open?";
  await starters.first().focus();
  await starters.first().press("Enter");
  assert.equal(await input.inputValue(), firstQuestion);
  assert.ok(await input.evaluate((node) => node === document.activeElement));
  assert.equal(requests.filter((path) => path.endsWith("/messages")).length, 0);
  assert.equal(await starters.nth(1).isDisabled(), true);
  await input.fill("");
  await starters.nth(1).click();
  assert.equal(await input.inputValue(), "Which items have insufficient stock for open orders?");
  await input.fill("");
  await starters.nth(2).click();
  assert.equal(await input.inputValue(), "Which customer invoices are overdue?");
  for (const [language, expected] of [
    ["de", "Welche Kundenaufträge sind noch offen?"],
    ["nl", "Welke klantorders staan nog open?"],
    ["es", "¿Qué pedidos de clientes siguen abiertos?"],
  ]) {
    user.language = language;
    await page.goto(`${base}/app?tenant=tenant_a&lang=${language}`);
    await starters.first().waitFor();
    assert.equal(await starters.first().textContent(), expected);
    await starters.first().click();
    assert.equal(await dock.locator("textarea").inputValue(), expected);
    assert.equal(requests.filter((path) => path.endsWith("/messages")).length, 0);
  }
  user.language = "en";
  fresh = false;
  await page.goto(`${base}/app?tenant=tenant_a&lang=en`);
  await dock.locator("table").waitFor();
  assert.equal(await starters.count(), 0);
  assert.equal(
    await dock
      .locator(".reality-chat-message")
      .first()
      .evaluate((n) => getComputedStyle(n).borderTopWidth),
    "0px",
  );
  assert.equal(await dock.getByRole("combobox", { name: "Conversation", exact: true }).count(), 0);
  await dock.getByRole("button", { name: "Conversation history", exact: true }).click();
  await dock.getByRole("combobox", { name: "Conversation", exact: true }).selectOption("chat_b");
  await page.waitForURL(/session=chat_b/);
  await dock.getByRole("button", { name: "New conversation", exact: true }).click();
  await page.waitForURL(/session=chat_a/);
  await input.fill("Keep draft");
  await input.press("Shift+Enter");
  assert.ok((await input.inputValue()).includes("\n"));
  await dock.locator("input[type=file]").setInputFiles({
    name: "notes.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Original <script>text</script>"),
  });
  await page.waitForFunction(() =>
    document
      .querySelector("[data-global-chat] textarea")
      .value.includes("Original <script>text</script>"),
  );
  await dock
    .locator("input[type=file]")
    .setInputFiles({ name: "image.png", mimeType: "image/png", buffer: Buffer.from([0, 1, 2]) });
  await dock.getByRole("alert").waitFor();
  await dock
    .locator("input[type=file]")
    .setInputFiles({ name: "big.txt", mimeType: "text/plain", buffer: Buffer.alloc(65537, 65) });
  assert.ok(!(await input.inputValue()).includes("big.txt"));
  await dock
    .locator("input[type=file]")
    .setInputFiles({ name: "long.txt", mimeType: "text/plain", buffer: Buffer.alloc(4100, 65) });
  await dock
    .getByText("This file would exceed the 4,000-character message limit.", { exact: true })
    .waitFor();
  assert.ok(!(await input.inputValue()).includes("long.txt"));
  await dock.getByRole("button", { name: "Dictate", exact: true }).click();
  await page.evaluate(() =>
    window.voice.onresult({
      results: [Object.assign([{ transcript: "Voice draft" }], { isFinal: true })],
    }),
  );
  await page.waitForFunction(() =>
    document.querySelector("[data-global-chat] textarea").value.includes("Voice draft"),
  );
  await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  assert.equal(await page.evaluate(() => window.voiceStopped), true);
  await page.getByRole("button", { name: "Show chat", exact: true }).click();
  assert.ok((await input.inputValue()).includes("Voice draft"));
  await page.evaluate(() => {
    window.SpeechRecognition = undefined;
    window.webkitSpeechRecognition = undefined;
  });
  await dock.getByRole("button", { name: "Dictate", exact: true }).click();
  await dock.getByText("Voice input is unavailable in this browser.", { exact: true }).waitFor();
  await input.fill("Question with retained failure");
  await input.press("Enter");
  // The sent question shows up as the person's message at once and the field empties.
  const pending = dock.locator("[data-chat-pending]");
  await pending.waitFor();
  assert.ok((await pending.textContent()).includes("Question with retained failure"));
  assert.ok((await pending.textContent()).startsWith("You"));
  assert.equal(await input.inputValue(), "");
  const userTurn = pending;
  const assistantTurn = dock.locator('[data-chat-role="assistant"]').first();
  const userBox = await userTurn.boundingBox();
  const assistantBox = await assistantTurn.boundingBox();
  assert.ok(userBox.x > assistantBox.x, "user bubbles are right aligned");
  assert.ok(userBox.width < assistantBox.width, "user bubbles fit their content");
  assert.notEqual(
    await userTurn.evaluate((node) => getComputedStyle(node).backgroundColor),
    "rgba(0, 0, 0, 0)",
  );
  assert.equal(
    await assistantTurn.evaluate((node) => getComputedStyle(node).backgroundColor),
    "rgba(0, 0, 0, 0)",
  );
  await dock.getByRole("status").filter({ hasText: "Reality is working…" }).waitFor();
  const indicator = dock.locator("[data-chat-working] svg");
  assert.notEqual(await indicator.evaluate((node) => getComputedStyle(node).animationName), "none");
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(await indicator.evaluate((node) => getComputedStyle(node).animationName), "none");
  await page.screenshot({ path: "/private/tmp/chat-working-preview.png" });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await dock.getByRole("alert").filter({ hasText: "Provider unavailable" }).waitFor();
  // A failed send returns the draft to the field and withdraws the unsent message.
  assert.equal(await input.inputValue(), "Question with retained failure");
  assert.equal(await pending.count(), 0);
  assert.equal(
    await dock.getByRole("status").filter({ hasText: "Reality is working…" }).count(),
    0,
  );
  await page.waitForFunction(
    () => document.activeElement === document.querySelector("[data-global-chat] textarea"),
  );
  await dock.locator("button[type=submit]").click();
  await pending.waitFor();
  assert.equal(await input.inputValue(), "");
  await dock.getByText("Recorded answer 1.", { exact: true }).waitFor();
  // The recorded copy replaces the echo: exactly one message from the person remains.
  assert.equal(await pending.count(), 0);
  assert.equal(
    await dock
      .locator(".reality-chat-message")
      .filter({ hasText: "Question with retained failure" })
      .count(),
    1,
  );
  assert.equal(await input.inputValue(), "");
  assert.equal(
    await dock.getByRole("status").filter({ hasText: "Reality is working…" }).count(),
    0,
  );
  await page.waitForFunction(
    () => document.activeElement === document.querySelector("[data-global-chat] textarea"),
  );
  await input.fill("Keep my new focus");
  await input.press("Enter");
  await pending.waitFor();
  await dock.getByRole("button", { name: "Conversation history", exact: true }).click();
  const history = dock.getByRole("button", { name: "Conversation history", exact: true });
  await history.focus();
  await dock.getByText("Recorded answer 2.", { exact: true }).waitFor();
  assert.equal(await history.evaluate((node) => node === document.activeElement), true);
  await mkdir("/private/tmp/reality-136-browser", { recursive: true });
  for (const width of [390, 1440])
    for (const theme of ["light", "dark"]) {
      await page.setViewportSize({ width, height: 900 });
      await page.evaluate(
        (theme) => document.documentElement.setAttribute("data-theme", theme),
        theme,
      );
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({
        animations: "disabled",
        path: `/private/tmp/reality-136-browser/${width}-${theme}.png`,
      });
    }
  fresh = true;
  await page.goto(`${base}/app/chat?tenant=tenant_a&lang=en`);
  const chatPage = page.locator("[data-independent-free-play]");
  await chatPage.locator("[data-chat-starters] button").first().waitFor();
  assert.equal(await chatPage.locator("[data-chat-starters] button").count(), 3);
  await page.screenshot({ path: "/private/tmp/reality-202-chat-page.png" });
  // FR-023: compact persistent history; retain the larger drawer targets.
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    if (width < 1280)
      await chatPage.getByRole("button", { name: "Conversation history", exact: true }).click();
    const first = await page.locator('[data-chat-session="chat_a"]').boundingBox();
    const second = await page.locator('[data-chat-session="chat_b"]').boundingBox();
    assert.ok(first && second);
    const sidebar = await page.locator("[data-free-play-sessions]").boundingBox();
    assert.equal(sidebar.width, width >= 1280 ? 288 : 256, "history width");
    assert.equal(first.height, width >= 1280 ? 36 : 40, "session button height");
    assert.equal(second.y - first.y, width >= 1280 ? 36 : 44, "session row spacing");
    await page.screenshot({ path: `/private/tmp/reality-session-spacing-${width}.png` });
    if (width < 1280)
      await page
        .locator("[data-free-play-sessions]")
        .getByRole("button", { name: "Close", exact: true })
        .click();
  }
  await page.setViewportSize({ width: 1440, height: 900 });

  // FR-024: keyboard and hover reveal options without changing row geometry.
  const menu = page.locator('[data-chat-session-menu="chat_b"]');
  const opacity = () => menu.evaluate((el) => getComputedStyle(el).opacity);
  await page.mouse.move(1000, 800);
  assert.equal(await opacity(), "0");
  await menu.locator("summary").focus();
  assert.equal(await opacity(), "1");
  await menu.locator("summary").evaluate((el) => el.blur());
  await page.locator('[data-chat-session="chat_b"]').hover();
  assert.equal(await opacity(), "1");
  await menu.locator("summary").click();
  await page.mouse.move(1000, 800);
  await menu.locator("summary").evaluate((el) => el.blur());
  assert.equal(await opacity(), "1", "open menu remains visible");
  await menu.locator("summary").click();
  const touch = await context.newCDPSession(page);
  await touch.send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 1 });
  await page.mouse.move(1000, 800);
  await menu.locator("summary").evaluate((el) => el.blur());
  assert.equal(await opacity(), "1", "touch options remain visible without hover");
  await touch.send("Emulation.setTouchEmulationEnabled", { enabled: false });
  await touch.detach();
  await page.goto(`${base}/app/chat?tenant=tenant_a&lang=de`);
  await menu.locator("summary").click();
  const archive = menu.getByRole("button", { name: "Chat archivieren", exact: true });
  await archive.waitFor();
  const label = await archive.evaluate((el) => {
    const range = document.createRange();
    range.selectNode(el.lastChild);
    return { lines: range.getClientRects().length, overflow: el.scrollWidth > el.clientWidth };
  });
  assert.equal(label.lines, 1);
  assert.equal(label.overflow, false);
  await page.screenshot({ path: "/private/tmp/reality-chat-history-room.png" });
  await page.goto(`${base}/app/chat?tenant=tenant_a&lang=en`);

  await page.locator('[data-chat-session-menu="chat_a"] summary').click();
  await page.getByRole("button", { name: "Delete chat", exact: true }).click();
  const removalDialog = page.getByRole("dialog", { name: "Delete chat", exact: true });
  await removalDialog.waitFor();
  await removalDialog
    .getByText(
      "This empty chat has no messages. It will be permanently deleted and cannot be restored.",
      { exact: true },
    )
    .waitFor();
  await mkdir("/private/tmp/reality-205-dialog", { recursive: true });
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const box = await removalDialog.boundingBox();
    assert.ok(box && box.x >= 0 && box.x + box.width <= width);
    await page.screenshot({
      animations: "disabled",
      path: `/private/tmp/reality-205-dialog/${width}.png`,
    });
  }
  await removalDialog.getByRole("button", { name: "Cancel", exact: true }).click();
  assert.equal(await removalDialog.count(), 0);
  await chatPage.locator("[data-chat-starters] button").first().click();
  assert.equal(await chatPage.locator("textarea").inputValue(), firstQuestion);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: reference chat header, text attachment, voice draft/teardown, keyboard, immediate echo and send-failure retention.",
  );
} finally {
  await browser.close();
}
