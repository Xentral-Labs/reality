import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { reference } from "./tool-catalog-fixture.mjs";

const playwrightModule = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const chromium = playwrightModule.chromium ?? playwrightModule.default?.chromium;
if (!chromium) throw new Error("The configured Playwright module does not expose Chromium.");
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
page.setDefaultTimeout(12000);
await page.addInitScript(() => {
  localStorage.setItem(
    "reality:command-palette:v1:operator:company",
    JSON.stringify({
      version: 1,
      favorites: [
        {
          key: "action:commitment_revise",
          target: { kind: "action", id: "commitment_revise" },
        },
      ],
      recents: [],
    }),
  );
});
const errors = [];
const writes = [];
page.on("pageerror", (error) => errors.push(error.message));
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
const commitment = {
  id: "com_browser_250",
  type: "customer_delivery",
  counterparty: "CanisPro Retail",
  party_id: "pty_customer",
  item_id: "itm_food",
  item: "CanisPro Adult 12 kg",
  location_id: "loc_main",
  location: "Main warehouse",
  unit: "bags",
  promised: "10",
  reserved: "10",
  fulfilled: "0",
  open: "10",
  status: "open",
  due_at: "2026-09-25T08:00:00Z",
};
let proposal = null;
const pager = { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false };
const detail = () => ({
  id: "prp_browser_250",
  tool: "commitment_revise",
  status: proposal?.status || "proposed",
  review: {
    token: "review-token-250",
    intent: { commitment_id: commitment.id, quantity: "6" },
    state: { commitment_id: commitment.id, status: "open", quantity: "10", open: "10" },
    effect: {
      revised_open: "6",
      retained_reservation_quantity: "6",
      released_reservation_quantity: "4",
      selection_required: false,
      document_changes: false,
      movement_changes: false,
    },
  },
  receipt:
    proposal?.status === "executed"
      ? { records: [{ family: "commitment_revision", id: "rev_250" }] }
      : null,
  verification: proposal?.status === "executed" ? "verified" : "pending",
  links: proposal?.status === "executed" ? [{ kind: "commitment", id: commitment.id }] : [],
  observation:
    proposal?.status === "executed"
      ? { commitment_id: commitment.id, status: "open", quantity: "6", open: "6" }
      : null,
  observation_error: null,
});

await page.route("**/api/**", async (route) => {
  const request = route.request();
  const path = new URL(request.url()).pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: "company", name: "CanisPro", role: "owner" }],
      default_tenant_id: "company",
    });
  if (path.endsWith("/application-reference")) return reply(reference);
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path.endsWith("/search/query")) {
    const body = request.postDataJSON();
    return reply({
      items: [],
      has_more: false,
      next_cursor: null,
      provider: body.provider,
      scope: "company",
    });
  }
  if (path.endsWith("/delivery-work")) return reply({ items: [commitment], page: pager });
  if (path.endsWith("/delivery-actions/prepare")) {
    const body = request.postDataJSON();
    writes.push({ path, body });
    assert.equal(body.tool, "commitment_revise");
    assert.deepEqual(body.arguments, { commitment_id: commitment.id, quantity: "6", note: "" });
    proposal = { status: "proposed" };
    return reply(detail());
  }
  if (path.endsWith("/change-proposals/prp_browser_250/approve")) {
    const body = request.postDataJSON();
    writes.push({ path, body });
    assert.deepEqual(body, { review_token: "review-token-250", confirmed: true });
    proposal.status = "executed";
    return reply({ id: "prp_browser_250", status: "executed", output: detail().receipt });
  }
  if (path.endsWith("/delivery-actions/prp_browser_250/review")) return reply(detail());
  if (path.endsWith("/delivery-actions/prp_browser_250")) return reply(detail());
  if (path.includes("/warehouse/"))
    return reply({ scope: {}, items: [], page: { ...pager, total: 0 } });
  return reply({ items: [], page: { ...pager, total: 0 } });
});

try {
  await page.goto(`${base}/app/warehouse?tenant=company&warehouse_view=movements`);
  await page.locator("[data-action-launcher] > button").click();
  const menu = page.locator("[data-action-menu]");
  await menu.waitFor({ state: "visible" });
  await menu.locator('[data-palette-key="action:commitment_revise"]').click();
  const dialog = page.getByRole("dialog", { name: "Revise commitment" });
  await dialog.getByLabel("Delivery").selectOption(commitment.id);
  await dialog.getByLabel("Quantity").fill("6");
  await dialog.getByRole("button", { name: "Review change" }).click();
  await dialog.getByText("Expected result", { exact: true }).waitFor();
  assert.match(await dialog.innerText(), /released reservation quantity/i);
  assert.equal(writes.length, 1, "Review must be the first write and must not execute the effect.");
  await dialog.getByRole("button", { name: "Confirm change" }).click();
  await dialog.getByText("Change completed").waitFor();
  await dialog.getByText('"quantity": "6"').waitFor();
  assert.equal(writes.length, 2);
  assert.deepEqual(errors, []);
  console.log("Operational integrity browser review/confirm parity passed.");
} finally {
  await browser.close();
}
