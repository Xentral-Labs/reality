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
  id: "incoming",
  type: "supplier_delivery",
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
        effect: release ? { released: "6" } : { received: prepared.arguments.quantity },
        state: { case: row, inventory, reservation },
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
    return reply({ id: proposal.id, status: "executed", output: proposal.receipt });
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.includes("/change-proposals")) return reply({ items: [], page: pager });
  return reply({ detail: "Fixture unavailable" }, 404);
});
try {
  // FR-006 regression: field spacing and useful pagination in the global form.
  await mkdir("/private/tmp/reality-116-browser", { recursive: true });
  for (const multiple of [false, true]) {
    multiplePages = multiple;
    await page.goto(`${base}/app/warehouse?tenant=ops&warehouse_view=reservations`);
    await page.locator("[data-action-launcher] > summary").click();
    await page
      .locator("details[open]")
      .getByRole("button", { name: "Release reservation", exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog.locator("select option").nth(1).waitFor({ state: "attached" });
    assert.equal(
      await dialog.getByRole("button", { name: "Previous", exact: true }).count(),
      multiple ? 1 : 0,
    );
    assert.equal(
      await dialog.getByRole("button", { name: "Next", exact: true }).count(),
      multiple ? 1 : 0,
    );
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      const gap = await dialog.evaluate((node) => {
        const labels = node.querySelectorAll("form > label");
        return labels[1].getBoundingClientRect().top - labels[0].getBoundingClientRect().bottom;
      });
      assert.ok(gap >= 15, `Field gap: ${gap}`);
      if (multiple) {
        const next = dialog.getByRole("button", { name: "Next", exact: true });
        const previous = dialog.getByRole("button", { name: "Previous", exact: true });
        assert.ok(Math.abs((await next.boundingBox()).y - (await previous.boundingBox()).y) < 1);
      }
      await page.screenshot({
        path: `/private/tmp/reality-116-browser/pagination-${multiple}-${width}.png`,
        fullPage: true,
      });
    }
    if (multiple) {
      await dialog.getByRole("button", { name: "Next", exact: true }).click();
      await dialog.getByText("2 / 2", { exact: true }).waitFor();
      assert.equal(
        await dialog.getByRole("button", { name: "Next", exact: true }).isDisabled(),
        true,
      );
      await dialog.getByRole("button", { name: "Previous", exact: true }).click();
      await dialog.getByText("1 / 2", { exact: true }).waitFor();
    }
  }
  multiplePages = false;
  if (process.env.ACTION_LAYOUT_ONLY === "1") {
    assert.deepEqual(errors, []);
    console.log(
      "PASS: single-page navigation hidden; multi-page navigation works; field gaps and aligned controls at 390/1440px.",
    );
    await browser.close();
    process.exit(0);
  }
  await page.goto(`${base}/app/orders-deliveries?tenant=ops&delivery_type=supplier_delivery`);
  await page.getByRole("button", { name: "Receive goods", exact: true }).click();
  await page.getByRole("textbox", { name: "Quantity", exact: true }).fill("3");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  assert.deepEqual(prepared.arguments, {
    movement_type: "receipt",
    commitment_id: "incoming",
    item_id: "lamp",
    to_location_id: "main",
    quantity: "3",
  });
  assert.equal(confirmations, 0);
  await page.waitForURL(/proposal=receipt-proposal/);
  await page.reload();
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByRole("textbox", { name: "Quantity", exact: true }).fill("2");
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/proposal=receipt-proposal-2/);
  assert.equal(prepared.arguments.movement_type, "receipt");
  assert.equal(prepared.arguments.quantity, "2");
  await mkdir("/private/tmp/reality-116-browser", { recursive: true });
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  await page.screenshot({
    path: "/private/tmp/reality-116-browser/receipt-review.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Confirm change", exact: true }).click();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.goto(`${base}/app/warehouse?tenant=ops&warehouse_view=reservations`);
  // The header bar offers the same action; this step starts it from the register row.
  await page.getByRole("button", { name: "Release reservation", exact: true }).last().click();
  assert.equal(await page.getByRole("textbox", { name: "Quantity", exact: true }).count(), 0);
  await page.getByRole("button", { name: "Review change", exact: true }).click();
  assert.deepEqual(prepared.arguments, { reservation_id: "reservation" });
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  await page.waitForURL(/proposal=release-proposal/);
  for (const lang of ["en", "de", "nl", "es"])
    for (const width of [390, 1440])
      for (const dark of [false, true]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.reload();
        await page.locator("dialog[open] pre").waitFor({ state: "attached" });
        await page.evaluate(
          (d) => document.documentElement.setAttribute("data-theme", d ? "dark" : "light"),
          dark,
        );
        await page.screenshot({
          path: `/private/tmp/reality-116-browser/release-${lang}-${width}-${dark}.png`,
          fullPage: true,
        });
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      }
  language = "en";
  await page.reload();
  await page.getByRole("button", { name: "Confirm change", exact: true }).click();
  assert.equal(confirmations, 2);
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.locator("[data-action-launcher] > summary").click();
  await page.getByRole("button", { name: "Release reservation", exact: true }).last().waitFor();
  await page.getByRole("button", { name: "Receive goods", exact: true }).click();
  await page.getByRole("textbox", { name: "Search deliveries", exact: true }).fill("missing");
  await page.getByText("No matching records", { exact: true }).waitFor();
  await mkdir("/private/tmp/reality-116-browser", { recursive: true });
  for (const width of [390, 1440])
    for (const dark of [false, true]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(
        (d) => document.documentElement.setAttribute("data-theme", d ? "dark" : "light"),
        dark,
      );
      await page.screenshot({
        path: `/private/tmp/reality-116-browser/form-${width}-${dark}.png`,
        fullPage: true,
      });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    }
  assert.deepEqual(errors, []);
  console.log(
    "Receipt/release register, launcher, review, reload, confirmation and layout passed.",
  );
} catch (error) {
  console.error(await page.locator("body").innerText());
  throw error;
} finally {
  await browser.close();
}
