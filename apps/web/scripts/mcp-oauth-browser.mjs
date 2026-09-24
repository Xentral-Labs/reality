import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";

const playwrightModule = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const { chromium } = playwrightModule.default ?? playwrightModule;
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const interactionId = "oai_browser_contract_123";
const secretMarkers = ["authorization-code", "refresh-token", "pkce-verifier"];

const interaction = {
  id: interactionId,
  client: { id: "client-a", name: "Example MCP Client", uri: "https://client.example" },
  requested_scopes: ["reality:read", "reality:propose"],
  eligible_tools: [
    { name: "inventory_read", label: "Inventory", access: "read" },
    { name: "exceptions_list", label: "Exceptions", access: "read" },
    { name: "reservation_propose", label: "Reserve inventory", access: "propose" },
  ],
  selected_tools: ["inventory_read", "exceptions_list", "reservation_propose"],
  companies: [
    { id: "ten_alpha", name: "Same Name GmbH", role: "owner", ready: true },
    { id: "ten_beta", name: "Same Name GmbH", role: "member", ready: true },
  ],
  company_setup: { eligible: true, external_mcp_requires_business_company: false },
  expires_at: "2026-09-24T12:00:00Z",
  status: "pending",
};

async function journey(decision) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const requests = [];
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const reply = (body, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/auth/me")
      return reply({
        id: "user_1",
        email: "owner@example.test",
        display_name: "Owner",
        status: "active",
        language: "en",
        locale: "en-GB",
        timezone: "UTC",
        is_platform_admin: false,
        application: null,
      });
    if (path === `/api/oauth/interactions/${interactionId}`) return reply(interaction);
    if (path.endsWith("/approve") || path.endsWith("/deny")) {
      requests.push({ path, body: request.postDataJSON() });
      return reply({ completion_path: `/oauth/complete/${interactionId}` });
    }
    throw new Error(`Unexpected OAuth browser request: ${path}`);
  });
  await page.route(`**/oauth/complete/${interactionId}`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<!doctype html><title>Done</title>",
    }),
  );

  await page.goto(`${base}/oauth/authorize?interaction=${interactionId}`);
  try {
    await page.getByRole("heading", { name: "Authorize Example MCP Client" }).waitFor();
  } catch (error) {
    throw new Error(
      `Consent did not render at ${page.url()}. Body: ${await page.locator("body").innerText()} Errors: ${errors.join(" | ")}`,
      { cause: error },
    );
  }
  assert.equal(await page.getByRole("checkbox").count(), 3);
  assert.equal(await page.getByRole("checkbox").first().isChecked(), true);

  if (decision === "approve") {
    await page.getByRole("checkbox", { name: /Exceptions/ }).uncheck();
    await page.getByLabel("Company").selectOption("ten_beta");
    await page.getByRole("button", { name: "Allow selected access" }).click();
    await page.waitForURL(`**/oauth/complete/${interactionId}`);
    assert.deepEqual(requests, [
      {
        path: `/api/oauth/interactions/${interactionId}/approve`,
        body: {
          company_id: "ten_beta",
          allowed_tools: ["inventory_read", "reservation_propose"],
          confirmed: true,
        },
      },
    ]);
  } else {
    await page.getByRole("button", { name: "Cancel authorization" }).click();
    await page.waitForURL(`**/oauth/complete/${interactionId}`);
    assert.deepEqual(requests, [
      {
        path: `/api/oauth/interactions/${interactionId}/deny`,
        body: { confirmed: true },
      },
    ]);
  }

  const persisted = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
    html: document.documentElement.outerHTML,
    url: location.href,
  }));
  const exposed = JSON.stringify(persisted);
  for (const marker of secretMarkers) assert.equal(exposed.includes(marker), false, marker);
  assert.deepEqual(errors, []);
  await context.close();
}

