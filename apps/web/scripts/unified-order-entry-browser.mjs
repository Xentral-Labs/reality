import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
// Fixture browser behavior; isolated PostgreSQL tests prove business effects.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
let language = "en",
  proposal,
  prepared,
  confirmations = 0,
  count = 0;
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const pager = { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false };
const partyChoices = [
  { value: "our-company", label: "Northstar", description: "company" },
  { value: "customer", label: "Müller", description: "customer" },
  { value: "supplier", label: "Weber", description: "supplier" },
];
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
  if (p.includes("/suggestions/"))
    return reply({
      items: p.endsWith("/parties")
        ? partyChoices
        : p.endsWith("/items")
          ? [{ value: "lamp", label: "LAMP · Desk lamp", description: "pcs" }]
          : [{ value: "main", label: "Main warehouse", description: "warehouse" }],
      allow_custom: false,
    });
  if (p.endsWith("/documents")) return reply({ items: [], page: pager });
  if (p.endsWith("/deliveries")) return reply({ items: [], page: pager });
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    count++;
    const args = prepared.arguments;
    proposal = {
      id: `order-${count}`,
      tool: "order_create",
      status: "proposed",
      review: {
        token: "exact",
        intent: args,
        state: {
          creation: {
            direction: args.direction,
            document: {
              ...args,
              type: args.direction === "sales" ? "sales_order" : "purchase_order",
            },
            lines: args.lines.map((line) => ({
              ...line,
              unit: line.unit || "pcs",
              description: line.description || "Desk lamp",
            })),
          },
          references: {
            company_party_id: { id: "our-company", name: "Northstar" },
            counterparty_id: {
              id: args.counterparty_id,
              name: args.direction === "sales" ? "Müller" : "Weber",
            },
            location_id: { id: "main", name: "Main warehouse" },
          },
          items: { lamp: { id: "lamp", name: "Desk lamp", sku: "LAMP", unit: "pcs" } },
        },
      },
      receipt: null,
      verification: "pending",
      links: [],
      observation: null,
    };
    return reply(proposal);
  }
  if (p.endsWith("/approve")) {
    confirmations++;
    proposal.status = "executed";
    proposal.verification = "verified";
    proposal.receipt = {
      source_record_id: "source",
      document_id: "document",
      document_line_ids: ["line-a", "line-b"],
      commitment_ids: ["delivery-a", "delivery-b"],
    };
    proposal.observation_error = "Current read temporarily unavailable";
    return reply({ detail: "Response lost after commit" }, 503);
  }
  if (p.endsWith("/reject")) {
    proposal.status = "rejected";
    return reply(proposal);
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/change-proposals"))
    return reply({
      items: proposal
        ? [{ ...proposal, input: proposal.review.intent, created_at: "2026-09-08T10:00:00Z" }]
        : [],
      page: pager,
    });
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "conversation", title: "Correction" }],
      active_session_id: "conversation",
      messages: [],
      proposals: proposal ? [{ ...proposal, input: proposal.review.intent }] : [],
      suggestions: [],
      has_archived: false,
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
try {
  await mkdir("/private/tmp/reality-119-browser", { recursive: true });
  await page.goto(`${base}/app/orders-deliveries?tenant=company&orders_view=customer-orders`);
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "New order", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Company party", { exact: true }).selectOption("our-company");
  await dialog.getByLabel("Customer", { exact: true }).selectOption("customer");
  await dialog.getByLabel("Warehouse", { exact: true }).selectOption("main");
  await dialog.getByLabel("Order number", { exact: true }).fill("SO-119");
  await dialog.getByLabel("Stated order total", { exact: true }).fill("98.73");
  await dialog.getByLabel("Item", { exact: true }).selectOption("lamp");
  await dialog.getByLabel("Quantity", { exact: true }).fill("2");
  await dialog.getByLabel("Unit price", { exact: true }).fill("12.50");
  await dialog.getByLabel("Stated line amount", { exact: true }).fill("24.91");
  await dialog.getByRole("button", { name: "Add line", exact: true }).click();
  await dialog.getByLabel("Item", { exact: true }).nth(1).selectOption("lamp");
  await dialog.getByLabel("Quantity", { exact: true }).nth(1).fill("3");
  await dialog.getByLabel("Unit price", { exact: true }).nth(1).fill("12.50");
  await dialog.getByLabel("Stated line amount", { exact: true }).nth(1).fill("37.11");
  await dialog.getByRole("button", { name: "Add line", exact: true }).click();
  await dialog.getByRole("button", { name: "Remove line", exact: true }).nth(2).click();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/proposal=order/);
  assert.equal(prepared.tool, "order_create");
  assert.equal(prepared.arguments.lines.length, 2);
  assert.equal(prepared.arguments.gross_amount, "98.73");
  assert.equal(confirmations, 0);
  // Canonical richer intent survives a deterministic edit.
  proposal.review.intent.customer_reference = "Keep <original> reference";
  await page.reload();
  await dialog.getByRole("button", { name: "Edit", exact: true }).click();
  await dialog.getByLabel("Quantity", { exact: true }).nth(1).fill("4");
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/proposal=order-2/);
  assert.equal(prepared.arguments.customer_reference, "Keep <original> reference");
  for (const lang of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.reload();
        await dialog.locator("pre").waitFor({ state: "attached" });
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        assert.ok(await dialog.evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
        await page.screenshot({
          path: `/private/tmp/reality-119-browser/review-${lang}-${theme}-${width}.png`,
          fullPage: true,
        });
      }
  language = "en";
  await page.reload();
  await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
  await dialog.getByText("Recorded", { exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await dialog.getByRole("link", { name: "Open order", exact: true }).waitFor();
  assert.match(
    await dialog
      .getByRole("link", { name: /Open delivery/ })
      .first()
      .getAttribute("href"),
    /^\/app\/work\?tenant=company&commitment=delivery-a$/,
  );
  proposal.verification = "unresolved";
  await page.reload();
  await dialog.getByText("Recorded result is not yet verified.", { exact: true }).waitFor();
  assert.equal(await dialog.getByRole("link", { name: "Open order", exact: true }).count(), 0);
  proposal.verification = "verified";
  await dialog.getByRole("button", { name: "Check outcome", exact: true }).click();
  assert.equal(confirmations, 1);
  await page.goto(`${base}/app/orders-deliveries?tenant=company`);
  await page.locator("[data-action-launcher] > summary").click();
  await page
    .locator("details[open]")
    .getByRole("button", { name: "New order", exact: true })
    .click();
  await dialog.getByLabel("Order direction", { exact: true }).selectOption("purchase");
  await dialog.getByLabel("Company party", { exact: true }).selectOption("our-company");
  await dialog.getByLabel("Supplier", { exact: true }).selectOption("supplier");
  await dialog.getByLabel("Warehouse", { exact: true }).selectOption("main");
  await dialog.getByLabel("Order number", { exact: true }).fill("PO-119");
  await dialog.getByLabel("Stated order total", { exact: true }).fill("10");
  await dialog.getByLabel("Item", { exact: true }).selectOption("lamp");
  await dialog.getByLabel("Quantity", { exact: true }).fill("2");
  await dialog.getByLabel("Unit price", { exact: true }).fill("5");
  await dialog.getByLabel("Stated line amount", { exact: true }).fill("10");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: "/private/tmp/reality-119-browser/purchase-form-en-1440.png",
    fullPage: true,
  });
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/proposal=order-3/);
  assert.equal(prepared.arguments.direction, "purchase");
  assert.equal(prepared.arguments.counterparty_id, "supplier");
  assert.equal(confirmations, 1);
  await page.goto(`${base}/app/decisions?tenant=company`);
  await page.locator("[data-work-list=decisions] [data-work-row]").first().click();
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await dialog.getByRole("heading", { name: "New order", exact: true }).waitFor();
  await page.goto(`${base}/app/copilot?tenant=company`);
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await dialog.getByRole("heading", { name: "New order", exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Reject", exact: true }).click();
  await dialog.getByText("Rejected", { exact: true }).waitFor();
  assert.deepEqual(errors, []);
  console.log(
    "PASS: order entry, multi-line editor, exact stated totals, preserved richer intent, four entry points, reload/edit/reject/response-loss recovery, 16 localized responsive reviews.",
  );
} finally {
  await browser.close();
}
