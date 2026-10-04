// Feature 168 acceptance against a running stack: real API, real scheduler, real browser.
// Never synthesizes business responses. It creates one disposable Sandbox company, starts
// Demo Data, waits for the settlement stream and drives the Payments dialog by hand.
//
// Required: PLAYWRIGHT_MODULE, DEMO_O2C_EMAIL, DEMO_O2C_PASSWORD.
// Optional: PLAYWRIGHT_EXECUTABLE, DEMO_O2C_BASE_URL (default http://127.0.0.1:8080),
//           DEMO_O2C_TENANT (reuse an existing connected company instead of creating one),
//           DEMO_O2C_RATE (300), DEMO_O2C_WAIT_MINUTES (25, first settled invoice),
//           DEMO_O2C_DIFFERENCE_WAIT_MINUTES (150, residual and unmatched payment),
//           DEMO_O2C_ARTIFACTS (default /tmp/reality-demo-o2c-browser).
import assert from "node:assert/strict";
import { createHash } from "node:crypto";

const canonicalSource = (value) => Array.isArray(value)
  ? value.map(canonicalSource)
  : value !== null && typeof value === "object"
    ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalSource(value[key])]))
    : value;

import { pathToFileURL } from "node:url";
import { mkdir, writeFile } from "node:fs/promises";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = (process.env.DEMO_O2C_BASE_URL || "http://127.0.0.1:8080").replace(/\/$/, "");
const out = process.env.DEMO_O2C_ARTIFACTS || "/tmp/reality-demo-o2c-browser";
const rate = Number(process.env.DEMO_O2C_RATE || 300);
const waitMinutes = Number(process.env.DEMO_O2C_WAIT_MINUTES || 25);
const differenceWaitMinutes = Number(process.env.DEMO_O2C_DIFFERENCE_WAIT_MINUTES || 150);
assert.ok(process.env.DEMO_O2C_EMAIL && process.env.DEMO_O2C_PASSWORD, "login is required");
await mkdir(out, { recursive: true });

const log = (message, extra = {}) =>
  console.log(JSON.stringify({ at: new Date().toISOString(), message, ...extra }));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
const page = await context.newPage();
page.setDefaultTimeout(20000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));

const request = async (method, path, data) => {
  const response = await context.request.fetch(`${base}${path}`, {
    method,
    data,
    headers: data ? { "content-type": "application/json" } : undefined,
  });
  const text = await response.text();
  assert.ok(response.ok(), `${method} ${path}: ${response.status()} ${text}`);
  return text ? JSON.parse(text) : null;
};
const key = (label) => `o2c-${label}-${Date.now().toString(36)}`;

// 1. Sign in with the local owner account; the cookie lives in the browser context.
await request("POST", "/api/auth/login", {
  email: process.env.DEMO_O2C_EMAIL,
  password: process.env.DEMO_O2C_PASSWORD,
});
log("signed in");

// 2. One disposable Sandbox company with Demo Data connected and started.
let tenant = process.env.DEMO_O2C_TENANT;
if (!tenant) {
  const created = await request("POST", "/api/company-setup", {
    request_key: key("company"),
    name: `Order to cash ${new Date().toISOString().slice(0, 16)}`,
    environment: "sandbox",
    content: "empty",
    live_simulation: false,
    confirmed: true,
  });
  tenant = created.tenant_id;
  assert.ok(tenant, JSON.stringify(created));
  log("company created", { tenant });
}
const demo = `/api/tenants/${encodeURIComponent(tenant)}/demo-data`;
let status = await request("GET", demo);
if (status.state === "not_connected") {
  const preview = await request("GET", `${demo}/preview`);
  assert.ok(
    preview.add.payment_terms.length + Object.keys(preview.references.payment_terms).length === 1,
    "the discount payment term is a prerequisite",
  );
  status = await request("POST", `${demo}/connect`, {
    request_key: key("connect"),
    preview_fingerprint: preview.fingerprint,
    confirmed: true,
  });
  log("connected", { revision: status.revision });
}
if (status.state === "stopped") {
  status = await request("POST", `${demo}/control`, {
    action: "start",
    expected_revision: status.revision,
    request_key: key("start"),
    confirmed: true,
    rate,
  });
  log("started", { rate: status.rate, settlement_schedule: status.settlement_schedule_id });
}
assert.equal(status.state, "running");
assert.ok(status.settlement_schedule_id, "start creates the settlement schedule");
assert.ok(status.order_to_cash.next_settlement, "the settlement schedule is due");

