// Stateful intercepted transport; PostgreSQL tests prove actual business mutations.
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
const PLACE = "party_delivery_hold",
  RELEASE = "party_delivery_hold_release";
let language = "en",
  holds = [],
  latest,
  prepares = [],
  confirmations = 0,
  reconciles = 0,
  losePrepare = true,
  loseConfirm = false;
const proposals = new Map(),
  requests = new Map(),
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const party = {
  id: "customer",
  family: "customer",
  name: "Müller",
  type: "customer",
  roles: ["customer"],
  is_active: true,
  expected_revision: "current",
};
const pager = { number: 1, size: 25, total: 1, pages: 1, has_previous: false, has_next: false };
const own = {
  id: "own",
  scope: "commitment",
  reason: "manual_review",
  note: "Keep this delivery paused",
};
const row = () => ({
  id: "outgoing",
  type: "customer_delivery",
  tenant_id: "company",
  counterparty: "Müller",
  party_id: "customer",
  item_id: "lamp",
  item: "Desk lamp",
  unit: "pcs",
  location_id: "main",
  location: "Main warehouse",
  promised: "8",
  reserved: "2",
  fulfilled: "0",
  open: "8",
  status: "open",
  blockers: [
    own,
    ...holds.map((h) => ({ id: h.id, scope: "party", reason: h.reason_code, note: h.note })),
  ],
});
const context = () => ({
  party,
  holds: structuredClone(holds),
  reasons: ["manual_review", "credit_check", "other"],
});
const review = (tool, intent) => ({
  token: "exact",
  intent,
  state: { party, holds: structuredClone(holds) },
  effect: tool === PLACE ? { holds_set: "1" } : { holds_released: String(holds.length) },
});
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
    return reply({
      tenants: [
        { id: "company", name: "Northstar" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: "company",
    });
  if (p.endsWith("/application-reference"))
    return reply({
      commands: [
        {
          service: "hold_party_delivery",
          related_services: ["release_party_delivery_hold"],
          mode: "mutation",
          adapters: ["Web"],
        },
      ],
      workspaces: [],
    });
  if (p.endsWith("/delivery-work")) return reply({ items: [row()], page: pager });
  if (p.includes("/delivery-work/"))
    return reply({
      case: row(),
      inventory: { physical: "20", reserved: "2", available: "18", unit: "pcs" },
      links: [],
      history: { items: [], has_more: false },
      hold_reasons: ["manual_review", "credit_check", "other"],
      observation: {},
    });
  if (p.endsWith("/master-data")) {
    const q = u.searchParams.get("q"),
      number = Number(u.searchParams.get("page") || 1);
    return reply({
      items: q === "missing" ? [] : [party],
      page:
        q === "paging"
          ? {
              ...pager,
              number,
              pages: 2,
              total: 26,
              has_next: number === 1,
              has_previous: number === 2,
            }
          : pager,
    });
  }
  if (p.includes("/master-data/customer/")) return reply(party);
  if (p.includes("/customer-holds/")) return reply(context());
  if (p.endsWith("/delivery-actions/prepare")) {
    const body = req.postDataJSON();
    prepares.push(body);
    assert.ok([PLACE, RELEASE].includes(body.tool));
    if (requests.has(body.request_id)) latest = requests.get(body.request_id);
    else {
      const intent = {
        ...body.arguments,
        ...(body.tool === PLACE ? { note: String(body.arguments.note || "").trim() } : {}),
      };
      latest = {
        id: `hold-${proposals.size + 1}`,
        tool: body.tool,
        status: "proposed",
        intent,
        review: review(body.tool, intent),
        receipt: null,
        verification: "pending",
        links: [],
        observation: null,
        observation_error: null,
      };
      requests.set(body.request_id, latest);
      proposals.set(latest.id, latest);
    }
    if (losePrepare) {
      losePrepare = false;
      return route.abort("failed");
    }
    return reply(latest);
  }
  if (p.includes("/change-proposals/") && p.endsWith("/approve")) {
    const value = proposals.get(p.split("/change-proposals/")[1].split("/")[0]);
    assert.deepEqual(req.postDataJSON(), { review_token: "exact", confirmed: true });
    confirmations++;
    if (value.tool === PLACE)
      holds = [
        {
          id: `placed-${confirmations}`,
          party_id: "customer",
          hold_type: "delivery",
          reason_code: value.intent.reason_code,
          note: value.intent.note,
          created_by: "human",
          created_at: "2026-09-08T10:00:00Z",
        },
      ];
    else holds = [];
    value.status = loseConfirm ? "executing" : "executed";
    value.verification = loseConfirm ? "recorded_unsettled" : "verified";
    value.links = [
      { kind: "party", id: "customer" },
      { kind: "business_event", id: `event-${confirmations}` },
    ];
    value.receipt = { records: [{ family: "party_hold", id: "held" }] };
    if (loseConfirm) {
      loseConfirm = false;
      return route.abort("failed");
    }
    return reply({ id: value.id, status: value.status, output: value.receipt });
  }
  if (p.includes("/change-proposals/") && p.endsWith("/reject")) {
    const value = proposals.get(p.split("/change-proposals/")[1].split("/")[0]);
    value.status = "rejected";
    return reply(value);
  }
  if (p.includes("/delivery-actions/")) {
    const value = proposals.get(p.split("/delivery-actions/")[1].split("/")[0]);
    if (p.endsWith("/review") && !value.review) value.review = review(value.tool, value.intent);
    if (p.endsWith("/reconcile")) {
      reconciles++;
      value.status = "executed";
      value.verification = "verified";
    }
    return reply({ ...value, observation: context() });
  }
  if (p.endsWith("/change-proposals"))
    return reply({
      items: latest
        ? [{ ...latest, input: latest.intent, created_at: "2026-09-08T10:00:00Z" }]
        : [],
      page: pager,
    });
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "conversation", title: "Customer hold" }],
      active_session_id: "conversation",
      messages: [],
      proposals: latest ? [{ ...latest, input: latest.intent }] : [],
      suggestions: [],
      has_archived: false,
    });
  if (p.includes("/inspector/"))
    return reply({
      title: "Customer evidence",
      subtitle: "Müller",
      meaning: "Exact customer",
      sections: [],
      technical_rows: [],
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
const dialog = page.getByRole("dialog");
const casePage = () => page.goto(`${base}/app/work?tenant=company&commitment=outgoing`);
const fill = async () => {
  await dialog.getByLabel("Hold reason", { exact: true }).selectOption("credit_check");
  await dialog.getByLabel("Hold note (optional)", { exact: true }).fill("Check <credit> & contact");
};
const layouts = async (stage) => {
  for (const lang of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.reload();
        await dialog.locator("h3").first().waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        assert.ok(await dialog.evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
        await page.screenshot({
          path: `/private/tmp/reality-133-browser/${stage}-${lang}-${theme}-${width}.png`,
          fullPage: true,
          animations: "disabled",
        });
      }
  language = "en";
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.reload();
};
try {
  await mkdir("/private/tmp/reality-133-browser", { recursive: true });
  await casePage();
  await page.getByRole("button", { name: "Place customer delivery hold", exact: true }).click();
  await fill();
  await page.screenshot({
    path: "/private/tmp/reality-133-browser/form-en.png",
    fullPage: true,
    animations: "disabled",
  });
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await dialog.getByRole("button", { name: "Recover review", exact: true }).waitFor();
  assert.equal(confirmations, 0);
  await page.reload();
  await page.getByRole("button", { name: "Place customer delivery hold", exact: true }).click();
  await dialog.getByRole("button", { name: "Recover review", exact: true }).click();
  await page.waitForURL(/proposal=hold-1/);
  assert.deepEqual(prepares[0], prepares[1]);
  assert.equal(proposals.size, 1);
  await layouts("place");
  await dialog.getByRole("button", { name: "Confirm customer hold", exact: true }).click();
  await dialog.getByText("Customer hold recorded", { exact: true }).waitFor();
  assert.equal(confirmations, 1);
  await dialog.getByRole("button", { name: "Inspect customer", exact: true }).click();
  await page.getByRole("heading", { name: "Customer evidence", exact: true }).waitFor();
  await casePage();
  await page.getByRole("button", { name: "Release customer delivery hold", exact: true }).click();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/proposal=hold-2/);
  assert.deepEqual(prepares.at(-1).arguments, { party_id: "customer" });
  await layouts("release");
  loseConfirm = true;
  await dialog.getByRole("button", { name: "Confirm customer hold release", exact: true }).click();
  await dialog.getByRole("button", { name: "Check status", exact: true }).waitFor();
  assert.equal(confirmations, 2);
  await page.reload();
  await dialog.getByRole("button", { name: "Recover recorded result", exact: true }).click();
  await dialog.getByText("Customer hold released", { exact: true }).waitFor();
  assert.equal(reconciles, 1);
  assert.equal(confirmations, 2);
  await page.goto(`${base}/app/decisions?tenant=company&proposal=hold-1`);
  await dialog.getByText("Customer hold recorded", { exact: true }).waitFor();
  await dialog.getByText("This customer has no active delivery hold.", { exact: true }).waitFor();
  await casePage();
  await page.getByText("Keep this delivery paused", { exact: true }).waitFor();
  assert.equal(await page.getByText("Customer-wide hold", { exact: true }).count(), 0);
  await page.goto(`${base}/app/master-data?tenant=company&family=customer&record=customer`);
  await page.getByRole("button", { name: "Customer delivery holds", exact: true }).click();
  await fill();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/decisions.*proposal=hold-3/);
  await dialog.getByRole("button", { name: "Discard proposal", exact: true }).click();
  await dialog
    .getByText("Proposal discarded. The hold was not changed.", { exact: true })
    .waitFor();
  await casePage();
  await page.getByText("Actions", { exact: true }).first().click();
  await page
    .locator("details[open]")
    .getByRole("button", { name: "Place customer delivery hold", exact: true })
    .click();
  await dialog.getByLabel("Search customers", { exact: true }).fill("missing");
  await dialog.getByText("No matching records", { exact: true }).waitFor();
  await dialog.getByLabel("Search customers", { exact: true }).fill("paging");
  await dialog.getByRole("button", { name: "Next", exact: true }).click();
  await dialog.getByText("2 / 2", { exact: true }).waitFor();
  await dialog.getByLabel("Customer", { exact: true }).selectOption("customer");
  await fill();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await page.waitForURL(/proposal=hold-4/);
  await page.goto(`${base}/app/decisions?tenant=company`);
  await page.getByRole("button", { name: "Review proposed changes", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm customer hold", exact: true }).waitFor();
  latest.review = null;
  await page.goto(`${base}/app/copilot?tenant=company`);
  await page.getByRole("button", { name: /Review proposed changes/ }).click();
  await dialog.getByRole("button", { name: "Review change", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm customer hold", exact: true }).waitFor();
  await dialog.getByRole("button", { name: "Discard proposal", exact: true }).click();
  await dialog
    .getByText("Proposal discarded. The hold was not changed.", { exact: true })
    .waitFor();
  assert.equal(confirmations, 2);
  await page.goto(`${base}/app/master-data?tenant=other&family=customer&record=customer`);
  assert.equal(await dialog.count(), 0);
  await page.getByRole("button", { name: "Customer delivery holds", exact: true }).click();
  await dialog.getByLabel("Hold note (optional)", { exact: true }).waitFor();
  assert.equal(await dialog.getByLabel("Hold note (optional)", { exact: true }).inputValue(), "");
  await page.keyboard.press("Escape");
  assert.equal(await dialog.count(), 0);
  assert.equal(
    await page
      .getByRole("button", { name: "Customer delivery holds", exact: true })
      .evaluate((el) => el === document.activeElement),
    true,
  );
  assert.deepEqual(errors, []);
  console.log(
    "PASS: five customer-hold entries, placement/release scope and retained own hold, empty/paged customers, lost prepare request recovery, lost release confirmation/reconciliation without replay, historical proof, raw Chat review, reject/company/keyboard and 32 localized light/dark responsive reviews.",
  );
} catch (error) {
  console.error(await page.locator("body").innerText());
  console.error(errors);
  throw error;
} finally {
  await browser.close();
}
