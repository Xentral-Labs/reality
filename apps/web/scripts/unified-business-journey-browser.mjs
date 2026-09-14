// Real API and disposable PostgreSQL only; never synthesize business responses.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir, writeFile } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const fixture = JSON.parse(process.env.JOURNEY_FIXTURE);
const base = process.env.JOURNEY_BASE_URL;
const out = process.env.JOURNEY_ARTIFACTS;
assert.ok(
  base && !/:(5177|8007)(\/|$)/.test(base),
  "Use the isolated runner, never shared development services",
);
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
const page = await context.newPage();
page.setDefaultTimeout(15000);
const errors = [],
  proposals = [];
page.on("pageerror", (error) => errors.push(error.message));
const api = `/api/tenants/${fixture.tenant}`;
const get = async (path) => {
  const response = await context.request.get(`${base}${api}${path}`);
  assert.equal(response.status(), 200, `${path}: ${await response.text()}`);
  return response.json();
};
const goto = async (path, query = "") => {
  await page.goto(`${base}/app/${path}?tenant=${fixture.tenant}${query ? "&" + query : ""}`);
  await page.getByRole("heading", { level: 1 }).first().waitFor();
  await page.waitForLoadState("networkidle");
};
const button = (name) => page.getByRole("button", { name, exact: true });
const rowAction = async (row, name) => {
  const trigger = row.locator('[data-action-meaning="preview"]').first();
  const id = await trigger.getAttribute("aria-controls");
  if ((await trigger.getAttribute("aria-expanded")) !== "true") await trigger.click();
  await page
    .locator(`[id="${id}"]`)
    .getByRole("button", { name: name === "Explain" ? "Open full explanation" : name, exact: true })
    .click();
};
const field = (name) =>
  page.getByLabel(name, { exact: true }).and(page.locator("input, select, textarea"));
const choose = async (name, value) => {
  await field(name).locator(`option[value="${value}"]`).waitFor({ state: "attached" });
  await field(name).selectOption(value);
};
const record = (proposal, family) =>
  proposal.receipt.records.find((row) => row.family === family).id;
