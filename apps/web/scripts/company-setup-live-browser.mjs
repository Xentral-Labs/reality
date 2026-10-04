import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";

const canonicalSource = (value) =>
  Array.isArray(value)
    ? value.map(canonicalSource)
    : value !== null && typeof value === "object"
      ? Object.fromEntries(
          Object.keys(value)
            .sort()
            .map((key) => [key, canonicalSource(value[key])]),
        )
      : value;

import { pathToFileURL } from "node:url";

const modulePath =
  process.env.PLAYWRIGHT_MODULE ||
  "/private/tmp/reality-playwright/node_modules/playwright-core/index.js";
const playwright = await import(pathToFileURL(modulePath));
const { chromium } = playwright.default;
// A local checkout may keep the admin credentials in the repository's .env; a harness
// passes them in the environment instead.
const localEnv = Object.fromEntries(
  (await readFile(new URL("../../../.env", import.meta.url), "utf8").catch(() => ""))
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith("#") && line.includes("="))
    .map((line) => {
      const position = line.indexOf("=");
      return [line.slice(0, position), line.slice(position + 1).replace(/^['"]|['"]$/g, "")];
    }),
);
const browser = await chromium.launch({
  headless: process.env.HEADLESS !== "false",
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
  slowMo: process.env.HEADLESS === "false" ? 250 : 0,
});
const output = process.env.SHOTS || "/private/tmp/reality-251-browser";
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
  await page.waitForURL(/\/app/, { waitUntil: "commit" });
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
  let setupTenant;
  page.on("response", async (response) => {
    if (response.url().includes("/api/company-setup") && response.status() < 300) {
      const receipt = await response.json().catch(() => null);
      if (receipt?.tenant_id) setupTenant = receipt.tenant_id;
    }
  });
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
  await page.waitForURL(
    (url) => Boolean(setupTenant) && url.searchParams.get("tenant") === setupTenant,
    { timeout: 30_000 },
  );
  const tenant = new URL(page.url()).searchParams.get("tenant");
  assert.ok(tenant, "The confirmed setup must open its actual company");
  const demo = `${base}/api/tenants/${encodeURIComponent(tenant)}/demo-data`;
  const get = async (url) => {
    const response = await page.request.get(url);
    assert.equal(response.status(), 200, await response.text());
    return response.json();
  };
  let waiting;
  const sourceDeadline = Date.now() + 60_000;
  while (Date.now() < sourceDeadline) {
    waiting = await get(demo);
    if (waiting.awaiting_decision >= 1) break;
    await page.waitForTimeout(500);
  }
  assert.ok(
    waiting.awaiting_decision >= 1,
    `Initial sources must await actual decisions: ${JSON.stringify(waiting)}`,
  );
  assert.equal(waiting.imported, 0, "Starting a source must not approve its business effects");
  await page.goto(`${base}/app/demo-data?tenant=${encodeURIComponent(tenant)}`);
  await page.locator("[data-awaiting-reviewer]").waitFor();
  await page.screenshot({ path: `${output}/04-awaiting-review.png`, fullPage: true });
  const pauseRequestKey = `review-proof-pause-${Date.now()}`;
  let paused;
  const pauseDeadline = Date.now() + 60_000;
  while (Date.now() < pauseDeadline) {
    const current = await get(demo);
    paused = await page.request.post(`${demo}/control`, {
      data: {
        action: "pause",
        expected_revision: current.revision,
        request_key: pauseRequestKey,
        confirmed: true,
      },
    });
    if (paused.status() !== 409) break;
    assert.equal((await paused.json()).code, "unfinished_run");
    // A claimed worker run must finish before a source control can cancel its queue.
    await page.waitForTimeout(500);
  }
  assert.equal(paused.status(), 200, await paused.text());
  const beforeReview = await get(demo);
  const pending = await get(
    `${base}/api/tenants/${encodeURIComponent(tenant)}/change-proposals?tool=intake_apply&size=100`,
  );
  const proposal = pending.items[0];
  assert.ok(proposal, "A retained prepared source must be reviewable");
  const review = await get(
    `${base}/api/tenants/${encodeURIComponent(tenant)}/change-proposals/${proposal.id}/review`,
  );
  assert.equal(review.status, "proposed");
  assert.equal(review.input.plan.profile, "demo.order");
  const original = await page.request.get(
    `${base}/api/tenants/${encodeURIComponent(tenant)}/intake-units/${proposal.id}/original`,
  );
  assert.equal(original.status(), 200);
  const originalText = await original.text();
  assert.equal(original.headers()["x-source-digest"], review.input.plan.source_hash);
  assert.equal(
    createHash("sha256")
      .update(JSON.stringify(canonicalSource(JSON.parse(originalText))))
      .digest("hex"),
    review.input.plan.source_hash,
  );
  assert.equal(JSON.parse(originalText).synthetic, true);
  await page.goto(
    `${base}/app/decisions?tenant=${encodeURIComponent(tenant)}&proposal=${proposal.id}`,
  );
  const sourceReview = page
    .getByRole("dialog")
    .filter({ has: page.locator("#proposal-review-title") });
  await sourceReview.waitFor();
  await sourceReview.getByRole("button", { name: /Confirm change|Änderung bestätigen/ }).click();
  let decided;
  const decisionDeadline = Date.now() + 15_000;
  while (Date.now() < decisionDeadline) {
    decided = await get(
      `${base}/api/tenants/${encodeURIComponent(tenant)}/change-proposals/${proposal.id}/review`,
    );
    if (decided.status === "executed") break;
    await page.waitForTimeout(200);
  }
  assert.equal(decided.status, "executed", JSON.stringify(decided));
  assert.equal(decided.decider.kind, "person");
  assert.equal(decided.receipt.source_record_id, review.input.plan.source_record_id);
  const after = await get(demo);
  assert.equal(after.imported, 1);
  assert.equal(
    after.awaiting_decision,
    beforeReview.awaiting_decision - 1,
    "Confirming one source must leave every other source pending",
  );
  await page.screenshot({ path: `${output}/05-exact-source-confirmed.png`, fullPage: true });
  await writeFile(
    `${output}/review-result.json`,
    JSON.stringify(
      {
        tenant,
        proposal_id: proposal.id,
        source_record_id: decided.receipt.source_record_id,
        digest: decided.receipt.digest,
        original: originalText,
      },
      null,
      2,
    ),
  );
  assert.equal(errors.length, 0, errors.join("\n"));
  console.log(
    JSON.stringify({ name, observed: [...observed].sort(), completionRect, output }, null, 2),
  );
} finally {
  if (process.env.KEEP_BROWSER_OPEN === "true") await page.waitForTimeout(10_000);
  await browser.close();
}
