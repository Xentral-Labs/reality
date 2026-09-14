// Stateful HTTP fixtures: no invitation or company is created in a real database.
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
const out = "/private/tmp/reality-128-browser";
await mkdir(out, { recursive: true });
const requests = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let companies = [];
let setupResult;
let setupCount = 0;
let members = [
  { id: "m1", email: "owner@example.test", display_name: "Owner", role: "owner" },
  { id: "m2", email: "member@example.test", display_name: "Member", role: "member" },
];
let invitations = [];
let mode = "ok",
  failRead = false,
  language = "en";
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
    return reply({
      id: "owner",
      email: "owner@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/company-setup/playground")
    return reply({
      requested: false,
      enabled: true,
      eligible: true,
      archived: false,
      receipt: null,
    });
  if (path === "/api/company-setup/options")
    return reply({
      actor_id: "owner",
      suggested_name: "Harbor Supply",
      environments: ["business", "sandbox"],
      practice_enabled: true,
      pending: false,
    });
  if (path === "/api/company-setup" && req.method() === "POST") {
    const body = req.postDataJSON();
    setupCount++;
    assert.equal(body.content, "international_demo");
    assert.equal(body.environment, "sandbox");
    assert.equal(body.live_simulation, true);
    setupResult = {
      tenant_id: "live-company",
      run_id: "live-run",
      name: body.name,
      status: "ready",
      environment: "sandbox",
      destination: "/app?tenant=live-company",
      profile: { key: "international_demo", version: 1 },
    };
    return reply(setupResult, 201);
  }
  if (path.startsWith("/api/company-setup/requests/")) return reply(setupResult);
  if (path === "/api/v1/bootstrap")
    return failRead
      ? reply({ detail: "Unavailable" }, 503)
      : reply({ tenants: companies, default_tenant_id: companies[0]?.id || null });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.endsWith("/dashboard"))
    return reply({ totals: { open_deliveries: 0, exceptions: 0, pending_decisions: 0 } });
  if (path.endsWith("/analytics"))
    return reply({
      position: {
        open: 0,
        fully_reserved: 0,
        needs_reservation: 0,
        overdue: 0,
        unknown_due: 0,
        coverage_percent: "0",
      },
      series: [],
    });
  if (path === "/api/v1/companies" && req.method() === "GET")
    return reply(
      companies.map((company) => ({
        ...company,
        created_at: "2026-09-14T12:00:00Z",
        archived_at: null,
        state: "empty",
        source_count: 0,
        evidence_count: 0,
        reality_count: 0,
        configured_count: 0,
        last_activity_at: null,
      })),
    );
  if (path === "/api/v1/companies" && req.method() === "POST") {
    if (mode === "reject") return reply({ detail: "Rejected name" }, 422);
    const company = {
      id: `c${companies.length + 1}`,
      name: req.postDataJSON().name,
      role: "owner",
    };
    companies.push(company);
    if (mode === "refresh-lost") failRead = true;
    return mode === "lost" ? route.abort("failed") : reply(company);
  }
  if (path.endsWith("/settings/members"))
    return failRead ? reply({ detail: "Unavailable" }, 503) : reply({ members, invitations });
  if (path.includes("/settings/") && req.method() === "POST") {
    if (mode === "reject")
      return reply({ detail: "Please wait before resending this invitation." }, 409);
    if (path.endsWith("/invitations"))
      invitations.push({
        id: `i${invitations.length + 1}`,
        email: req.postDataJSON().email,
        status: "pending",
        delivery_status: "processing",
        expires_at: "2026-10-01T00:00:00Z",
      });
    if (path.endsWith("/resend")) {
      const i = invitations.find((i) => path.includes(`/${i.id}/`));
      i.status = "pending";
      i.delivery_status = "processing";
    }
    if (path.endsWith("/revoke"))
      invitations = invitations.filter((i) => !path.includes(`/${i.id}/`));
    if (path.endsWith("/remove")) members = members.filter((m) => !path.includes(`/${m.id}/`));
    return mode === "lost" ? route.abort("failed") : reply({ status: "pending" });
  }
  if (path === "/api/auth/invitations/accept")
    return reply({ status: "accepted", company: companies[1] });
  if (path === "/api/auth/invitations/inspect")
    return reply({ status: "pending", company_name: "Other company", email: "owner@example.test" });
  if (req.method() !== "GET") throw new Error(`Unexpected write: ${path}`);
  return reply({ items: [], total: 0 });
});
const go = (view = "access", tenant = companies[0]?.id || "") =>
  page.goto(`${base}/app/settings?settings_view=${view}&tenant=${tenant}`);
