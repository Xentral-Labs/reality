// Real API, authentication and projections; no network responses are mocked.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { writeFile } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const fixture = JSON.parse(process.env.JOURNEY_FIXTURE);
const base = process.env.JOURNEY_BASE_URL;
const prefix = `${base}/api/tenants/${fixture.tenant}`;
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();
page.setDefaultTimeout(20000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
async function openItems(predicate) {
  const deadline = Date.now() + 90000;
  while (Date.now() < deadline) {
    const response = await context.request.get(
      `${prefix}/finance/open-items?flow=receivable&status=outstanding`,
    );
    assert.equal(response.status(), 200);
    const data = await response.json();
    if (data.metadata?.state === "ready" && predicate(data)) return data;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("Open items did not reach the required projected state");
}
try {
  assert.equal(
    (
      await context.request.post(`${base}/api/auth/login`, {
        data: { email: fixture.email, password: fixture.password },
      })
    ).status(),
    200,
  );
  await openItems((data) => data.items.length === 0);
  await page.goto(`${base}/app/finance?tenant=${fixture.tenant}`);
  await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "Record customer payment", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByText("No matching open invoices", { exact: true }).waitFor();
  const accepted = await context.request.post(
    `${prefix}/change-proposals/${fixture.proposal}/approve`,
    { data: { confirmed: true, review_token: fixture.digest } },
  );
  assert.equal(accepted.status(), 200, await accepted.text());
  const projected = await openItems((data) => data.items.length === 1);
  const invoice = projected.items[0];
  // The dialog remains mounted while an independent client accepts the invoice.
  assert.equal(
    await dialog
      .getByLabel("Invoice", { exact: true })
      .locator(`option[value="${invoice.document_id}"]`)
      .count(),
    0,
  );
  await dialog.getByRole("button", { name: "Refresh", exact: true }).click();
  await dialog
    .getByLabel("Invoice", { exact: true })
    .locator(`option[value="${invoice.document_id}"]`)
    .waitFor({ state: "attached" });
  await dialog.getByLabel("Invoice", { exact: true }).selectOption(invoice.document_id);
  await dialog.getByLabel("Payment amount", { exact: true }).fill("5");
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
  const settled = await openItems(
    (data) => data.items.length === 1 && Number(data.items[0].settled) === 5,
  );
  assert.equal(Number(settled.items[0].open), Number(invoice.open) - 5);
  assert.deepEqual(errors, []);
  await writeFile(
    `${process.env.JOURNEY_ARTIFACTS}/result.json`,
    JSON.stringify(
      {
        outcome: "PASS",
        invoice: invoice.document_id,
        open_before: invoice.open,
        open_after: settled.items[0].open,
        payment: "5",
        reopened_dialog: false,
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
}
