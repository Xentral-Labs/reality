// Synthetic credentials and intercepted HTTP only; no real provider or token changes.
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
const out = "/private/tmp/reality-131-browser";
await mkdir(out, { recursive: true });
const fakeKey = "fixture-key-not-a-real-credential",
  fakeToken = "fixture-token-not-a-real-credential";
let language = "en",
  mode = "ok",
  failRead = false,
  releaseWrite;
let config = {
  managed: true,
  available: true,
  credential_mode: "managed",
  provider_preset: "managed",
  model: "",
  base_url: "",
  has_company_api_key: false,
  api_key_fingerprint: "",
};
const presets = [
  { id: "managed", name: "Reality-managed", base_url: "", models: [] },
  {
    id: "anthropic",
    name: "Anthropic",
    base_url: "https://api.anthropic.com",
    models: [["fixed-model", "Fixed model"]],
  },
  { id: "custom", name: "Custom", base_url: "", models: [] },
];
let tokens = [
  {
    id: "existing",
    name: "Same name",
    token_prefix: "prefix_old",
    allowed_tools: ["*"],
    created_at: "2026-09-08T00:00:00Z",
    last_used_at: null,
  },
];
const tools = [
  {
    name: "read_orders",
    label: "Read orders",
    description: "Read orders",
    access: "read",
    group: "orders",
  },
  {
    name: "prepare_order",
    label: "Prepare order",
    description: "Prepare an order",
    access: "propose",
    group: "orders",
  },
  {
    name: "approve_proposal",
    label: "Approve proposal",
    description: "Approve exact proposal",
    access: "confirm",
    group: "control",
  },
];
const writes = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    p = new URL(req.url()).pathname;
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (p === "/api/auth/me")
    return reply({
      id: "owner",
      email: "owner@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (p === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "main", name: "Main company", role: "owner" },
        { id: "other", name: "Other company", role: "owner" },
        { id: "member", name: "Member company", role: "member" },
      ],
      default_tenant_id: "main",
    });
  if (p.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (p.includes("/member/settings/ai")) throw new Error("Member requested privileged AI settings");
  if (p.endsWith("/settings/ai") && req.method() === "GET")
    return failRead
      ? reply({ detail: "Unavailable" }, 503)
      : reply({
          copilot: { ...config, presets },
          tokens: p.includes("/other/") ? [] : tokens,
          tools,
          mcp_url: "https://mcp.example.test/mcp",
        });
  if (req.method() !== "GET") {
    const b = req.postDataJSON();
    writes.push({ p, body: b });
    if (mode === "reject") return reply({ detail: fakeKey }, 400);
    if (p.endsWith("/settings/ai"))
      config = {
        ...config,
        provider_preset: b.provider_preset,
        credential_mode: b.provider_preset === "managed" ? "managed" : "company",
        has_company_api_key: b.provider_preset !== "managed",
        model: b.provider_preset === "managed" ? "" : "fixed-model",
        base_url: b.provider_preset === "managed" ? "" : "https://api.anthropic.com",
      };
    let result = {};
    if (p.endsWith("/tokens")) {
      const row = {
        id: "token" + writes.length,
        name: b.name,
        token_prefix: "prefix_new",
        allowed_tools: b.allowed_tools,
        created_at: "2026-09-08T00:00:00Z",
        last_used_at: null,
      };
      tokens.unshift(row);
      result = { ...row, token: fakeToken };
    }
    if (p.endsWith("/revoke")) tokens = tokens.filter((t) => !p.includes("/" + t.id + "/"));
    if (mode === "held")
      await new Promise((resolve) => {
        releaseWrite = resolve;
      });
    return mode === "lost" ? route.abort("failed") : reply(result);
  }
  return reply({});
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const go = (tenant = "main") => page.goto(`${base}/app/settings?tenant=${tenant}&settings_view=ai`);
const button = (name) => page.getByRole("button", { name, exact: true });
const storage = () =>
  page.evaluate(() =>
    JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }),
  );
