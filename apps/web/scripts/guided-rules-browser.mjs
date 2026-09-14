import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { reference } from "./action-discovery-fixture.mjs";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
let language = "en",
  role = "owner",
  failWrite = false,
  failSimulation = false;
const errors = [],
  writes = [];
page.on("pageerror", (e) => errors.push(e.message));
const initial = () => ({
  gap: {
    id: "gap",
    question: "Which orders need priority handling?",
    intended_use: "Help warehouse staff find urgent work",
    origin: "web",
    status: "open",
    destination: null,
    revision: 1,
    created_at: "2026-09-10T08:00:00Z",
    updated_at: "2026-09-10T08:00:00Z",
  },
  entries: [],
  rules: [],
});
let detail = initial();
const simulation = {
  sources_considered: 4,
  matches: 2,
  expected_facts: 2,
  invalid_values: 1,
  ambiguous_subjects: 0,
  conflicts: 1,
  not_applicable: 0,
  examples: [
    { source_record_id: "src", external_id: "SO-42", status: "matched" },
    {
      source_record_id: "src",
      external_id: "SO-42",
      status: "conflict",
      detail: "Existing observation differs",
    },
  ],
};
await page.route("**/api/**", (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname,
    body = req.postDataJSON();
  const reply = (value, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(value) });
  if (path === "/api/auth/me")
    return reply({
      id: "rules_user",
      email: "rules@example.test",
      language,
      locale: language === "de" ? "de-DE" : "en-GB",
      timezone: "UTC",
      status: "active",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "company", name: "Rules test", role },
        { id: "other", name: "Other test", role },
      ],
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
      active_session_id: null,
    });
  if (
    path.endsWith("/source-examples/search") &&
    new URL(req.url()).searchParams.get("q") === "missing"
  )
    return reply({ items: [] });
  if (path.endsWith("/source-examples/search"))
    return reply({
      items: [
        {
          source_record_id: "src",
          source_system: "shop",
          source_type: "order",
          external_id: "SO-42",
          received_at: "2026-09-10T08:00:00Z",
          candidates: [{ path: "priority", value: "True", value_type: "boolean" }],
        },
      ],
    });
  if (req.method() === "GET" && path.endsWith("/reality-gaps"))
    return reply({
      items: [{ ...detail.gap, rule_statuses: detail.rules.map((r) => r.status) }],
      total: 1,
      page: 1,
      size: 50,
      counts: { all: 1, open: 1, completed: 0 },
    });
  if (req.method() === "GET" && path.endsWith("/reality-gaps/gap")) return reply(detail);
  if (path.endsWith("/simulate"))
    return reply(
      failSimulation ? { detail: "Simulation unavailable" } : simulation,
      failSimulation ? 503 : 200,
    );
  if (req.method() === "POST" && path.includes("/reality-gaps")) {
    writes.push({ path, body });
    if (failWrite) return reply({ detail: "Unknown write outcome" }, 503);
    if (path.endsWith("/entries"))
      detail.entries.push({
        id: crypto.randomUUID(),
        type: body.entry_type,
        payload: body.payload,
        created_at: "2026-09-10T08:00:00Z",
        actor_type: "user",
      });
    if (path.endsWith("/recommend"))
      detail.entries.push({
        id: "rec",
        type: "recommendation",
        payload: {
          destination: "fact",
          reasons: ["The example records an observation."],
          limitations: ["Manual evidence is not an immutable source."],
        },
      });
    if (path.endsWith("/decide")) detail.gap.destination = body.destination;
    if (path.endsWith("/implementation") && body.draft) {
      const id = `r${detail.rules.length + 1}`;
      detail.entries.push({
        id: `p${id}`,
        type: "implementation_proposal",
        payload: { rule_id: id, draft: body.draft },
      });
      detail.rules.push({
        ...body.draft,
        id,
        version: detail.rules.length + 1,
        status: "draft",
        summary: { last_evaluated_at: null, counts: {}, examples: [], facts: [] },
      });
    }
    if (path.endsWith("/implementation") && !body.draft) {
      detail.gap.status = "implemented";
      detail.entries.push({
        type: "implementation_result",
        payload: {
          kind: "developer_package",
          question: detail.gap.question,
          destination: detail.gap.destination,
          requirements: ["Preserve Source → Evidence → Reality", "Add acceptance and tenant tests"],
        },
      });
    }
    if (path.endsWith("/activate")) {
      detail.rules.forEach(
        (r) => (r.status = r.id === path.split("/").at(-2) ? "active" : "disabled"),
      );
    }
    if (path.endsWith("/disable"))
      detail.rules.find((r) => r.id === path.split("/").at(-2)).status = "disabled";
    if (path.endsWith("/replay"))
      return reply({
        facts_created: body.cursor ? 1 : 2,
        facts_existing: 0,
        not_applicable: 0,
        conflicts: 0,
        failed: 0,
        cumulative: { facts_created: body.cursor ? 3 : 2 },
        next_cursor: body.cursor ? null : "next-page",
        complete: !!body.cursor,
      });
    detail.gap.revision++;
    return reply(detail);
  }
  return reply({ detail: "Fixture read unavailable" }, 503);
});
const go = async (tenant = "company") => {
  await page.goto(
    `${process.env.BASE_URL || "http://localhost:8095"}/app/inspector?tenant=${tenant}&inspector_view=rules`,
  );
  await page.locator("tbody button").first().click();
  await page.getByRole("dialog").waitFor();
};
const confirm = async () => {
  const button = page
    .locator("[data-wizard-confirm]")
    .or(page.getByRole("button", { name: "Confirm", exact: true }));
  await button.click();
  await button.waitFor({ state: "hidden" });
};
try {
  await go();
  assert.equal(
    await page.locator('[data-fact-rule-wizard][data-stage="1"] [data-rule-evidence]').count(),
    1,
  );
  assert.equal(
    await page.getByRole("dialog").getByText("Technical definition", { exact: true }).count(),
    0,
  );
  await page.getByLabel("Find an order or source record", { exact: true }).fill("missing");
  await page
    .locator("[data-rule-evidence]")
    .getByRole("button", { name: "Search", exact: true })
    .click();
  await page.getByText(/No matching source record found/).waitFor();
  await page.getByLabel("Find an order or source record", { exact: true }).fill("SO-42");
  await page
    .locator("[data-rule-evidence]")
    .getByRole("button", { name: "Search", exact: true })
    .click();
  await page.getByRole("button", { name: /Use this value/ }).click();
  assert.equal(writes.length, 0);
  await confirm();
  assert.equal(writes[0].body.payload.source_record_id, "src");
  assert.equal(writes[0].body.payload.displayed_value, "True");
  await page.getByRole("button", { name: "Create recommendation", exact: true }).click();
  await confirm();
  await page.getByRole("button", { name: "Accept recommendation", exact: true }).click();
  await confirm();
  const editor = page.locator("[data-guided-rule-editor]");
  await editor.waitFor();
  assert.equal(await editor.getByLabel("Condition group mode").count(), 0);
  await editor.locator("[data-rule-advanced] > summary").click();
  await editor.getByLabel("Rule name", { exact: true }).fill("order.priority");
  await editor.getByLabel("Characteristic", { exact: true }).fill("order.priority");
  await editor.getByRole("button", { name: "Add group", exact: true }).click();
  await editor.locator("[data-condition-group] details > summary").click();
  await editor.getByLabel("Field", { exact: true }).fill("total");
  await editor.getByLabel("Condition value type").selectOption("decimal");
  await editor.getByLabel("Comparison", { exact: true }).selectOption("greater_than");
  await editor.getByLabel("Value", { exact: true }).fill("1000.0001");
  const count = writes.length;
  await page.getByRole("button", { name: "Review draft", exact: true }).click();
  assert.equal(writes.length, count);
  await confirm();
  assert.equal(detail.rules[0].conditions[0].conditions[0].operand, "1000.0001");
  assert.ok(
    await page.getByRole("button", { name: "Review activation", exact: true }).isDisabled(),
  );
  await page.getByRole("button", { name: "Test saved draft", exact: true }).click();
  await page.getByRole("region", { name: "Simulation result", exact: true }).waitFor();
  await page.getByRole("button", { name: "Review activation", exact: true }).click();
  await page.getByRole("button", { name: "Activate rule", exact: true }).click();
  await confirm();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await go();
  const version = page.locator('[data-rule-version="r1"]');
  await version.getByRole("button", { name: "Replay history", exact: true }).click();
  await confirm();
  await version.getByRole("button", { name: "Continue replay", exact: true }).click();
  await confirm();
  assert.equal(writes.at(-1).body.cursor, "next-page");
  await page.getByText("Replay complete", { exact: true }).waitFor();
  // New version preserves advanced settings from its original implementation proposal.
  detail.entries.find((e) => e.type === "implementation_proposal").payload.draft.normalization = [
    "trim",
  ];
  detail.entries.find((e) => e.type === "implementation_proposal").payload.draft.value_mapping = {
    yes: true,
  };
  await go();
  assert.equal(
    await editor.getByLabel("Characteristic", { exact: true }).inputValue(),
    "order.priority",
  );
  await mkdir("/private/tmp/guided-rules-screens", { recursive: true });
  await page.screenshot({
    path: "/private/tmp/guided-rules-screens/prefilled-desktop.png",
    fullPage: true,
  });
  await page
    .locator('[data-rule-version="r1"]')
    .getByRole("button", { name: "Use as draft", exact: true })
    .click();
  await editor.getByLabel("Characteristic", { exact: true }).fill("order.priority_v2");
  await page
    .locator("[data-rule-footer]")
    .getByRole("button", { name: "Review changes", exact: true })
    .click();
  await confirm();
  assert.deepEqual(detail.rules[1].normalization, ["trim"]);
  assert.deepEqual(detail.rules[1].value_mapping, { yes: true });
  assert.equal(detail.rules[0].status, "active");
  failSimulation = true;
  const v2 = page.locator('[data-rule-version="r2"]');
  await v2.getByRole("button", { name: "Simulate rule", exact: true }).click();
  await page.getByRole("alert").first().waitFor();
  assert.ok(await v2.getByRole("button", { name: "Activate rule", exact: true }).isDisabled());
  failSimulation = false;
  await mkdir("/private/tmp/guided-rules-screens", { recursive: true });
  await page.screenshot({ path: "/private/tmp/guided-rules-screens/desktop.png", fullPage: true });
  // Permission and context reset.
  role = "member";
  await go();
  assert.ok(
    await page
      .locator('[data-rule-version="r1"]')
      .getByRole("button", { name: "Use as draft", exact: true })
      .isDisabled(),
  );
  role = "owner";
  await go();
  await page
    .locator('[data-rule-version="r1"]')
    .getByRole("button", { name: "Disable rule", exact: true })
    .click();
  const before = writes.length;
  await go("other");
  assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).count(), 0);
  assert.equal(writes.length, before);
  failWrite = true;
  await page
    .locator('[data-rule-version="r1"]')
    .getByRole("button", { name: "Disable rule", exact: true })
    .click();
  await confirm();
  await page.getByText(/The result is uncertain/).waitFor();
  assert.ok(
    await page
      .locator('[data-rule-version="r1"]')
      .getByRole("button", { name: "Disable rule", exact: true })
      .isDisabled(),
  );
  failWrite = false;
  const completedDetail = structuredClone(detail);
  detail = initial();
  await go();
  await page
    .locator("[data-rule-evidence] summary")
    .filter({ hasText: "Manual observation" })
    .click();
  await page
    .getByLabel("Manual observation", { exact: true })
    .fill("Email from buyer records priority.");
  const manualBefore = writes.length;
  await page.getByRole("button", { name: "Save manual observation", exact: true }).click();
  assert.equal(writes.length, manualBefore);
  await page.getByRole("button", { name: "Back to editing", exact: true }).click();
  assert.equal(writes.length, manualBefore);
  await page.getByRole("button", { name: "Save manual observation", exact: true }).click();
  await confirm();
  assert.equal(writes.at(-1).body.payload.evidence_kind, "manual_observation");
  await page.getByText("Choose a different outcome", { exact: true }).click();
  await page.getByLabel("Technical model destination", { exact: true }).selectOption("source_only");
  await page
    .getByLabel("Reason", { exact: true })
    .fill("Keep the stated source without a new Fact.");
  await page.getByRole("button", { name: "Use different outcome", exact: true }).click();
  await confirm();
  assert.equal(await page.locator("[data-guided-rule-editor]").count(), 0);
  await page.getByRole("button", { name: "Prepare implementation package", exact: true }).click();
  await confirm();
  assert.equal(writes.at(-1).body.draft, undefined);
  await page
    .getByRole("heading", { name: "Implementation package prepared", exact: true })
    .waitFor();
  // Start a new question through the existing reviewed creation flow.
  await page.keyboard.press("Escape");
  await page.locator("summary").filter({ hasText: "More actions" }).click();
  await page.getByRole("button", { name: "New rule", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByLabel("What should Reality remember?", { exact: true })
    .fill("Which orders need priority handling?");
  await page
    .getByRole("dialog")
    .getByLabel("How will this help your team?", { exact: true })
    .fill("Help warehouse staff find urgent work");
  await page.getByRole("button", { name: "Review goal", exact: true }).click();
  await confirm();
  assert.ok(writes.at(-1).body.idempotency_key);
  detail = completedDetail;
  language = "de";
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(
    `${process.env.BASE_URL || "http://localhost:8095"}/app/inspector?tenant=company&inspector_view=rules`,
  );
  await page.locator("tbody button").first().click();
  await editor.waitFor();
  const footer = await page.locator("[data-rule-footer]").boundingBox();
  assert.ok(footer.y >= 0 && footer.y + footer.height <= 844);
  await page.locator("[data-rule-dialog-body]").evaluate((el) => {
    el.scrollTop = el.scrollHeight;
  });
  const afterScroll = await page.locator("[data-rule-footer]").boundingBox();
  assert.equal(afterScroll.y, footer.y);
  assert.equal(await page.locator("[data-rule-support]").getAttribute("open"), null);
  assert.equal(await page.locator('[data-rule-step="test"] [data-rule-evidence]').count(), 1);
  assert.equal(
    await page.getByRole("dialog").getByText("Technical definition", { exact: true }).count(),
    0,
  );
  assert.equal(await page.getByRole("dialog").getByLabel("Rule draft JSON").count(), 0);
  await page.locator("[data-rule-dialog-body]").evaluate((el) => {
    el.scrollTop = 0;
  });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.screenshot({
    path: "/private/tmp/guided-rules-screens/mobile-de.png",
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  assert.equal(await page.getByRole("dialog").count(), 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS guided rule evidence, typed draft, simulation, activation, replay, preservation, access, uncertainty and mobile keyboard checks",
  );
} catch (error) {
  await mkdir("/private/tmp/guided-rules-screens", { recursive: true });
  await page.screenshot({ path: "/private/tmp/guided-rules-screens/error.png", fullPage: true });
  console.error(errors);
  throw error;
} finally {
  await browser.close();
}
