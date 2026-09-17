import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
page.setDefaultTimeout(10000);
const errors = [],
  writes = [],
  reads = [];
let status = "active";
let failLogout = true;
page.on("pageerror", (error) => errors.push(error.message));
const user = {
  id: "u1",
  email: "owner@example.test",
  display_name: "Owner",
  status: "active",
  language: "en",
  locale: "en-GB",
  timezone: "UTC",
};
const pager = { number: 1, size: 50, total: 0, pages: 1, has_previous: false, has_next: false };
await page.route("**/api/**", (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname;
  const json = (data, code = 200) =>
    route.fulfill({ status: code, contentType: "application/json", body: JSON.stringify(data) });
  if (req.method() !== "GET") writes.push(path);
  else reads.push(path);
  if (path === "/api/auth/logout") {
    if (failLogout) return json({ detail: "Temporary logout failure" }, 503);
    status = "out";
    return route.fulfill({ status: 204 });
  }
  if (path === "/api/auth/me")
    return status === "out"
      ? json({ detail: "Authentication required" }, 401)
      : json({ ...user, status });
  if (path === "/api/v1/bootstrap")
    return json({
      tenants: [
        { id: "t1", name: "First company", role: "owner" },
        { id: "t2", name: "Second company", role: "member" },
      ],
      default_tenant_id: "t1",
    });
  if (path.endsWith("/dashboard"))
    return json({
      totals: { exceptions: 0, open_commitments: 0, open_deliveries: 0, pending_decisions: 0 },
      exceptions: [],
      inventory: [],
      facts: [],
      capabilities: {},
    });
  if (path.endsWith("/copilot"))
    return json({
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path.endsWith("/analytics"))
    return json({
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
  if (path.endsWith("/settings/members")) return json({ members: [], invitations: [] });
  if (path.endsWith("/settings/ai"))
    return json({
      copilot: { available: false, credential_mode: "managed" },
      tokens: [],
      tools: [],
      mcp_url: "http://localhost:8001/mcp",
    });
  if (path.endsWith("/application-reference")) return json({ workspaces: [] });
  if (path.endsWith("/exception-catalog"))
    return json({
      version: 1,
      classes: [
        {
          id: "late",
          label: "Late delivery",
          description: "A promised delivery is overdue.",
          severity: "high",
          owner: "Operations",
          clears_through: "Record the shipment.",
        },
      ],
    });
  if (
    path.endsWith("/movements") ||
    path.endsWith("/payments") ||
    path.endsWith("/change-proposals")
  )
    return json({ items: [], page: pager, scope: { view: "movements" } });
  return json({ detail: `Unhandled fixture ${path}` }, 404);
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5188";
try {
  await page.goto(`${base}/app`);
  await page.getByRole("link", { name: "Orders & deliveries", exact: true }).waitFor();
  assert.equal(await page.locator('a[href^="/playground"]').count(), 0);
  assert.equal(await page.getByRole("link", { name: "Your work", exact: true }).count(), 0);
  await page.getByRole("button", { name: "Review commitments", exact: true }).click();
  await page.waitForURL("**/app/orders-deliveries?**");
  assert.equal(new URL(page.url()).searchParams.get("orders_view"), "deliveries");
  assert.equal(new URL(page.url()).searchParams.has("commitment"), false);
  await page.getByRole("link", { name: "Home", exact: true }).click();
  await page.getByRole("button", { name: "Profile", exact: true }).click();
  const profile = page.getByRole("dialog", { name: "Profile", exact: true });
  await profile.getByText(user.email, { exact: true }).waitFor();
  for (const name of ["Documentation", "Reality website"]) {
    const link = profile.getByRole("link", { name, exact: true });
    assert.equal(await link.getAttribute("target"), "_blank");
    assert.match(await link.getAttribute("href"), /^http:\/\/localhost:808[23]\/$/);
  }
  await page.screenshot({ path: "/private/tmp/profile-menu-desktop.png" });
  await page.keyboard.press("Escape");
  await profile.waitFor({ state: "hidden" });
  await page.getByRole("button", { name: "Profile", exact: true }).click();
  await profile.getByRole("link", { name: "Profile & preferences", exact: true }).click();
  await page.waitForURL("**/app/settings?**");
  assert.equal(new URL(page.url()).searchParams.get("settings_view"), "personal");
  assert.equal(await page.getByRole("link", { name: "Company access", exact: true }).count(), 0);
  assert.equal(
    await page.getByRole("link", { name: "Companies", exact: true }).count(),
    0,
    "Company management belongs to the company switcher, not the navigation",
  );
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-management="company"]').click();
  await page.waitForURL(/settings_view=company/);
  assert.equal(new URL(page.url()).searchParams.get("settings_view"), "company");
  assert.equal(await page.getByRole("navigation", { name: "Settings sections" }).count(), 0);
  const companies = page.getByRole("region", { name: "Companies", exact: true });
  await companies.getByText("First company", { exact: true }).waitFor();
  await companies.getByText("Second company", { exact: true }).waitFor();
  const ownerRow = companies.getByRole("listitem").filter({ hasText: "First company" });
  const memberRow = companies.getByRole("listitem").filter({ hasText: "Second company" });
  assert.equal(await memberRow.getByRole("button", { name: "Manage users" }).count(), 0);
  await memberRow
    .getByText("You are a member. Only company owners manage users and agent tokens.")
    .waitFor();
  assert.match(await companies.locator('[aria-current="true"]').textContent(), /First company/);
  await companies.getByRole("button", { name: /Second company/ }).click();
  await page.reload();
  assert.equal(new URL(page.url()).searchParams.get("tenant"), "t2");
  await companies.locator('[aria-current="true"]').waitFor();
  assert.match(await companies.locator('[aria-current="true"]').textContent(), /Second company/);
  const workspaceUrl = page.url();
  const userTrigger = ownerRow.getByRole("button", { name: "Manage users", exact: true });
  await userTrigger.click();
  const usersDialog = page.getByRole("dialog", { name: "Manage users", exact: true });
  await usersDialog.getByText("First company", { exact: true }).waitFor();
  await usersDialog.getByRole("textbox", { name: "Work email", exact: true }).waitFor();
  assert.equal(page.url(), workspaceUrl);
  assert.ok(reads.includes("/api/tenants/t1/settings/members"));
  await page.screenshot({ path: "/private/tmp/company-users-dialog.png" });
  await page.keyboard.press("Escape");
  await usersDialog.waitFor({ state: "hidden" });
  assert.equal(await userTrigger.evaluate((el) => el === document.activeElement), true);
  await ownerRow.getByRole("button", { name: "Agents & API tokens", exact: true }).click();
  const agentsDialog = page.getByRole("dialog", { name: "Agents & API tokens", exact: true });
  await agentsDialog.getByRole("button", { name: "New MCP token", exact: true }).waitFor();
  await agentsDialog.getByText("First company", { exact: true }).waitFor();
  assert.equal(page.url(), workspaceUrl);
  assert.ok(reads.includes("/api/tenants/t1/settings/ai"));
  assert.equal(
    await agentsDialog.getByText("AI credentials not configured", { exact: true }).count(),
    0,
  );
  await page.screenshot({ path: "/private/tmp/company-agents-dialog.png" });
  await agentsDialog.getByRole("button", { name: "Close", exact: true }).click();
  await ownerRow.getByRole("button", { name: "AI configuration", exact: true }).click();
  const aiDialog = page.getByRole("dialog", { name: "AI configuration", exact: true });
  await aiDialog.getByText("AI credentials not configured", { exact: true }).waitFor();
  assert.equal(
    await aiDialog.getByRole("button", { name: "New MCP token", exact: true }).count(),
    0,
  );
  await aiDialog.getByRole("button", { name: "Close", exact: true }).click();
  assert.equal(page.url(), workspaceUrl);
  assert.match(await companies.locator('[aria-current="true"]').textContent(), /Second company/);
  await page.goto(base + "/app/settings?tenant=t2&settings_view=agents");
  await agentsDialog
    .getByText("Only company owners can view these settings.", { exact: true })
    .waitFor();
  assert.equal(
    await agentsDialog.getByRole("button", { name: "New MCP token", exact: true }).count(),
    0,
  );
  assert.equal(
    reads.some((path) => path.startsWith("/api/tenants/t2/settings/")),
    false,
  );
  await agentsDialog.getByRole("button", { name: "Close", exact: true }).click();
  const newCompany = companies.getByRole("button", { name: "New company", exact: true });
  await newCompany.click();
  const creation = page.getByRole("dialog", { name: "New company", exact: true });
  await creation.getByRole("textbox", { name: "Company name", exact: true }).waitFor();
  await page.screenshot({ path: "/private/tmp/company-create-dialog.png" });
  await page.keyboard.press("Escape");
  await creation.waitFor({ state: "hidden" });
  assert.equal(await newCompany.evaluate((el) => el === document.activeElement), true);
  await page.screenshot({ path: "/private/tmp/company-settings.png" });
  assert.equal(writes.length, 0);
  await page.getByRole("button", { name: "Profile", exact: true }).click();
  await profile.getByRole("link", { name: "Profile & preferences", exact: true }).click();

  await page.getByRole("button", { name: "Profile", exact: true }).click();
  await profile.getByRole("button", { name: "Sign out", exact: true }).click();
  await profile.getByRole("alert").waitFor();
  assert.equal(new URL(page.url()).pathname, "/app/settings");
  failLogout = false;
  await profile.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.waitForURL("**/login");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  assert.deepEqual(writes.splice(0), ["/api/auth/logout", "/api/auth/logout"]);
  status = "active";
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base + "/app");
  await page.getByRole("button", { name: "Navigation", exact: true }).click();
  await page.getByRole("button", { name: "Profile", exact: true }).click();
  await profile.getByRole("button", { name: "Sign out", exact: true }).waitFor();
  const bounds = await profile.boundingBox();
  assert.ok(
    bounds.x >= 0 &&
      bounds.y >= 0 &&
      bounds.x + bounds.width <= 390 &&
      bounds.y + bounds.height <= 844,
  );
  await page.screenshot({ path: "/private/tmp/profile-menu-mobile.png" });
  await page.keyboard.press("Escape");
  await profile.waitFor({ state: "hidden" });
  await page.setViewportSize({ width: 1440, height: 950 });

  await page.goto(`${base}/app/movements?tenant=t2`);
  await page.getByText("Second company", { exact: true }).first().waitFor();
  assert.match(page.url(), /\/app\/warehouse\?/);
  assert.equal(new URL(page.url()).searchParams.get("tenant"), "t2");
  assert.equal(new URL(page.url()).searchParams.get("warehouse_view"), "movements");
  await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=exceptions`);
  await page.getByText("Late delivery", { exact: true }).click();
  await page.getByText("A promised delivery is overdue.").waitFor();
  for (const path of ["/playground", "/playground/runs/pgr_saved"]) {
    await page.goto(base + path);
    await page.getByRole("heading", { name: "Playground has been retired" }).waitFor();
    assert.equal(await page.getByRole("link", { name: "Open app" }).getAttribute("href"), "/app");
  }
  await page.screenshot({ path: "/private/tmp/retirement-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "/private/tmp/retirement-mobile.png", fullPage: true });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.goto(base + "/app/unknown");
  await page.getByRole("heading", { name: "Page unavailable" }).waitFor();
  status = "pending_approval";
  await page.goto(base + "/playground/runs/pgr_saved");
  await page.getByRole("heading", { name: "Playground has been retired" }).waitFor();
  await page.getByRole("link", { name: "Open app" }).click();
  await page.getByRole("heading", { name: "You’re on the list", exact: true }).waitFor();
  status = "out";
  await page.goto(base + "/app/movements?tenant=t2");
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor();
  assert.equal(
    await page.evaluate(() => sessionStorage.getItem("reality.app.return")),
    "/app/warehouse?tenant=t2&warehouse_view=movements",
  );
  assert.deepEqual(writes, []);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: profile settings/resources, logout failure and retry, mobile menu, sole app, redirects, company scope, catalog and auth boundaries; only explicit logout writes.",
  );
} catch (error) {
  console.error({ errors, body: await page.locator("body").innerText(), url: page.url() });
  throw error;
} finally {
  await browser.close();
}
