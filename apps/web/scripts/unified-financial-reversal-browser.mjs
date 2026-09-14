// Browser fixture only; financial mutations are verified against isolated PostgreSQL.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
let proposal,
  language = "en",
  confirmations = 0;
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const pager = { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false };
await mkdir("/private/tmp/reality-124-reversal-browser", { recursive: true });
await page.route("**/api/**", async (route) => {
  const p = new URL(route.request().url()).pathname;
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
  if (p.endsWith("/application-reference"))
    return reply({
      commands: [{ service: "reverse_ledger_posting_group", mode: "mutation", adapters: ["Web"] }],
      workspaces: [],
    });
  if (p.endsWith("/finance/reversal-choices"))
    return reply({
      items: [{ id: "group", number: "PAY-123", party: "Müller", currency: "EUR", amount: "125" }],
      page: pager,
    });
  if (p.endsWith("/delivery-actions/prepare")) {
    const args = route.request().postDataJSON().arguments;
    proposal = {
      id: "reversal",
      tool: "ledger_reverse",
      status: "proposed",
      verification: "pending",
      links: [],
      observation: null,
      review: {
        token: "review",
        intent: args,
        state: {
          party: { name: "Müller" },
          documents: [{ id: "payment", number: "PAY-123", type: "customer_payment" }],
          preview: {
            reason: args.reason,
            posting_group_id: "group",
            original_entries: [
              {
                id: "cash",
                account: "cash",
                debit_credit: "debit",
                amount: "125",
                currency: "EUR",
              },
            ],
            inverse_entries: [
              { account: "cash", debit_credit: "credit", amount: "125", currency: "EUR" },
              {
                account: "accounts_receivable",
                debit_credit: "debit",
                amount: "125",
                currency: "EUR",
              },
            ],
          },
          effects: {
            billing: [],
            newly_inactive: [{ id: "allocation", amount: "125", currency: "EUR" }],
            already_inactive: [],
            invoices: [
              { id: "invoice", number: "INV-123", currency: "EUR", before: "175", after: "300" },
            ],
            payments: [
              { id: "payment", number: "PAY-123", currency: "EUR", before: "0", after: "0" },
            ],
          },
        },
      },
    };
    return reply(proposal);
  }
  if (p.endsWith("/approve")) {
    confirmations++;
    proposal.status = "executed";
    proposal.verification = "verified";
    proposal.receipt = {
      reversal_id: "relation",
      original_posting_group_id: "group",
      reversing_posting_group_id: "inverse",
      replayed: false,
    };
    proposal.links = [
      { kind: "ledger_entry", id: "cash" },
      { kind: "ledger_entry", id: "inverse-cash" },
    ];
    proposal.observation = structuredClone(proposal.review.state.effects);
    proposal.observation.invoices[0].before = "300";
    return reply({ detail: "Simulated lost response" }, 503);
  }
  if (p.endsWith("/reject")) {
    proposal.status = "rejected";
    return reply(proposal);
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "conversation", title: "Reversal" }],
      active_session_id: "conversation",
      messages: [],
      proposals: proposal ? [{ ...proposal, input: proposal.review.intent }] : [],
      suggestions: [],
      has_archived: false,
    });
  if (p.endsWith("/change-proposals"))
    return reply({
      items: proposal
        ? [
            {
              ...proposal,
              type: "tool:ledger_reverse",
              input: proposal.review.intent,
              created_at: "2026-09-08T12:00:00Z",
            },
          ]
        : [],
      page: pager,
    });
  return reply({ items: [], totals: [], page: pager });
});
try {
  await page.goto("http://localhost:5177/app/finance?tenant=company");
  if (
    !(await page.getByRole("dialog").count()) &&
    (await page.locator(".register-actions:not([open]) > summary").count())
  )
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "Reverse posting", exact: true }).click();
  await page.getByLabel("Posting", { exact: true }).selectOption("group");
  await page.getByLabel("Reversal reason", { exact: true }).fill("Incorrect payment amount");
  await page.screenshot({ path: "/private/tmp/reality-124-reversal-browser/entry-1440.png" });
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm reversal", exact: true }).waitFor();
  await page.getByText("INV-123", { exact: true }).waitFor();
  assert.equal(confirmations, 0);
  for (const lang of ["en", "de", "nl", "es"])
    for (const width of [390, 1440])
      for (const theme of ["light", "dark"]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.goto("http://localhost:5177/app/finance?tenant=company&proposal=reversal");
        await page.locator("#financial-reversal-title").waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        await page.screenshot({
          path: `/private/tmp/reality-124-reversal-browser/${lang}-${width}-${theme}.png`,
        });
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      }
  language = "en";
  await page.goto("http://localhost:5177/app/finance?tenant=company&proposal=reversal");
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByLabel("Reversal reason", { exact: true }).waitFor();
  assert.equal(
    await page.getByLabel("Reversal reason", { exact: true }).inputValue(),
    "Incorrect payment amount",
  );
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm reversal", exact: true }).click();
  await page.getByRole("link", { name: "Open reversal", exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByText("Actions", { exact: true }).click();
  if (
    !(await page.getByRole("dialog").count()) &&
    (await page.locator(".register-actions:not([open]) > summary").count())
  )
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "Reverse posting", exact: true }).first().click();
  await page.getByLabel("Posting", { exact: true }).selectOption("group");
  await page.getByLabel("Reversal reason", { exact: true }).fill("Another review");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm reversal", exact: true }).waitFor();
  await page.goto("http://localhost:5177/app/decisions?tenant=company");
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await page.locator("#financial-reversal-title").waitFor();
  await page.goto("http://localhost:5177/app/copilot?tenant=company");
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await page.locator("#financial-reversal-title").waitFor();
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  await page.getByRole("dialog").getByText("Rejected", { exact: true }).waitFor();
  proposal.status = "proposed";
  proposal.verification = "pending";
  proposal.review.state.documents = [{ id: "invoice", number: "INV-123", type: "sales_invoice" }];
  proposal.review.state.effects.invoices[0].after = "0";
  proposal.review.state.effects.payments[0].after = "125";
  proposal.review.state.preview.inverse_entries = [
    { account: "accounts_receivable", debit_credit: "credit", amount: "300", currency: "EUR" },
    { account: "sales_revenue", debit_credit: "debit", amount: "300", currency: "EUR" },
  ];
  proposal.review.state.effects.billing = [
    {
      order_line_id: "line",
      order_id: "order",
      label: "Desk lamp",
      unit: "pcs",
      ordered: "2",
      invoiced: "2",
      remaining: "0",
      can_invoice: false,
      evidence: [],
      remaining_before: "0",
      remaining_after: "2",
      invoiced_before: "2",
      invoiced_after: "0",
    },
  ];
  await page.goto("http://localhost:5177/app/finance?tenant=company&proposal=reversal");
  await page.getByText("Remaining billable after reversal", { exact: true }).waitFor();
  await page.getByText("0 → 2 pcs", { exact: true }).waitFor();
  await page
    .getByText(
      "Invoice evidence stays in history. Its quantity becomes billable again once all invoice posting groups are reversed.",
      { exact: true },
    )
    .waitFor();
  await page.screenshot({
    path: "/private/tmp/reality-124-reversal-browser/invoice-availability.png",
  });
  assert.deepEqual(errors, []);
  console.log(
    "PASS financial reversal: effects, four entries, edit/reject, reload, response-loss recovery and 16 localized responsive views",
  );
} catch (error) {
  console.error(errors);
  await page.screenshot({ path: "/private/tmp/reality-124-reversal-browser-error.png" });
  throw error;
} finally {
  await browser.close();
}