const writes = () => requests.filter((r) => r.method === "POST").length;
const confirm = () => page.getByRole("button", { name: "Confirm", exact: true }).click();
try {
  for (const lang of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const mobile of [false, true]) {
        language = lang;
        companies = [
          { id: "existing", name: "Acme Trading", role: "member", company_kind: "company" },
          {
            id: "empty",
            name: "Warehouse Practice",
            role: "owner",
            sandbox_run_id: "empty-run",
            company_kind: "sandbox",
          },
          {
            id: "static",
            name: "Harbor International",
            role: "owner",
            sandbox_run_id: "static-run",
            company_kind: "demo",
          },
          {
            id: "live",
            name: "Northstar Live",
            role: "owner",
            sandbox_run_id: "live-run",
            company_kind: "demo",
            demo_data_state: "running",
          },
        ];
        await page.goto(base);
        await page.evaluate((theme) => {
          localStorage.setItem("reality.theme", theme);
          sessionStorage.clear();
        }, theme);
        await page.setViewportSize(
          mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 },
        );
        await page.goto(`${base}/app/settings?settings_view=company&tenant=existing`);
        await page.locator('[data-company-card="existing"]').waitFor();
        assert.equal(
          await page
            .locator('[data-company-card="existing"] [data-company-actions] button')
            .count(),
          0,
          "Members have no management actions",
        );
        assert.equal(
          await page
            .locator('[data-company-card="empty"] [data-company-actions="empty"] button')
            .count(),
          3,
          "Actions are inside their company card",
        );
        await page.screenshot({
          path: `${out}/company-cards-${lang}-${theme}-${mobile}.png`,
          fullPage: true,
        });
        if ((await page.locator("main .register-actions").getAttribute("open")) === null)
          await page.locator("main .register-actions summary").click();
        await page.locator('main [data-page-action="menu"]').first().click();
        await page.locator("dialog #setup-company-name").waitFor();
        assert.equal(await page.locator("dialog #setup-company-name").inputValue(), "");

        const choices = page.locator('dialog input[name="company-start"]');
        assert.equal(await choices.count(), 3);
        assert.equal(await choices.nth(0).isChecked(), true);
        assert.equal(await page.locator("dialog fieldset").count(), 1);
        assert.equal(await page.locator('dialog input[type="checkbox"]').count(), 0);
        await choices.nth(2).check();
        await page.locator('dialog input[type="checkbox"]').check();
        await choices.nth(1).check();
        assert.equal(await page.locator('dialog input[type="checkbox"]').count(), 0);
        await choices.nth(2).check();
        assert.equal(await page.locator('dialog input[type="checkbox"]').isChecked(), false);
        await page.locator('dialog input[type="checkbox"]').check();
        const nameInput = page.locator("dialog #setup-company-name");
        const createButton = page.locator("dialog .onboarding-form button.primary-button");
        const writesBeforeInvalid = setupCount;
        assert.equal(await createButton.isEnabled(), true);
        for (const invalidName of ["", "   "]) {
          await nameInput.fill(invalidName);
          await createButton.click();
          await page.locator("#setup-company-name-error").waitFor();
          assert.equal(await nameInput.getAttribute("aria-invalid"), "true");
          assert.equal(await nameInput.evaluate((el) => el === document.activeElement), true);
          assert.equal(setupCount, writesBeforeInvalid);
          assert.equal(await choices.nth(2).isChecked(), true);
          assert.equal(await page.locator('dialog input[type="checkbox"]').isChecked(), true);
        }
        await nameInput.fill("Harbor Live");
        assert.equal(await page.locator("#setup-company-name-error").count(), 0);
        await page.screenshot({
          path: `${out}/live-${lang}-${theme}-${mobile}.png`,
          fullPage: true,
        });
        const before = setupCount;
        const newCompany = {
          id: "live-company",
          name: "Harbor Live",
          role: "owner",
          sandbox_run_id: "live-run",
        };
        if (mobile) companies.push(newCompany);
        await page.locator("dialog .onboarding-form button.primary-button").click();
        if (!mobile) {
          // A ready receipt survives opening failure and reload without recreation.
          await page.locator('dialog [role="alert"]').waitFor();
          companies.push(newCompany);
          await page.reload();
          if ((await page.locator("main .register-actions").getAttribute("open")) === null)
            await page.locator("main .register-actions summary").click();
          await page.locator('main [data-page-action="menu"]').first().click();
        }
        await page.waitForURL(/tenant=live-company/);
        assert.equal(setupCount, before + 1);
        assert.equal(await page.locator("dialog[open]").count(), 0);
        await page.locator('[data-company-created="live-company"]').waitFor();
        assert.equal(await page.locator("main").count(), 1);
        assert.deepEqual(errors, []);
      }
  console.log(
    "PASS: 16 unified live-company creation/recovery/open combinations; no separate connect/start requests.",
  );
} catch (error) {
  console.error(errors);
  console.error(await page.locator("body").innerText());
  throw error;
} finally {
  await browser.close();
}
