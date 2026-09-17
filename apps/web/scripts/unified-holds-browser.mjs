import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
// HTTP fixtures verify presentation; PostgreSQL stories prove operational effects.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
let language = "en";
let multiplePages = false;
let proposal,
  prepared,
  confirmations = 0,
  prepareCount = 0;
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const pager = { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false };
const row = {
  id: "outgoing",
  type: "customer_delivery",
  tenant_id: "ops",
  counterparty: "Weber",
  party_id: "supplier",
  item_id: "lamp",
  item: "Desk lamp",
  unit: "pcs",
  location_id: "main",
  location: "Main warehouse",
  promised: "8",
  reserved: "0",
  fulfilled: "0",
  open: "8",
  status: "open",
  blockers: [],
};
const reservation = {
  id: "reservation",
  item_id: "lamp",
  item: "Desk lamp",
  sku: "LAMP",
  unit: "pcs",
  quantity: "6",
  status: "active",
  location: "Main warehouse",
  commitment_id: "outgoing",
  delivery_id: "outgoing",
};
const inventory = {
  item_id: "lamp",
  location_id: "main",
  unit: "pcs",
  physical: "20",
  reserved: "6",
  available: "14",
};
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    p = u.pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (p === "/api/auth/me")
    return reply({
      id: "user",
      email: "test@example.test",
      display_name: "Operator",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
    });
  if (p === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "ops", name: "Northstar" }], default_tenant_id: "ops" });
  if (p.endsWith("/application-reference")) return reply(discoveryReference);
  if (p.endsWith("/delivery-work"))
    return reply({ items: u.searchParams.get("q") === "missing" ? [] : [row], page: pager });
  if (p.includes("/delivery-work/"))
    return reply({
      hold_reasons: ["manual_review", "credit_check", "other"],
      case: row,
      inventory,
      links: [],
      history: { items: [], has_more: false },
      observation: {},
    });
  if (p.endsWith("/warehouse/reservations"))
    return reply({
      items: [reservation],
      page: multiplePages
        ? {
            ...pager,
            number: Number(u.searchParams.get("page") || 1),
            pages: 2,
            total: 51,
            has_next: u.searchParams.get("page") !== "2",
            has_previous: u.searchParams.get("page") === "2",
          }
        : pager,
      scope: { view: "reservations" },
      observed_at: "2026-09-07T12:00:00Z",
    });
  if (p.endsWith("/delivery-references")) return reply({ items: [], has_more: false });
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    prepareCount++;
    const release = prepared.tool === "reservation_release";
    proposal = {
      id: `${release ? "release-proposal" : "receipt-proposal"}-${prepareCount}`,
      tool: prepared.tool,
      status: "proposed",
      review: {
        token: "exact",
        intent: prepared.arguments,
        effect: prepared.tool === "commitment_hold" ? { holds_set: "1" } : { holds_released: "1" },
        state: {
          case: row,
          inventory,
          holds: row.blockers
            .filter((r) => r.scope === "commitment")
            .map((r) => ({ ...r, reason_code: r.reason })),
        },
      },
      receipt: null,
      verification: "pending",
      links: [],
      observation: null,
    };
    return reply(proposal);
  }
  if (p.endsWith("/reject")) {
    proposal.status = "rejected";
    return reply(proposal);
  }
  if (p.endsWith("/approve")) {
    confirmations++;
    proposal.status = "executed";
    proposal.receipt = { records: [] };
    row.blockers =
      proposal.tool === "commitment_hold"
        ? [
            {
              id: "own",
              scope: "commitment",
              reason: prepared.arguments.reason_code,
              note: prepared.arguments.note,
            },
          ]
        : row.blockers.filter((r) => r.scope === "party");
    return reply({ id: proposal.id, status: "executed", output: proposal.receipt });
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "conversation", title: "Delivery hold" }],
      active_session_id: "conversation",
      messages: [],
      proposals: proposal ? [{ ...proposal, input: proposal.review.intent }] : [],
      suggestions: [],
      has_archived: false,
    });
  if (p.includes("/change-proposals"))
    return reply({
      items: proposal
        ? [{ ...proposal, input: proposal.review.intent, created_at: "2026-09-08T12:00:00Z" }]
        : [],
      page: pager,
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
try {
  await mkdir("/private/tmp/reality-117-browser", { recursive: true });
  await page.goto(`${base}/app/work?tenant=ops&commitment=outgoing`);
  await page.getByRole("button", { name: "Place delivery hold", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Hold reason", { exact: true }).selectOption("manual_review");
  await dialog
    .getByLabel("Hold note (optional)", { exact: true })
    .fill("Check <address> & contact");
  assert.equal(await dialog.getByRole("button", { name: "Next", exact: true }).count(), 0);
  assert.equal(await dialog.getByLabel("Quantity", { exact: true }).count(), 0);
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  assert.deepEqual(prepared.arguments, {
    commitment_id: "outgoing",
    reason_code: "manual_review",
    note: "Check <address> & contact",
  });
  assert.equal(confirmations, 0);
  await page.waitForURL(/proposal=/);
  await page.reload();
  await dialog.getByText("Check <address> & contact", { exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Edit", exact: true }).click();
  assert.equal(
    await dialog.getByLabel("Hold note (optional)", { exact: true }).inputValue(),
    "Check <address> & contact",
  );
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
  await dialog.getByText("Recorded", { exact: true }).waitFor();
  assert.equal(confirmations, 1);
  row.blockers.push({
    id: "party",
    scope: "party",
    reason: "credit_check",
    note: "Customer-wide credit review",
  });
  await page.goto(`${base}/app/work?tenant=ops&commitment=outgoing`);
  await page.getByText("Customer-wide hold", { exact: true }).waitFor();
  await page.getByText("Check <address> & contact", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Release delivery hold", exact: true }).click();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  assert.deepEqual(prepared.arguments, { commitment_id: "outgoing" });
  await dialog.getByText("Check <address> & contact", { exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
  await dialog.getByText("Recorded", { exact: true }).waitFor();
  assert.equal(row.blockers.length, 1);
  await page.goto(`${base}/app/work?tenant=ops&commitment=outgoing`);
  await page.getByText("Customer-wide credit review", { exact: true }).waitFor();
  assert.equal(
    await page.getByRole("button", { name: "Release delivery hold", exact: true }).count(),
    0,
  );
  const labels = {
    en: "Place delivery hold",
    de: "Lieferung sperren",
    nl: "Levering blokkeren",
    es: "Bloquear entrega",
  };
  for (const lang of Object.keys(labels))
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.goto(`${base}/app/work?tenant=ops&commitment=outgoing`);
        await page.getByRole("button", { name: labels[lang], exact: true }).click();
        await dialog
          .locator("select")
          .nth(1)
          .locator("option")
          .nth(1)
          .waitFor({ state: "attached" });
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        assert.ok(await dialog.evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
        assert.equal(
          await page.evaluate(() => document.documentElement.getAttribute("data-theme")),
          theme,
        );
        await page.screenshot({
          path: `/private/tmp/reality-117-browser/hold-${lang}-${theme}-${width}.png`,
          fullPage: true,
        });
      }
  language = "en";
  await page.goto(`${base}/app/work?tenant=ops`);
  await page.locator("[data-action-launcher] > button").click();
  await page
    .locator("details[open]")
    .getByRole("button", { name: "Release delivery hold", exact: true })
    .waitFor();
  await page
    .locator("details[open]")
    .getByRole("button", { name: "Place delivery hold", exact: true })
    .click();
  await dialog.getByLabel("Delivery", { exact: true }).selectOption("outgoing");
  await dialog.getByLabel("Hold reason", { exact: true }).selectOption("other");
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  assert.equal(prepared.tool, "commitment_hold");
  assert.equal(prepared.arguments.reason_code, "other");
  await page.goto(`${base}/app/decisions?tenant=ops`);
  await page.locator("[data-work-list=decisions] [data-work-row]").first().click();
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await dialog.getByRole("heading", { name: "Place delivery hold", exact: true }).waitFor();
  await page.goto(`${base}/app/copilot?tenant=ops`);
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await dialog.getByRole("heading", { name: "Place delivery hold", exact: true }).waitFor();
  assert.equal(confirmations, 2);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: hold/release case and launcher, reason/note, exact review, edit/reload/confirmation, party scope and 16 localized responsive screenshots.",
  );
} catch (error) {
  console.error(await page.locator("body").innerText());
  console.error(errors);
  await page.screenshot({ path: "/private/tmp/reality-117-browser/failure.png" });
  throw error;
} finally {
  await browser.close();
}
