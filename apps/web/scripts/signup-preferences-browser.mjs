// A real browser states its own zone and language; fixtures capture what signup sends.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";

async function register(url, contextOptions) {
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  let sent = null;
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const reply = (body, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/auth/me") return reply({ detail: "Not signed in" }, 401);
    if (path === "/api/auth/signup") {
      sent = route.request().postDataJSON();
      return reply({ email: "registrant@example.test", next: "verify_email" }, 201);
    }
    return reply({});
  });
  await page.goto(url);
  await page.locator("input[name=email]").fill("registrant@example.test");
  await page.locator("input[name=password]").fill("Synthetic-password-only");
  await page.locator("input[type=checkbox]").check();
  await page.locator("form button").click();
  await page.waitForURL("**/verify-email**");
  await context.close();
  return sent;
}

try {
  const chosen = await register(`${base}/signup?lang=de`, {
    timezoneId: "America/Denver",
    locale: "en-US",
  });
  assert.equal(chosen.timezone, "America/Denver");
  assert.equal(chosen.language, "de", "an explicit page language wins over the browser request");
  assert.equal(chosen.locale, undefined, "a client never states a display locale");

  const requested = await register(`${base}/signup`, {
    timezoneId: "Europe/Amsterdam",
    locale: "nl-NL",
  });
  assert.equal(requested.timezone, "Europe/Amsterdam");
  assert.equal(requested.language, "nl", "without a choice the browser's language is taken");

  const unsupported = await register(`${base}/signup`, {
    timezoneId: "Asia/Tokyo",
    locale: "fr-FR",
  });
  assert.equal(unsupported.timezone, "Asia/Tokyo");
  assert.equal(
    unsupported.language,
    undefined,
    "an unsupported language states nothing, so the account keeps the server default",
  );

  console.log("PASS: signup states the browser's time zone and language, never a locale");
} finally {
  await browser.close();
}
