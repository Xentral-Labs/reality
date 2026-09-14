import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
let proposal,
  prepared,
  language = "en",
  confirmations = 0;
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const pager = { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false };
const context = {
  invoice: {
    id: "invoice",
    number: "INV-125",
    currency: "EUR",
    gross_amount: "300",
    party_id: "customer",
  },
  party: { name: "Müller" },
  open_amount: "175",
  remaining_amount: "300",
  credited_amount: "0",
  positions: [
    {
      id: "line",
      label: "Desk lamp",
      quantity: "3",
      credited: "1",
      remaining: "2",
      unit: "pcs",
      legacy_credit_ids: [],
      evidence: [],
    },
    {
      id: "line2",
      label: "Office chair",
      quantity: "2",
      credited: "0",
      remaining: "2",
      unit: "pcs",
      legacy_credit_ids: [],
      evidence: [],
    },
    {
      id: "exhausted",
      label: "Fully credited",
      quantity: "1",
      credited: "1",
      remaining: "0",
      unit: "pcs",
      legacy_credit_ids: [],
      evidence: [],
    },
  ],
};
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
  if (p.endsWith("/application-reference"))
    return reply({
      commands: [{ service: "record_sales_credit", mode: "mutation", adapters: ["Web"] }],
      workspaces: [],
    });
  if (p.endsWith("/finance/open-items"))
    return reply({
      items: [
        {
          document_id: "invoice",
          number: "INV-125",
          document_type: "sales_invoice",
          party: "Müller",
          gross: "300",
          settled: "125",
          open: "175",
          currency: "EUR",
          status: "partial",
        },
      ],
      totals: [],
      page: pager,
    });
  if (p.endsWith("/evidence-documents"))
    return reply({
      items: [
        { id: "invoice", number: "INV-125", party: "Müller", currency: "EUR", gross_amount: "300" },
      ],
      page: pager,
    });
  if (p.includes("/finance/invoice-credit/")) return reply(context);
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    const a = prepared.arguments;
    proposal = {
      id: "credit",
      tool: "sales_credit_record",
      status: "proposed",
      verification: "pending",
      links: [],
      observation: null,
      review: {
        token: "exact",
        intent: a,
        state: {
          context,
          creation: { ...a, selections: a.lines },
          invoice_after: "155",
          credit_open: "70",
        },
      },
    };
    return reply(proposal);
  }
  if (p.endsWith("/approve")) {
    confirmations++;
    proposal.status = "executed";
    proposal.verification = "verified";
    proposal.receipt = { records: [{ family: "document", id: "credit-doc" }] };
    return reply({ detail: "Lost response" }, 503);
  }
  if (p.endsWith("/reject")) {
    proposal.status = "rejected";
    return reply(proposal);
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/change-proposals"))
    return reply({
      items: proposal
        ? [
            {
              ...proposal,
              type: "tool:sales_credit_record",
              input: proposal.review.intent,
              created_at: "2026-09-08T12:00:00Z",
            },
          ]
        : [],
      page: pager,
    });
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "conversation", title: "Credit" }],
      active_session_id: "conversation",
      messages: [],
      proposals: proposal ? [{ ...proposal, input: proposal.review.intent }] : [],
      suggestions: [],
      has_archived: false,
    });
  return reply({ items: [], totals: [], page: pager });
});
await mkdir("/private/tmp/reality-125-browser", { recursive: true });
try {
  await page.goto("http://localhost:5177/app/finance?tenant=company");
  await page
    .locator("tr")
    .filter({ hasText: "INV-125" })
    .getByRole("button", { name: "New credit note", exact: true })
    .click();
  assert.equal(await page.getByLabel("Invoice", { exact: true }).inputValue(), "invoice");
  await page.getByLabel("Invoice position", { exact: true }).selectOption("line");
  await page.waitForFunction(
    () => document.querySelector('option[value="exhausted"]')?.disabled === true,
  );
  await page.getByLabel("Quantity", { exact: true }).fill("1");
  await page.getByLabel("Stated line amount", { exact: true }).fill("31");
  await page.getByRole("button", { name: "Add credit position", exact: true }).click();
  await page.getByLabel("Invoice position", { exact: true }).nth(1).selectOption("line2");
  await page.getByLabel("Quantity", { exact: true }).nth(1).fill("1");
  await page.getByLabel("Stated line amount", { exact: true }).nth(1).fill("32");
  await page.getByLabel("Credit note number", { exact: true }).fill("CR-125");
  await page.getByLabel("Stated credit amount", { exact: true }).fill("90");
  await page.getByLabel("Credit reason", { exact: true }).fill("Agreed price correction");
  await page.getByLabel("Amount to offset against this invoice", { exact: true }).fill("20");
  await page.screenshot({ path: "/private/tmp/reality-125-browser/entry.png" });
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  assert.equal(prepared.arguments.lines.length, 2);
  assert.equal(prepared.arguments.gross_amount, "90");
  assert.equal(prepared.arguments.allocation_amount, "20");
  await page.getByText("Invoice open after credit", { exact: true }).waitFor();
  for (const lang of ["en", "de", "nl", "es"])
    for (const width of [390, 1440])
      for (const theme of ["light", "dark"]) {
        language = lang;
        await page.setViewportSize({ width, height: 1100 });
        await page.goto("http://localhost:5177/app/finance?tenant=company&proposal=credit");
        await page.locator("#credit-title").waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        await page.screenshot({
          path: `/private/tmp/reality-125-browser/${lang}-${width}-${theme}.png`,
        });
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      }
  language = "en";
  await page.goto("http://localhost:5177/app/finance?tenant=company&proposal=credit");
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByLabel("Invoice position", { exact: true }).nth(1).waitFor();
  assert.equal(
    await page.getByLabel("Credit reason", { exact: true }).inputValue(),
    "Agreed price correction",
  );
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).click();
  await page.getByRole("link", { name: "Open credit note", exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByText("Actions", { exact: true }).click();
  if (
    !(await page.getByRole("dialog").count()) &&
    (await page.locator(".register-actions:not([open]) > summary").count())
  )
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "New credit note", exact: true }).first().click();
  await page.getByLabel("Invoice", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  proposal.status = "proposed";
  proposal.verification = "pending";
  await page.goto("http://localhost:5177/app/decisions?tenant=company");
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await page.locator("#credit-title").waitFor();
  await page.goto("http://localhost:5177/app/copilot?tenant=company");
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await page.locator("#credit-title").waitFor();
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  await page.getByRole("dialog").getByText("Rejected", { exact: true }).waitFor();
  assert.deepEqual(errors, []);
  console.log(
    "PASS credit entry: multiple positions, independent values, netting review, four entries, edit/reject/reload/recovery and 16 localized views",
  );
} catch (error) {
  console.error(errors);
  await page.screenshot({ path: "/private/tmp/reality-125-browser/error.png" });
  throw error;
} finally {
  await browser.close();
}
