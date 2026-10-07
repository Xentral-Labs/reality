// Real authenticated API and UI proof: use only the user's existing private company access.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.UNIFIED_BASE_URL;
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
const errors = [];
try {
  const login = await context.request.post(`${base}/api/auth/login`, {
    data: { email: "cockpit-owner@example.test", password: "a-long-account-password" },
  });
  assert.equal(login.status(), 200, await login.text());
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  page.on("pageerror", (error) => errors.push(error.message));
  for (const tenant of process.env.PLAYGROUND_TENANTS.split(",")) {
    const capability = await context.request.get(
      `${base}/api/tenants/${tenant}/operations-cockpit/capabilities`,
    );
    assert.equal(capability.status(), 200, await capability.text());
    assert.deepEqual(await capability.json(), { enabled: true });
    await page.goto(`${base}/app/cockpit?tenant=${tenant}&lang=en`);
    await page.locator("[data-operating-status]").waitFor();
    await page.locator("[data-cockpit-observed-at]").waitFor();
    assert.equal(await page.locator("[data-control-tower-unavailable]").count(), 0);
    assert.equal(new URL(page.url()).searchParams.get("tenant"), tenant);
    const status = await context.request.get(
      `${base}/api/tenants/${tenant}/operational-cases/status`,
    );
    assert.equal(status.status(), 200, await status.text());
    assert.equal((await status.json()).can_control, false);
    const register = await context.request.get(
      `${base}/api/tenants/${tenant}/operational-cases/register`,
    );
    assert.equal(register.status(), 200, await register.text());
    await page.screenshot({
      path: `${process.env.SHOTS}/playground-${tenant}.png`,
      fullPage: true,
    });
  }
  const foreign = process.env.FOREIGN_PLAYGROUND;
  const denied = await context.request.get(
    `${base}/api/tenants/${foreign}/operations-cockpit/capabilities`,
  );
  assert.equal(denied.status(), 404, await denied.text());
  const foreignBootstrap = await context.request.get(
    `${base}/api/v1/bootstrap?cockpit_tenant=${foreign}`,
  );
  assert.equal(foreignBootstrap.status(), 404, await foreignBootstrap.text());
  assert.deepEqual(errors, []);
  console.log(
    "Real practice and temporary Control Tower pages render without activation; other private companies stay inaccessible.",
  );
} finally {
  await browser.close();
}
