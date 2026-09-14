import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
// Intercepted browser fixture; financial effects are tested in isolated PostgreSQL.
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
  prepared,
  confirmations = 0,
  language = "en";
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const billing = (id, ordered, invoiced, remaining) => ({
  order_line_id: id,
  order_id: "order",
  label: id === "line" ? "Desk lamp" : "Office chair",
  unit: "pcs",
  ordered,
  invoiced,
  remaining,
  can_invoice: remaining !== "0",
  evidence: [],
});
const availability = {
  line: billing("line", "5", "2", "3"),
  line2: billing("line2", "4", "0", "4"),
  exhausted: billing("exhausted", "1", "1", "0"),
};
const pager = { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false };
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    p = u.pathname;
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
  if (p.endsWith("/evidence-documents"))
    return reply({
      items: [
        {
          id: "order",
          number: "ORDER-120",
          party: "Müller",
          currency: "EUR",
          gross_amount: "300",
          line_count: 1,
        },
      ],
      page: pager,
    });
  if (p.includes("/inspector/"))
    return reply({
      id: "order",
      evidence_lines: [
        {
          id: "line",
          label: "Desk lamp",
          quantity: "5",
          gross_amount: "300",
          unit: "pcs",
          billing: availability.line,
        },
        {
          id: "line2",
          label: "Office chair",
          quantity: "4",
          gross_amount: "400",
          unit: "pcs",
          billing: availability.line2,
        },
        {
          id: "exhausted",
          label: "Fully billed item",
          quantity: "1",
          unit: "pcs",
          billing: availability.exhausted,
        },
      ],
    });
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    const a = prepared.arguments;
    proposal = {
      id: "invoice",
      tool: prepared.tool,
      status: "proposed",
      verification: "pending",
      links: [],
      observation: null,
      review: {
        token: "exact",
        intent: a,
        effect: { debit: "accounts_receivable", credit: "sales_revenue" },
        state: {
          billing: a.lines?.map((row) => ({
            ...availability[row.order_line_id],
            requested: row.quantity,
            remaining_after: String(
              Number(availability[row.order_line_id].remaining) - Number(row.quantity),
            ),
          })),
          positions: a.lines?.map((row) => ({
            ...row,
            item: { name: row.order_line_id === "line" ? "Desk lamp" : "Office chair" },
            line: { unit: "pcs" },
          })),
          creation: {
            ...a,
            direction: prepared.tool === "sales_invoice_record" ? "sales" : "purchase",
            currency: "EUR",
            unit: "pcs",
          },
          order: { id: "order", number: "ORDER-120" },
          party: { name: "Müller" },
          item: { name: "Desk lamp" },
        },
      },
    };
    return reply(proposal);
  }
  if (p.endsWith("/approve")) {
    confirmations++;
    proposal.status = "executed";
    proposal.verification = "verified";
    proposal.receipt = { records: [{ family: "document", id: "invoice-doc" }] };
    return reply({ detail: "Simulated lost response" }, 503);
  }
  if (p.endsWith("/reject")) {
    proposal.status = "rejected";
    return reply(proposal);
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "conversation", title: "Invoice" }],
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
              type: `tool:${proposal.tool}`,
              input: proposal.review.intent,
              created_at: "2026-09-08T12:00:00Z",
            },
          ]
        : [],
      page: pager,
    });
  if (
    ["/dashboard", "/activity-volume", "/readiness", "/analytics"].some((path) => p.endsWith(path))
  )
    return reply({ detail: "Home reads are outside this invoice fixture" }, 503);
  return reply({ items: [], totals: [], page: pager });
});
try {
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://localhost:5177") + "/app/finance?tenant=company",
  );
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "New customer invoice", exact: true }).click();
  await page.getByLabel("Order", { exact: true }).selectOption("order");
  await page.getByLabel("Order line", { exact: true }).selectOption("line");
  await page.waitForFunction(
    () => document.querySelector('option[value="exhausted"]')?.disabled === true,
  );
  await page.getByText("Remaining billable", { exact: true }).first().waitFor();
  await page.getByLabel("Invoice number", { exact: true }).fill("INV-120");
  await page.getByLabel("Quantity", { exact: true }).fill("2");
  await page.getByLabel("Stated line amount", { exact: true }).fill("101");
  await page.getByRole("button", { name: "Add invoice position", exact: true }).click();
  await page.getByLabel("Order line", { exact: true }).nth(1).selectOption("line2");
  await page.getByLabel("Quantity", { exact: true }).nth(1).fill("3");
  await page.getByLabel("Stated line amount", { exact: true }).nth(1).fill("102");
  await page.getByRole("button", { name: "Add invoice position", exact: true }).click();
  await page.getByRole("button", { name: "Remove position", exact: true }).last().click();
  await page.getByLabel("Stated invoice amount", { exact: true }).fill("301");
  await mkdir("/private/tmp/reality-124-invoice-browser", { recursive: true });
  await page.screenshot({ path: "/private/tmp/reality-124-invoice-browser/entry-1440.png" });
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  await page.getByText("Remaining after this invoice", { exact: true }).first().waitFor();
  assert.equal(prepared.arguments.gross_amount, "301");
  assert.deepEqual(prepared.arguments.lines, [
    { order_line_id: "line", quantity: "2", gross_amount: "101" },
    { order_line_id: "line2", quantity: "3", gross_amount: "102" },
  ]);
  await page.getByText("Office chair", { exact: true }).first().waitFor();
  await mkdir("/private/tmp/reality-124-invoice-browser", { recursive: true });
  for (const lang of ["en", "de", "nl", "es"])
    for (const width of [390, 1440])
      for (const theme of ["light", "dark"]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.goto(
          (process.env.UNIFIED_BASE_URL || "http://localhost:5177") +
            "/app/finance?tenant=company&proposal=invoice",
        );
        await page.locator("#invoice-title").waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        await page.screenshot({
          path: `/private/tmp/reality-124-invoice-browser/${lang}-${width}-${theme}.png`,
        });
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
        );
      }
  language = "en";
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://localhost:5177") +
      "/app/finance?tenant=company&proposal=invoice",
  );
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByLabel("Order line", { exact: true }).nth(1).waitFor();
  assert.equal(await page.getByLabel("Order line", { exact: true }).count(), 2);
  assert.equal(await page.getByLabel("Order line", { exact: true }).nth(1).inputValue(), "line2");
  assert.equal(
    await page.getByLabel("Stated line amount", { exact: true }).nth(1).inputValue(),
    "102",
  );
  assert.equal(await page.getByLabel("Stated invoice amount", { exact: true }).inputValue(), "301");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).click();
  await page.getByRole("link", { name: "Open invoice", exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.locator("[data-action-launcher] > summary").click();
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "New customer invoice", exact: true }).last().click();
  await page.getByLabel("Invoice type", { exact: true }).selectOption("supplier_invoice_record");
  await page.getByLabel("Order", { exact: true }).selectOption("order");
  await page.getByLabel("Order line", { exact: true }).selectOption("line");
  await page.getByLabel("Invoice number", { exact: true }).fill("SUP-120");
  await page.getByLabel("Quantity", { exact: true }).fill("3");
  await page.getByLabel("Stated line amount", { exact: true }).fill("299");
  await page.getByLabel("Stated invoice amount", { exact: true }).fill("299");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  assert.equal(await page.getByLabel("Invoice number", { exact: true }).inputValue(), "SUP-120");
  assert.equal(
    await page.getByLabel("Invoice type", { exact: true }).inputValue(),
    "supplier_invoice_record",
  );
  await page.getByLabel("Quantity", { exact: true }).fill("2");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  assert.equal(prepared.tool, "supplier_invoice_record");
  assert.equal(prepared.arguments.lines[0].quantity, "2");
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://localhost:5177") + "/app/decisions?tenant=company",
  );
  await page.locator("[data-work-list=decisions] [data-work-row]").first().click();
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await page.locator("#invoice-title").waitFor();
  await page.goto(
    (process.env.UNIFIED_BASE_URL || "http://localhost:5177") + "/app/copilot?tenant=company",
  );
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await page.locator("#invoice-title").waitFor();
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  await page.getByRole("dialog").getByText("Rejected", { exact: true }).waitFor();
  assert.deepEqual(errors, []);
  console.log(
    "PASS invoice entry, stated amount, localized responsive review and lost-response recovery",
  );
} catch (error) {
  console.error(errors);
  console.error("Failure URL:", page.url());
  console.error("Failure body:", (await page.locator("body").innerText()).slice(0, 3000));
  await page.screenshot({ path: "/private/tmp/reality-124-invoice-browser-error.png" });
  throw error;
} finally {
  await browser.close();
}
