import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const modulePath =
  process.env.PLAYWRIGHT_MODULE ||
  "/private/tmp/reality-playwright/node_modules/playwright-core/index.js";
const playwright = await import(pathToFileURL(modulePath));
const { chromium } = playwright.default;
const localEnv = Object.fromEntries(
  (await readFile(new URL("../../../.env", import.meta.url), "utf8"))
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith("#") && line.includes("="))
    .map((line) => {
      const position = line.indexOf("=");
      return [line.slice(0, position), line.slice(position + 1).replace(/^['"]|['"]$/g, "")];
    }),
);
const browser = await chromium.launch({
  headless: process.env.HEADLESS !== "false",
  executablePath:
    process.env.PLAYWRIGHT_EXECUTABLE ||
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  slowMo: process.env.HEADLESS === "false" ? 250 : 0,
});
const output = "/private/tmp/reality-251-browser";
await mkdir(output, { recursive: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(20_000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));

try {
  const email = process.env.REALITY_PLATFORM_ADMIN_EMAIL || localEnv.REALITY_PLATFORM_ADMIN_EMAIL;
  const password =
    process.env.REALITY_PLATFORM_ADMIN_PASSWORD || localEnv.REALITY_PLATFORM_ADMIN_PASSWORD;
  assert.ok(email, "Admin email is required");
  assert.ok(password, "Admin password is required");
  const base = process.env.UNIFIED_APP_URL || "http://localhost:8080";
  await page.goto(`${base}/login?lang=de`);
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.locator('form button[type="submit"], form button').first().click();
  await page.waitForURL(/\/app/);
  await page.evaluate(() => sessionStorage.clear());
  const recovery = process.env.RECOVER_REQUEST_KEY
    ? {
        actor: process.env.RECOVER_ACTOR_ID,
        request_key: process.env.RECOVER_REQUEST_KEY,
        confirmed: true,
        name: process.env.RECOVER_NAME,
        environment: "sandbox",
        content: "international_demo",
        live_simulation: true,
      }
    : null;
  if (recovery) {
    assert.ok(recovery.actor && recovery.name, "Recovery actor and company name are required");
    await page.evaluate(
      (request) =>
        sessionStorage.setItem(`reality.company-setup.${request.actor}`, JSON.stringify(request)),
      recovery,
    );
  }
  await page.goto(`${base}/app/settings?settings_view=new&lang=de`);
  const dialog = page.locator("dialog.company-setup-dialog");
  await dialog.waitFor({ state: "visible" });
  const name = recovery?.name || `Reality Demo Cost Ready ${Date.now()}`;
  if (!recovery) {
    await dialog.locator("#setup-company-name").fill(name);
    await dialog.locator('input[value="demo"]').check();
    const live = dialog.locator('input[type="checkbox"]');
    if (!(await live.isChecked())) await live.check();
    await page.screenshot({ path: `${output}/01-before-create.png`, fullPage: true });
    await dialog.getByRole("button", { name: /Unternehmen erstellen|Create company/ }).click();
  }

  const observed = new Set();
  let completionRect = null;
  const deadline = Date.now() + 180_000;
  while (Date.now() < deadline) {
    const alert = dialog.locator('[role="alert"]');
    if (await alert.count()) throw new Error(await alert.innerText());
    const steps = page.locator("[data-setup-step]");
    for (let index = 0; index < (await steps.count()); index++) {
      const step = steps.nth(index);
      observed.add(
        `${await step.getAttribute("data-setup-step")}:${await step.getAttribute("data-state")}`,
      );
    }
    if (observed.has("calculation:current"))
      await page.screenshot({ path: `${output}/02-calculation-confirmed.png`, fullPage: true });
    if (observed.has("ready:current")) {
      completionRect = await dialog.boundingBox();
      await page.screenshot({ path: `${output}/03-ready.png`, fullPage: true });
      break;
    }
    await page.waitForTimeout(250);
  }
  if (!recovery) assert.ok(observed.has("data:current"), "Data preparation was not visible");
  assert.ok(observed.has("calculation:current"), "Calculation completion was not visible");
  assert.ok(observed.has("ready:current"), "Ready completion was not visible");
  await page.waitForURL(new RegExp(`/app.*tenant=`), { timeout: 30_000 });
  assert.equal(errors.length, 0, errors.join("\n"));
  console.log(
    JSON.stringify({ name, observed: [...observed].sort(), completionRect, output }, null, 2),
  );
} finally {
  if (process.env.KEEP_BROWSER_OPEN === "true") await page.waitForTimeout(10_000);
  await browser.close();
}
