// Spec 279 T908 / SC-001: a German sweep over real pages of a running stack. Every
// surface that explains a missing basis must read as words; no catalog code, stage or
// tool name may reach the visible text of those surfaces.
//
// Environment: UNIFIED_APP_URL, TENANT (a company with business data, e.g. a demo
// company), INVOICES (comma-separated `number=document_id` pairs whose contribution
// panels to open), ITEM (a stock row to expand), REALITY_PLATFORM_ADMIN_EMAIL / _PASSWORD,
// PLAYWRIGHT_MODULE / PLAYWRIGHT_EXECUTABLE.
import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.UNIFIED_APP_URL || "http://localhost:8180";
const tenant = process.env.TENANT;
const out = "/private/tmp/reality-279-sweep";
await mkdir(out, { recursive: true });
const catalog = JSON.parse(
  await readFile(
    new URL("../../../packages/reality-core/config/resolution_guidance.json", import.meta.url),
    "utf8",
  ),
);
// Codes that must never be visible: catalog keys (multi-word snake case only, so plain
// words such as "category" do not match prose), cost stages and agent tool names.
const codes = [
  ...Object.keys(catalog.reasons),
  ...Object.keys(catalog.steps),
  "uninitialized",
  "cost_change_propose",
  "cost_query_get",
  "cost_evidence_get",
  "authenticated_active_owner",
  "authorized_reader",
].filter((code) => code.includes("_") || code === "uninitialized");
const pattern = new RegExp(`\\b(${codes.join("|")})\\b`, "u");
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_EXECUTABLE });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(45_000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const checked = [];
const open = (path) => page.goto(`${base}${path}${path.includes("?") ? "&" : "?"}lang=de`);
function assertWords(surface, text) {
  const match = text.match(pattern);
  assert.equal(match?.[1], undefined, `${surface} shows the raw code ${match?.[1]}`);
  checked.push(`${surface}: ${text.length} characters, no raw code`);
}

try {
  await page.goto(`${base}/login?lang=de`);
  await page.locator('input[name="email"]').fill(process.env.REALITY_PLATFORM_ADMIN_EMAIL);
  await page.locator('input[name="password"]').fill(process.env.REALITY_PLATFORM_ADMIN_PASSWORD);
  await page.locator("form button").first().click();
  await page.waitForURL(/\/app/);

  // 1. Contribution panels in Finance > Open items, one invoice at a time.
  for (const pair of (process.env.INVOICES || "").split(",").filter(Boolean)) {
    const [number, document] = pair.split("=");
    await open(
      `/app/finance?tenant=${tenant}&finance_view=open-items&finance_status=&q=${number}&entry=${document}`,
    );
    const panel = page.locator("section", { has: page.locator("[data-resolution-guidance]") });
    await panel.first().waitFor();
    const texts = await panel.evaluateAll((nodes) => nodes.map((node) => node.innerText));
    texts.forEach((text, index) => assertWords(`finance ${number} panel ${index + 1}`, text));
    await page.screenshot({ path: `${out}/finance-${number}.png`, fullPage: true });
  }

  // 2. The inventory cost panel of one stock row.
  await open(
    `/app/warehouse?tenant=${tenant}&warehouse_view=stock&item=${process.env.ITEM}&entry=${process.env.ITEM}`,
  );
  const stock = page.getByRole("region", { name: "Kostenerklärung" }).first();
  await stock.waitFor();
  assertWords("warehouse cost panel", await stock.innerText());

  // 3. Exceptions: the list, the stored-result notice and the first finding's detail.
  await open(`/app/attention?tenant=${tenant}`);
  const list = page.locator('[data-work-list="exceptions"]');
  await list.waitFor();
  await page.waitForTimeout(2000);
  assertWords("exceptions list", await list.innerText());
  const firstRow = list
    .locator("[data-work-row], button[aria-controls^='finding-preview-']")
    .first();
  if (await firstRow.count()) {
    await firstRow.click();
    const preview = page.locator("[id^='finding-preview-']").first();
    await preview.waitFor();
    await page.waitForTimeout(2000);
    assertWords("exception detail", await preview.innerText());
    await page.screenshot({ path: `${out}/exception-detail.png`, fullPage: true });
  } else checked.push("exceptions: no current finding to open");

  // 4. Delivery blockers report, table and first row's guidance.
  await open(`/app/inspector?tenant=${tenant}&inspector_view=views`);
  await page.locator("[data-tool-catalog]").waitFor();
  const capability = page.locator('[data-tool-capability="report:fulfillment_blockers"]');
  if (await capability.count()) {
    await capability.locator("button.tool-capability").click();
    await capability.locator("[data-tool-report-open]").click();
    const dialog = page.getByRole("dialog", { name: "Lieferhindernisse" });
    await dialog.locator("[data-report-data]").waitFor();
    await page.waitForTimeout(3000);
    const details = dialog.getByRole("button", { name: "Details anzeigen" }).first();
    if (await details.count()) await details.click();
    // The table and the guidance must read as words. The expanded record's own field
    // list and technical definition stay raw on purpose (the Inspector convention).
    const table = await dialog
      .locator("[data-report-data] tbody tr:not([data-inline-preview])")
      .evaluateAll((rows) => rows.map((row) => row.innerText).join("\n"));
    assertWords("delivery blockers table", table);
    const guidance = dialog.locator("[data-blocker-guidance]").first();
    await guidance.waitFor();
    assertWords("delivery blocker guidance", await guidance.innerText());
    await page.screenshot({ path: `${out}/delivery-blockers.png`, fullPage: true });
  } else checked.push("delivery blockers: report not offered in this company");

  assert.deepEqual(errors, []);
  console.log(checked.join("\n"));
  console.log("PASS: German missing-basis sweep found no raw codes.");
} catch (error) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  console.log(checked.join("\n"));
  throw error;
} finally {
  await browser.close();
}