// 3. The panel shows the order-to-cash block with its links.
await page.goto(`${base}/app/demo-data?tenant=${encodeURIComponent(tenant)}`);
const block = page.locator(".demo-order-to-cash");
await block.waitFor();
await block.getByText("Invoices issued", { exact: true }).waitFor();
await block.getByText("Unmatched payments", { exact: true }).waitFor();
assert.ok((await block.locator("a[href*='finance_view=payments']").count()) === 1);
assert.ok((await block.locator("a[href*='finance_view=open-items']").count()) === 1);
assert.ok((await block.locator("a[href*='finance_view=journal']").count()) === 1);
await page.screenshot({ path: `${out}/01-panel-started.png`, fullPage: true });
log("panel shows the order-to-cash block");

// The explicitly invoked soak fixture supplies a bounded Owner reviewer. Production
// source controls still grant no decision authority. Every original is read and each
// retained exact digest is separately confirmed using the authenticated Owner cookie.
const reviewLimit = Number(process.env.DEMO_O2C_REVIEW_LIMIT || 5000);
assert.ok(Number.isInteger(reviewLimit) && reviewLimit > 0 && reviewLimit <= 5000);
let reviewed = 0;
const reviewSources = async () => {
  const prefix = `/api/tenants/${encodeURIComponent(tenant)}`;
  const pending = await request("GET", `${prefix}/change-proposals?status=pending&tool=intake_apply&size=25`);
  for (const candidate of pending.items) {
    assert.ok(reviewed < reviewLimit, "The explicitly bounded reviewer fixture is exhausted");
    let id = candidate.id;
    let accepted = false;
    for (let attempt = 0; attempt < 3 && !accepted; attempt++) {
      const review = await request("GET", `${prefix}/change-proposals/${id}/review`);
      const plan = review.input.plan;
      assert.equal(review.status, "proposed");
      assert.ok(["demo.order", "sales_invoice.v1", "customer_payment.v1"].includes(plan.profile));
      const original = await context.request.get(`${base}${prefix}/intake-units/${id}/original`);
      assert.equal(original.status(), 200);
      const text = await original.text();
      assert.equal(original.headers()["x-source-digest"], plan.source_hash);
      assert.equal(createHash("sha256").update(JSON.stringify(canonicalSource(JSON.parse(text)))).digest("hex"), plan.source_hash);
      assert.equal(JSON.parse(text).synthetic, true);
      const response = await context.request.post(`${base}${prefix}/change-proposals/${id}/approve`, {
        data: { confirmed: true, review_token: review.input.digest },
      });
      const result = await response.json();
      if (!response.ok()) {
        assert.equal(result.code, "intake_review_stale", JSON.stringify(result));
        assert.ok(attempt < 2, "Current-state changes exhausted the bounded fresh-review attempts");
        const renewed = await request("POST", `${prefix}/intake-units/${id}/renew`, {
          job_id: plan.import_job_id, request_id: key("fresh-review"),
        });
        id = renewed.id;
        continue;
      }
      const receipt = await request("GET", `${prefix}/change-proposals/${id}/review`);
      assert.equal(receipt.status, "executed");
      assert.equal(receipt.decider.kind, "person");
      assert.equal(receipt.receipt.source_record_id, plan.source_record_id);
      assert.equal(receipt.receipt.digest, review.input.digest);
      accepted = true;
      reviewed++;
      log("explicit Owner fixture confirmed exact synthetic source", {
        proposal_id: id, source_record_id: plan.source_record_id, digest: review.input.digest, reviewed, reviewLimit,
      });
    }
  }
};

// 4. Wait for the stream: the first booked invoice and the first settled invoice.
const until = async (label, minutes, predicate) => {
  const deadline = Date.now() + minutes * 60_000;
  let last;
  while (Date.now() < deadline) {
    await reviewSources();
    last = (await request("GET", demo)).order_to_cash;
    if (predicate(last)) {
      log(label, last);
      return last;
    }
    await sleep(30_000);
  }
  throw new Error(`${label}: not reached within ${minutes} minutes; last ${JSON.stringify(last)}`);
};
const settled = await until(
  "first invoice settled",
  waitMinutes,
  (b) => b.invoices_issued >= 1 && b.invoices_settled >= 1 && b.payments_allocated >= 1,
);
await page.reload();
await block.waitFor();
assert.ok(
  Number(await block.locator("dd").nth(0).innerText()) >= 1,
  "the panel counts issued invoices",
);
await page.screenshot({ path: `${out}/02-panel-settling.png`, fullPage: true });

const finance = (query) =>
  page.goto(`${base}/app/finance?tenant=${encodeURIComponent(tenant)}&${query}`);
await finance("finance_view=open-items&flow=receivable&finance_status=paid");
await page.getByRole("heading", { level: 1 }).first().waitFor();
await page.getByText(/^INV-/).first().waitFor();
await page.screenshot({ path: `${out}/03-open-items-paid.png`, fullPage: true });
log("a synthetic invoice shows as paid in Open items");

