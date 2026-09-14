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
let delayedSimulation = null;
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
  if (path.endsWith("/simulate") && delayedSimulation) return delayedSimulation(route);
  if (path.endsWith("/simulate"))
    return reply(
      failSimulation ? { detail: "Simulation unavailable" } : simulation,
      failSimulation ? 503 : 200,
    );
  if (req.method() === "POST" && path.includes("/reality-gaps")) {
    writes.push({ path, body });
    if (failWrite) return reply({ detail: "Unknown write outcome" }, 503);
    if (path.endsWith("/reality-gaps")) {
      detail = initial();
      detail.gap.question = body.question;
      detail.gap.intended_use = body.intended_use;
    }
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
const base = process.env.BASE_URL || "http://localhost:8095";
const wizard = page.locator("[data-fact-rule-wizard]");
const showActions = async () => {
  const menu = page.locator("details.register-actions");
  if ((await menu.getAttribute("open")) === null) await menu.locator("summary").click();
};
const click = async (name) => {
  if (name === "New rule") await showActions();
  await page.getByRole("button", { name, exact: true }).click();
};
const confirm = async () => {
  await page.locator("[data-wizard-confirm]").click();
  await page.locator("[data-wizard-confirm]").waitFor({ state: "hidden" });
};
const stage = async (index) => {
  await page.locator(`[data-fact-rule-wizard][data-stage="${index}"]`).waitFor();
};
const open = async () => {
  await page.goto(`${base}/app/inspector?tenant=company&inspector_view=rules`);
  await click("New rule");
};
try {
  await open();
  await stage(0);
  const purposeSpacing = await page
    .getByLabel("How will this help your team?", { exact: true })
    .evaluate((el) => {
      const css = getComputedStyle(el);
      return {
        top: parseFloat(css.paddingTop),
        bottom: parseFloat(css.paddingBottom),
        height: el.getBoundingClientRect().height,
      };
    });
  assert.ok(
    purposeSpacing.top >= 10 && purposeSpacing.bottom >= 10 && purposeSpacing.height >= 60,
    "Multiline purpose input must leave room above and below the caret",
  );
  assert.equal(await wizard.locator("[aria-current=step]").count(), 1);
  await click("Review goal");
  assert.equal(
    await page
      .getByLabel("What should Reality remember?", { exact: true })
      .evaluate((el) => el === document.activeElement),
    true,
  );
  assert.equal(writes.length, 0);
  await click("Priority handling");
  await click("Delivery instructions");
  assert.match(
    await page.getByLabel("What should Reality remember?", { exact: true }).inputValue(),
    /delivery instruction/,
  );
  await page
    .getByLabel("What should Reality remember?", { exact: true })
    .fill("Retain the delivery instruction from each order");
  await click("Review goal");
  assert.equal(writes.length, 0);
  await click("Back to editing");
  await click("Review goal");
  await page.locator("[data-wizard-confirm]").dblclick();
  await page.locator("[data-wizard-confirm]").waitFor({ state: "hidden" });
  await stage(1);
  assert.equal(writes.length, 1);
  const goalKey = writes[0].body.idempotency_key;
  assert.ok(goalKey);
  await click("Back");
  await stage(0);
  assert.match(await wizard.innerText(), /Retain the delivery instruction/);
  await click("Find an example");
  assert.equal(writes.length, 1);
  await page.getByLabel("Find an order or source record", { exact: true }).fill("SO-42");
  await click("Back");
  await click("Find an example");
  assert.equal(
    await page.getByLabel("Find an order or source record", { exact: true }).inputValue(),
    "SO-42",
  );
  await page.getByLabel("Find an order or source record", { exact: true }).fill("missing");
  await wizard.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByText(/No matching source record found/).waitFor();
  await page.getByLabel("Find an order or source record", { exact: true }).fill("SO-42");
  await wizard.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByRole("button", { name: /Use this value/ }).click();
  assert.equal(writes.length, 1);
  await confirm();
  assert.equal(writes.at(-1).body.payload.displayed_value, "True");
  assert.equal(writes.at(-1).body.payload.source_record_id, "src");
  await click("Create recommendation");
  await confirm();
  await click("Accept recommendation");
  await confirm();
  await stage(2);
  await mkdir("/private/tmp/fact-rule-wizard", { recursive: true });
  await page.screenshot({
    path: "/private/tmp/fact-rule-wizard/configuration.png",
    fullPage: true,
  });
  assert.equal(await wizard.getByLabel("Source", { exact: true }).inputValue(), "shop");
  await wizard.getByLabel("Characteristic", { exact: true }).fill("order.delivery_instruction");
  await click("Review draft");
  assert.equal(detail.rules.length, 0);
  await confirm();
  await stage(3);
  assert.equal(detail.rules.length, 1);
  // Closing/reopening a saved draft requires testing, never another implicit save.
  await page.keyboard.press("Escape");
  await page.locator("tbody button").first().click();
  await stage(3);
  assert.equal(detail.rules.length, 1);
  assert.ok(
    await page.getByRole("button", { name: "Review activation", exact: true }).isDisabled(),
  );
  failSimulation = true;
  await click("Test saved draft");
  await page.getByText("Simulation unavailable", { exact: true }).waitFor();
  failSimulation = false;
  await click("Test saved draft");
  await page.getByRole("region", { name: "Simulation result" }).waitFor();
  await click("Review activation");
  await stage(4);
  await click("Back");
  await click("Back");
  await stage(2);
  await wizard.getByLabel("Characteristic", { exact: true }).fill("order.priority_flag");
  await click("Review draft");
  await confirm();
  await stage(3);
  assert.equal(detail.rules.length, 2);
  assert.ok(
    await page.getByRole("button", { name: "Review activation", exact: true }).isDisabled(),
  );
  await click("Test saved draft");
  await page.getByRole("region", { name: "Simulation result" }).waitFor();
  await click("Review activation");
  await stage(4);
  assert.match(await wizard.innerText(), /future matching data/);
  const savedSetup = structuredClone(detail);
  await page.screenshot({ path: "/private/tmp/fact-rule-wizard/activation.png", fullPage: true });
  await click("Activate rule");
  assert.equal(writes.filter((w) => w.path.endsWith("/activate")).length, 0);
  await confirm();
  await page.getByRole("heading", { name: "Your rule is active", exact: true }).waitFor();
  assert.ok(writes.at(-1).path.endsWith("/r2/activate"));
  assert.equal(writes.filter((w) => w.path.endsWith("/replay")).length, 0);
  await click("Done");
  // Active versions retain the existing editor.
  await page.locator("tbody button").first().click();
  await page.locator("[data-guided-rule-editor]").waitFor();
  assert.equal(await wizard.count(), 0);
  await page.keyboard.press("Escape");
  // Unknown writes cannot be retried from another wizard session.
  await click("New rule");
  await click("Delivery instructions");
  await click("Review goal");
  failWrite = true;
  await confirm();
  await page.getByText(/The result is uncertain/).waitFor();
  assert.ok(await page.getByRole("button", { name: "Review goal", exact: true }).isDisabled());
  await page.keyboard.press("Escape");
  await showActions();
  assert.ok(await page.getByRole("button", { name: "New rule", exact: true }).isDisabled());
  failWrite = false;
  await mkdir("/private/tmp/fact-rule-wizard", { recursive: true });
  for (const lang of ["en", "de", "nl", "es"]) {
    language = lang;
    await page.setViewportSize({ width: lang === "en" ? 1440 : 390, height: 900 });
    await page.goto(`${base}/app/inspector?tenant=company&inspector_view=rules`);
    await showActions();
    await page
      .locator("[data-page-action=menu]")
      .filter({ hasText: /New rule|Neue Regel|Nieuwe regel|Nueva regla/ })
      .click();
    await stage(0);
    const footer = await page.locator("[data-wizard-footer]").boundingBox();
    assert.ok(footer.y >= 0 && footer.y + footer.height <= 900);
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
    );
    await page.screenshot({ path: `/private/tmp/fact-rule-wizard/${lang}.png`, fullPage: true });
    await page.keyboard.press("Escape");
    assert.equal(await page.getByRole("dialog").count(), 0);
    detail = structuredClone(savedSetup);
    await page.reload();
    await page.locator("tbody button").first().click();
    await stage(3);
    await page.locator("[data-wizard-footer] button").first().click();
    await stage(2);
    const configFooter = await page.locator("[data-wizard-footer]").boundingBox();
    assert.ok(configFooter.y + configFooter.height <= 900);
    await page.locator("[data-rule-dialog-body]").evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    assert.equal((await page.locator("[data-wizard-footer]").boundingBox()).y, configFooter.y);
    const box = await page
      .locator("[data-rule-dialog-body]")
      .evaluate((el) => ({ width: el.clientWidth, scroll: el.scrollWidth }));
    assert.ok(box.scroll <= box.width + 1);
    await page.screenshot({
      path: `/private/tmp/fact-rule-wizard/configuration-${lang}.png`,
      fullPage: true,
    });
    await page.keyboard.press("Escape");
    assert.equal(await page.getByRole("dialog").count(), 0);
    assert.equal(
      await page
        .locator("tbody button")
        .first()
        .evaluate((el) => el === document.activeElement),
      true,
    );
  }
  language = "en";
  detail = savedSetup;
  // Delayed simulation from another company cannot unlock this company's wizard.
  await page.goto(`${base}/app/inspector?tenant=company&inspector_view=rules`);
  await page.locator("tbody button").first().click();
  await stage(3);
  let release;
  delayedSimulation = (route) =>
    new Promise((resolve) => {
      release = async () => {
        await route.fulfill({ contentType: "application/json", body: JSON.stringify(simulation) });
        resolve();
      };
    });
  const pendingSimulation = page.waitForRequest((request) => request.url().endsWith("/simulate"));
  await click("Test saved draft");
  await pendingSimulation;
  await page.evaluate(() => {
    history.pushState({}, "", "/app/inspector?tenant=other&inspector_view=rules");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page.locator("tbody button").first().click();
  await stage(3);
  await release();
  delayedSimulation = null;
  assert.equal(await page.getByRole("region", { name: "Simulation result" }).count(), 0);
  assert.ok(
    await page.getByRole("button", { name: "Review activation", exact: true }).isDisabled(),
  );
  // Zero matches are explicitly reported, not called successful coverage.
  simulation.matches = 0;
  simulation.expected_facts = 0;
  await click("Test saved draft");
  await page.getByText(/No matching examples were found/).waitFor();
  await page.keyboard.press("Escape");
  role = "member";
  await page.goto(`${base}/app/inspector?tenant=company&inspector_view=rules`);
  await showActions();
  assert.ok(await page.getByRole("button", { name: "New rule", exact: true }).isDisabled());
  assert.deepEqual(errors, []);
  console.log(
    "PASS wizard goal, evidence, saved-version testing, activation, resume, uncertainty, languages and mobile",
  );
} catch (error) {
  await mkdir("/private/tmp/fact-rule-wizard", { recursive: true });
  await page.screenshot({ path: "/private/tmp/fact-rule-wizard/error.png", fullPage: true });
  throw error;
} finally {
  await browser.close();
}
