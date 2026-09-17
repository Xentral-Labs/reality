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
const original = {
  id: "movement",
  type: "receipt",
  item_id: "lamp",
  quantity: "10",
  from_location_id: null,
  to_location_id: "main",
  commitment_id: null,
  source_record_id: "source",
  handling_unit_id: null,
  lot_id: null,
  serial_unit_id: null,
  occurred_at: "2026-09-08T10:00:00+00:00",
  resolves_movement_id: null,
  return_announcement_id: null,
};
const row = {
  ...original,
  item: "Desk lamp",
  unit: "pcs",
  sku: "LAMP",
  from_location: null,
  to_location: "Main warehouse",
  correction_role: "normal",
  at: original.occurred_at,
};
const snapshot = {
  movement_id: original.id,
  revision: "revision",
  role: "normal",
  status: "recorded",
  correctable: true,
  original,
  compensation: null,
  replacement: null,
  correction: null,
};
const pool = {
  item_id: "lamp",
  item: "Desk lamp",
  location_id: "main",
  location: "Main warehouse",
  unit: "pcs",
  physical: "10",
  reserved: "0",
  delta: "-3",
  after: "7",
  available_after: "7",
  identities: [],
};
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
  if (p.endsWith("/warehouse/movements"))
    return reply({
      items: [row],
      page: pager,
      scope: { view: "movements" },
      observed_at: original.occurred_at,
    });
  if (p.endsWith("/movements/movement/correction")) return reply(snapshot);
  if (p.endsWith("/delivery-actions/prepare")) {
    prepared = req.postDataJSON();
    count++;
    const replacement = prepared.arguments.replacement || null;
    proposal = {
      id: `correction-${count}`,
      tool: "movement_correct",
      status: "proposed",
      review: {
        token: "exact",
        intent: prepared.arguments,
        effect: {},
        state: {
          correction: {
            movement_id: original.id,
            reason: prepared.arguments.reason,
            original,
            compensation: {
              ...original,
              id: null,
              type: "correction",
              from_location_id: "main",
              to_location_id: null,
              source_record_id: null,
            },
            replacement,
          },
          pools: [
            {
              ...pool,
              after: replacement?.quantity || "0",
              available_after: replacement?.quantity || "0",
              delta: String(Number(replacement?.quantity || 0) - 10),
            },
          ],
          commitments: [],
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
      correction_id: "chain",
      original_movement_id: "movement",
      compensating_movement_id: "inverse",
      replacement_movement_id: "new",
      replayed: false,
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
        ? [{ ...proposal, input: proposal.review.intent, created_at: original.occurred_at }]
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
  await mkdir("/private/tmp/reality-118-browser", { recursive: true });
  await page.goto(`${base}/app/warehouse?tenant=company&warehouse_view=movements`);
  await page.getByRole("button", { name: "Correct movement", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Correction type", { exact: true }).selectOption("replace");
  await dialog.getByLabel("Correct quantity", { exact: true }).fill("7");
  await dialog.getByLabel("Correction reason", { exact: true }).fill("Count <checked> & verified");
  assert.equal(await dialog.getByRole("button", { name: "Next", exact: true }).count(), 0);
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  assert.equal(prepared.tool, "movement_correct");
  assert.equal(prepared.arguments.replacement.quantity, "7");
  assert.equal(prepared.arguments.replacement.source_record_id, "source");
  assert.equal(confirmations, 0);
  await page.waitForURL(/proposal=correction/);
  await page.reload();
  await dialog.getByText("Count <checked> & verified", { exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Edit", exact: true }).click();
  await dialog.getByLabel("Correct quantity", { exact: true }).fill("6");
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  assert.equal(prepared.arguments.replacement.source_record_id, "source");
  assert.equal(prepared.arguments.replacement.quantity, "6");
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
          path: `/private/tmp/reality-118-browser/review-${lang}-${theme}-${width}.png`,
          fullPage: true,
        });
      }
  language = "en";
  await page.reload();
  await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
  await dialog.getByText("Recorded", { exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await dialog.getByText(/Recorded result is separate/).waitFor();
  await dialog.getByRole("button", { name: "Check outcome", exact: true }).click();
  assert.equal(confirmations, 1);
  await page.goto(`${base}/app/warehouse?tenant=company&warehouse_view=movements`);
  await page.locator("[data-action-launcher] > button").click();
  await page
    .locator("details[open]")
    .getByRole("button", { name: "Correct movement", exact: true })
    .click();
  await dialog.getByLabel("Movement", { exact: true }).selectOption("movement");
  await dialog.getByLabel("Correction reason", { exact: true }).fill("Duplicate");
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  assert.ok(!prepared.arguments.replacement);
  await page.goto(`${base}/app/decisions?tenant=company`);
  await page.locator("[data-work-list=decisions] [data-work-row]").first().click();
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await dialog.getByRole("heading", { name: "Correct movement", exact: true }).waitFor();
  await page.goto(`${base}/app/copilot?tenant=company`);
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await dialog.getByRole("heading", { name: "Correct movement", exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Reject", exact: true }).click();
  await dialog.getByText("Rejected", { exact: true }).waitFor();
  assert.equal(confirmations, 1);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: correction Warehouse/launcher/Chat/Decisions, exact preserved references, reverse/replace, no prepare effect, edit/reload/confirm/reject, 16 localized responsive reviews.",
  );
} catch (error) {
  console.error(await page.locator("body").innerText());
  console.error(errors);
  throw error;
} finally {
  await browser.close();
}
