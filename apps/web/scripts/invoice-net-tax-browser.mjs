import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
// Spec 284: an invoice position states net and tax. Intercepted fixture; the service
// check and the recorded detail are proven in test_invoice_stated_amounts.py.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
const shots = "/private/tmp/reality-284-invoice-browser";
await mkdir(shots, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  prepared;
const pager = { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false };
const billing = (id) => ({
  order_line_id: id,
  order_id: "order",
  label: id === "line" ? "Desk lamp" : "Office chair",
  unit: "pcs",
  ordered: "4",
  invoiced: "0",
  remaining: "4",
  can_invoice: true,
  evidence: [],
});
const review = (tool, a) => ({
  id: "invoice",
  tool,
  status: "proposed",
  verification: "pending",
  links: [],
  observation: null,
  review: {
    token: "exact",
    intent: a,
    effect: { debit: "accounts_receivable", credit: "sales_revenue" },
    state: {
      billing: a.lines.map((row) => ({
        ...billing(row.order_line_id),
        requested: row.quantity,
        remaining_after: "2",
      })),
      // As the service does: each position spreads its selection, stated detail included.
      positions: a.lines.map((row) => ({
        ...row,
        item: { name: row.order_line_id === "line" ? "Desk lamp" : "Office chair" },
        line: { unit: "pcs" },
      })),
      creation: { ...a, direction: "sales", currency: "EUR", unit: "pcs" },
      order: { id: "order", number: "ORDER-284" },
      party: { name: "Müller" },
      item: { name: "Desk lamp" },
    },
  },
});
let proposal = review("sales_invoice_record", {
  lines: [
    {
      order_line_id: "line",
      quantity: "2",
      gross_amount: "59.50",
      reality_finance_v1: { net: "50.00", tax: "9.50" },
    },
    { order_line_id: "line2", quantity: "2", gross_amount: "60.00" },
  ],
  gross_amount: "119.50",
  number: "INV-284",
});
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
  if (p.endsWith("/evidence-documents"))
    return reply({
      items: [
        {
          id: "order",
          number: "ORDER-284",
          party: "Müller",
          currency: "EUR",
          gross_amount: "238",
          line_count: 2,
        },
      ],
      page: pager,
    });
  if (p.includes("/inspector/"))
    return reply({
      id: "order",
      evidence_lines: ["line", "line2"].map((id) => ({
        id,
        label: id === "line" ? "Desk lamp" : "Office chair",
        quantity: "4",
        gross_amount: "119",
        unit: "pcs",
        billing: billing(id),
      })),
    });
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    proposal = review(prepared.tool, prepared.arguments);
    return reply(proposal);
  }
  // The decision entry hands delivery-family proposals to their own card.
  if (p.endsWith("/change-proposals/invoice/review"))
    return reply({ id: "invoice", review_kind: "delivery", status: proposal.status });
  if (p.endsWith("/reject")) return reply({ ...proposal, status: "rejected" });
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (
    ["/dashboard", "/activity-volume", "/readiness", "/analytics"].some((path) => p.endsWith(path))
  )
    return reply({ detail: "Home reads are outside this invoice fixture" }, 503);
  return reply({ items: [], totals: [], page: pager });
});
const open = async () => {
  await page.goto(`${base}/app/finance?tenant=company&proposal=invoice`);
  await page.locator("#invoice-title").waitFor();
};
try {
  // FR-005: the review shows the stated net and tax beside the gross of that position.
  await open();
  const stated = page.locator("[data-stated-amounts]");
  await stated.first().waitFor();
  assert.equal(await stated.count(), 1, "only the position that states amounts shows them");
  assert.match(await stated.innerText(), /Net\s+€50\.00.*Tax\s+€9\.50/s);

  for (const lang of ["de", "nl", "es"])
    for (const width of [390, 1440]) {
      language = lang;
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(`${base}/app/finance?tenant=company&proposal=invoice&lang=${lang}`);
      await page.locator("[data-stated-amounts]").waitFor();
      await page.screenshot({ path: `${shots}/review-${lang}-${width}.png` });
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
        true,
        `overflow ${lang} ${width}`,
      );
    }
  language = "de";
  await page.goto(`${base}/app/finance?tenant=company&proposal=invoice&lang=de`);
  assert.match(await page.locator("[data-stated-amounts]").innerText(), /Netto.*Steuer/s);

  // FR-001: editing restores the stated amounts into their position's fields.
  language = "en";
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/app/finance?tenant=company&proposal=invoice&lang=en`);
  await page.locator("#invoice-title").waitFor();
  await page.getByRole("button", { name: "Request changes", exact: true }).click();
  const net = page.getByLabel("Net (as stated on the invoice)", { exact: true });
  const tax = page.getByLabel("Tax (as stated on the invoice)", { exact: true });
  await net.nth(1).waitFor();
  assert.equal(await net.first().inputValue(), "50.00");
  assert.equal(await tax.first().inputValue(), "9.50");
  assert.equal(await net.nth(1).inputValue(), "");

  // The second position states tax only; the first changes its split. Gross stays typed.
  await net.first().fill("49.00");
  await tax.first().fill("10.50");
  await tax.nth(1).fill(" 9.58 ");
  await page.screenshot({ path: `${shots}/entry-1440.png` });
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  assert.deepEqual(prepared.arguments.lines, [
    {
      order_line_id: "line",
      quantity: "2",
      gross_amount: "59.50",
      reality_finance_v1: { net: "49.00", tax: "10.50" },
    },
    {
      order_line_id: "line2",
      quantity: "2",
      gross_amount: "60.00",
      reality_finance_v1: { tax: "9.58" },
    },
  ]);
  assert.equal(await page.locator("[data-stated-amounts]").count(), 2);

  // FR-006: clearing the fields sends a gross-only position without the key.
  await page.getByRole("button", { name: "Request changes", exact: true }).click();
  await net.first().fill("");
  await tax.first().fill("");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  assert.deepEqual(prepared.arguments.lines[0], {
    order_line_id: "line",
    quantity: "2",
    gross_amount: "59.50",
  });
  assert.deepEqual(errors, []);
  console.log("PASS invoice positions state net and tax, review shows them, gross stays typed");
} catch (error) {
  console.error(errors);
  console.error("Failure URL:", page.url());
  console.error("Failure body:", (await page.locator("body").innerText()).slice(0, 3000));
  await page.screenshot({ path: `${shots}/error.png` });
  throw error;
} finally {
  await browser.close();
}
