// Synthetic HTTP fixtures prove presentation; PostgreSQL tests prove account/service effects.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5190";
const out = "/private/tmp/reality-190-browser";
await mkdir(out, { recursive: true });
let ready = false,
  failSetup = true,
  posts = 0,
  language = "en",
  attentionState = "uninitialized",
  failAttention = false,
  remaining = 1,
  sent = 0;
let usageGrants = [],
  grantRequests = [],
  failGrant = true,
  adminUsage = false;
let archived = false,
  entryReceiptStatus = null,
  startContent = null,
  preparation = null,
  seedDelay = 50;
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const company = {
  id: "trial_company",
  name: "My demo company",
  purpose: "playground",
  role: "owner",
  company_kind: "sandbox",
  sandbox_run_id: "trial_run",
};
const pager = { number: 1, size: 50, total: 0, pages: 1, has_previous: false, has_next: false };
const metadata = () => ({
  projection: "test",
  calculation_mode: "stored",
  state: attentionState,
  completed_at: attentionState === "uninitialized" ? null : "2026-09-14T12:00:00Z",
  processed_event_sequence: 1,
  target_event_sequence: 1,
  projection_version: 1,
  upstream_freshness: "unknown",
  consistency: "completed_snapshot",
});
const delivery = {
  id: "commitment_one",
  tenant_id: company.id,
  type: "customer_delivery",
  document_id: null,
  document_line_id: null,
  party_id: "customer_one",
  counterparty: "Northstar",
  item_id: "item_one",
  item: "Bicycle light",
  location_id: "location_one",
  location: "Main warehouse",
  unit: "pcs",
  promised: "10",
  fulfilled: "4",
  reserved: "2",
  open: "6",
  status: "open",
  due_at: null,
  blockers: [],
};
await page.route("**/api/**", async (route) => {
  const request = route.request(),
    url = new URL(request.url()),
    path = url.pathname;
  const reply = (value, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(value) });
  if (path === "/api/auth/me")
    return reply({
      id: "trial_user",
      is_platform_admin: adminUsage,
      email: "trial@example.test",
      display_name: "",
      status: "active",
      language,
      locale: language === "de" ? "de-DE" : "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({ tenants: ready ? [company] : [], default_tenant_id: ready ? company.id : null });
  if (path === "/api/company-setup/ai-usage") {
    if (request.method() === "POST") {
      const body = request.postDataJSON();
      grantRequests.push(body);
      assert.equal(body.confirmed, true);
      if (failGrant) {
        failGrant = false;
        return reply({ detail: "Temporary grant failure" }, 503);
      }
      usageGrants.unshift({
        id: String(usageGrants.length),
        actor_user_id: "trial_user",
        actor_name: "Trial User",
        recipient_user_id: "trial_user",
        occurred_at: "2026-09-15T12:00:00Z",
        expires_at: "2099-09-15T00:00:00Z",
        questions: body.questions,
        mode: body.mode,
        reason: body.reason || "Continued testing",
      });
      remaining += body.questions;
    }
    return reply({
      allowance: {
        limit: 20,
        used: 20 + usageGrants.reduce((sum, row) => sum + row.questions, 0) - remaining,
        remaining,
        base_remaining: 0,
        bonus_questions: usageGrants.reduce((sum, row) => sum + row.questions, 0),
        bonus_remaining: remaining,
        resets_at: "2099-09-15T00:00:00Z",
      },
      recipient: { id: "trial_user", email: "trial@example.test", name: "Trial User" },
      can_admin_grant: adminUsage,
      self_extensions_remaining: 3 - usageGrants.filter((row) => row.mode === "self").length,
      self_extension_questions: 20,
      history: usageGrants,
    });
  }
  if (path === "/api/company-setup/playground") {
    if (request.method() === "GET")
      return reply({
        requested: true,
        eligible: true,
        enabled: true,
        archived,
        receipt: entryReceiptStatus
          ? { tenant_id: company.id, status: entryReceiptStatus, preparation }
          : null,
      });
    assert.equal(request.postDataJSON().confirmed, true);
    startContent = request.postDataJSON().content;
    assert.ok(["international_demo", "empty"].includes(startContent));
    posts++;
    // Feature 199: creation answers with the committed company; the worker seeds it
    // and the screen follows the receipt from here.
    entryReceiptStatus = "initializing";
    preparation = "queued";
    setTimeout(() => (preparation = "preparing"), Math.round(seedDelay / 2));
    setTimeout(() => {
      ready = !failSetup;
      entryReceiptStatus = ready ? "ready" : "initialization_failed";
      preparation = null;
    }, seedDelay);
    return reply({
      tenant_id: company.id,
      run_id: "trial_run",
      name: company.name,
      status: "initializing",
      environment: "sandbox",
      destination: null,
      preparation,
    });
  }
  if (path.endsWith("/application-reference"))
    return reply({
      workspaces: [{ actions: [{ command: "reserve" }, { command: "record_movement" }] }],
    });
  if (path.endsWith("/dashboard"))
    return reply({
      tenant: company,
      totals: { open_deliveries: 1, open_commitments: 1, exceptions: 0, pending_decisions: 0 },
      exceptions: [],
      inventory: [],
      facts: [],
      capabilities: {},
    });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "chat_one", title: "New conversation" }],
      active_session_id: "chat_one",
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
      allowance: { limit: 20, used: 20 - remaining, remaining, resets_at: "2099-09-15T00:00:00Z" },
    });
  if (path.endsWith("/messages")) {
    sent++;
    remaining = 0;
    return reply({ detail: "Daily allowance used" }, 422);
  }
  if (path.endsWith("/attention")) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return failAttention
      ? reply({ detail: "Read unavailable" }, 503)
      : reply({ items: [], page: pager, metadata: metadata() });
  }
  if (path.endsWith("/open-items"))
    return reply({ items: [], page: pager, totals: [], metadata: metadata() });
  if (path.endsWith("/delivery-work"))
    return reply({ items: [delivery], page: { ...pager, total: 1 } });
  if (path.endsWith("/delivery-work/commitment_one"))
    return reply({
      case: delivery,
      inventory: {
        item_id: "item_one",
        location_id: "location_one",
        unit: "pcs",
        physical: "4",
        reserved: "2",
        available: "2",
      },
      links: [{ kind: "commitment", id: delivery.id, label: "Commitment" }],
      history: { items: [], has_more: false, next_cursor: null },
      observation: { observed_at: "2026-09-14T12:00:00Z", evidence_available: true },
    });
  if (path.endsWith("/change-proposals")) return reply({ items: [], page: pager });
  return reply({ detail: `Unused fixture: ${path}` }, 404);
});
try {
  if (process.env.USAGE_ONLY === "1") {
    ready = true;
    failSetup = false;
    remaining = 0;
    await page.goto(`${base}/app/settings?tenant=${company.id}&settings_view=usage`);
    const settings = page.locator("[data-usage-settings]");
    const reset = settings.getByRole("button", { name: "Reset usage", exact: true });
    await reset.waitFor();
    assert.equal(grantRequests.length, 0);
    await reset.click();
    await settings.getByRole("alert").getByText("Temporary grant failure").waitFor();
    await reset.click();
    await settings.getByRole("status").waitFor();
    assert.equal(grantRequests.length, 2);
    assert.equal(grantRequests[0].request_key, grantRequests[1].request_key);
    assert.equal(usageGrants.length, 1);
    assert.equal(await reset.count(), 0);
    assert.equal(await settings.locator("[data-usage-history], input, select").count(), 0);
    for (const lang of ["en", "de", "nl", "es"]) {
      language = lang;
      adminUsage = true;
      remaining = 0;
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(`${base}/app/settings?tenant=${company.id}&settings_view=usage&lang=${lang}`);
      await settings.locator("[data-usage-reset]").waitFor();
      assert.equal(await settings.locator("input, select, [data-usage-history]").count(), 0);
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
        false,
      );
      await page.screenshot({ path: `${out}/usage-${lang}.png`, fullPage: true });
    }
    usageGrants = Array.from({ length: 3 }, (_, id) => ({
      id: String(id),
      questions: 20,
      mode: "self",
    }));
    await page.reload();
    await settings.locator("[data-usage-details]").waitFor();
    assert.equal(await settings.locator("[data-usage-reset]").count(), 0);
    assert.equal(grantRequests.length, 2);
    assert.deepEqual(errors, []);
    console.log(
      "PASS: simple usage reset, explicit click, retry identity, eligibility, hidden admin/history controls and four mobile locales",
    );
    await browser.close();
    process.exit(0);
  }
  // Feature 198: the first entry offers two starts and creates nothing until one is chosen.
  for (const locale of ["en", "de", "nl", "es"]) {
    language = locale;
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/app?lang=${locale}`);
    await page.locator("[data-entry-choice]").waitFor();
    assert.equal(posts, 0, "No company may be created before a start is chosen");
    assert.equal(await page.locator("[data-start]").count(), 2);
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
    );
    await page.screenshot({ path: `${out}/start-choice-${locale}.png`, fullPage: true });
  }
  language = "en";
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/app`);
  await page.locator("[data-entry-choice]").waitFor();
  await page.screenshot({ path: `${out}/start-choice-desktop.png`, fullPage: true });
  await page.locator('[data-start="empty"]').click();
  await page
    .getByText("Your company is not ready yet. Retry to continue with the same company.")
    .waitFor();
  assert.equal(startContent, "empty");
  assert.equal(posts, 1, "Exactly one creation follows one chosen start");
  // Feature 199: a seed that outlives the request keeps showing progress, not an error,
  // and the company opens as soon as its receipt reports ready.
  seedDelay = 4000;
  failSetup = false;
  entryReceiptStatus = null;
  await page.goto(`${base}/app`);
  await page.locator('[data-start="international_demo"]').click();
  await page.getByText("Preparing your demo company", { exact: true }).waitFor();
  assert.equal(await page.getByRole("alert").count(), 0);
  assert.equal(ready, false, "the company is still being seeded");
  // Feature 201: three steps from real state, and the middle one only claims work
  // once a worker actually holds it.
  const steps = page.locator("[data-setup-steps]");
  await steps.waitFor();
  assert.equal(await steps.locator("[data-setup-step]").count(), 3);
  assert.equal(
    await steps.locator('[data-setup-step="created"]').getAttribute("data-state"),
    "done",
  );
  await steps.getByText("Waiting to start", { exact: true }).waitFor();
  await steps.getByText("Preparing orders, deliveries and invoices", { exact: true }).waitFor();
  assert.equal(await steps.locator('[data-setup-step="data"][data-state="current"]').count(), 1);
  await page.screenshot({ path: `${out}/setup-steps.png`, fullPage: true });
  await page.locator("[data-trial-tasks]").waitFor({ timeout: 20000 });
  assert.equal(posts, 2, "following the receipt must not create a second company");
  seedDelay = 50;
  ready = false;
  failSetup = true;
  entryReceiptStatus = null;
  await page.goto(`${base}/app`);
  await page.locator('[data-start="international_demo"]').click();
  await page
    .getByText("Your demo is not ready yet. Retry to continue with the same company.")
    .waitFor();
  assert.equal(startContent, "international_demo");
  assert.equal(ready, false);
  failSetup = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.locator("[data-trial-tasks]").waitFor();
  assert.ok(posts >= 4);
  assert.ok(!page.url().includes("settings"));
  assert.equal(await page.locator("[data-trial-github]").count(), 0);
  await page.getByRole("button", { name: "Which orders need attention?", exact: true }).focus();
  await page.keyboard.press("Enter");
  await page.getByText("Awaiting first calculation.").first().waitFor();
  assert.equal(await page.locator("[data-trial-github]").count(), 0);
  attentionState = "ready";
  await page.getByRole("link", { name: "Home", exact: true }).click();
  failAttention = true;
  await page.getByRole("button", { name: "Which orders need attention?", exact: true }).click();
  await page.locator('[data-work-list="exceptions"] [role="alert"]').waitFor();
  assert.equal(await page.locator("[data-trial-github]").count(), 0);
  failAttention = false;
  await page.getByRole("button", { name: "Retry", exact: true }).first().click();
  await page.locator("[data-trial-github]").waitFor();
  await page.screenshot({ path: `${out}/first-result-desktop.png`, fullPage: true });
  await page.getByRole("button", { name: "Keep exploring", exact: true }).click();
  await page.reload();
  assert.equal(await page.locator("[data-trial-github]").count(), 0);
  await page.getByRole("link", { name: "Home", exact: true }).click();
  await page.getByRole("button", { name: "Which invoices remain open?", exact: true }).click();
  assert.ok(page.url().includes("finance_status=outstanding"));
  await page.getByRole("link", { name: "Home", exact: true }).click();
  await page
    .getByRole("button", { name: "Why is this order not fully delivered?", exact: true })
    .click();
  await page.getByText("Northstar", { exact: true }).first().click();
  await page.getByRole("button", { name: "Open commitment", exact: true }).click();
  await page.getByRole("button", { name: "Back to commitments", exact: true }).waitFor();
  const chat = page.locator("[data-global-chat]");
  assert.equal(await chat.locator("[data-ai-allowance]").count(), 0);
  const usage = chat.locator("header [data-chat-usage] button").first();
  await usage.focus();
  await page.keyboard.press("Enter");
  const usageDialog = page.getByRole("dialog", { name: "Usage", exact: true });
  await usageDialog.getByText(/Resets at/).waitFor();
  await page.keyboard.press("Escape");
  assert.equal(await usageDialog.isVisible(), false);
  await usage.click();
  await usageDialog.getByRole("button", { name: "View usage", exact: true }).click();
  await page.locator("[data-usage-settings]").waitFor();
  await page.getByRole("link", { name: "Home", exact: true }).click();
  await chat.locator("textarea").fill("Keep this question after exhaustion");
  await chat.locator('button[type="submit"]').click();
  await chat
    .getByText(
      "Your daily AI allowance is used. Keep exploring the records or return after the reset.",
    )
    .waitFor();
  assert.equal(await chat.locator("textarea").inputValue(), "Keep this question after exhaustion");
  assert.equal(await chat.locator('button[type="submit"]').isDisabled(), true);
  assert.equal(sent, 1);
  await chat
    .locator("[data-ai-allowance]")
    .getByText(/Resets at/)
    .waitFor();
  for (const locale of ["en", "de", "nl", "es"]) {
    language = locale;
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/app?tenant=${company.id}&lang=${locale}`);
    await page.locator("[data-trial-tasks]").waitFor();
    await page
      .getByText(
        {
          en: "Try these three questions",
          de: "Starte mit diesen drei Fragen",
          nl: "Begin met deze drie vragen",
          es: "Empieza con estas tres preguntas",
        }[locale],
        { exact: true },
      )
      .waitFor();
    assert.equal(await page.locator("html").getAttribute("lang"), locale);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.screenshot({ path: `${out}/${locale}-mobile.png`, fullPage: true });
  }
  language = "en";
  ready = true;
  failSetup = true;
  entryReceiptStatus = "initialization_failed";
  await page.goto(`${base}/app?lang=en`);
  await page.locator('[data-start="international_demo"]').click();
  await page
    .getByText("Your demo is not ready yet. Retry to continue with the same company.")
    .waitFor();
  failSetup = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.locator("[data-trial-tasks]").waitFor();
  const beforeArchive = posts;
  archived = true;
  ready = false;
  entryReceiptStatus = "archived";
  await page.goto(`${base}/app?lang=en`);
  await page
    .getByRole("heading", { name: "Create your first company", exact: true })
    .first()
    .waitFor();
  assert.equal(posts, beforeArchive, "An archived receipt must not trigger another creation");
  assert.deepEqual(errors, []);
  console.log(
    "PASS: two offered starts before any creation, a followed setup receipt, recoverable trial entry, truthful result prompt, dismissal, starters, exhausted draft and four mobile locales",
  );
} catch (error) {
  console.error(await page.locator("body").innerText());
  await page.screenshot({ path: `${out}/failure.png`, fullPage: true });
  throw error;
} finally {
  await browser.close();
}
