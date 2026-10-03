import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
let reads = 0;
await page.route("**/api/business-logic/entries/**", async (route) => {
  reads++;
  if (reads === 1) await new Promise((resolve) => setTimeout(resolve, 1400));
  if (reads === 3) return route.fulfill({ status: 503, body: "Unavailable" });
  return route.fulfill({
    contentType: "application/json",
    body: JSON.stringify({
      kind: "tool",
      key: "credit_exposure",
      purpose: "<img src=x onerror=alert(1)>",
      status: "partial",
      release: { version: `live-${reads}`, commit: `revision-${reads}` },
      business: {
        language: "en",
        mode: "llm",
        heading: "Business explanation",
        notice: "AI interpretation from current code",
        steps: [
          {
            id: "limit",
            function: "credit",
            kind: "decision",
            text: `Live business rule ${reads}: compare exposure with the current credit limit.`,
            rule_ids: ["limit"],
            evidence_ids: ["e"],
            line: 150,
          },
        ],
        edges: [],
        scenarios: [
          {
            id: "test",
            title: "credit boundary case",
            given: ["Credit limit: 1000 EUR"],
            when: ["Read the current exposure"],
            then: ["The limit is exceeded"],
            notice: "No passing run is inferred",
            unexplained_assertions: 0,
          },
        ],
      },
      limitations: ["English explanation; unknown dependency"],
      inputs: ["party_id"],
      prerequisites: [],
      sources: [
        {
          id: "e",
          function: "credit",
          path: "current.py",
          start_line: 100,
          digest: "current",
          code: Array.from({ length: 80 }, (_, i) =>
            i === 50
              ? "if exposure > limit:"
              : i === 51
                ? "    return True"
                : `# context ${i + 100}`,
          ).join("\n"),
        },
      ],
      nodes: [
        {
          id: "limit",
          function: "credit",
          kind: "decision",
          text: "Credit exposure is greater than credit limit",
          expression: "exposure > limit",
          line: 150,
          end_line: 151,
          evidence_id: "e",
          context: [],
        },
      ],
      edges: [],
      test_gaps: ["limit"],
      scenarios: [
        {
          id: "test",
          name: "credit boundary case",
          relationship: "candidate",
          setup: ["Credit limit 1000 EUR"],
          action: ["Read exposure"],
          expectations: ["over limit equals yes"],
          assumptions: ["Fixture not executed"],
          code: "assert result",
          helpers: [],
          run: { outcome: "unknown", revision_match: false },
        },
      ],
    }),
  });
});
try {
  await page.goto(
    `${process.env.DOCS_BASE_URL || "http://127.0.0.1:5178"}/tool-usage/#tool:credit_exposure`,
  );
  const read = page.getByRole("button", { name: "Explain steps and rules →", exact: true });
  await read.click();
  await page
    .getByRole("status")
    .getByText("Reading current source and tests…", { exact: true })
    .waitFor();
  assert.equal(await read.isDisabled(), true);
  await page
    .locator("[data-business-reading-view]")
    .getByText(/Live business rule 1/)
    .first()
    .waitFor();
  await page.getByRole("tab", { name: "Steps", exact: true }).press("ArrowRight");
  await page.getByRole("button", { name: "credit boundary case", exact: true }).click();
  await page.getByText("The limit is exceeded", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Technical evidence", exact: true }).click();
  await page.getByText("live-1", { exact: false }).waitFor();
  assert.equal(await page.locator("[data-live-blueprint] img").count(), 0);
  await page.getByRole("tab", { name: /Test cases/ }).click();
  await page.getByRole("button", { name: "credit boundary case", exact: true }).click();
  assert.ok(await page.getByText("Unverified for this release", { exact: false }).count());
  await page.getByRole("tab", { name: "Steps", exact: true }).click();
  await page
    .locator("[data-business-reading-view]")
    .getByText("Show referenced source", { exact: true })
    .first()
    .click();
  assert.deepEqual(
    await page
      .locator("[data-business-reading-view] [data-source-highlight] .line-number")
      .allTextContents(),
    ["150", "151"],
  );
  await page
    .locator("[data-business-reading-view]")
    .getByRole("button", { name: "Full function", exact: true })
    .click();
  const first = page.locator("[data-business-reading-view] [data-source-highlight]").first();
  const located = await first.evaluate((el) => {
    const pane = el.closest("pre");
    const a = el.getBoundingClientRect(),
      b = pane.getBoundingClientRect();
    return a.top >= b.top && a.bottom <= b.bottom;
  });
  assert.ok(located);
  assert.equal(reads, 1);
  await page
    .locator("[data-business-reading-view]")
    .getByRole("button", { name: "Show excerpt", exact: true })
    .click();
  assert.equal(await page.locator("[data-business-flow]").count(), 0);
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 });
    const bounds = await page.locator(".rule-cards").evaluate((el) => ({
      scroll: el.scrollWidth,
      client: el.clientWidth,
      font: parseFloat(getComputedStyle(el.querySelector("p")).fontSize),
    }));
    assert.ok(bounds.scroll <= bounds.client + 1);
    assert.ok(bounds.font >= 14);
    await page.locator(".rule-cards").screenshot({ path: `/tmp/blueprint-steps-${width}.png` });
  }
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.getByRole("button", { name: "Refresh explanation", exact: true }).click();
  await page
    .locator("[data-business-reading-view]")
    .getByText(/Live business rule 2/)
    .first()
    .waitFor();
  assert.equal(reads, 2);
  assert.ok(
    await page
      .locator("[data-business-reading-view]")
      .getByText(/Live business rule 2/)
      .count(),
  );
  await page.getByRole("button", { name: "Refresh explanation", exact: true }).click();
  await page.getByRole("alert").waitFor();
  assert.equal(await page.getByText("live-2", { exact: false }).count(), 0);
  await page.getByRole("button", { name: "Explain steps and rules →", exact: true }).click();
  await page
    .locator("[data-business-reading-view]")
    .getByText(/Live business rule 4/)
    .first()
    .waitFor();
  await page.screenshot({ path: "/tmp/business-blueprints-docs.png", fullPage: true });
  console.log("Live docs browser: freshness, escaping, tests, graph and retry passed.");
} finally {
  await browser.close();
}
