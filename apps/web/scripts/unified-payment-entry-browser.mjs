import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
// Financial execution is verified separately in isolated PostgreSQL tests.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
import { openPageActions } from "./page-actions.mjs";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
let proposal,
  prepared,
  language = "en",
  confirmations = 0;
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const pager = { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false };
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    p = new URL(req.url()).pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (p === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
    });
  if (p === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "company", name: "Northstar" }], default_tenant_id: "company" });
  if (p.endsWith("/application-reference")) return reply(discoveryReference);
  if (p.endsWith("/finance/open-items"))
    return reply({
      items: [
        {
          document_id: "invoice-doc",
          document_type: "sales_invoice",
          number: "INV-121",
          party: "Müller",
          currency: "USD",
          gross: "300",
          settled: "0",
          open: "300",
          status: "open",
        },
      ],
      totals: [],
      page: pager,
    });
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    const a = prepared.arguments;
    proposal = {
      id: "payment",
      tool: prepared.tool,
      status: "proposed",
      verification: "pending",
      links: [],
      observation: null,
      review: {
        token: "exact",
        intent: a,
        state: {
          creation: {
            ...a,
            direction: prepared.tool === "customer_payment_post" ? "customer" : "supplier",
            currency: "USD",
          },
          invoice: { id: "invoice-doc", number: "INV-121" },
          party: { name: "Müller" },
          source: null,
          open_before: "300",
          open_after: a.amount === "125.1234" ? "174.8766" : "175",
        },
      },
    };
    return reply(proposal);
  }
  // Decision reviews (spec 276) hand a delivery-kind proposal to the shared action card.
  if (p.endsWith("/change-proposals/payment/review"))
    return reply({
      id: "payment",
      tool: proposal.tool,
      label: "Payment",
      purpose: "",
      review_kind: "delivery",
      status: proposal.status,
      actor_type: "human",
      created_at: "2026-09-08T12:00:00Z",
      decided_at: null,
      decider: null,
      input: proposal.review.intent,
      preview: {},
      receipt: {},
      next_step: {
        review_required: true,
        required_principal: "authorized_human",
        reconciliation_read: "delivery_proposal_detail",
        verification_reads: [],
      },
    });
  if (p.endsWith("/approve")) {
    confirmations++;
    proposal.status = "executed";
    proposal.verification = "verified";
    proposal.receipt = {
      records: [
        { family: "ledger_entry", id: "cash" },
        { family: "ledger_entry", id: "control" },
      ],
    };
    proposal.payment_entry_id = "cash";
    proposal.observation = { open: "175", allocation_active: true };
    return reply({ detail: "Simulated response loss" }, 503);
  }
  if (p.endsWith("/reject")) {
    proposal.status = "rejected";
    return reply(proposal);
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/change-proposals"))
    return reply({
      items: proposal
        ? [{ ...proposal, input: proposal.review.intent, created_at: "2026-09-08T12:00:00Z" }]
        : [],
      page: pager,
    });
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "chat", title: "Payment" }],
      active_session_id: "chat",
      messages: [],
      proposals: proposal ? [{ ...proposal, input: proposal.review.intent }] : [],
      suggestions: [],
      has_archived: false,
    });
  return reply({ items: [], totals: [], page: pager });
});
try {
  await mkdir("/private/tmp/reality-121-browser", { recursive: true });
  await page.goto("http://localhost:5177/app/finance?tenant=company");
  await page.locator(".register-actions > summary").waitFor();
  if (
    !(await page.getByRole("dialog").count()) &&
    (await page.locator(".register-actions:not([open]) > summary").count())
  )
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "Record customer payment", exact: true }).click();
  await page.getByLabel("Invoice", { exact: true }).selectOption("invoice-doc");
  await page.getByLabel("Payment amount", { exact: true }).fill("125.1234");
  await page.getByLabel("Payment reference", { exact: true }).fill("PAY-121");
  await page.screenshot({ path: "/private/tmp/reality-121-browser/entry-1440.png" });
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  assert.equal(prepared.arguments.amount, "125.1234");
  assert.equal(prepared.arguments.invoice_id, "invoice-doc");
  await page.getByText("US$125.1234", { exact: true }).waitFor();
  assert.equal(
    await page.evaluate(() =>
      new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 4,
      }).format("99999999999999.1234"),
    ),
    "US$99,999,999,999,999.1234",
  );
  for (const lang of ["en", "de", "nl", "es"])
    for (const width of [390, 1440])
      for (const theme of ["light", "dark"]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.goto(
          `http://localhost:5177/app/finance?tenant=company&proposal=payment&lang=${language}`,
        );
        await page.locator("#payment-title").waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        await page.screenshot({
          path: `/private/tmp/reality-121-browser/${lang}-${width}-${theme}.png`,
        });
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
        );
      }
  language = "en";
  await page.goto(
    `http://localhost:5177/app/finance?tenant=company&proposal=payment&lang=${language}`,
  );
  await page.getByRole("button", { name: "Confirm change", exact: true }).click();
  // A decision opened from its review closes once the lost response is recovered.
  await page.locator("#payment-title").waitFor({ state: "detached" });
  assert.equal(confirmations, 1);
  assert.equal(proposal.status, "executed");
  // Start the next payment from the page actions. (Searching the command palette for
  // "Record customer payment" currently finds nothing in this fixture; see the PR.)
  await openPageActions(page);
  await page.getByRole("button", { name: "Record customer payment", exact: true }).first().click();
  await page.getByLabel("Payment direction", { exact: true }).selectOption("supplier_payment_post");
  await page.getByLabel("Invoice", { exact: true }).selectOption("invoice-doc");
  await page.getByLabel("Payment amount", { exact: true }).fill("100");
  await page.getByLabel("Payment reference", { exact: true }).fill("SUP-PAY");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Request changes", exact: true }).click();
  assert.equal(await page.getByLabel("Payment reference", { exact: true }).inputValue(), "SUP-PAY");
  assert.equal(
    await page.getByLabel("Payment direction", { exact: true }).inputValue(),
    "supplier_payment_post",
  );
  await page.getByLabel("Payment amount", { exact: true }).fill("125");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  assert.equal(prepared.tool, "supplier_payment_post");
  await page.goto("http://localhost:5177/app/decisions?tenant=company");
  await page.locator("[data-work-list=decisions] [data-work-row]").first().click();
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await page.locator("#payment-title").waitFor();
  // Copilot is the shared dock; the financial fixture intentionally owns no Home reads.
  await page.goto("http://localhost:5177/app/finance?tenant=company");
  await page.getByRole("button", { name: "Review and decide", exact: true }).click();
  await page.locator("#payment-title").waitFor();
  await page.getByRole("button", { name: "Do not approve", exact: true }).click();
  await page.locator("#payment-title").waitFor({ state: "detached" });
  assert.equal(proposal.status, "rejected");
  assert.deepEqual(errors, []);
  console.log(
    "PASS payment entry, partial balance review, customer/supplier, four entries, edit/reject, reload/recovery and 16 localized responsive views",
  );
} catch (error) {
  console.error(errors);
  await page.screenshot({ path: "/private/tmp/reality-121-browser/error.png" });
  throw error;
} finally {
  await browser.close();
}
