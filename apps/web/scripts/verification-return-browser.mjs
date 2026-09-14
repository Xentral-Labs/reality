// Fresh-tab recovery and resend use mock transport; no account or email is created.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_APP_URL || "http://localhost:5196";
try {
  for (const width of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    page.setDefaultTimeout(10000);
    let verifies = 0,
      resends = 0;
    await page.addInitScript(() => {
      sessionStorage.setItem("reality.signupEmail", "stale@example.test");
      sessionStorage.setItem("reality.localVerificationCode", "999999");
      sessionStorage.setItem("reality.invitationToken", "stale-token");
    });
    await page.route("**/api/**", async (route) => {
      const path = new URL(route.request().url()).pathname;
      const reply = (body, status = 200) =>
        route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
      if (path === "/api/auth/me") return reply({ detail: "Not signed in" }, 401);
      if (path === "/api/auth/resend-code") {
        resends++;
        assert.deepEqual(route.request().postDataJSON(), { email: "owner+trial@example.test" });
        return reply({ ok: true });
      }
      if (path === "/api/auth/verify-email") {
        verifies++;
        assert.deepEqual(route.request().postDataJSON(), {
          email: "owner+trial@example.test",
          code: "123456",
        });
        return reply({ detail: "Expired code" }, 400);
      }
      return reply({});
    });
    await page.goto(`${base}/verify-email#email=owner%2Btrial%40example.test`);
    await page.getByLabel("Email", { exact: true }).waitFor();
    assert.equal(
      await page.getByLabel("Email", { exact: true }).inputValue(),
      "owner+trial@example.test",
    );
    assert.equal(await page.getByLabel("Verification code", { exact: true }).inputValue(), "");
    assert.equal(new URL(page.url()).hash, "");
    assert.equal(
      await page.evaluate(() => sessionStorage.getItem("reality.signupEmail")),
      "owner+trial@example.test",
    );
    assert.equal(verifies, 0);
    await page.getByRole("button", { name: "Send a new code" }).click();
    await page.getByRole("status").filter({ hasText: "If this address" }).waitFor();
    assert.equal(resends, 1);
    await page.getByLabel("Verification code", { exact: true }).fill("123456");
    await page.getByRole("button", { name: "Verify email", exact: true }).click();
    await page.getByRole("alert").waitFor();
    assert.equal(verifies, 1);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({ path: `/private/tmp/verification-return-${width}.png` });
    await page.close();
  }
  const fresh = await browser.newPage();
  await fresh.route("**/api/**", (route) =>
    route.fulfill({
      status: 401,
      contentType: "application/json",
      body: '{"detail":"Not signed in"}',
    }),
  );
  await fresh.goto(`${base}/verify-email`);
  await fresh.getByLabel("Email", { exact: true }).waitFor();
  assert.equal(await fresh.getByLabel("Email", { exact: true }).inputValue(), "");
  await fresh.getByLabel("Email", { exact: true }).fill("manual@example.test");
  assert.equal(
    await fresh.getByLabel("Email", { exact: true }).inputValue(),
    "manual@example.test",
  );
  console.log(
    "PASS: fresh/stale tab, fragment scrubbing, manual email, explicit verification, resend and responsive layout",
  );
} finally {
  await browser.close();
}