try {
  await go();
  await button("Change AI setup").click();
  await page.getByLabel("AI credential source", { exact: true }).selectOption("anthropic");
  await page.getByLabel("API key", { exact: true }).fill(fakeKey);
  await button("Review AI setup").click();
  assert.equal(writes.length, 0);
  assert.ok(!(await page.locator("main").innerText()).includes(fakeKey));
  assert.ok(!(await storage()).includes(fakeKey));
  await button("Cancel").click();
  assert.equal(writes.length, 0);
  await page.getByLabel("API key", { exact: true }).fill(fakeKey);
  await button("Review AI setup").click();
  await button("Confirm").click();
  await page.getByText("AI setup saved.", { exact: true }).waitFor();
  assert.equal(writes.length, 1);
  assert.equal(writes[0].body.api_key, fakeKey);
  await button("Change AI setup").click();
  await button("Review AI setup").click();
  await page.getByText("Keep the stored company key.", { exact: true }).waitFor();
  await button("Cancel").click();
  await page.getByLabel("AI credential source", { exact: true }).selectOption("managed");
  await button("Review AI setup").click();
  await page
    .getByText("Remove the company key and use deployment-managed AI.", { exact: true })
    .waitFor();
  await button("Confirm").click();
  await page.getByText("AI setup saved.", { exact: true }).waitFor();
  await page.getByText("External agents · MCP", { exact: true }).click();
  await button("New MCP token").click();
  await page.getByLabel("Token name", { exact: true }).fill("Same name");
  assert.equal(await button("Review token").isDisabled(), true);
  await page.getByRole("checkbox", { name: "Read orders", exact: true }).check();
  await page.getByRole("checkbox", { name: "Approve proposal", exact: true }).check();
  await button("Review token").click();
  await page
    .getByText("This token may approve and execute changes through its selected tools.", {
      exact: true,
    })
    .waitFor();
  await button("Cancel").click();
  await button("Review token").click();
  await button("Confirm").click();
  await page.getByLabel("New MCP token secret", { exact: true }).waitFor();
  assert.deepEqual(writes.at(-1).body.allowed_tools, ["read_orders", "approve_proposal"]);
  assert.ok(!(await storage()).includes(fakeToken));
  await page.evaluate(() =>
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => {
          throw new Error("denied");
        },
      },
    }),
  );
  await button("Copy token").click();
  await page
    .getByText("Copy failed. Select and copy the value manually.", { exact: true })
    .waitFor();
  assert.equal(
    await page.getByLabel("New MCP token secret", { exact: true }).inputValue(),
    fakeToken,
  );
  await button("Hide token secret").click();
  assert.equal(await page.getByLabel("New MCP token secret", { exact: true }).count(), 0);
  const target = tokens[0].id;
  await page
    .locator(`[data-token-id="${target}"]`)
    .getByRole("button", { name: "Revoke", exact: true })
    .click();
  await button("Confirm").click();
  await page.getByText("MCP token revoked.", { exact: true }).waitFor();
  assert.ok(!tokens.some((t) => t.id === target));
  await button("New MCP token").click();
  await page.getByLabel("Token name", { exact: true }).fill("Lost response");
  await page.getByRole("checkbox", { name: "Read orders", exact: true }).check();
  await button("Review token").click();
  mode = "lost";
  await button("Confirm").click();
  await button("Check saved AI settings").waitFor();
  await page.waitForFunction(() => !document.querySelector("[data-ai-recovery]")?.disabled);
  const count = writes.length;
  await page.reload();
  await button("Check saved AI settings").waitFor();
  assert.equal(writes.length, count);
  assert.ok(!(await storage()).includes(fakeToken));
  failRead = true;
  await button("Check saved AI settings").click();
  await page.getByRole("alert").first().waitFor();
  assert.equal(await button("Change AI setup").isDisabled(), true);
  failRead = false;
  mode = "ok";
  await button("Check saved AI settings").click();
  await page
    .getByText("Current AI settings loaded. This is not a receipt for the previous request.", {
      exact: true,
    })
    .waitFor();
  assert.equal(writes.length, count);
  await page.getByText("External agents · MCP", { exact: true }).click();
  await page.getByText("Lost response", { exact: true }).waitFor();
  assert.equal(await page.getByLabel("New MCP token secret", { exact: true }).count(), 0);
  const lostToken = tokens.find((t) => t.name === "Lost response");
  await page
    .locator(`[data-token-id="${lostToken.id}"]`)
    .getByRole("button", { name: "Revoke", exact: true })
    .click();
  mode = "lost";
  await button("Confirm").click();
  await page.waitForFunction(() => !document.querySelector("[data-ai-recovery]")?.disabled);
  mode = "ok";
  await button("Check saved AI settings").click();
  await page
    .getByText("Current AI settings loaded. This is not a receipt for the previous request.", {
      exact: true,
    })
    .waitFor();
  assert.ok(!tokens.some((t) => t.id === lostToken.id));
  await button("Change AI setup").click();
  await page.getByLabel("AI credential source", { exact: true }).selectOption("anthropic");
  await page.getByLabel("API key", { exact: true }).fill(fakeKey);
  await button("Review AI setup").click();
  mode = "reject";
  await button("Confirm").click();
  await page
    .getByText(
      "The change was rejected. Review the current settings and enter credentials again if needed.",
      { exact: true },
    )
    .waitFor();
  assert.ok(!(await page.locator("main").innerText()).includes(fakeKey));
  await button("Change AI setup").click();
  await page.getByLabel("AI credential source", { exact: true }).selectOption("anthropic");
  await page.getByLabel("API key", { exact: true }).fill(fakeKey);
  await button("Review AI setup").click();
  mode = "lost";
  await button("Confirm").click();
  await page.waitForFunction(() => !document.querySelector("[data-ai-recovery]")?.disabled);
  assert.ok(!(await storage()).includes(fakeKey));
  await page.reload();
  await button("Check saved AI settings").waitFor();
  mode = "ok";
  await button("Check saved AI settings").click();
  await page
    .getByText("Current AI settings loaded. This is not a receipt for the previous request.", {
      exact: true,
    })
    .waitFor();
  config = {
    ...config,
    provider_preset: "custom",
    credential_mode: "company",
    model: "stored-other-model",
    base_url: "https://saved.example.test",
  };
  await go();
  await page
    .getByText(
      "Other provider settings are stored, but Ask Reality currently uses managed AI or a company Anthropic key.",
      { exact: true },
    )
    .waitFor();
  await page.getByText("Stored provider details", { exact: true }).click();
  await page.getByText("https://saved.example.test", { exact: true }).waitFor();
  await page.getByText("Stored provider details", { exact: true }).click();
  await button("Change AI setup").click();
  await page.getByLabel("AI credential source", { exact: true }).selectOption("anthropic");
  assert.equal(await button("Review AI setup").isDisabled(), true);
  await button("Close").click();
  await page.getByText("External agents · MCP", { exact: true }).click();
  await button("New MCP token").click();
  await page.getByLabel("Token name", { exact: true }).fill("Delayed token");
  await page.getByRole("checkbox", { name: "Read orders", exact: true }).check();
  await button("Review token").click();
  const beforeHeld = writes.length;
  mode = "held";
  await button("Confirm").evaluate((b) => {
    b.click();
    b.click();
  });
  for (let i = 0; !releaseWrite && i < 100; i++) await page.waitForTimeout(20);
  assert.ok(releaseWrite);
  assert.equal(writes.length, beforeHeld + 1);
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="other"]').click();
  releaseWrite();
  mode = "ok";
  await page.getByText("Other company", { exact: true }).last().waitFor();
  await page.waitForTimeout(100);
  assert.equal(await page.getByLabel("New MCP token secret", { exact: true }).count(), 0);
  assert.equal(new URL(page.url()).searchParams.get("tenant"), "other");
  assert.ok(!(await storage()).includes(fakeToken));
  await go();
  for (const lang of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.reload();
        await page.locator("[data-ai-settings]").waitFor();
        await page.locator("[data-mcp-access] > summary").click();
        await page.locator("[data-token-id]").first().waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
        );
        await page.screenshot({
          path: `${out}/${lang}-${theme}-${width}.png`,
          fullPage: true,
          animations: "disabled",
        });
      }
  language = "en";
  tools.push(
    ...Array.from({ length: 28 }, (_, i) => ({
      name: `extra_read_${i}`,
      label: `Read extra ${i}`,
      description: "Read sample",
      access: "read",
      group: "sample",
    })),
  );
  tokens.push(
    ...Array.from({ length: 28 }, (_, i) => ({
      id: `extra_token_${i}`,
      name: `Existing ${i}`,
      token_prefix: `prefix_${i}`,
      allowed_tools: ["read_orders"],
      created_at: "2026-09-08T00:00:00Z",
      last_used_at: null,
    })),
  );
  await go();
  await page.locator("[data-mcp-access] > summary").click();
  assert.equal(await page.locator("[data-token-id]").count(), 25);
  await button("Next").click();
  assert.equal(await page.locator("[data-token-id]").count(), 5);
  await button("New MCP token").click();
  await page.getByLabel("Token name", { exact: true }).fill("Selected reads");
  const form = page.locator("[data-mcp-access] form");
  assert.equal(await form.getByRole("checkbox").count(), 25);
  await form.getByRole("button", { name: "Next", exact: true }).click();
  assert.equal(await form.getByRole("checkbox").count(), 6);
  await button("Select read tools").click();
  await page.getByLabel("Search tools", { exact: true }).fill("approve_proposal");
  assert.equal(
    await page.getByRole("checkbox", { name: "Approve proposal", exact: true }).isChecked(),
    false,
  );
  await page.getByLabel("Search tools", { exact: true }).fill("no matching fixture tool");
  await page.getByText("No matching tools.", { exact: true }).waitFor();
  await button("Review token").click();
  assert.equal(await page.locator("[data-ai-review] li").count(), 29);
  assert.ok(!(await page.locator("[data-ai-review]").innerText()).includes("approve_proposal"));
  await button("Cancel").click();
  await go("other");
  await page.locator("[data-mcp-access] > summary").click();
  await page.getByText("No active MCP tokens.", { exact: true }).waitFor();
  await go("member");
  await page.getByText("Only company owners can view these settings.", { exact: true }).waitFor();
  assert.equal(await button("Change AI setup").count(), 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS reviewed AI modes, key effects, explicit MCP scopes, one-time secret, revocation, unknown token/reload/recovery, owner gating and 16 localized layouts.",
  );
} catch (e) {
  await page.screenshot({ path: out + "/error.png", fullPage: true, animations: "disabled" });
  throw e;
} finally {
  await browser.close();
}
