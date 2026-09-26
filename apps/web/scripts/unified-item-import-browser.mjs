// Real isolated API/database. Only fault injection drops an already committed response.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { openPageActions } from "./page-actions.mjs";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.JOURNEY_BASE_URL;
assert.ok(base && !["5177", "8007", "8080"].includes(new URL(base).port));
const fixture = JSON.parse(process.env.JOURNEY_FIXTURE);
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
page.setDefaultTimeout(15000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenantBase = `/api/tenants/${fixture.tenant}`;
const content = Buffer.from(
  '\ufeffnumber;title;measure;ignored\r\nCSV-A;Schreibtischlampe;pcs;original\r\nCSV-B;"Büroleuchte";;=2+2\r\n',
);
const panel = page.getByRole("dialog", { name: "Import items", exact: true });
try {
  const login = await context.request.post(`${base}/api/auth/login`, {
    data: { email: fixture.email, password: fixture.password },
  });
  assert.equal(login.status(), 200);
  await page.goto(`${base}/app/data-sources?tenant=${fixture.tenant}`);
  await openPageActions(page);
  await page.getByRole("button", { name: "Import items", exact: true }).click();
  await panel
    .getByLabel("CSV file", { exact: true })
    .setInputFiles({ name: "articles.csv", mimeType: "text/csv", buffer: content });
  await panel.getByRole("button", { name: "Upload and check", exact: true }).click();
  await panel.getByLabel("SKU column", { exact: true }).selectOption("number");
  await panel.getByLabel("Name column", { exact: true }).selectOption("title");
  await panel.getByLabel("Unit column", { exact: true }).selectOption("measure");
  await panel.getByLabel("Source code", { exact: true }).fill("catalog_import");
  const preparation = "**/item-imports/prepare";
  await page.route(preparation, async (route) => {
    const response = await route.fetch();
    assert.equal(response.status(), 200);
    await route.abort("failed");
  });
  await panel.getByRole("button", { name: "Review import", exact: true }).click();
  await panel.getByRole("button", { name: "Recover import review", exact: true }).waitFor();
  await page.waitForFunction(() =>
    [...document.querySelectorAll("button")].some(
      (button) => button.textContent === "Recover import review" && !button.disabled,
    ),
  );
  await page.unroute(preparation);
  await page.reload();
  await openPageActions(page);
  await page.getByRole("button", { name: "Import items", exact: true }).click();
  await panel.getByRole("button", { name: "Recover import review", exact: true }).click();
  await panel.getByRole("button", { name: "Confirm import", exact: true }).waitFor();
  const proposal = new URL(page.url()).searchParams.get("import_proposal");
  assert.ok(proposal);
  let data = await (
    await context.request.get(`${base}${tenantBase}/delivery-actions/${proposal}`)
  ).json();
  assert.equal(data.status, "proposed");
  assert.deepEqual(
    data.review.state.creation.rows.map((row) => row.unit),
    ["pcs", "pcs"],
  );
  await page.screenshot({ path: `${out}/review-en.png`, fullPage: true });
  await page.reload();
  await panel.getByRole("button", { name: "Confirm import", exact: true }).waitFor();
  const approval = `**/change-proposals/${proposal}/approve`;
  let writes = 0;
  await page.route(approval, async (route) => {
    writes++;
    const response = await route.fetch();
    assert.equal(response.status(), 200);
    await route.abort("failed");
  });
  await panel.getByRole("button", { name: "Confirm import", exact: true }).click();
  await panel.getByRole("button", { name: "Check import status", exact: true }).waitFor();
  assert.equal(
    await panel.getByRole("button", { name: "Confirm import", exact: true }).isDisabled(),
    true,
  );
  await panel.getByRole("button", { name: "Check import status", exact: true }).click();
  await panel.getByRole("heading", { name: "Items imported", exact: true }).waitFor();
  assert.equal(writes, 1);
  await page.unroute(approval);
  await page.reload();
  await panel.getByRole("heading", { name: "Items imported", exact: true }).waitFor();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    panel.getByRole("link", { name: "Download original CSV", exact: true }).click(),
  ]);
  assert.deepEqual(await readFile(await download.path()), content);
  data = await (
    await context.request.get(`${base}${tenantBase}/delivery-actions/${proposal}`)
  ).json();
  assert.equal(data.verification, "verified");
  const foreign = await context.request.get(
    `${base}/api/tenants/${fixture.foreign}/item-imports/artifacts/${data.receipt.artifact_id}/download`,
  );
  assert.ok([403, 404].includes(foreign.status()));
  const replay = await context.request.post(
    `${base}${tenantBase}/change-proposals/${proposal}/approve`,
    { data: { confirmed: true, review_token: data.review.token } },
  );
  assert.equal(replay.status(), 200);
  await panel.getByRole("button", { name: "CSV-A", exact: true }).click();
  await page.getByRole("dialog").last().waitFor();
  await page.screenshot({ path: `${out}/item-evidence.png`, fullPage: true });
  await page.getByRole("dialog").last().getByRole("button", { name: "Close", exact: true }).click();
  for (const language of ["en", "de", "nl", "es"]) {
    const profile = await context.request.put(`${base}/api/auth/profile`, {
      data: { display_name: "Import member", language, locale: "en-GB", timezone: "UTC" },
    });
    assert.equal(profile.status(), 200);
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.reload();
      await page.locator("table").filter({ hasText: "CSV-A" }).waitFor();
      await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: `${out}/${language}-${width}-recorded.png`, fullPage: true });
    }
  }
  await context.request.put(`${base}/api/auth/profile`, {
    data: { display_name: "Import member", language: "en", locale: "en-GB", timezone: "UTC" },
  });
  await page.goto(`${base}/app/data-sources?tenant=${fixture.tenant}`);
  await openPageActions(page);
  await page.getByRole("button", { name: "Import items", exact: true }).click();
  await panel.getByLabel("CSV file", { exact: true }).setInputFiles({
    name: "cancel.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("sku,name\nCSV-C,Cancelled item\n"),
  });
  await panel.getByRole("button", { name: "Upload and check", exact: true }).click();
  await panel.getByRole("button", { name: "Review import", exact: true }).click();
  await panel.getByRole("button", { name: "Cancel import", exact: true }).click();
  await panel.getByText("Import cancelled. No items were created.", { exact: true }).waitFor();
  await page.screenshot({ path: `${out}/cancelled.png`, fullPage: true });
  assert.deepEqual(errors, []);
  await writeFile(
    `${out}/result.json`,
    JSON.stringify({ proposal, receipt: data.receipt }, null, 2),
  );
  console.log(
    "Real CSV upload, explicit mapping/defaults, lost confirmation recovery, replay, tenant download and localized results passed.",
  );
} catch (error) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  await writeFile(`${out}/error.txt`, await page.locator("body").innerText());
  throw error;
} finally {
  await browser.close();
}