async function companySetupJourney(kind, cancel = false) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const requests = [];
  const createdCompany = {
    id: `ten_created_${kind}`,
    name: kind === "business" ? "Created Business" : "Created Sandbox",
    role: "owner",
    ready: true,
  };
  let ready = false;
  const noCompanyInteraction = { ...interaction, companies: [] };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const reply = (body, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/auth/me")
      return reply({
        id: "user_1",
        email: "owner@example.test",
        display_name: "Owner",
        status: "active",
        language: "en",
        locale: "en-GB",
        timezone: "UTC",
        is_platform_admin: false,
        application: null,
      });
    if (path === `/api/oauth/interactions/${interactionId}`)
      return reply(ready ? { ...interaction, companies: [createdCompany] } : noCompanyInteraction);
    if (path === "/api/company-setup/options")
      return reply({
        actor_id: "user_1",
        suggested_name: "",
        environments: ["business", "sandbox"],
        practice_enabled: true,
        pending: false,
        desktop_anthropic_setup: false,
      });
    if (path === "/api/company-setup" && request.method() === "POST") {
      const body = request.postDataJSON();
      requests.push({ path, body });
      ready = true;
      return reply(
        {
          tenant_id: createdCompany.id,
          run_id: kind === "sandbox" ? "run_created" : null,
          name: createdCompany.name,
          status: "ready",
          environment: kind,
          destination: "/home",
          error_code: null,
          profile: null,
        },
        201,
      );
    }
    if (path.endsWith("/approve")) {
      requests.push({ path, body: request.postDataJSON() });
      return reply({ completion_path: `/oauth/complete/${interactionId}` });
    }
    throw new Error(`Unexpected company setup browser request: ${request.method()} ${path}`);
  });
  await page.route(`**/oauth/complete/${interactionId}`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<!doctype html><title>Done</title>",
    }),
  );

  await page.goto(`${base}/oauth/authorize?interaction=${interactionId}`);
  await page.getByRole("button", { name: "Create company" }).click();
  await page.getByLabel("Company name (required)").fill(createdCompany.name);
  if (kind === "sandbox") await page.getByLabel("Create an empty Sandbox").check();
  if (cancel) {
    await page.getByRole("button", { name: "Cancel", exact: true }).click();
    await page.getByRole("button", { name: "Create company" }).waitFor();
    assert.deepEqual(requests, []);
  } else {
    await page.getByRole("button", { name: "Create company" }).last().click();
    await page.locator("select").selectOption(createdCompany.id);
    await page.getByRole("button", { name: "Allow selected access" }).click();
    await page.waitForURL(`**/oauth/complete/${interactionId}`);
    assert.equal(requests[0].path, "/api/company-setup");
    assert.equal(requests[0].body.confirmed, true);
    assert.equal(requests[0].body.environment, kind);
    assert.equal(requests[1].body.company_id, createdCompany.id);
  }
  await context.close();
}

async function companySetupRecoveryJourney(initialStatus) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const requestKey = `recover-${initialStatus}`;
  const company = {
    id: `ten_${requestKey}`,
    name: `Recovered ${initialStatus}`,
    role: "owner",
    ready: true,
  };
  const savedRequest = {
    request_key: requestKey,
    name: company.name,
    environment: "sandbox",
    content: "international_demo",
    live_simulation: false,
    confirmed: true,
  };
  let receiptReads = 0;
  let ready = false;
  let retries = 0;
  let creates = 0;
  const receipt = (status) => ({
    tenant_id: company.id,
    run_id: `run_${requestKey}`,
    name: company.name,
    status,
    environment: "sandbox",
    destination: status === "ready" ? "/home" : null,
    error_code: status === "initialization_failed" ? "profile_initialization_failed" : null,
    profile: { key: "international-demo", version: 1 },
    preparation: status === "initializing" ? "queued" : null,
  });
  await page.addInitScript(
    ({ key, value }) => {
      if (!location.pathname.startsWith("/oauth/complete/"))
        sessionStorage.setItem(key, JSON.stringify(value));
    },
    {
      key: "reality.company-setup.user_1",
      value: savedRequest,
    },
  );
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const reply = (body, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/auth/me")
      return reply({
        id: "user_1",
        email: "owner@example.test",
        display_name: "Owner",
        status: "active",
        language: "en",
        locale: "en-GB",
        timezone: "UTC",
        is_platform_admin: false,
        application: null,
      });
    if (path === `/api/oauth/interactions/${interactionId}`)
      return reply(
        ready ? { ...interaction, companies: [company] } : { ...interaction, companies: [] },
      );
    if (path === "/api/company-setup/options")
      return reply({
        actor_id: "user_1",
        suggested_name: "",
        environments: ["business", "sandbox"],
        practice_enabled: true,
        pending: false,
        desktop_anthropic_setup: false,
      });
    if (path === `/api/company-setup/requests/${requestKey}` && request.method() === "GET") {
      receiptReads += 1;
      if (initialStatus === "initialization_failed" && retries === 0)
        return reply(receipt("initialization_failed"));
      if (receiptReads === 1) return reply(receipt("initializing"));
      ready = true;
      return reply(receipt("ready"));
    }
    if (path === `/api/company-setup/requests/${requestKey}/retry`) {
      retries += 1;
      return reply(receipt("initializing"));
    }
    if (path === "/api/company-setup") {
      creates += 1;
      return reply({ detail: "duplicate create path used" }, 500);
    }
    if (path.endsWith("/approve"))
      return reply({ completion_path: `/oauth/complete/${interactionId}` });
    throw new Error(`Unexpected recovery browser request: ${request.method()} ${path}`);
  });
  await page.route(`**/oauth/complete/${interactionId}`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<!doctype html><title>Done</title>",
    }),
  );

  await page.goto(`${base}/oauth/authorize?interaction=${interactionId}`);
  await page.getByRole("button", { name: "Create company" }).click();
  if (initialStatus === "initialization_failed")
    await page.getByRole("button", { name: "Retry company setup" }).click();
  await page.locator("select").selectOption(company.id);
  await page.getByRole("button", { name: "Allow selected access" }).click();
  await page.waitForURL(`**/oauth/complete/${interactionId}`);
  assert.equal(creates, 0);
  assert.equal(retries, initialStatus === "initialization_failed" ? 1 : 0);
  assert.equal(
    await page.evaluate((key) => sessionStorage.getItem(key), "reality.company-setup.user_1"),
    null,
  );
  await context.close();
}

