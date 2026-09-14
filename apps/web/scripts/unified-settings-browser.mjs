// HTTP fixtures exercise UI transitions; existing PostgreSQL suites cover authorities.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const out = "/private/tmp/reality-112-browser";
const requests = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let user = {
  id: "operator",
  email: "operator@example.test",
  display_name: "Operator",
  status: "active",
  language: "en",
  locale: "en-GB",
  timezone: "Europe/Rome",
  is_platform_admin: false,
};
let mode = "ok",
  failRead = false,
  failRecovery = false,
  empty = false,
  deliveryStatus = "delivered";
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname;
  requests.push({ path, method: req.method(), body: req.postDataJSON() });
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path === "/api/auth/me")
    return failRecovery ? reply({ detail: "Unavailable" }, 503) : reply(user);
  if (path === "/api/auth/profile") {
    if (mode === "reject") return reply({ detail: "Invalid timezone" }, 422);
    if (mode !== "lost-unapplied")
      user = {
        ...user,
        ...req.postDataJSON(),
        display_name: req.postDataJSON().display_name.trim(),
      };
    if (mode.startsWith("lost")) return route.abort("failed");
    return reply(user);
  }
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "owner", name: "Northstar Commerce", role: "owner" },
        { id: "member", name: "Other company", role: "member" },
      ],
      default_tenant_id: "owner",
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.endsWith("/settings/members") && empty) return reply({ members: [], invitations: [] });
  if (path.endsWith("/settings/members"))
    return failRead
      ? reply({ detail: "Unavailable" }, 503)
      : reply({
          members: [
            {
              id: "m1",
              email: "owner@example.test",
              display_name: "Northstar owner",
              role: "owner",
            },
          ],
          invitations: [
            {
              id: "i1",
              email: "invite@example.test",
              status: "pending",
              delivery_status: deliveryStatus,
              expires_at: "2026-10-01T00:00:00Z",
            },
          ],
        });
  if (path.endsWith("/settings/ai") && failRead) return reply({ detail: "Unavailable" }, 503);
  if (path.endsWith("/settings/ai"))
    return reply({
      copilot: {
        available: true,
        credential_mode: "company",
        provider_preset: "custom",
        has_company_api_key: true,
        presets: [
          { id: "managed", name: "Reality-managed", base_url: "", models: [] },
          {
            id: "anthropic",
            name: "Anthropic",
            base_url: "https://api.anthropic.com",
            models: [["fixed-model", "Fixed model"]],
          },
        ],
        model: "sample-model",
        api_key_fingerprint: "HIDDEN-FINGERPRINT",
        base_url: "https://hidden.example.test",
      },
      mcp_url: "https://mcp.example.test/mcp",
      tools: [],
      tokens: [
        {
          id: "mcp1",
          name: "Existing token",
          token_prefix: "HIDDEN-TOKEN",
          allowed_tools: ["*"],
          created_at: "2026-09-08T00:00:00Z",
          last_used_at: null,
        },
      ],
    });
  throw new Error(`Unexpected request ${req.method()} ${path}`);
});
const go = async (view = "personal", tenant = "owner") => {
  await page.goto(`${base}/app/settings?tenant=${tenant}&settings_view=${view}`);
  await page.locator("[data-settings-view]").waitFor();
  assert.equal(await page.locator("[data-shell-header] .register-heading:visible").count(), 1);
};
const puts = () => requests.filter((r) => r.method === "PUT").length;
try {
  await mkdir(out, { recursive: true });
  await go();
  assert.equal(await page.getByLabel("Time zone", { exact: true }).inputValue(), "Europe/Rome");
  await page.getByLabel("Time zone", { exact: true }).selectOption("Europe/Berlin");
  await page.getByLabel("Display name", { exact: true }).fill(" Changed operator ");
  await page.keyboard.press("Tab");
  assert.equal(
    await page.locator("select[name=language]").evaluate((n) => n === document.activeElement),
    true,
  );
  await page.getByLabel("Language", { exact: true }).selectOption("de");
  await page.getByLabel("Number and date format", { exact: true }).selectOption("nl-NL");
  await page.getByRole("button", { name: "Save preferences", exact: true }).focus();
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.documentElement.lang === "de");
  assert.equal(puts(), 1);
  assert.deepEqual(requests.find((r) => r.method === "PUT").body, {
    display_name: " Changed operator ",
    language: "de",
    locale: "nl-NL",
    timezone: "Europe/Berlin",
  });
  await page.reload();
  assert.equal(await page.locator("select[name=timezone]").inputValue(), "Europe/Berlin");
  assert.equal(await page.locator('input[name="display_name"]').inputValue(), "Changed operator");
  assert.equal(await page.locator('select[name="locale"]').inputValue(), "nl-NL");
  user.language = "en";
  await go();
  mode = "reject";
  await page.getByLabel("Time zone", { exact: true }).selectOption("Europe/Berlin");
  await page.getByRole("button", { name: "Save preferences", exact: true }).click();
  await page.getByRole("alert").waitFor();
  assert.equal(await page.locator("select[name=timezone]").inputValue(), "Europe/Berlin");
  assert.equal(
    await page.getByRole("button", { name: "Save preferences", exact: true }).isEnabled(),
    true,
  );
  await page.getByLabel("Time zone", { exact: true }).selectOption("UTC");
  mode = "lost-applied";
  await page.getByRole("button", { name: "Save preferences", exact: true }).click();
  await page.getByRole("button", { name: "Check saved preferences", exact: true }).waitFor();
  const count = puts();
  failRecovery = true;
  await page.getByRole("button", { name: "Check saved preferences", exact: true }).click();
  await page
    .getByText("Could not check saved preferences. Try checking again.", { exact: true })
    .waitFor();
  assert.equal(
    await page.getByRole("button", { name: "Save preferences", exact: true }).isDisabled(),
    true,
  );
  failRecovery = false;
  await page.getByRole("button", { name: "Check saved preferences", exact: true }).click();
  await page.getByText("Preferences saved.", { exact: true }).waitFor();
  assert.equal(puts(), count);
  mode = "lost-unapplied";
  await page.getByLabel("Time zone", { exact: true }).selectOption("Europe/Berlin");
  await page.getByLabel("Display name", { exact: true }).fill("Unapplied draft");
  await page.getByRole("button", { name: "Save preferences", exact: true }).click();
  await page.getByRole("button", { name: "Check saved preferences", exact: true }).click();
  await page
    .getByText("Saved preferences differ from your draft. Review it before saving again.", {
      exact: true,
    })
    .waitFor();
  assert.equal(
    await page.getByLabel("Display name", { exact: true }).inputValue(),
    "Unapplied draft",
  );
  assert.equal(
    await page.getByRole("button", { name: "Save preferences", exact: true }).isEnabled(),
    true,
  );
  await page.getByRole("combobox", { name: "Appearance", exact: true }).selectOption("dark");
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "dark");
  await page.getByRole("button", { name: "Appearance", exact: true }).click();
  assert.equal(
    await page.getByRole("combobox", { name: "Appearance", exact: true }).inputValue(),
    "light",
  );
  await page.getByRole("combobox", { name: "Appearance", exact: true }).selectOption("system");
  await page.emulateMedia({ colorScheme: "dark" });
  await page.waitForFunction(() => document.documentElement.dataset.theme === "dark");
  await page.emulateMedia({ colorScheme: "light" });
  await page.waitForFunction(() => document.documentElement.dataset.theme === "light");
  if (process.env.PROFILE_ONLY) {
    assert.deepEqual(errors, []);
    console.log("PASS profile timezone selection, save/reload, rejection, recovery and appearance");
    process.exitCode = 0;
  } else {
    await go("access");
    await page.getByText("owner@example.test", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Switch company", exact: true }).click();
    await page.locator('[data-company-option="member"]').click();
    await page.getByText("Only company owners can view these settings.", { exact: true }).waitFor();
    assert.equal(await page.getByText("owner@example.test", { exact: true }).count(), 0);
    await go("ai", "member");
    await page.getByText("Only company owners can view these settings.", { exact: true }).waitFor();
    assert.equal(requests.filter((r) => r.path.includes("/member/settings/")).length, 0);
    failRead = true;
    await go("access");
    await page.getByRole("alert").waitFor();
    failRead = false;
    await page.getByRole("button", { name: "Retry", exact: true }).click();
    await page.getByText("owner@example.test", { exact: true }).waitFor();
    deliveryStatus = "retry";
    await go("access");
    await page.getByText(/Delivery retry scheduled/).waitFor();
    deliveryStatus = "delivered";
    empty = true;
    await go("access");
    await page.getByText("No active members.", { exact: true }).waitFor();
    await page.getByText("No invitations.", { exact: true }).waitFor();
    empty = false;
    failRead = true;
    await go("ai");
    await page.getByRole("alert").waitFor();
    failRead = false;
    await page.getByRole("button", { name: "Retry", exact: true }).click();
    await page.getByText("sample-model", { exact: true }).waitFor();
    assert.doesNotMatch(await page.locator("main").innerText(), /HIDDEN|hidden.example/);
    for (const language of ["en", "de", "nl", "es"])
      for (const theme of ["light", "dark"])
        for (const width of [390, 1440]) {
          user.language = language;
          await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
          await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
          for (const view of ["personal", "access", "ai"]) {
            await go(view);
            assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), theme);
            if (view === "access")
              await page.getByText("owner@example.test", { exact: true }).waitFor();
            if (view === "ai") await page.getByText("sample-model", { exact: true }).waitFor();
            if (view === "access") {
              const delivered = {
                en: "Invitation delivered",
                de: "Einladung zugestellt",
                nl: "Uitnodiging bezorgd",
                es: "Invitación entregada",
              };
              assert.ok((await page.locator("main").innerText()).includes(delivered[language]));
            }
            assert.ok(
              await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
              `${language}/${theme}/${width}/${view}`,
            );
            await page.screenshot({
              path: `${out}/${language}-${theme}-${width}-${view}.png`,
              fullPage: true,
            });
          }
        }
    assert.ok(
      requests.every(
        (r) => r.method === "GET" || (r.method === "PUT" && r.path === "/api/auth/profile"),
      ),
    );
    assert.deepEqual(errors, []);
    console.log(
      "PASS: profile save/reload/localization, rejection, applied/unapplied/recovery-failure ambiguity, no duplicate writes, appearance/header/system sync, owner isolation/retry, secret exclusion and 48 localized screenshots.",
    );
  }
} finally {
  await browser.close();
}