// 5. Differences: a short payment leaves a residual, an unmatched payment offers candidates.
const differences = await until(
  "residual and unmatched payment present",
  differenceWaitMinutes,
  (b) => b.open_residuals >= 1 && b.unmatched_payments >= 1,
);
await finance("finance_view=open-items&flow=receivable&finance_status=partial");
await page.getByText(/^INV-/).first().waitFor();
await page.screenshot({ path: `${out}/04-open-items-partial.png`, fullPage: true });
log("a short payment leaves the invoice partially paid");

// Pick the unallocated payment that carries candidates, through the same reads the page uses.
let settlementContext = null,
  creditRow = null,
  seen = 0;
for (let pageNumber = 1; pageNumber <= 5 && !creditRow; pageNumber++) {
  const credits = await request(
    "GET",
    `/api/tenants/${encodeURIComponent(tenant)}/finance/open-items?q=&flow=customer-balance&item_status=outstanding&page=${pageNumber}`,
  );
  const open = credits.items.filter(
    (item) => item.document_type === "customer_payment" && Number(item.open) > 0,
  );
  seen += open.length;
  for (const row of open) {
    const found = await request(
      "GET",
      `/api/tenants/${encodeURIComponent(tenant)}/finance/settlements/context/${row.document_id}`,
    );
    if (found.candidates?.length) {
      settlementContext = found;
      creditRow = row;
      break;
    }
  }
  if (!credits.page?.has_next) break;
}
assert.ok(creditRow, `no unallocated payment with candidates among ${seen} open credits`);
// The row's actions live in its inline preview, which the `entry` parameter opens.
await finance(
  `finance_view=open-items&flow=customer-balance&q=${encodeURIComponent(creditRow.number)}&entry=${encodeURIComponent(creditRow.document_id)}`,
);
await page.getByText(creditRow.number, { exact: true }).first().waitFor();
const preview = page.locator(`#finance-preview-${creditRow.document_id}`);
await preview.getByRole("button", { name: "Use available credit", exact: true }).click();
const dialog = page.getByRole("dialog");
await dialog.getByText("Suggested invoices", { exact: true }).waitFor();
const suggestions = dialog.locator("[data-testid='settlement-candidates'] li");
assert.ok((await suggestions.count()) >= 1, "at least one suggested invoice with a reason");
const firstSuggestion = await suggestions.first().innerText();
assert.match(
  firstSuggestion,
  /Amount equals the open amount|Invoice number appears|Stated reference/,
);
await page.screenshot({ path: `${out}/05-candidates.png`, fullPage: true });
log("candidates with reasons are shown", { first: firstSuggestion });

const select = dialog.locator("select[name='invoice']");
const suggested = await select.locator("option", { hasText: "suggested" }).first();
const invoiceId = await suggested.getAttribute("value");
await select.selectOption(invoiceId);
const open = (await suggested.innerText()).match(/[\d.,]+\s*[A-Z]{3}|[A-Z]{3}\s*[\d.,]+/)?.[0];
const beforeUnmatched = differences.unmatched_payments;
// Allocate the lesser of the available credit and the chosen invoice's open amount.
const chosen = settlementContext.invoices.find((choice) => choice.id === invoiceId);
const amount = Math.min(Number(settlementContext.available), Number(chosen.open));
await dialog.locator("input[name='amount']").fill(String(amount));
await dialog.getByRole("button", { name: "Review settlement", exact: true }).click();
await dialog.getByRole("button", { name: "Confirm settlement", exact: true }).waitFor();
await page.screenshot({ path: `${out}/06-review.png`, fullPage: true });
await dialog.getByRole("button", { name: "Confirm settlement", exact: true }).click();
// The receipt replaces the decision buttons with explanation links.
await dialog.getByRole("button", { name: "Explain invoice", exact: true }).waitFor();
await dialog.getByRole("button", { name: "Explain credit", exact: true }).waitFor();
await page.screenshot({ path: `${out}/07-confirmed.png`, fullPage: true });
const after = (await request("GET", demo)).order_to_cash;
assert.ok(
  after.unmatched_payments <= beforeUnmatched,
  `confirming a candidate never adds unmatched payments: ${JSON.stringify(after)}`,
);
log("candidate confirmed through the guided settlement", { open, amount, after });

assert.deepEqual(errors, [], "no page errors");
await writeFile(
  `${out}/summary.json`,
  JSON.stringify({ tenant, settled, differences, after, artifacts: out }, null, 2),
);
log("done", { tenant, artifacts: out });
await browser.close();
