// Delayed transport fixtures prove visible entry feedback without creating real accounts.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage();
const base = process.env.UNIFIED_APP_URL || "http://localhost:8080";
let active = false,
  failedVerification = true;
let verificationPosts = 0;
const user = {
  id: "progress_user",
  email: "progress@example.test",
  status: "active",
  language: "de",
  locale: "de-DE",
  timezone: "UTC",
};
const delay = () => new Promise((resolve) => setTimeout(resolve, 1200));
await page.route("**/api/**", async (route) => {
  const path = new URL(route.request().url()).pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (path === "/api/auth/me") {
    await delay();
    return reply(active ? user : { detail: "Not signed in" }, active ? 200 : 401);
  }
  if (path === "/api/auth/signup") {
    await delay();
    return reply({ verification_code: "123456" }, 201);
  }
  if (path === "/api/auth/verify-email") {
    verificationPosts++;
    await delay();
    if (failedVerification) return reply({ detail: "Invalid code" }, 400);
    active = true;
    return reply(user);
  }
  if (path === "/api/v1/bootstrap") {
    await delay();
    return reply({ tenants: [], default_tenant_id: null });
  }
  if (path === "/api/company-setup/playground") {
    await delay();
    if (route.request().method() === "GET")
      return reply({
        requested: true,
        enabled: true,
        eligible: true,
        archived: false,
        receipt: null,
      });
    return reply({ status: "initialization_failed" }, 201);
  }
  return reply({});
});
try {
  await page.goto(`${base}/signup?lang=de`);
  await page
    .getByRole("status")
    .filter({ hasText: "Dein Zugang wird geladen" })
    .waitFor({ timeout: 900 });
  await page.locator("input[name=email]").fill(user.email);
  await page.locator("input[name=password]").fill("Synthetic-password-only");
  await page.locator("input[type=checkbox]").check();
  await page.locator("form button").click();
  assert.equal(await page.locator("form button").isDisabled(), true);
  await page.waitForURL("**/verify-email?lang=de");
  await page.locator("input.auth-code").waitFor();
  await page.locator("form button").click();
  await page
    .getByRole("status")
    .filter({ hasText: "Deine E-Mail-Adresse wird bestätigt" })
    .waitFor({ timeout: 900 });
  assert.equal(await page.locator("form button").isDisabled(), true);
  await page.locator(".auth-error").waitFor();
  assert.equal(await page.locator("form button").isEnabled(), true);
  assert.equal(verificationPosts, 1);
  failedVerification = false;
  await page.locator("form button").click();
  await page.waitForURL("**/app?lang=de");
  await page
    .getByRole("status")
    .filter({ hasText: "Dein Zugang wird geladen" })
    .waitFor({ timeout: 900 });
  await page.getByRole("status").filter({ hasText: "Dein Arbeitsbereich wird geladen" }).waitFor();
  await page.getByRole("status").filter({ hasText: "Dein Zugang wird geladen" }).waitFor();
  await page.getByRole("status").filter({ hasText: "Deine Demo-Firma wird vorbereitet" }).waitFor();
  await page.screenshot({ path: "/private/tmp/reality-190-entry-progress.png" });
  await page.getByRole("button", { name: "Erneut versuchen", exact: true }).waitFor();
  console.log(
    "PASS: slow auth/signup/verification/bootstrap/policy/setup feedback; retry and language continuity",
  );
} finally {
  await browser.close();
}
