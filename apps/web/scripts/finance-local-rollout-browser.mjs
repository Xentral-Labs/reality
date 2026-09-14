// Explicit local rollout acceptance. Uses the existing owner's temporary test session.
import assert from "node:assert/strict";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const access = JSON.parse(await readFile(process.env.FINANCE_BROWSER_ACCESS, "utf8"));
const base = process.env.REALITY_BROWSER_URL || "http://127.0.0.1:8080";
assert.equal(new URL(base).hostname, "127.0.0.1", "This script is local-only");
const output = process.env.FINANCE_SCREENSHOTS || "/private/tmp/reality-finance-rollout";
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
await context.addCookies([
  { name: access.cookie_name, value: access.cookie, url: base, httpOnly: true, sameSite: "Lax" },
]);
const page = await context.newPage();
page.setDefaultTimeout(20000);
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const api = `${base}/api/tenants/${access.tenant_id}`;
async function accounts() {
  const response = await context.request.get(`${api}/finance/accounts`);
  assert.equal(response.status(), 200);
  return response.json();
}
try {
  const before = await accounts();
  await page.goto(`${base}/app/finance?tenant=${access.tenant_id}&finance_view=settings`);
  const panel = page.locator("details").filter({
    has: page.locator("summary").filter({ hasText: /Operational accounts|Operative Konten/ }),
  });
  await panel.locator("summary").click();
  await panel.locator('input[name="code"]').fill("BANK-LOCAL");
  await panel.locator('input[name="name"]').fill("Local test bank");
  await panel.locator('select[name="role"]').selectOption("cash");
  await panel.getByRole("button", { name: /^(Create account|Konto anlegen)$/ }).click();
  await panel
    .getByRole("heading", { name: /Confirm account change|Kontenänderung bestätigen/ })
    .waitFor();
  assert.equal(
    (await accounts()).accounts.length,
    before.accounts.length,
    "Proposal must not mutate account configuration",
  );
  await panel.getByRole("button", { name: /^(Confirm|Bestätigen)$/ }).click();
  await panel.getByRole("cell", { name: "BANK-LOCAL", exact: true }).waitFor();
  assert.equal((await accounts()).accounts.length, before.accounts.length + 1);
  await page.screenshot({ path: `${output}/accounts-desktop.png`, fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: `${output}/accounts-mobile.png`, fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/app/finance?tenant=${access.tenant_id}&finance_view=journal`);
  await page.getByRole("table").waitFor();
  const journalResponse = await context.request.get(`${api}/finance/journal`);
  assert.equal(journalResponse.status(), 200);
  const journal = await journalResponse.json();
  assert.ok(journal.items.length > 0);
  assert.ok(journal.items.every((e) => e.account_id && e.account_code && e.account_name));
  await page.screenshot({ path: `${output}/journal-desktop.png`, fullPage: true });
  for (const flow of ["receivable", "payable"]) {
    const response = await context.request.get(`${api}/finance/open-items?flow=${flow}`);
    assert.equal(response.status(), 200);
    const result = await response.json();
    assert.ok(
      result.items.some((e) => Number(e.open) === 38),
      `${flow}: source-backed open amount 38`,
    );
  }
  assert.deepEqual(errors, []);
  await writeFile(
    `${output}/result.json`,
    JSON.stringify(
      {
        account_count: (await accounts()).accounts.length,
        journal_entries: journal.page.total,
        receivable: "38",
        payable: "38",
        browser_errors: errors,
      },
      null,
      2,
    ),
  );
  console.log(
    "PASS live localhost account proposal/confirmation, desktop/mobile settings, journal identities and customer/supplier balances.",
  );
} catch (error) {
  await page.screenshot({ path: `${output}/error.png`, fullPage: true });
  await writeFile(`${output}/error-state.txt`, await page.locator("body").innerText());
  throw error;
} finally {
  await browser.close();
}
