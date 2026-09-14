import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
// Stateful transport fixture. PostgreSQL tests independently prove actual business effects.
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
  count = 0,
  confirmations = 0,
  prepareRequests = [],
  losePrepare = true,
  loseConfirm = true,
  reconciles = 0;
const errors = [],
  requests = new Map();
page.on("pageerror", (e) => errors.push(e.message));
const pager = { number: 1, size: 50, total: 0, pages: 1, has_next: false, has_previous: false };
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    p = u.pathname;
  const reply = (value, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(value) });
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
    return reply({
      tenants: [
        { id: "company", name: "Northstar" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: "company",
    });
  if (p.endsWith("/application-reference")) return reply(discoveryReference);
  if (p.includes("/warehouse/"))
    return reply({
      items: [],
      page: pager,
      scope: { view: "stock" },
      observed_at: "2026-09-08T10:00:00Z",
    });
  if (p.endsWith("/suggestions/items"))
    return reply({
      items:
        u.searchParams.get("q") === "missing"
          ? []
          : [{ value: "lamp", label: "Desk lamp", description: "LAMP" }],
    });
  if (p.endsWith("/suggestions/locations"))
    return reply({ items: [{ value: "main", label: "Main warehouse", description: "Warehouse" }] });
  if (p.endsWith("/delivery-actions/prepare")) {
    const body = req.postDataJSON();
    prepareRequests.push(body);
    assert.equal(body.tool, "movement_create");
    assert.equal(body.arguments.movement_type, "opening_stock");
    if (requests.has(body.request_id)) proposal = requests.get(body.request_id);
    else {
      proposal = {
        id: `opening-${++count}`,
        tool: "movement_create",
        movement_type: "opening_stock",
        status: "proposed",
        intent: body.arguments,
        review: {
          token: "exact",
          intent: body.arguments,
          state: {
            item: { id: "lamp", name: "Desk lamp", unit: "pcs" },
            location: { id: "main", name: "Main warehouse" },
            physical: "10",
            reserved: "2",
          },
          effect: { added: "5.25", physical_after: "15.25", reserved_after: "2" },
        },
        receipt: null,
        verification: "pending",
        links: [],
        observation: null,
        observation_error: null,
      };
      requests.set(body.request_id, proposal);
    }
    if (losePrepare) {
      losePrepare = false;
      return route.abort("failed");
    }
    return reply(proposal);
  }
  if (p.endsWith("/approve")) {
    const body = req.postDataJSON();
    assert.equal(body.confirmed, true);
    assert.equal(body.review_token, "exact");
    confirmations++;
    proposal.status = loseConfirm ? "executing" : "executed";
    proposal.verification = loseConfirm ? "recorded_unsettled" : "verified";
    proposal.links = [
      { kind: "movement", id: "movement" },
      { kind: "business_event", id: "event" },
    ];
    proposal.observation = { physical: "15.25", reserved: "2" };
    if (loseConfirm) {
      loseConfirm = false;
      return route.abort("failed");
    }
    return reply({
      id: proposal.id,
      status: proposal.status,
      output: { records: [{ family: "movement", id: "movement" }] },
    });
  }
  if (p.endsWith("/reconcile")) {
    reconciles++;
    proposal.status = "executed";
    proposal.verification = "verified";
    return reply(proposal);
  }
  if (p.endsWith("/reject")) {
    proposal.status = "rejected";
    return reply(proposal);
  }
  if (p.endsWith("/review") && !proposal.review) {
    proposal.review = {
      token: "exact",
      intent: proposal.intent,
      state: {
        item: { id: "lamp", name: "Desk lamp", unit: "pcs" },
        location: { id: "main", name: "Main warehouse" },
        physical: "10",
        reserved: "2",
      },
      effect: { added: "5.25", physical_after: "15.25", reserved_after: "2" },
    };
  }
  if (p.includes("/delivery-actions/")) return reply(proposal);
  if (p.endsWith("/change-proposals"))
    return reply({
      items: proposal
        ? [{ ...proposal, input: proposal.intent, created_at: "2026-09-08T10:00:00Z" }]
        : [],
      page: { ...pager, total: 1 },
    });
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "conversation", title: "Opening" }],
      active_session_id: "conversation",
      messages: [],
      proposals: proposal ? [{ ...proposal, input: proposal.intent }] : [],
      suggestions: [],
      has_archived: false,
    });
  if (p.includes("/inspector/"))
    return reply({
      title: "Opening movement",
      subtitle: "Manual declaration",
      meaning: "Movement recorded",
      sections: [],
      technical_rows: [],
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
const dialog = page.getByRole("dialog");
const openWarehouse = async () => {
  await page.goto(`${base}/app/warehouse?tenant=company`);
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "Record opening stock", exact: true }).click();
};
const fill = async () => {
  await dialog.getByLabel("Item", { exact: true }).selectOption("lamp");
  await dialog.getByLabel("Location", { exact: true }).selectOption("main");
  await dialog.getByLabel("Quantity to add", { exact: true }).fill("5.25");
};
try {
  await mkdir("/private/tmp/reality-132-browser", { recursive: true });
  await openWarehouse();
  await dialog.getByLabel("Quantity to add", { exact: true }).waitFor();
  await page.screenshot({
    path: "/private/tmp/reality-132-browser/form-en-light-1440.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 390, height: 1000 });
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  await page.screenshot({
    path: "/private/tmp/reality-132-browser/form-en-dark-390.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
  await dialog.getByLabel("Search Item", { exact: true }).fill("missing");
  await dialog.getByText("No matching records", { exact: true }).waitFor();
  await dialog.getByLabel("Search Item", { exact: true }).fill("");
  await fill();
  await dialog.getByLabel("Occurrence time (optional)", { exact: true }).fill("2026-09-08T10:00");
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await dialog.getByRole("button", { name: "Recover review", exact: true }).waitFor();
  assert.equal(confirmations, 0);
  await page.reload();
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "Record opening stock", exact: true }).click();
  await dialog.getByRole("button", { name: "Recover review", exact: true }).click();
  await dialog.getByText("Reviewed stock effect", { exact: true }).waitFor();
  assert.equal(count, 1);
  assert.deepEqual(prepareRequests[0], prepareRequests[1]);
  assert.equal(
    prepareRequests[0].arguments.occurred_at,
    await page.evaluate(() => new Date("2026-09-08T10:00").toISOString()),
  );
  await page.waitForURL(/proposal=opening/);
  for (const lang of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.reload();
        await dialog.locator("section strong").waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        assert.ok(await dialog.evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
        await page.screenshot({
          path: `/private/tmp/reality-132-browser/review-${lang}-${theme}-${width}.png`,
          fullPage: true,
          animations: "disabled",
        });
      }
  language = "en";
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.reload();
  await dialog.getByRole("button", { name: "Confirm opening stock", exact: true }).click();
  await dialog.getByRole("button", { name: "Check status", exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await page.reload();
  await dialog.getByRole("button", { name: "Recover recorded result", exact: true }).click();
  await dialog.getByText("Opening stock recorded", { exact: true }).waitFor();
  await page.screenshot({
    path: "/private/tmp/reality-132-browser/result-en-1440.png",
    fullPage: true,
    animations: "disabled",
  });
  assert.equal(reconciles, 1);
  assert.equal(confirmations, 1);
  await page.reload();
  await dialog.getByText("Opening stock recorded", { exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Inspect movement", exact: true }).click();
  await page.getByRole("heading", { name: "Opening movement" }).waitFor();
  await page.goto(`${base}/app/warehouse?tenant=company`);
  await page.locator("[data-action-launcher] > summary").click();
  await page
    .locator("details[open]")
    .getByRole("button", { name: "Record opening stock", exact: true })
    .click();
  await fill();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/proposal=opening-2/);
  await page.goto(`${base}/app/decisions?tenant=company`);
  await page.locator("[data-work-list=decisions] [data-work-row]").first().click();
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await dialog.getByRole("heading", { name: "Record opening stock", exact: true }).waitFor();
  proposal.review = null;
  await page.goto(`${base}/app/copilot?tenant=company`);
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await dialog.getByRole("heading", { name: "Record opening stock", exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm opening stock", exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Discard proposal", exact: true }).click();
  await dialog.getByText("Proposal discarded. No stock was recorded.", { exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await page.goto(`${base}/app/warehouse?tenant=other`);
  assert.equal(await dialog.count(), 0);
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await page.getByRole("button", { name: "Record opening stock", exact: true }).click();
  await dialog.getByLabel("Quantity to add", { exact: true }).waitFor();
  assert.equal(await dialog.getByLabel("Quantity to add", { exact: true }).inputValue(), "");
  await page.keyboard.press("Escape");
  assert.equal(await dialog.count(), 0);
  assert.equal(
    await page
      .getByRole("button", { name: "Record opening stock", exact: true })
      .evaluate((el) => el === document.activeElement),
    true,
  );
  assert.deepEqual(errors, []);
  console.log(
    "PASS: opening stock Warehouse/launcher/Chat/Decisions, empty search, persistent lost preparation, exact confirmation, lost-confirm reconciliation without replay, reload/history/Inspector/reject/company isolation and 16 localized responsive reviews.",
  );
} catch (error) {
  console.error(await page.locator("body").innerText());
  console.error(errors);
  throw error;
} finally {
  await browser.close();
}
