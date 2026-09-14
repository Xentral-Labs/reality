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
  await go("company");
  await page.getByLabel("Company name", { exact: true }).fill("Northstar Commerce");
  await page.getByRole("button", { name: "Review company", exact: true }).click();
  assert.equal(writes(), 0);
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  assert.equal(writes(), 0);
  await page.getByRole("button", { name: "Review company", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).evaluate((button) => {
    button.click();
    button.click();
  });
  await page.waitForURL(/tenant=c1/);
  assert.equal(writes(), 1);
  assert.equal(requests.find((r) => r.path === "/api/v1/companies").body.guided_demo, false);
  await go();
  await page.getByLabel("Work email", { exact: true }).fill("invite@example.test");
  await page.getByRole("button", { name: "Review invitation", exact: true }).click();
  assert.equal(writes(), 1);
  await page.screenshot({ path: `${out}/invitation-review.png`, fullPage: true });
  await confirm();
  await page.getByText(/Sending invitation/).waitFor();
  assert.equal(await page.getByText("Invitation delivered", { exact: true }).count(), 0);
  assert.equal(writes(), 2);
  mode = "reject";
  await page.getByRole("button", { name: "Resend", exact: true }).click();
  await confirm();
  await page.getByRole("alert").waitFor();
  assert.match(await page.getByRole("alert").innerText(), /wait/);
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  mode = "lost";
  await page.getByLabel("Work email", { exact: true }).fill("unknown@example.test");
  await page.getByRole("button", { name: "Review invitation", exact: true }).click();
  await confirm();
  await page.getByRole("button", { name: "Check current access", exact: true }).waitFor();
  const before = writes();
  failRead = true;
  await page.getByRole("button", { name: "Check current access", exact: true }).click();
  await page
    .getByText("Could not check current access. Try checking again.", { exact: true })
    .waitFor();
  assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).isDisabled(), true);
  failRead = false;
  mode = "ok";
  await page.getByRole("button", { name: "Check current access", exact: true }).click();
  await page.getByText("unknown@example.test", { exact: true }).waitFor();
  assert.equal(writes(), before);
  await page.getByRole("button", { name: "Revoke", exact: true }).first().click();
  await confirm();
  await page
    .locator("li")
    .getByText("invite@example.test", { exact: true })
    .waitFor({ state: "detached" });
  await page.getByRole("button", { name: "Remove", exact: true }).click();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  assert.equal(members.length, 2);
  await page.getByRole("button", { name: "Remove", exact: true }).click();
  await confirm();
  await page
    .locator("li")
    .getByText("member@example.test", { exact: true })
    .waitFor({ state: "detached" });
  assert.equal(await page.getByRole("button", { name: "Remove", exact: true }).count(), 0);
  invitations[0].status = "expired";
  await go();
  await page.getByRole("button", { name: "Resend", exact: true }).click();
  await confirm();
  await page.getByText(/Sending invitation/).waitFor();
  companies.push({ id: "other", name: "Northstar Commerce", role: "member" });
  await go();
  await page.getByLabel("Work email", { exact: true }).fill("discard@example.test");
  await page.getByRole("button", { name: "Review invitation", exact: true }).click();
  assert.match(await page.locator('[data-company-option="other"]').innerText(), /other/);
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="other"]').click();
  await page.getByText("Only company owners can view these settings.", { exact: true }).waitFor();
  assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).count(), 0);
  assert.equal(requests.filter((r) => r.path.includes("/other/settings/")).length, 0);
  await go("company");
  await page.getByRole("button", { name: "New company", exact: true }).click();
  await page.getByLabel("Company name", { exact: true }).fill("Northstar Commerce");
  await page.getByRole("button", { name: "Review company", exact: true }).click();
  mode = "lost";
  await confirm();
  await page.getByRole("button", { name: "Check companies", exact: true }).waitFor();
  const createdWrites = writes();
  failRead = true;
  await page.getByRole("button", { name: "Check companies", exact: true }).click();
  await page.getByText("Could not check companies. Try checking again.", { exact: true }).waitFor();
  failRead = false;
  mode = "ok";
  await page.getByRole("button", { name: "Check companies", exact: true }).click();
  await page
    .getByText("Choose the company to open. Names may be identical.", { exact: true })
    .waitFor();
  assert.equal(writes(), createdWrites);
  await page.getByRole("button", { name: /c3/ }).click();
  await page.waitForURL(/tenant=c3/);
  await page.getByRole("button", { name: "New company", exact: true }).click();
  await page.getByLabel("Company name", { exact: true }).fill("Rejected company");
  await page.getByRole("button", { name: "Review company", exact: true }).click();
  mode = "reject";
  await confirm();
  await page.getByRole("alert").waitFor();
  assert.equal(companies.length, 3);
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page.getByLabel("Company name", { exact: true }).fill("Known company");
  await page.getByRole("button", { name: "Review company", exact: true }).click();
  mode = "refresh-lost";
  await confirm();
  await page.getByRole("button", { name: "Check companies", exact: true }).waitFor();
  const knownWrites = writes();
  failRead = false;
  mode = "ok";
  await page.getByRole("button", { name: "Check companies", exact: true }).click();
  await page.waitForURL(/tenant=c4/);
  assert.equal(writes(), knownWrites);
  for (const lang of ["en", "de", "nl", "es"]) {
    language = lang;
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await go();
      await page.locator('input[type="email"]').waitFor();
      await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: `${out}/${lang}-${width}-access.png`, fullPage: true });
      await page.locator('input[type="email"]').fill("review@example.test");
      await page.locator("main form button").click();
      const review = page.locator('section[tabindex="-1"]');
      await review.waitFor();
      const expected = {
        en: "Send an invitation",
        de: "Einladung an diese",
        nl: "Een uitnodiging",
        es: "Enviar una invitación",
      };
      assert.ok((await review.innerText()).includes(expected[lang]));
      await page.screenshot({ path: `${out}/${lang}-${width}-review.png`, fullPage: true });
      await go("company");
      await page.locator('section[data-settings-view="company"]').waitFor();
      await page.screenshot({ path: `${out}/${lang}-${width}-company.png`, fullPage: true });
    }
  }
  language = "en";
  await page.goto(`${base}/invitation#token=fixture-secret`);
  await page.getByRole("button", { name: "Accept invitation", exact: true }).click();
  await page.waitForURL(/\/app\?tenant=other/);
  await page.getByRole("heading", { name: "Your business, in focus.", exact: true }).waitFor();
  await page.getByRole("button", { name: "Open analytics", exact: true }).waitFor();
  assert.equal(
    await page
      .getByRole("button", { name: "Switch company", exact: true })
      .getAttribute("data-company-id"),
    "other",
  );
  assert.equal(await page.evaluate(() => sessionStorage.getItem("reality.invitationToken")), null);
  assert.deepEqual(errors, []);
  console.log(
    "Company creation, invitation/member controls, recovery, permissions, context and responsive localization passed.",
  );
} catch (e) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  throw e;
} finally {
  await browser.close();
}
