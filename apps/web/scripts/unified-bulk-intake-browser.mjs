// Real API/worker stack. Fault injection drops only already-committed responses.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir, readFile, writeFile } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const fixture = JSON.parse(process.env.JOURNEY_FIXTURE);
const base = process.env.JOURNEY_BASE_URL;
const out = process.env.JOURNEY_ARTIFACTS;
await mkdir(out, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  acceptDownloads: true,
});
const page = await context.newPage();
page.setDefaultTimeout(20000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
try {
  assert.equal(
    (
      await context.request.post(`${base}/api/auth/login`, {
        data: { email: fixture.email, password: fixture.password },
      })
    ).status(),
    200,
  );
  await page.goto(`${base}/app/decisions?tenant=${fixture.tenant}`);
  await page.getByRole("button", { name: "Select visible sources", exact: true }).click();
  assert.equal(await page.locator("[data-select-source]:checked").count(), 3);
  await page.getByRole("button", { name: "Clear selection", exact: true }).click();
  assert.equal(await page.locator("[data-select-source]:checked").count(), 0);
  await page.getByRole("button", { name: "Select visible sources", exact: true }).click();
  const preparePattern = "**/intake-batches/prepare";
  let preparedId;
  let originalRequest;
  await page.route(preparePattern, async (route) => {
    originalRequest = route.request().postDataJSON();
    const response = await route.fetch();
    assert.equal(response.status(), 200);
    preparedId = (await response.json()).id;
    await route.abort("failed");
  });
  await page.getByRole("button", { name: "Review selected sources", exact: true }).click();
  await page.getByRole("alert").waitFor();
  assert.equal(await page.locator("[data-select-source]:checked").count(), 3);
  await page.unroute(preparePattern);
  let retriedRequest;
  page.on("request", (request) => {
    if (request.url().endsWith("/intake-batches/prepare")) retriedRequest = request.postDataJSON();
  });
  await page.getByRole("button", { name: "Review selected sources", exact: true }).click();
  await page.locator("[data-intake-batch-review]").waitFor();
  assert.equal(new URL(page.url()).searchParams.get("proposal"), preparedId);
  assert.deepEqual(retriedRequest, originalRequest);
  const panel = page.getByRole("dialog");
  const members = panel.locator("[data-intake-member]");
  assert.equal(await members.count(), 3);
  const first = members.first();
  const memberId = await first.getAttribute("data-intake-member");
  await first.getByRole("button", { name: "Review source meaning", exact: true }).click();
  await first.locator("[data-source-meaning]").waitFor();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    first.getByRole("link", { name: "Download original source", exact: true }).click(),
  ]);
  assert.deepEqual(await readFile(await download.path()), Buffer.from(fixture.originals[memberId]));
  const pending = await (
    await context.request.get(
      `${base}/api/tenants/${fixture.tenant}/intake-batches/${preparedId}/status`,
    )
  ).json();
  assert.equal(pending.settled, 0);
  await page.screenshot({ path: `${out}/source-review.png`, fullPage: true });
  const approvePattern = `**/change-proposals/${preparedId}/approve`;
  await page.route(approvePattern, async (route) => {
    const response = await route.fetch();
    assert.equal(response.status(), 200);
    await route.abort("failed");
  });
  await panel.getByRole("button", { name: "Confirm change", exact: true }).click();
  await panel.getByRole("alert").waitFor();
  await page.unroute(approvePattern);
  await panel.getByRole("button", { name: "Confirm change", exact: true }).click();
  let completed;
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    completed = await (
      await context.request.get(
        `${base}/api/tenants/${fixture.tenant}/intake-batches/${preparedId}/status`,
      )
    ).json();
    if (completed.status === "executed" && completed.settled === 3) break;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  await writeFile(`${out}/before-reload.json`, JSON.stringify(completed, null, 2));
  assert.equal(completed.status, "executed");
  assert.deepEqual(completed.counts, { applied: 3 });
  await page.reload();
  await page.locator("[data-intake-batch-review]").waitFor();
  const status = await (
    await context.request.get(
      `${base}/api/tenants/${fixture.tenant}/intake-batches/${preparedId}/status`,
    )
  ).json();
  await writeFile(`${out}/status-debug.json`, JSON.stringify(status, null, 2));
  assert.deepEqual(status.counts, { applied: 3 });
  assert.ok(status.results.every((result) => result.receipt));
  const foreign = await context.request.get(
    `${base}/api/tenants/${fixture.foreign}/intake-units/${memberId}/original`,
  );
  assert.equal(foreign.status(), 404);
  for (const language of ["en", "de", "nl", "es"]) {
    assert.equal(
      (
        await context.request.put(`${base}/api/auth/profile`, {
          data: { display_name: "Bulk Owner", language, locale: "en-GB", timezone: "UTC" },
        })
      ).status(),
      200,
    );
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.reload();
      await page.locator("[data-intake-batch-review]").waitFor();
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: `${out}/${language}-${width}-results.png`, fullPage: true });
    }
  }
  assert.deepEqual(errors, []);
  await writeFile(`${out}/result.json`, JSON.stringify({ batch_id: preparedId, status }, null, 2));
  console.log(
    "Real bulk selection, lost prepare/approval recovery, original bytes, queue receipts and localized results passed.",
  );
} finally {
  await context.close();
  await browser.close();
}
