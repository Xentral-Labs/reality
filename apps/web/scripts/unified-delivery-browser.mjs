// HTTP fixture responses verify the actual UI; PostgreSQL tests prove the quantities.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
import { reference as discoveryReference } from "./action-discovery-fixture.mjs";
if (!process.env.PLAYWRIGHT_MODULE) throw new Error("Set PLAYWRIGHT_MODULE.");
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const tenant = "tenant_fixture",
  commitment = "commitment_fixture";
let language = "en";
let phase = 0,
  proposed = [],
  messages = [],
  confirmed = 0;
const positions = [
  { reserved: "0", physical: "20", available: "20", fulfilled: "0", open: "12" },
  { reserved: "12", physical: "20", available: "8", fulfilled: "0", open: "12" },
  { reserved: "7", physical: "15", available: "8", fulfilled: "5", open: "7" },
  { reserved: "0", physical: "8", available: "8", fulfilled: "12", open: "0" },
];
const row = () => ({
  type: "customer_delivery",
  id: commitment,
  tenant_id: tenant,
  document_id: null,
  document_line_id: null,
  party_id: "party_fixture",
  counterparty: "Müller",
  item_id: "item_fixture",
  item: "Desk lamp",
  location_id: "location_fixture",
  location: "Main warehouse",
  unit: "pcs",
  promised: "12",
  due_at: null,
  ...positions[phase],
  status: phase === 3 ? "fulfilled" : "open",
  blockers: [],
});
const detail = () => ({
  case: row(),
  inventory: {
    item_id: "item_fixture",
    location_id: "location_fixture",
    unit: "pcs",
    ...positions[phase],
  },
  links: [],
  history: { items: [], has_more: false, next_cursor: null },
  observation: { observed_at: "2026-09-07T12:00:00Z", evidence_available: false },
});
const pager = (total) => ({
  number: 1,
  size: 50,
  total,
  pages: 1,
  has_next: false,
  has_previous: false,
});
const prepare = (tool, args) => {
  const proposal = {
    id: `proposal_${proposed.length + 1}`,
    tool,
    status: "proposed",
    review: {
      token: `review_${proposed.length + 1}`,
      intent: args,
      effect:
        tool === "reserve"
          ? { requested: "12", applied: "12", shortage: "0" }
          : { shipped: args.quantity },
      state: { case: row(), inventory: detail().inventory },
    },
    receipt: null,
    verification: "pending",
    links: [],
    observation: detail(),
    observation_error: null,
  };
  proposed.push(proposal);
  return proposal;
};
await page.route("**/api/**", async (route) => {
  const request = route.request(),
    url = new URL(request.url()),
    path = url.pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (url.pathname.endsWith("/application-reference")) return reply(discoveryReference);
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: tenant, name: "Northstar Commerce" }],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/analytics"))
    return reply({
      position: {
        open: 1,
        fully_reserved: 0,
        needs_reservation: 1,
        overdue: 0,
        unknown_due: 1,
        coverage_percent: "0",
      },
      series: [],
    });
  if (path.endsWith("/dashboard"))
    return reply({
      tenant: { id: tenant, name: "Northstar Commerce" },
      totals: {
        open_commitments: phase === 3 ? 0 : 1,
        open_deliveries: phase === 3 ? 0 : 1,
        exceptions: 0,
        pending_decisions: proposed.filter((p) => p.status === "proposed").length,
      },
      exceptions: [],
      inventory: [],
      facts: [],
      capabilities: {},
    });
  if (path.endsWith("/delivery-work"))
    return reply({ items: phase === 3 ? [] : [row()], page: pager(phase === 3 ? 0 : 1) });
  if (path.endsWith(`/delivery-work/${commitment}`)) return reply(detail());
  if (path.includes("/inspector/"))
    return reply({
      title: "Delivery evidence",
      subtitle: "Müller · Desk lamp",
      meaning: "Derived from linked records",
      sections: [],
      technical_rows: [],
      source_payload: '{"external":"<script>alert(1)</script>"}',
    });
  if (path.endsWith("/delivery-references")) return reply({ items: [], has_more: false });
  if (path.endsWith("/delivery-actions/prepare")) {
    const body = request.postDataJSON();
    assert.ok(body.request_id);
    assert.equal(body.arguments.commitment_id, commitment);
    return reply(prepare(body.tool, body.arguments));
  }
  if (path.includes("/delivery-actions/proposal_")) {
    const id = path.split("/delivery-actions/")[1].split("/")[0];
    return reply(proposed.find((p) => p.id === id));
  }
  if (path.endsWith("/approve")) {
    const proposal = proposed.find((p) => path.includes(p.id));
    const body = request.postDataJSON();
    assert.equal(body.confirmed, true);
    assert.equal(body.review_token, proposal.review.token);
    if (proposal.status !== "executed") {
      confirmed++;
      phase = proposal.tool === "reserve" ? 1 : proposal.review.intent.quantity === "5" ? 2 : 3;
      proposal.status = "executed";
      proposal.verification = "verified";
      proposal.receipt = { recorded: true };
      proposal.observation = detail();
    }
    return reply({ id: proposal.id, status: proposal.status, output: proposal.receipt });
  }
  if (path.endsWith("/reject")) {
    const proposal = proposed.find((p) => path.includes(p.id));
    proposal.status = "rejected";
    return reply({ id: proposal.id, status: "rejected" });
  }
  if (path.endsWith("/change-proposals")) {
    const items = proposed
      .filter((p) =>
        url.searchParams.get("status") === "history"
          ? p.status !== "proposed"
          : p.status === "proposed",
      )
      .map((p) => ({ ...p, input: p.review.intent, created_at: "2026-09-07T12:00:00Z" }));
    return reply({ items, page: pager(items.length) });
  }
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [{ id: "chat_fixture", title: "Delivery conversation" }],
      active_session_id: "chat_fixture",
      messages,
      proposals: proposed
        .filter((p) => p.status === "proposed")
        .map((p) => ({ ...p, input: p.review.intent })),
      suggestions: [],
      has_archived: false,
    });
  if (path.endsWith("/messages")) {
    const body = request.postDataJSON();
    const tool = body.message.includes("shipment") ? "movement_create" : "reserve";
    const args =
      tool === "reserve"
        ? { commitment_id: commitment, quantity: "12" }
        : {
            movement_type: "shipment",
            commitment_id: commitment,
            item_id: "item_fixture",
            from_location_id: "location_fixture",
            quantity: "5",
          };
    prepare(tool, args);
    messages = [
      { id: "question", role: "user", content: body.message },
      { id: "answer", role: "assistant", content: "The delivery action is ready for your review." },
    ];
    return reply({ user: messages[0], assistant: messages[1] });
  }
  return reply({ detail: `Unexpected fixture request ${path}` }, 404);
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const out = process.env.UNIFIED_SCREENSHOTS || "/private/tmp/reality-107-browser";
await mkdir(out, { recursive: true });
try {
  for (const entry of ["case", "launcher", "chat"])
    for (const tool of ["reserve", "movement_create"]) {
      phase = tool === "reserve" ? 0 : 1;
      proposed = [];
      messages = [];
      confirmed = 0;
      await page.goto(`${base}/app?tenant=${tenant}`);
      await page.locator("[data-home-pulse]").waitFor();
      const action = tool === "reserve" ? "Reserve stock" : "Record shipment";
      if (entry === "case") {
        await page.getByRole("link", { name: "Orders & deliveries", exact: true }).click();
        await page.getByRole("button", { name: "Open commitment", exact: true }).first().click();
        await page.getByRole("button", { name: action, exact: true }).click();
      } else if (entry === "launcher") {
        await page.getByText("Actions", { exact: true }).click();
        await page.getByRole("button", { name: action, exact: true }).click();
      } else {
        if (!(await page.locator("[data-global-chat]").isVisible()))
          await page.getByRole("button", { name: "Show chat", exact: true }).click();
        await page
          .getByRole("textbox", { name: "Ask about your company" })
          .fill(`Prepare ${tool === "reserve" ? "reservation" : "shipment"}`);
        await page.getByRole("button", { name: "Send question" }).click();
        await page.getByRole("button").filter({ hasText: "Review proposed changes" }).click();
      }
      const dialog = page.getByRole("dialog");
      if (entry !== "chat") {
        if (entry === "launcher")
          await dialog
            .getByRole("combobox", { name: "Delivery", exact: true })
            .selectOption(commitment);
        await dialog
          .getByRole("textbox", { name: "Quantity", exact: true })
          .fill(tool === "reserve" ? "12" : "5");
        await dialog.getByRole("button", { name: "Review change", exact: true }).click();
      }
      await dialog.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
      assert.equal(confirmed, 0, "preparation must not execute");
      assert.ok(new URL(page.url()).searchParams.get("proposal"));
      await page.reload();
      await page
        .getByRole("dialog")
        .getByRole("button", { name: "Confirm change", exact: true })
        .click();
      await page.getByRole("dialog").getByRole("status").filter({ hasText: "Recorded" }).waitFor();
      assert.equal(confirmed, 1);
      await page.screenshot({ path: `${out}/${entry}-${tool}.png`, fullPage: true });
      await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
    }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${base}/app/work?tenant=${tenant}&commitment=${commitment}`);
  await page.getByRole("heading", { name: "Müller", exact: true }).waitFor();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: `${out}/delivery-mobile.png`, fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("button", { name: "Explain", exact: true }).click();
  await page.getByRole("dialog").getByRole("heading", { name: "Delivery evidence" }).waitFor();
  await page.getByRole("dialog").getByText("Original source", { exact: true }).click();
  assert.ok((await page.getByRole("dialog").locator("pre").textContent()).includes("<script>"));
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Discuss with Reality", exact: true }).click();
  await page.locator("textarea").waitFor();
  await page.screenshot({ path: `${out}/case-assistant-desktop.png`, fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: `${out}/case-assistant-mobile.png`, fullPage: true });
  // Final fulfillment stays directly accessible after leaving the open worklist.
  phase = 2;
  await page.goto(`${base}/app/work?tenant=${tenant}&commitment=${commitment}`);
  await page.getByRole("button", { name: "Record shipment", exact: true }).click();
  await page.getByRole("dialog").getByRole("textbox", { name: "Quantity", exact: true }).fill("7");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Review change", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm change", exact: true })
    .click();
  await page.getByRole("dialog").getByRole("status").filter({ hasText: "Recorded" }).waitFor();
  assert.equal(phase, 3);
  await page.reload();
  await page.getByRole("dialog").getByRole("status").filter({ hasText: "Recorded" }).waitFor();
  const labels = {
    en: ["Reserve stock", "Review change", "Confirm change", "Discuss with Reality", "Explain"],
    de: [
      "Bestand reservieren",
      "Änderung prüfen",
      "Änderung bestätigen",
      "Mit Reality besprechen",
      "Erklären",
    ],
    nl: [
      "Reserveer voorraad",
      "Wijziging beoordelen",
      "Wijziging bevestigen",
      "Bespreken met Reality",
      "Uitleggen",
    ],
    es: ["Reservar stock", "Revisar cambio", "Confirmar cambio", "Hablar con Reality", "Explicar"],
  };
  for (language of process.env.UNIFIED_SKIP_MATRIX ? [] : ["en", "de", "nl", "es"]) {
    for (const theme of ["light", "dark"]) {
      for (const width of [390, 1440]) {
        phase = 0;
        proposed = [];
        messages = [];
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        const shot = async (state) => {
          assert.ok(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            `${language}/${theme}/${width}/${state} overflows`,
          );
          await page.screenshot({
            path: `${out}/${language}-${theme}-${width}-${state}.png`,
            fullPage: true,
          });
        };
        await page.goto(`${base}/app?tenant=${tenant}`);
        await page.locator("h1").waitFor();
        await shot("home");
        await page.goto(`${base}/app/copilot?tenant=${tenant}`);
        await page.locator("textarea").waitFor();
        await shot("chat");
        await page.goto(`${base}/app/work?tenant=${tenant}&commitment=${commitment}`);
        await page.getByRole("heading", { name: "Müller", exact: true }).waitFor();
        await shot("case");
        // Keyboard opens the exact action, native dialog traps focus and Escape restores it.
        const reserve = page.getByRole("button", { name: labels[language][0], exact: true });
        await reserve.focus();
        await page.keyboard.press("Enter");
        await page.getByRole("dialog").waitFor();
        await page.keyboard.press("Escape");
        await page.getByRole("dialog").waitFor({ state: "hidden" });
        assert.equal(await reserve.evaluate((node) => node === document.activeElement), true);
        await reserve.click();
        await page.getByRole("dialog").locator('input[inputmode="decimal"]').fill("12");
        await page
          .getByRole("dialog")
          .getByRole("button", { name: labels[language][1], exact: true })
          .click();
        await page
          .getByRole("dialog")
          .getByRole("button", { name: labels[language][2], exact: true })
          .waitFor();
        await shot("review");
        await page
          .getByRole("dialog")
          .getByRole("button", { name: labels[language][2], exact: true })
          .click();
        await page.getByRole("dialog").getByRole("status").waitFor();
        await shot("result");
      }
    }
  }
  language = "en";
  phase = 1;
  proposed = [];
  const uncertainProposal = prepare("movement_create", {
    movement_type: "shipment",
    commitment_id: commitment,
    item_id: "item_fixture",
    from_location_id: "location_fixture",
    quantity: "5",
  });
  uncertainProposal.status = "executing";
  uncertainProposal.verification = "unknown";
  const beforeRecovery = confirmed;
  await page.goto(`${base}/app/decisions?tenant=${tenant}&proposal=${uncertainProposal.id}`);
  await page.getByRole("dialog").getByRole("status").filter({ hasText: "Do not repeat" }).waitFor();
  assert.equal(
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Confirm change", exact: true })
      .count(),
    0,
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Check outcome", exact: true })
    .click();
  assert.equal(confirmed, beforeRecovery);
  await page.screenshot({ path: `${out}/unknown-outcome.png`, fullPage: true });
  uncertainProposal.status = "executed";
  uncertainProposal.receipt = { recorded: true };
  uncertainProposal.observation = null;
  uncertainProposal.observation_error = "Current observation unavailable";
  await page.reload();
  await page.getByRole("dialog").getByRole("status").filter({ hasText: "Recorded" }).waitFor();
  await page
    .getByRole("dialog")
    .getByRole("alert")
    .filter({ hasText: "Current observation unavailable" })
    .waitFor();
  assert.equal(confirmed, beforeRecovery);
  await page.screenshot({ path: `${out}/observation-unavailable.png`, fullPage: true });
  assert.deepEqual(errors, []);
  console.log(
    "PASS: both delivery actions from case, launcher and Chat; reload before confirmation; no preparation effects; final fulfillment; safe Inspector; contextual Chat; keyboard focus; matrix (unless explicitly skipped); unresolved and unavailable-observation recovery.",
  );
} finally {
  await browser.close();
}