const counts = async () => {
  const docs = await get("/evidence-documents?size=100"),
    movements = await get("/movements"),
    journal = await get("/finance/journal?size=100");
  return [docs.page.total, movements.length, journal.page.total];
};
const settle = async (label) => {
  const before = await counts();
  const prepared = page.waitForResponse(
    (response) =>
      response.url().endsWith("/delivery-actions/prepare") &&
      response.request().method() === "POST",
  );
  await button("Review change").click();
  const response = await prepared;
  assert.equal(response.status(), 200, await response.text());
  const proposal = await response.json();
  const confirmLabel = label === "08-refund-reversal" ? "Confirm reversal" : "Confirm change";
  await button(confirmLabel).waitFor();
  if (label === "08-refund-reversal")
    assert.equal(
      await page.getByRole("dialog").getByText("Open amount", { exact: true }).count(),
      2,
      "Credit/refund balances must not be labeled invoice amounts",
    );
  assert.deepEqual(await counts(), before, `${label}: preparation changed business records`);
  await page.screenshot({ path: `${out}/${label}-review.png` });
  const confirmed = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/change-proposals/${proposal.id}/approve`) &&
      response.request().method() === "POST",
  );
  await button(confirmLabel).click();
  const execution = await confirmed;
  assert.equal(execution.status(), 200, await execution.text());
  const result = await get(`/delivery-actions/${proposal.id}`);
  assert.equal(result.verification, "verified", JSON.stringify(result));
  proposals.push(result);
  await page.reload();
  await page.getByRole("dialog").getByText("Recorded", { exact: true }).waitFor();
  assert.equal((await get(`/delivery-actions/${proposal.id}`)).verification, "verified");
  await page.screenshot({ path: `${out}/${label}-recorded.png` });
  await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
  console.log(`PASS ${label}: reviewed, confirmed and reloaded real evidence`);
  return result;
};
const openAction = async (name) => {
  await page.getByRole("banner").getByText("Actions", { exact: true }).click();
  await button(name).first().click();
};
try {
  await mkdir(out, { recursive: true });
  const login = await context.request.post(`${base}/api/auth/login`, {
    data: { email: fixture.email, password: fixture.password },
  });
  assert.equal(login.status(), 200, await login.text());
  await goto("orders-deliveries", "orders_view=customer-orders");
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await button("New order").click();
  await choose("Company party", fixture.company);
  await choose("Customer", fixture.customer);
  await choose("Warehouse", fixture.warehouse);
  await field("Order number").fill("SO-127");
  await field("Stated order total").fill("1000");
  await choose("Item", fixture.item);
  await field("Quantity").fill("10");
  await field("Unit price").fill("100");
  await field("Stated line amount").fill("1000");
  const order = await settle("01-order");
  const orderId = order.receipt.document_id,
    orderLine = order.receipt.document_line_ids[0],
    commitment = order.receipt.commitment_ids[0];
  await openAction("Reserve stock");
  await choose("Delivery", commitment);
  await field("Quantity").fill("10");
  await settle("02-reservation");
  let delivery = await get(`/delivery-work/${commitment}`);
  assert.equal(Number(delivery.case.reserved), 10);
  await openAction("Record shipment");
  await choose("Delivery", commitment);
  await field("Quantity").fill("6");
  await settle("03-shipment");
  delivery = await get(`/delivery-work/${commitment}`);
  assert.equal(Number(delivery.case.open), 4);
  assert.equal(Number(delivery.case.reserved), 4);
  assert.equal(Number(delivery.inventory.physical), 14);
  await goto("finance");
  await openAction("New customer invoice");
  await choose("Order", orderId);
  await choose("Order line", orderLine);
  await field("Invoice number").fill("INV-127");
  await field("Quantity").fill("4");
  await field("Stated line amount").fill("400");
  await field("Stated invoice amount").fill("400");
  const invoiceResult = await settle("04-invoice");
  const invoice = record(invoiceResult, "document"),
    invoiceLine = record(invoiceResult, "document_line");
  await openAction("Record customer payment");
  await choose("Invoice", invoice);
  await field("Payment amount").fill("400");
  await field("Payment reference").fill("PAY-127");
  await settle("05-payment");
  const invoiceRows = await get("/finance/open-items?flow=receivable");
  assert.equal(Number(invoiceRows.items.find((row) => row.document_id === invoice).open), 0);
  await goto("finance", "finance_status=");
  await rowAction(page.locator("tr").filter({ hasText: "INV-127" }), "New credit note");
  assert.equal(await field("Invoice").inputValue(), invoice);
  await choose("Invoice position", invoiceLine);
  await field("Quantity").fill("2");
  await field("Stated line amount").fill("200");
  await field("Credit note number").fill("CR-127");
  await field("Stated credit amount").fill("200");
  await field("Credit reason").fill("Agreed partial credit");
  await field("Amount to offset against this invoice").fill("0");
  const creditResult = await settle("06-credit");
  const credit = record(creditResult, "document"),
    creditLine = record(creditResult, "document_line");
  await goto("finance", "flow=customer-credit");
  await rowAction(page.locator("tr").filter({ hasText: "CR-127" }), "Record refund");
  assert.equal(await field("Credit note").inputValue(), credit);
  await field("Refund amount").fill("75");
  await field("Refund reference").fill("REF-127");
  const refund = await settle("07-refund");
  assert.equal(Number(refund.observation.open), 125);
  const choices = await get("/finance/reversal-choices?q=REF-127");
  assert.equal(choices.items.length, 1);
  await openAction("Reverse posting");
  await choose("Posting", choices.items[0].id);
  await field("Reversal reason").fill("Refund recorded incorrectly");
  await settle("08-refund-reversal");
  const finalCredit = await get("/finance/open-items?flow=customer-credit");
  assert.equal(Number(finalCredit.items.find((row) => row.document_id === credit).open), 200);
  const historical = await get(`/delivery-actions/${refund.id}`);
  assert.equal(historical.verification, "verified");
  assert.equal(historical.observation.allocation_active, false);
  delivery = await get(`/delivery-work/${commitment}`);
  assert.equal(Number(delivery.case.open), 4);
  assert.equal(Number(delivery.inventory.physical), 14);
  // Open actual credit evidence and follow its invoice position link in the Inspector.
  await rowAction(page.locator("tr").filter({ hasText: "CR-127" }), "Explain");
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Referenced positions", exact: true })
    .waitFor();
  await page.screenshot({ path: `${out}/09-credit-evidence.png` });
  await writeFile(
    `${out}/result.json`,
    JSON.stringify(
      { proposals, invoice, invoiceLine, credit, creditLine, orderLine, commitment },
      null,
      2,
    ),
  );
  // Spec 148: credit remains discoverable without an outstanding invoice.
  for (const [side, reference, amount] of [
    ["customer", "CUSTOMER-AVAILABLE", 30],
    ["supplier", "SUPPLIER-AVAILABLE", 50],
  ]) {
    await goto("finance", `flow=${side}-balance`);
    const row = page.locator("tr").filter({ hasText: reference });
    await row.waitFor();
    await page.getByRole("columnheader", { name: /^Available credit/ }).waitFor();
    const credits = await get(`/finance/open-items?flow=${side}-balance&item_status=outstanding`);
    assert.equal(Number(credits.items.find((item) => item.number === reference).open), amount);
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1050 });
      await page.screenshot({ path: `${out}/${side}-credit-${width}.png` });
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
        true,
      );
    }
  }
  const reductions = [];
  for (const side of ["customer", "supplier"]) {
    await page.setViewportSize({ width: 1440, height: 1050 });
    await goto("finance", `flow=${side === "customer" ? "receivable" : "payable"}`);
    const invoiceRow = page.locator("tr").filter({ hasText: `${side.toUpperCase()}-REDUCTION` });
    await rowAction(invoiceRow, "Accept settlement reduction");
    await field("Stated reduction amount").fill("20");
    await field("Explanation").fill("Agreed stated discount");
    if (side === "supplier")
      await field("Supplier entitlement or agreement").fill(
        "Supplier terms grant the stated discount",
      );
    const before = await counts();
    const prepared = page.waitForResponse(
      (response) =>
        response.url().endsWith("/finance/adjustments/proposals") &&
        response.request().method() === "POST",
    );
    await button("Review reduction").click();
    const response = await prepared;
    assert.equal(response.status(), 200, await response.text());
    const proposal = await response.json();
    assert.equal(proposal.preview.adjustment.cash_change, "0");
    assert.equal(Number(proposal.preview.adjustment.remaining), 0);
    assert.deepEqual(await counts(), before);
    await button("Confirm reduction").waitFor();
    await page.screenshot({ path: `${out}/${side}-reduction-review.png` });
    for (const theme of ["light", "dark"]) {
      await page.setViewportSize({ width: 390, height: 950 });
      await page.evaluate((theme) => {
        document.documentElement.dataset.theme = theme;
        document.documentElement.classList.toggle("dark", theme === "dark");
      }, theme);
      await page.screenshot({ path: `${out}/${side}-reduction-${theme}-390.png` });
      assert.equal(
        await page.getByRole("dialog").evaluate((node) => node.scrollWidth <= node.clientWidth),
        true,
      );
    }
    await page.setViewportSize({ width: 1440, height: 1050 });

    await page.reload();
    await rowAction(invoiceRow, "Accept settlement reduction");
    await button("Confirm reduction").waitFor();
    const confirmed = page.waitForResponse((response) =>
      response.url().endsWith(`/change-proposals/${proposal.id}/approve`),
    );
    await button("Confirm reduction").click();
    const approval = await confirmed;
    assert.equal(approval.status(), 200, await approval.text());
    reductions.push((await approval.json()).output);
    const openItems = await get(
      `/finance/open-items?flow=${side === "customer" ? "receivable" : "payable"}`,
    );
    assert.equal(
      Number(openItems.items.find((row) => row.number === `${side.toUpperCase()}-REDUCTION`).open),
      0,
    );
  }
  await writeFile(`${out}/reductions.json`, JSON.stringify(reductions, null, 2));

  const settlements = [];
  async function confirmSettlement({ reloadRow } = {}) {
    const before = await counts();
    const preparing = page.waitForResponse(
      (response) =>
        response.url().endsWith("/finance/settlements/proposals") &&
        response.request().method() === "POST",
    );
    await button("Review settlement").click();
    const response = await preparing;
    assert.equal(response.status(), 200, await response.text());
    const proposal = await response.json();
    assert.deepEqual(await counts(), before);
    await button("Confirm settlement").waitFor();
    if (reloadRow) {
      for (const theme of ["light", "dark"]) {
        await page.setViewportSize({ width: 390, height: 950 });
        await page.evaluate((theme) => {
          document.documentElement.dataset.theme = theme;
          document.documentElement.classList.toggle("dark", theme === "dark");
        }, theme);
        await page.screenshot({ path: `${out}/${reloadRow}-settlement-${theme}-390.png` });
        assert.equal(
          await page.getByRole("dialog").evaluate((node) => node.scrollWidth <= node.clientWidth),
          true,
        );
      }
      await page.setViewportSize({ width: 1440, height: 1050 });
      await page.reload();
      await rowAction(
        page.locator("tr").filter({ hasText: reloadRow }),
        "Record payment and allocation",
      );
      await button("Confirm settlement").waitFor();
    }
    const confirming = page.waitForResponse((response) =>
      response.url().endsWith(`/change-proposals/${proposal.id}/approve`),
    );
    await button("Confirm settlement").click();
    const approval = await confirming;
    assert.equal(approval.status(), 200, await approval.text());
    const receipt = (await approval.json()).output;
    settlements.push(receipt);
    await page.getByRole("status").filter({ hasText: "Settlement recorded" }).waitFor();
    await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
    return receipt;
  }
  for (const side of ["customer", "supplier"]) {
    for (const suffix of ["COMBINED", "EXCESS"]) {
      await goto("finance", `flow=${side === "customer" ? "receivable" : "payable"}`);
      const reference = `${side.toUpperCase()}-${suffix}`;
      await rowAction(
        page.locator("tr").filter({ hasText: reference }),
        "Record payment and allocation",
      );
      await field("Actual cash amount").fill(suffix === "COMBINED" ? "98" : "102");
      await field("Amount allocated to this invoice").fill(suffix === "COMBINED" ? "98" : "100");
      await field("Actual payment reference").fill(`${reference}-PAYMENT`);
      await field("Actual payment time (with timezone)").fill("2026-09-10T08:00:00Z");
      if (suffix === "COMBINED") {
        await page.getByRole("checkbox", { name: "Also accept a stated reduction" }).check();
        await field("Stated reduction amount").fill("2");
        await field("Explanation").fill("Explicit stated discount of two");
        if (side === "supplier")
          await field("Supplier entitlement or agreement").fill(
            "Supplier accepted the stated discount",
          );
      }
      const receipt = await confirmSettlement({
        reloadRow: suffix === "COMBINED" ? reference : undefined,
      });
      assert.equal(Number(receipt.remaining_claim), 0);
      assert.equal(Number(receipt.remaining_credit), suffix === "COMBINED" ? 0 : 2);
    }
    const reference = `${side.toUpperCase()}-EXCESS-PAYMENT`;
    await goto("finance", `flow=${side}-balance`);
    await rowAction(page.locator("tr").filter({ hasText: reference }), "Use available credit");
    await field("Find matching invoice").fill(`${side.toUpperCase()}-TARGET`);
    const target = page
      .getByRole("dialog")
      .locator('select[name="invoice"] option')
      .filter({ hasText: `${side.toUpperCase()}-TARGET` });
    await target.waitFor({ state: "attached" });
    await field("Invoice").selectOption(await target.getAttribute("value"));
    await field("Allocated amount").fill("1");
    const allocation = await confirmSettlement();
    assert.equal(Number(allocation.cash_amount), 0);
    assert.equal(Number(allocation.remaining_claim), 9);
    await goto("finance", `flow=${side}-balance`);
    await rowAction(page.locator("tr").filter({ hasText: reference }), "Use available credit");
    await field("Credit action").selectOption("refund_credit");
    await field("Actual cash amount").fill("1");
    await field("Actual payment reference").fill(`${side}-REFUND`);
    await field("Actual payment time (with timezone)").fill("2026-09-10T09:00:00Z");
    const refund = await confirmSettlement();
    assert.equal(Number(refund.remaining_credit), 0);
    assert.equal(refund.cash_direction, side === "customer" ? "outgoing" : "incoming");
  }
  await goto("finance");
  await page.getByText("More actions", { exact: true }).click();
  await button("Import opening positions").click();
  await field("Previous system").fill("legacy-browser");
  await field("Snapshot reference").fill("opening-2026");
  await field("Cutover date").fill("2026-01-01");
  await field("Explanation").fill("Owner-stated residuals from the previous system");
  for (let index = 0; index < 4; index++) {
    if (index === 2) {
      const searched = page.waitForResponse((response) =>
        response.url().includes("/finance/opening/context?query=Opening%20supplier"),
      );
      await field("Find party").fill("Opening supplier");
      assert.equal((await searched).status(), 200);
    }
    if (index) await button("Add opening position").click();
    const row = page.getByRole("dialog").locator("fieldset").nth(index);
    const direction = ["customer_debt", "customer_credit", "supplier_debt", "supplier_credit"][
      index
    ];
    await row
      .locator(`select[name="${index}:party"]`)
      .selectOption(index < 2 ? fixture.opening_customer : fixture.opening_supplier);
    await row.locator(`select[name="${index}:direction"]`).selectOption(direction);
    await row.locator(`input[name="${index}:amount"]`).fill(["1000", "100", "800", "50"][index]);
    await row.locator(`input[name="${index}:key"]`).fill(direction);
    await row.locator(`input[name="${index}:reference"]`).fill(`OPENING-${direction}`);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  const openingDialog = page.getByRole("dialog");
  assert.ok(await openingDialog.evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
  await page.screenshot({ path: `${out}/opening-mobile.png` });
  await page.setViewportSize({ width: 1440, height: 1050 });
  const openingBefore = await counts();
  const openingPrepared = page.waitForResponse(
    (r) => r.url().endsWith("/finance/opening/proposals") && r.request().method() === "POST",
  );
  await button("Review opening positions").click();
  const openingResponse = await openingPrepared;
  assert.equal(openingResponse.status(), 200, await openingResponse.text());
  const openingProposal = await openingResponse.json();
  assert.deepEqual(await counts(), openingBefore);
  await page.reload();
  await page.getByText("More actions", { exact: true }).click();
  await button("Import opening positions").click();
  await button("Confirm opening positions").waitFor();
  await page.screenshot({ path: `${out}/opening-review.png` });
  const openingConfirmed = page.waitForResponse(
    (r) =>
      r.url().endsWith(`/change-proposals/${openingProposal.id}/approve`) &&
      r.request().method() === "POST",
  );
  await button("Confirm opening positions").click();
  const openingExecution = await openingConfirmed;
  assert.equal(openingExecution.status(), 200, await openingExecution.text());
  const openingReceipt = (await openingExecution.json()).output;
  await page.getByRole("status").filter({ hasText: "Opening positions recorded" }).waitFor();
  await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
  await writeFile(`${out}/opening.json`, JSON.stringify(openingReceipt, null, 2));
  await goto("finance", "flow=receivable");
  await rowAction(
    page.locator("tr").filter({ hasText: "OPENING-customer_debt" }),
    "Record payment and allocation",
  );
  await field("Actual cash amount").fill("400");
  await field("Amount allocated to this invoice").fill("400");
  await field("Actual payment reference").fill("OPENING-PAID");
  await field("Actual payment time (with timezone)").fill("2026-02-01T12:00:00Z");
  const openingPayment = await confirmSettlement();
  assert.equal(Number(openingPayment.remaining_claim), 600);
  console.log(
    "PASS opening positions: four directions, no-effect preview, reload, explicit confirmation and actual payment",
  );
  await goto("settings", "settings_view=company");
  assert.equal(await page.getByText("Operational accounts", { exact: true }).count(), 0);
  assert.equal(await page.getByText("Finance references", { exact: true }).count(), 0);
  const settingsRegisterReads = [];
  const captureSettingsRead = (request) => {
    if (/\/finance\/(open-items|payments|journal)(\?|$)/.test(request.url()))
      settingsRegisterReads.push(request.url());
  };
  page.on("request", captureSettingsRead);
  await goto("finance", "finance_view=settings");
  await page.getByRole("region", { name: "Finance settings", exact: true }).waitFor();
  assert.equal(await page.getByLabel("Search finance", { exact: true }).count(), 0);
  assert.deepEqual(settingsRegisterReads, []);
  await page.reload();
  await page.getByRole("region", { name: "Finance settings", exact: true }).waitFor();
  assert.equal(new URL(page.url()).searchParams.get("finance_view"), "settings");
  assert.deepEqual(settingsRegisterReads, []);
  page.off("request", captureSettingsRead);
  console.log(
    "PASS Finance settings: canonical workspace, reload, no register reads or duplicate Company editors",
  );
  const selectFinanceArea = async (name) => {
    await page
      .getByRole("navigation", { name: "Finance settings areas", exact: true })
      .getByRole("button", { name, exact: true })
      .click();
  };
  const references = page.getByRole("region", {
    name: /^(Cost centers|Case codes & coding groups)$/,
  });
  const accountSettings = page.getByRole("region", {
    name: "Accounts & account mapping",
    exact: true,
  });
  const openUsage = () =>
    accountSettings.getByRole("button", { name: "View account usage", exact: true }).click();
  const matrix = page.getByRole("dialog", {
    name: "Accounts for business transactions",
    exact: true,
  });
  await openUsage();
  await matrix.getByRole("article", { name: "Sales invoice", exact: true }).waitFor();
  assert.equal(await matrix.getByRole("article").count(), 14);
  assert.equal(await matrix.getByRole("alert").count(), 0);
  const matrixBefore = await get("/finance/matrix");
  assert.equal(matrixBefore.operations.length, 14);
  const matrixCounts = await counts();
  await matrix.getByRole("button", { name: "Back to accounts", exact: true }).click();
  const cashRow = accountSettings
    .locator("tr")
    .filter({ has: page.getByRole("cell", { name: "cash", exact: true }) });
  for (const label of ["Block account", "Activate account"]) {
    await cashRow.getByRole("button", { name: "More actions", exact: true }).click();
    await cashRow.getByRole("button", { name: label, exact: true }).click();
    await accountSettings
      .getByRole("region", { name: "Confirm account change", exact: true })
      .getByRole("button", { name: "Confirm", exact: true })
      .click();
    await openUsage();
    const paymentCard = matrix.getByRole("article", { name: "Customer payment", exact: true });
    await paymentCard
      .locator("dd")
      .filter({ hasText: /Blocked/ })
      .waitFor({ state: label === "Block account" ? "visible" : "hidden" });
    await matrix.getByRole("button", { name: "Back to accounts", exact: true }).click();
  }

  await openUsage();
  await matrix.getByRole("button", { name: "Refresh", exact: true }).click();
  assert.deepEqual(await counts(), matrixCounts);
  await matrix
    .getByRole("article", { name: "Customer payment", exact: true })
    .getByText("Original control account when linked", { exact: true })
    .waitFor();
  await page.screenshot({ path: `${out}/transaction-matrix.png` });
  if (
    (await page.getByRole("dialog").count()) === 0 &&
    (await page.getByRole("button", { name: "Hide chat", exact: true }).isVisible())
  ) {
    await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await matrix
    .getByRole("article", { name: "Supplier invoice", exact: true })
    .scrollIntoViewIfNeeded();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await page.screenshot({ path: `${out}/transaction-matrix-mobile.png` });
  await page.setViewportSize({ width: 1440, height: 1050 });
  await matrix.getByRole("button", { name: "Back to accounts", exact: true }).click();
  console.log(
    "PASS transaction matrix: fourteen operations, explicit default/control semantics, no read effect, account configuration and mobile",
  );
  await accountSettings.getByRole("button", { name: "Add account", exact: true }).click();
  let accountDialog = page.getByRole("dialog", { name: "Create account", exact: true });
  await accountDialog.getByLabel("Code", { exact: true }).fill("CONFIG-BANK");
  await accountDialog.getByLabel("Name", { exact: true }).fill("Configuration bank");
  await accountDialog.getByLabel("Role", { exact: true }).selectOption("cash");
  await accountDialog.getByRole("button", { name: "Review account change", exact: true }).click();
  await page
    .getByRole("dialog", { name: "Confirm account change", exact: true })
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await accountSettings.getByRole("dialog").waitFor({ state: "detached" });
  const configuredBank = (await get("/finance/accounts")).accounts.find(
    (a) => a.code === "CONFIG-BANK",
  );
  await openUsage();
  await matrix
    .getByRole("article", { name: "Customer payment", exact: true })
    .getByRole("button", { name: "Change default", exact: true })
    .first()
    .click();
  const defaultDialog = page.getByRole("dialog", { name: "Change default account", exact: true });
  await defaultDialog.getByLabel("Account", { exact: true }).selectOption(configuredBank.id);
  await defaultDialog.getByRole("button", { name: "Review account change", exact: true }).click();
  await page
    .getByRole("dialog", { name: "Confirm account change", exact: true })
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await accountSettings.getByRole("dialog").waitFor({ state: "detached" });
  assert.equal((await get("/finance/accounts")).defaults.cash, configuredBank.id);
  assert.deepEqual(await counts(), matrixCounts);
  console.log("PASS role default change from account usage with no historical financial effects");
  const referenceResults = [];
  for (const kind of ["cost_center", "case_code", "coding_group"]) {
    await selectFinanceArea(kind === "cost_center" ? "Cost centers" : "Case codes & coding groups");
    if (kind !== "cost_center")
      await references.getByLabel("Reference type", { exact: true }).selectOption(kind);
    await references
      .getByRole("button", {
        name:
          kind === "cost_center"
            ? "Create cost center"
            : kind === "case_code"
              ? "Create case code"
              : "Create coding group",
        exact: true,
      })
      .click();
    await references.getByLabel("Code", { exact: true }).fill("OPERATIONS");
    await references.getByLabel("Name", { exact: true }).fill(`Operations ${kind}`);
    await references.getByLabel("Reason", { exact: true }).fill("Explicit classification policy");
    const prior = await get("/finance/references");
    const preparedResponse = page.waitForResponse(
      (r) => r.url().endsWith("/finance/references/proposals") && r.request().method() === "POST",
    );
    await references
      .getByRole("button", { name: /^Review (reference change|cost center)$/, exact: true })
      .click();
    let prepared = await preparedResponse;
    if (prepared.status() === 409) {
      const refreshedReferences = page.waitForResponse(
        (r) => r.url().includes("/finance/references?") && r.request().method() === "GET",
      );
      await references.getByRole("button", { name: "Retry", exact: true }).click();
      await (await refreshedReferences).finished();
      await references
        .getByRole("status")
        .filter({ hasText: "Loading" })
        .waitFor({ state: "hidden" });
      await references
        .getByRole("button", {
          name:
            kind === "cost_center"
              ? "Create cost center"
              : kind === "case_code"
                ? "Create case code"
                : "Create coding group",
          exact: true,
        })
        .click();
      await references.getByLabel("Code", { exact: true }).fill("OPERATIONS");
      await references.getByLabel("Name", { exact: true }).fill(`Operations ${kind}`);
      await references.getByLabel("Reason", { exact: true }).fill("Explicit classification policy");
      const retried = page.waitForResponse(
        (r) => r.url().endsWith("/finance/references/proposals") && r.request().method() === "POST",
      );
      await references
        .getByRole("button", { name: /^Review (reference change|cost center)$/, exact: true })
        .click();
      prepared = await retried;
    }
    assert.equal(prepared.status(), 200, await prepared.text());
    assert.equal((await get("/finance/references")).total, prior.total);
    const preparedBody = await prepared.json();
    if (kind === "cost_center") {
      await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
      await selectFinanceArea("Case codes & coding groups");
      assert.equal(
        await page.getByRole("region", { name: "Confirm reference change", exact: true }).count(),
        0,
      );
      await selectFinanceArea("Cost centers");
      await references
        .getByRole("region", { name: "Confirm reference change", exact: true })
        .waitFor();
      await page.reload();
      await references
        .getByRole("region", { name: "Confirm reference change", exact: true })
        .waitFor();
      await page.screenshot({ path: `${out}/reference-review.png` });
    }
    const acceptedResponse = page.waitForResponse(
      (r) =>
        r.url().endsWith(`/change-proposals/${preparedBody.id}/approve`) &&
        r.request().method() === "POST",
    );
    await references.getByRole("button", { name: "Confirm", exact: true }).click();
    const accepted = await acceptedResponse;
    assert.equal(accepted.status(), 200, await accepted.text());
    referenceResults.push((await accepted.json()).output);
    await references.getByRole("status").filter({ hasText: "Reference saved" }).waitFor();
  }
  await selectFinanceArea("Cost centers");
  const referenceRow = references.locator("tr").filter({ hasText: "Operations cost_center" });
  await referenceRow.getByRole("button", { name: "Edit", exact: true }).click();
  await references.getByLabel("Name", { exact: true }).fill("Former warehouse");
  await references.getByLabel("Reference status", { exact: true }).selectOption("blocked");
  await references.getByLabel("Reason", { exact: true }).fill("Warehouse closed");
  await references
    .getByRole("button", { name: /^Review (reference change|cost center)$/, exact: true })
    .click();
  await references.getByRole("button", { name: "Confirm", exact: true }).click();
  const renamedRow = references.locator("tr").filter({ hasText: "Former warehouse" });
  await renamedRow.getByRole("button", { name: "History", exact: true }).click();
  await references
    .getByRole("region", { name: "Reference history", exact: true })
    .getByText("Reason: Warehouse closed", { exact: true })
    .waitFor();
  const referenceHistory = await get(`/finance/references/${referenceResults[0].id}/history`);
  assert.equal(referenceHistory.total, 2);
  assert.equal(referenceHistory.items[0].before.name, "Operations cost_center");
  assert.equal(referenceHistory.items[0].after.state, "blocked");
  assert.ok(referenceHistory.items[0].actor_id);
  await references.getByLabel("Search references", { exact: true }).fill("Former warehouse");
  await renamedRow.waitFor();
  await references
    .getByRole("region", { name: "Reference history", exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${out}/reference-history.png` });
  if (
    (await page.getByRole("dialog").count()) === 0 &&
    (await page.getByRole("button", { name: "Hide chat", exact: true }).isVisible())
  ) {
    await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => {
      document.documentElement.dataset.theme = value;
      document.documentElement.classList.toggle("dark", value === "dark");
    }, theme);
    await references.getByLabel("Search references", { exact: true }).scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${out}/references-mobile-${theme}.png` });
    assert.equal(
      await references.getByLabel("Search references", { exact: true }).isVisible(),
      true,
    );
  }
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    true,
  );
  await writeFile(
    `${out}/references.json`,
    JSON.stringify({ references: referenceResults, history: referenceHistory }, null, 2),
  );
  console.log(
    "PASS finance reference settings: three kinds, no-effect review, reload, owner confirmation, blocking, historical snapshots and mobile",
  );
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page
    .getByRole("dialog", { name: "Reference history", exact: true })
    .getByRole("button", { name: "Close", exact: true })
    .first()
    .click();
  await selectFinanceArea("Source code mappings");
  const mappings = page.getByRole("region", { name: "Source code mappings", exact: true });
  await mappings.getByRole("button", { name: "New source mapping", exact: true }).click();
  await mappings.getByLabel("Source system", { exact: true }).selectOption(fixture.mapping_source);
  await mappings.getByLabel("Source namespace", { exact: true }).fill("journey-tax");
  await mappings.getByLabel("Declared source code", { exact: true }).fill("EU");
  await mappings
    .getByLabel("Internal reference", { exact: true })
    .selectOption(referenceResults.find((r) => r.kind === "case_code").id);
  await mappings
    .getByLabel("Reason", { exact: true })
    .fill("Reviewed declared source classification");
  const mappingCounts = await counts();
  await mappings.getByRole("button", { name: "Review source mapping", exact: true }).click();
  await mappings.getByRole("region", { name: "Confirm source mapping", exact: true }).waitFor();
  assert.equal((await get("/finance/source-mappings")).total, 0);
  assert.deepEqual(await counts(), mappingCounts);
  await page.reload();
  await mappings.getByRole("region", { name: "Confirm source mapping", exact: true }).waitFor();
  await page.screenshot({ path: `${out}/source-mapping-review.png` });
  await mappings.getByRole("button", { name: "Confirm", exact: true }).click();
  await mappings.locator("article").first().waitFor();
  for (const state of ["blocked", "active"]) {
    await mappings
      .locator("article")
      .first()
      .getByRole("button", { name: "Edit", exact: true })
      .click();
    await mappings.getByLabel("Status", { exact: true }).selectOption(state);
    await mappings.getByLabel("Reason", { exact: true }).fill(`Reviewed ${state} source mapping`);
    await mappings.getByRole("button", { name: "Review source mapping", exact: true }).click();
    await mappings.getByRole("button", { name: "Confirm", exact: true }).click();
    await mappings.getByRole("dialog").waitFor({ state: "detached" });
    assert.equal((await get("/finance/source-mappings")).items[0].state, state);
  }
  await mappings
    .locator("article")
    .first()
    .getByRole("button", { name: "History", exact: true })
    .click();
  await mappings.getByRole("region", { name: "Source mapping history", exact: true }).waitFor();
  assert.equal(
    await mappings
      .getByRole("region", { name: "Source mapping history", exact: true })
      .locator("article")
      .count(),
    3,
  );
  await mappings
    .getByRole("region", { name: "Source mapping history", exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${out}/source-mapping-history.png` });
  if (
    (await page.getByRole("dialog").count()) === 0 &&
    (await page.getByRole("button", { name: "Hide chat", exact: true }).isVisible())
  ) {
    await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await mappings
    .getByRole("heading", { name: "Source mapping history", exact: true })
    .scrollIntoViewIfNeeded();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: `${out}/source-mapping-mobile.png` });
  assert.deepEqual(await counts(), mappingCounts);
  console.log(
    "PASS source mapping: exact declaration, no-effect preview, reload recovery, owner confirmation, block/reactivate, immutable history and mobile",
  );
  await page.setViewportSize({ width: 1440, height: 1050 });
  await goto("finance", "flow=receivable");
  const attributionRow = page.locator("tr").filter({ hasText: "ATTRIBUTION" });
  await rowAction(attributionRow, "Financial detail");
  const attribution = page.getByRole("dialog", { name: "Financial detail", exact: true });
  await attribution.getByRole("heading", { name: "Received component", exact: true }).waitFor();
  assert.match(await attribution.innerText(), /1,000/);
  assert.match(await attribution.innerText(), /190/);
  await attribution.getByText("Source code resolved", { exact: false }).waitFor();
  await attribution.getByRole("button", { name: "Source mapping history", exact: true }).click();
  const sourceHistory = attribution.getByRole("region", {
    name: "Source mapping history",
    exact: true,
  });
  await sourceHistory.locator("article").first().waitFor();
  assert.equal(await sourceHistory.locator("article").count(), 3);
  await sourceHistory.getByRole("button", { name: "Close", exact: true }).click();
  const attributionCounts = await counts();
  for (const [index, value] of ["600", "400"].entries()) {
    await attribution.getByRole("button", { name: "Add cost-center share", exact: true }).click();
    await attribution
      .getByLabel("Cost center", { exact: true })
      .nth(index)
      .selectOption(fixture.attribution_centers[index]);
    await attribution.getByLabel("Share amount", { exact: true }).nth(index).fill(value);
  }
  await attribution
    .getByLabel("Reason", { exact: true })
    .fill("Distribution by operational responsibility");
  await attribution.getByRole("button", { name: "Review attribution", exact: true }).click();
  await attribution.getByRole("button", { name: "Confirm attribution", exact: true }).waitFor();
  assert.deepEqual(await counts(), attributionCounts);
  assert.equal(
    await attribution.getByRole("alert").count(),
    0,
    "Loaded attribution must not show a read error",
  );
  await page.screenshot({ path: `${out}/attribution-review.png` });
  await page.reload();
  await rowAction(page.locator("tr").filter({ hasText: "ATTRIBUTION" }), "Financial detail");
  await attribution.getByRole("button", { name: "Confirm attribution", exact: true }).click();
  await attribution.getByRole("heading", { name: "Attribution saved", exact: true }).waitFor();
  let component = (await get(`/finance/components/context/${fixture.attribution_invoice}`))
    .items[0];
  assert.equal(component.current.assigned, "1000");
  assert.equal(component.current.unassigned, "0");
  assert.ok(component.current.actor_id);
  assert.deepEqual(await counts(), attributionCounts);
  await attribution.getByRole("button", { name: "Remove share", exact: true }).nth(1).click();
  await attribution.getByLabel("Reason", { exact: true }).fill("Leave remainder unassigned");
  await attribution.getByRole("button", { name: "Review attribution", exact: true }).click();
  await attribution.getByRole("button", { name: "Confirm attribution", exact: true }).click();
  await attribution.getByRole("heading", { name: "Attribution saved", exact: true }).waitFor();
  component = (await get(`/finance/components/context/${fixture.attribution_invoice}`)).items[0];
  assert.equal(component.current.parts.length, 1);
  assert.equal(Number(component.current.assigned) + Number(component.current.unassigned), 1000);
  await attribution.getByRole("button", { name: "Attribution history", exact: true }).click();
  await attribution.getByRole("region", { name: "Attribution history", exact: true }).waitFor();
  const componentHistory = await get(`/finance/components/${component.component_id}/history`);
  assert.equal(componentHistory.total, 2);
  assert.equal(componentHistory.items[1].assigned, "1000");
  await page.screenshot({ path: `${out}/attribution-history.png` });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await attribution.isVisible());
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await page.screenshot({ path: `${out}/attribution-mobile.png` });
  await attribution.getByRole("button", { name: "Inspect source", exact: true }).click();
  await writeFile(
    `${out}/attribution.json`,
    JSON.stringify({ component, history: componentHistory }, null, 2),
  );
  console.log(
    "PASS component attribution: received net/tax/gross, exact split, no posting effect, reload, owner confirmation, partial replacement, immutable history and mobile",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await goto("finance", "flow=customer-credit&finance_status=");
  const canonicalCredits = await get("/finance/open-items?flow=customer-credit&item_status=");
  const actualCredit = canonicalCredits.items.find((row) => row.document_type === "credit_note");
  assert.ok(actualCredit, "Actual canonical customer credit must exist");
  await rowAction(page.locator("tr").filter({ hasText: actualCredit.number }), "Financial detail");
  const creditDetails = page.getByRole("dialog", { name: "Financial detail", exact: true });
  await creditDetails.getByRole("heading", { name: "Received component", exact: true }).waitFor();
  assert.equal(await creditDetails.getByRole("alert").count(), 0);
  await creditDetails.getByRole("button", { name: "Close", exact: true }).click();
  console.log("PASS canonical customer credit financial detail");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await goto("finance", "finance_view=settings&finance_settings=accounts");
  await page.getByRole("button", { name: "External accounting", exact: true }).click();
  const external = page.getByRole("region", { name: "External accounting", exact: true });
  const financeBeforeTargets = await counts();
  async function reviewTarget(reloadReview = false) {
    await external.getByRole("button", { name: "Review configuration", exact: true }).click();
    await external.getByRole("button", { name: "Confirm", exact: true }).waitFor();
    if (reloadReview) {
      await page.reload();
      await external.getByRole("button", { name: "Confirm", exact: true }).waitFor();
    }
    assert.deepEqual(await counts(), financeBeforeTargets);
    await external.getByRole("button", { name: "Confirm", exact: true }).click();
    await external.getByRole("dialog").waitFor({ state: "detached" });
  }
  await external.getByRole("button", { name: "Create accounting target", exact: true }).click();
  await external.getByLabel("Target identifier", { exact: true }).fill("journey-accounting");
  await external.getByLabel("Name", { exact: true }).fill("Journey accounting");
  await external.getByLabel("Reason", { exact: true }).fill("Reviewed target");
  await reviewTarget();
  const target = (await get("/finance/targets")).items.find(
    (r) => r.namespace === "journey-accounting",
  );
  await external
    .locator("article")
    .filter({ hasText: "journey-accounting" })
    .getByRole("button", { name: "Open account setup", exact: true })
    .click();
  await external.getByRole("button", { name: "External accounts", exact: true }).click();
  await external.getByRole("button", { name: "Create external account", exact: true }).click();
  await external.getByLabel("Code", { exact: true }).fill("SALES-EXTERNAL");
  await external.getByLabel("Name", { exact: true }).fill("Sales destination");
  await external.getByLabel("Reason", { exact: true }).fill("Reviewed permitted account");
  await reviewTarget();
  const account = (await get(`/finance/target-references?target_id=${target.id}`)).items[0];
  await external.getByRole("button", { name: "Rules", exact: true }).click();
  const sourceCase = (await get(`/finance/components/context/${fixture.attribution_invoice}`))
    .items[0].source_resolution.case.reference.id;
  await external.getByRole("button", { name: "Create mapping rule", exact: true }).click();
  await external.getByLabel("Case code", { exact: true }).selectOption(sourceCase);
  await external.getByLabel("External account", { exact: true }).selectOption(account.id);
  await external.getByLabel("Reason", { exact: true }).fill("Reviewed exact invoice destination");
  await reviewTarget(true);
  const mapping = (await get(`/finance/target-mappings?target_id=${target.id}`)).items[0];
  await external.getByRole("button", { name: "History", exact: true }).click();
  await external.getByRole("region", { name: "Mapping history", exact: true }).waitFor();
  assert.deepEqual(await counts(), financeBeforeTargets);
  await page.screenshot({ path: `${out}/target-mappings-desktop.png` });
  await external
    .getByRole("dialog")
    .getByRole("button", { name: "Close", exact: true })
    .first()
    .click();
  const hideChat = page.getByRole("button", { name: "Hide chat", exact: true });
  if (await hideChat.isVisible()) await hideChat.click();
  for (const width of [390, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const theme of ["light", "dark"]) {
      await page.evaluate((value) => {
        document.documentElement.dataset.theme = value;
        document.documentElement.style.colorScheme = value;
        document.documentElement.classList.toggle("dark", value === "dark");
      }, theme);
      await page.evaluate(() =>
        Promise.all(document.getAnimations().map((a) => a.finished.catch(() => undefined))),
      );
      assert.ok(await external.isVisible());
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await external
        .getByRole("heading", { name: "External accounting", exact: true })
        .scrollIntoViewIfNeeded();
      await page.screenshot({ path: `${out}/target-mappings-${width}-${theme}.png` });
    }
  }
  await page.evaluate(() => {
    document.documentElement.dataset.theme = "light";
    document.documentElement.classList.remove("dark");
    document.documentElement.style.colorScheme = "light";
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await goto("finance", "flow=customer&finance_status=");
  await rowAction(page.locator("tr").filter({ hasText: "ATTRIBUTION" }), "Financial detail");
  const targetPreview = page.getByRole("region", { name: "Mapping preview", exact: true });
  await targetPreview.getByLabel("Accounting target", { exact: true }).selectOption(target.id);
  await targetPreview.getByText("Mapping resolved", { exact: true }).waitFor();
  const resolved = await get(
    `/finance/target-mappings/preview?target_id=${target.id}&document_id=${fixture.attribution_invoice}`,
  );
  assert.equal(resolved.items[0].mapping.id, mapping.id);
  assert.equal(resolved.items[0].received.amounts.net, "1000");
  assert.equal(resolved.scope, "mapping_resolution_only");
  assert.deepEqual(await counts(), financeBeforeTargets);
  await page.screenshot({ path: `${out}/target-preview.png` });
  console.log(
    "PASS external target setup, allowed references, confirmed exact mapping, immutable history, real component preview and unchanged financial counts",
  );
  await writeFile(`${out}/settlements.json`, JSON.stringify(settlements, null, 2));
  assert.deepEqual(errors, []);
  console.log(
    "PASS complete real business journey: partial delivery/invoice/refund, reversal, remaining balances and evidence",
  );
} catch (error) {
  await page.screenshot({ path: `${out}/error.png` });
  await writeFile(`${out}/error-state.txt`, await page.locator("body").innerText());
  console.error(errors);
  throw error;
} finally {
  await browser.close();
}