async function ineligibleCompanySetupJourney() {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  let mutations = 0;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") mutations += 1;
    if (path === "/api/auth/me")
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "user_1",
          email: "owner@example.test",
          display_name: "Owner",
          status: "active",
          language: "en",
          locale: "en-GB",
          timezone: "UTC",
          is_platform_admin: false,
          application: null,
        }),
      });
    if (path === `/api/oauth/interactions/${interactionId}`)
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...interaction,
          companies: [],
          company_setup: { ...interaction.company_setup, eligible: false },
        }),
      });
    throw new Error(`Unexpected ineligible browser request: ${request.method()} ${path}`);
  });
  await page.goto(`${base}/oauth/authorize?interaction=${interactionId}`);
  await page.getByRole("heading", { name: "Authorize Example MCP Client" }).waitFor();
  assert.match(await page.locator("body").innerText(), /No ready company is available/);
  assert.equal(await page.getByRole("button", { name: "Create company" }).count(), 0);
  assert.equal(
    await page.getByRole("button", { name: "Allow selected access" }).isDisabled(),
    true,
  );
  assert.equal(mutations, 0);
  await context.close();
}

async function grantManagementJourney() {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const secret = "ros_access_secret-never-render";
  const refresh = "ros_refresh_secret-never-render";
  const writes = [];
  const paths = [];
  let losePersonalResponse = true;
  const grant = (id, state = "active") => ({
    id,
    client: { id: `client-${id}`, name: `Client ${id}`, uri: "https://client.example" },
    company: { id: "main", name: "Main company" },
    tools: [{ name: "exceptions_list", label: "Exceptions", access: "read" }],
    scopes: ["reality:read"],
    created_at: "2026-09-24T08:00:00Z",
    last_used_at: null,
    revoked_at: state === "revoked" ? "2026-09-24T09:00:00Z" : null,
    effective_state: state,
    effective_reason: state === "revoked" ? "user" : null,
  });
  let personal = grant("personal");
  let company = {
    ...grant("company"),
    authorized_by: { id: "owner", display_name: "Owner", email: "owner@example.test" },
  };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    paths.push(`${request.method()} ${path}`);
    const reply = (body, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/auth/me")
      return reply({
        id: "owner",
        email: "owner@example.test",
        display_name: "Owner",
        status: "active",
        language: "en",
        locale: "en-GB",
        timezone: "UTC",
        is_platform_admin: false,
        application: null,
      });
    if (path === "/api/v1/bootstrap")
      return reply({
        tenants: [{ id: "main", name: "Main company", role: "owner" }],
        default_tenant_id: "main",
      });
    if (path === "/api/auth/mcp-grants" && request.method() === "GET")
      return reply({ grants: [personal] });
    if (path === "/api/tenants/main/settings/mcp/grants" && request.method() === "GET")
      return reply({ grants: [company] });
    if (path.endsWith("/mcp-grants/personal/revoke")) {
      writes.push({ path, body: request.postDataJSON() });
      personal = grant("personal", "revoked");
      if (losePersonalResponse) {
        losePersonalResponse = false;
        return route.abort("failed");
      }
      return reply({});
    }
    if (path.endsWith("/mcp/grants/company/revoke")) {
      writes.push({ path, body: request.postDataJSON() });
      company = { ...company, effective_state: "revoked", revoked_at: "2026-09-24T09:00:00Z" };
      return reply({});
    }
    if (path.endsWith("/settings/ai"))
      return reply({ copilot: {}, tokens: [], tools: [], mcp_url: "https://mcp.example.test" });
    if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
    if (path.endsWith("/analytics/graph/templates")) return reply({ templates: [] });
    if (path.endsWith("/copilot"))
      return reply({
        sessions: [],
        messages: [],
        proposals: [],
        suggestions: [],
        has_archived: false,
        active_session_id: null,
      });
    if (path.endsWith("/change-proposals"))
      return reply({ items: [], page: { page: 1, size: 50, total: 0, pages: 0 } });
    if (path === "/api/v1/companies") return reply([]);
    if (path.includes("/company-setup/ai-usage"))
      return reply({
        allowance: null,
        recipient: { id: "owner", email: "owner@example.test", name: "Owner" },
        can_admin_grant: false,
        self_extensions_remaining: 0,
        self_extension_questions: 20,
        history: [],
      });
    if (request.method() === "GET") return reply({});
    throw new Error(`Unexpected grant management request: ${request.method()} ${path}`);
  });

  await page.goto(`${base}/app/settings?tenant=main&settings_view=personal`);
  try {
    await page.getByRole("heading", { name: "Connected clients" }).waitFor();
  } catch (error) {
    throw new Error(
      `Personal grant management did not render: ${await page.locator("body").innerText()}`,
      {
        cause: error,
      },
    );
  }
  try {
    await page.getByText("Client personal", { exact: true }).waitFor();
  } catch (error) {
    throw new Error(
      `Personal grant missing. Requests: ${paths.join(", ")}. Body: ${await page.locator("body").innerText()}`,
      { cause: error },
    );
  }
  if (!(await page.getByRole("button", { name: "Revoke connected client" }).count()))
    throw new Error(
      `Personal grant revoke action missing: ${await page.locator("body").innerText()}`,
    );
  await page.getByRole("button", { name: "Revoke connected client" }).click();
  assert.equal(writes.length, 0);
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page
    .getByText("The revoke result is unknown. Reload connected clients before trying again.")
    .waitFor();
  assert.deepEqual(writes[0].body, { confirmed: true });
  await page.getByRole("button", { name: "Reload connected clients" }).click();
  await page.getByText("Connected client access revoked.", { exact: true }).waitFor();

  await page.goto(`${base}/app/settings?tenant=main&settings_view=agents`);
  await page.getByText("Client company", { exact: true }).waitFor();
  await page.getByText("Authorized by: Owner", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Revoke connected client" }).click();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  assert.equal(writes.length, 1);
  await page.getByRole("button", { name: "Revoke connected client" }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await page.getByText("Connected client access revoked.", { exact: true }).waitFor();

  const exposed = await page.evaluate(() =>
    JSON.stringify({
      html: document.documentElement.outerHTML,
      local: { ...localStorage },
      session: { ...sessionStorage },
    }),
  );
  assert.equal(exposed.includes(secret), false);
  assert.equal(exposed.includes(refresh), false);
  assert.equal(exposed.includes("token_prefix"), false);
  assert.equal(writes.length, 2);
  await context.close();
}

try {
  if (!process.env.MCP_BROWSER_GRANTS_ONLY) {
    await journey("approve");
    await journey("deny");
    await companySetupJourney("business", true);
    await companySetupJourney("business");
    await companySetupJourney("sandbox");
    await companySetupRecoveryJourney("initializing");
    await companySetupRecoveryJourney("initialization_failed");
    await ineligibleCompanySetupJourney();
  }
  await grantManagementJourney();
  console.log(
    "PASS: MCP OAuth consent and company setup pass; personal/company grant inventory confirms revocation, recovers unknown responses and persists no secrets",
  );
} finally {
  await browser.close();
}
