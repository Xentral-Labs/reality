// Live source evidence is rendered as business conditions, never as executable HTML.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
let calls = 0;
const fixture = {
  kind: "command",
  key: "credit_exposure",
  business: {
    language: "en",
    mode: "llm",
    heading: "Business explanation",
    notice: "AI interpretation from current code",
    steps: [
      {
        id: "credit.limit",
        function: "reality.services.credit_exposure.credit_exposures",
        kind: "decision",
        text: "Compare credit exposure with the positive credit limit.",
        rule_ids: ["credit.limit"],
        evidence_ids: ["e1"],
        line: 281,
      },
    ],
    edges: [],
    scenarios: [
      {
        id: "test_credit_exposure.py::test_limit",
        title: "exposure past the limit",
        given: ["Credit limit: 1000 EUR"],
        when: ["Read credit exposure"],
        then: ["Limit exceeded"],
        notice: "Run unknown",
        unexplained_assertions: 0,
      },
    ],
  },
  label: "Credit exposure",
  purpose: "Inspect the running credit rules.",
  status: "complete",
  presentation_language: "en",
  release: { version: "test-release", commit: "abc123", source_digest: "digest" },
  limitations: [],
  prerequisites: [],
  inputs: ["party_id"],
  outputs: [],
  consumers: [],
  requirements: [],
  nodes: [
    {
      id: "credit.limit",
      function: "reality.services.credit_exposure.credit_exposures",
      kind: "decision",
      text: "Check whether credit limit is greater than 0 and credit exposure is greater than credit limit",
      expression: "limit > 0 and exposure > limit",
      evidence_id: "e1",
      line: 281,
      end_line: 282,
      context: [],
    },
  ],
  edges: [],
  sources: [
    {
      id: "e1",
      path: "packages/reality-core/src/reality/services/credit_exposure.py",
      function: "reality.services.credit_exposure.credit_exposures",
      start_line: 250,
      code: Array.from({ length: 80 }, (_, i) =>
        i === 31
          ? "if limit > 0 and exposure > limit:"
          : i === 32
            ? "    return True"
            : `# context ${i + 250}`,
      ).join("\n"),
      digest: "digest",
    },
  ],
  test_gaps: ["credit.limit"],
  scenarios: [
    {
      id: "test_credit_exposure.py::test_limit",
      name: "exposure past the limit",
      facts: [{ name: "limit", value: "1000", currency: "EUR" }],
      setup: ["Credit limit 1000"],
      action: ["Read credit exposure"],
      expectations: ["over limit equals yes"],
      assumptions: ["Fixture business is unresolved"],
      parameters: {},
      relationship: "candidate",
      rules: [],
      code: "assert result['over_limit']",
      helpers: [],
      run: { outcome: "unknown", revision_match: false },
    },
  ],
};
await page.route("**/api/**", async (route) => {
  const p = new URL(route.request().url()).pathname;
  const reply = (body) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(body) });
  if (p.endsWith("/business-logic/compare")) {
    const input = route.request().postDataJSON();
    assert.equal(input.scenario_ids[0], "test_credit_exposure.py::test_limit");
    assert.equal(input.facts[0].value, "1000");
    return reply({
      context: "caller_supplied",
      case_facts: input.facts,
      comparisons: [
        {
          scenario_id: input.scenario_ids[0],
          conditions: [
            {
              name: "limit",
              test_values: ["1000 EUR"],
              case_value: input.facts[0],
              status: input.facts[0].currency === "USD" ? "different" : "unknown",
            },
          ],
          unknown_assumptions: ["Fixture business is unresolved"],
          untested_aspects: ["Similarity does not prove an outcome"],
        },
      ],
      recorded_decisions: [],
      links: [],
      limitations: [],
      historical_rule_version: "unknown",
    });
  }
  if (p.endsWith("/business-logic/command/credit_exposure")) {
    calls++;
    return reply({ ...fixture, release: { ...fixture.release, version: `test-release-${calls}` } });
  }
  if (p === "/api/auth/me")
    return reply({
      id: "u1",
      email: "erp@example.test",
      display_name: "ERP",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (p === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "t1", name: "Northstar" }], default_tenant_id: "t1" });
  if (p.endsWith("/application-reference"))
    return reply({
      commands: [
        {
          name: "Credit exposure",
          service: "credit_exposure",
          effect: "Inspect the credit rules.",
          reads: [],
          writes: [],
          contracts: [],
        },
      ],
      projections: [],
      workspaces: [],
      events: [],
      fact_predicates: [],
      command_count: 1,
      event_count: 0,
      projection_count: 0,
      fact_predicate_count: 0,
      tool_catalog: {
        version: 1,
        topics: [{ key: "finance", label: "Finance" }],
        entries: [
          {
            id: "command:credit_exposure",
            title: "Credit exposure",
            labels: {},
            description: "Inspect credit rules.",
            topic: "finance",
            purpose: "understand",
            commands: ["credit_exposure"],
            mcp: [],
            views: [],
            projections: [],
            actions: [],
            discovery: [],
            related: [],
          },
        ],
        mcp_tools: [],
      },
    });
  if (p.endsWith("/copilot"))
    return reply({
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      active_session_id: null,
      has_archived: false,
    });
  if (p.endsWith("/inspect")) return reply({ tables: [] });
  return reply({
    items: [],
    rows: [],
    counts: {},
    readiness: { ready: true },
    capabilities: [],
    exceptions: [],
    activity: [],
    sources: [],
  });
});
try {
  await page.goto(
    `${process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177"}/app/inspector?tenant=t1&inspector_view=commands&lang=en`,
  );
  // Catalog navigation follows the existing unified tool catalog, no test-only product route.
  await page
    .getByRole("button", { name: /Credit exposure/ })
    .first()
    .click();
  await page.getByRole("button", { name: "Read live logic", exact: true }).first().click();
  await page
    .locator("[data-business-reading-view]")
    .getByText("Compare credit exposure with the positive credit limit.", { exact: true })
    .first()
    .waitFor();
  await page
    .locator("[data-business-reading-view]")
    .getByText("Show referenced source", { exact: true })
    .first()
    .click();
  assert.deepEqual(
    await page
      .locator("[data-business-reading-view] [data-source-highlight] span[aria-hidden=true]")
      .allTextContents(),
    ["281", "282"],
  );
  await page
    .locator("[data-business-reading-view]")
    .getByRole("button", { name: "Full function", exact: true })
    .first()
    .click();
  const focusVisible = await page
    .locator("[data-business-reading-view] [data-source-highlight]")
    .first()
    .evaluate((el) => {
      const pane = el.closest("pre");
      const a = el.getBoundingClientRect(),
        b = pane.getBoundingClientRect();
      return a.top >= b.top && a.bottom <= b.bottom;
    });
  assert.ok(focusVisible);
  assert.equal(calls, 1);
  await page.screenshot({ path: "/tmp/blueprint-ux-web-source.png" });
  await page.getByRole("tab", { name: "Technical evidence", exact: true }).click();
  await page.getByText("test-release-1", { exact: false }).waitFor();
  assert.ok(await page.getByText(/credit exposure is greater than credit limit/).count());
  await page.getByRole("tab", { name: /Test cases/ }).click();
  await page.getByRole("button", { name: "exposure past the limit", exact: true }).click();
  assert.ok(await page.getByText("unknown", { exact: false }).count());
  await page.getByText("Compare my case", { exact: true }).click();
  await page.getByLabel("limit", { exact: false }).first().fill("1000");
  await page.getByRole("button", { name: "Compare conditions", exact: true }).click();
  await page.getByText("Supplied case facts", { exact: true }).waitFor();

  await page.getByRole("button", { name: "Refresh live logic", exact: true }).click();
  await page.getByRole("tab", { name: "Steps", exact: true }).click();
  await page
    .locator("[data-business-reading-view]")
    .getByText("Compare credit exposure with the positive credit limit.", { exact: true })
    .first()
    .waitFor();
  await page.getByRole("tab", { name: "Technical evidence", exact: true }).click();
  assert.equal(await page.getByText("test-release-2", { exact: false }).count(), 1);
  await page.getByRole("tab", { name: "Steps", exact: true }).click();
  assert.equal(calls, 2);
  assert.equal(await page.locator("[data-business-flow]").count(), 0);
  await page.screenshot({ path: "/tmp/business-blueprints-web.png", fullPage: true });
  console.log("Live business blueprint browser checks passed.");
} finally {
  await browser.close();
}
