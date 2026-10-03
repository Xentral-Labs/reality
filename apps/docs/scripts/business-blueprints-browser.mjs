import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
let reads = 0;
const requests = [];
await page.route("**/api/business-logic/entries/**", async (route) => {
  reads++;
  const requestUrl = new URL(route.request().url());
  requests.push(requestUrl);
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
      ...(requestUrl.searchParams.get("interpret") === "false" ? { business: null } : {}),
    }),
  });
});
try {
  await page.goto(
    `${process.env.DOCS_BASE_URL || "http://127.0.0.1:5178"}/tool-usage/#tool:credit_exposure`,
  );
  const read = page.getByRole("tab", { name: "Steps & rules", exact: true });
  assert.equal(reads, 0, "Selecting a function must not start a live request");
  await read.click();
  await page
    .getByRole("status")
    .getByText("Reading current source and tests…", { exact: true })
    .waitFor();
  assert.equal(await page.getByRole("button", { name: "Refresh", exact: true }).isDisabled(), true);
  await page
    .locator("[data-business-reading-view]")
    .getByText(/Live business rule 1/)
    .first()
    .waitFor();
  await page.getByRole("tab", { name: /Test cases/ }).click();
  await page.getByRole("button", { name: "credit boundary case", exact: true }).click();
  await page.getByText("The limit is exceeded", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Technical details", exact: true }).click();
  await page.getByText("live-2", { exact: false }).waitFor();
  assert.equal(await page.locator("[data-live-blueprint] img").count(), 0);
  await page.getByRole("tab", { name: /Test cases/ }).click();
  await page.getByRole("button", { name: "credit boundary case", exact: true }).click();
  assert.ok(await page.getByText("Unverified for this release", { exact: false }).count());
  await page.getByRole("tab", { name: "Steps & rules", exact: true }).click();
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
  assert.equal(reads, 2, "Returning to loaded rules/technical/code must stay local");
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
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await page.getByRole("alert").waitFor();
  assert.equal(reads, 3);
  assert.equal(await page.getByText("live-2", { exact: false }).count(), 0);
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page
    .locator("[data-business-reading-view]")
    .getByText(/Live business rule 4/)
    .first()
    .waitFor();
  await page.getByRole("tab", { name: "Source code", exact: true }).click();
  await page.locator("[data-direct-source]").waitFor();
  assert.equal(reads, 4, "Opening already loaded source must remain local");
  assert.equal(await page.getByRole("button", { name: "Refresh code", exact: true }).count(), 0);
  assert.equal(reads, 4, "Source tab must not add a refresh request");
  await page.waitForFunction(() =>
    document.querySelector("[data-direct-source] .source-token[style*='color']"),
  );
  const pre = page.locator("[data-direct-source]");
  const codeMetrics = await pre.evaluate((element) => {
    const rows = [...element.querySelectorAll(".direct-source-line")];
    const token = element.querySelector(".source-token");
    return {
      font: parseFloat(getComputedStyle(token).fontSize),
      whiteSpace: getComputedStyle(token.parentElement).whiteSpace,
      height: rows[0].getBoundingClientRect().height,
      colors: new Set(
        [...element.querySelectorAll(".source-token")].map((el) => getComputedStyle(el).color),
      ).size,
      text: rows[50].lastElementChild.textContent,
      light: getComputedStyle(token).color,
    };
  });
  assert.equal(codeMetrics.font, 12);
  assert.equal(codeMetrics.whiteSpace, "pre");
  assert.ok(codeMetrics.height < 21, "An original row must not wrap");
  assert.ok(codeMetrics.colors >= 3, "Keywords, comments and values need syntax colors");
  assert.equal(codeMetrics.text, "if exposure > limit:");
  const keyword = pre.locator(".source-token").filter({ hasText: /^if$/u });
  const lightKeyword = await keyword.evaluate((el) => getComputedStyle(el).color);
  await page.evaluate(() => document.documentElement.classList.add("dark"));
  const darkColor = await pre
    .locator(".source-token")
    .first()
    .evaluate((el) => getComputedStyle(el).color);
  // Comments may use identical colors; code tokens still have explicit dark-theme styles.
  assert.ok(await pre.locator(".source-token[style*='--shiki-dark']").count());
  assert.ok(darkColor);
  const darkKeyword = await keyword.evaluate((el) => getComputedStyle(el).color);
  assert.notEqual(darkKeyword, lightKeyword, "Dark theme must apply its matching token colors");
  await page.evaluate(() => document.documentElement.classList.remove("dark"));
  assert.equal(requests[0].searchParams.get("brief"), "true");
  assert.equal(requests[0].searchParams.get("interpret"), "true");
  assert.equal(requests[1].searchParams.get("brief"), "false");
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await page.locator("[data-direct-source]").waitFor();
  assert.equal(reads, 5);
  assert.equal(requests[4].searchParams.get("interpret"), "false");
  await page.getByRole("tab", { name: "Technical details", exact: true }).click();
  assert.equal(reads, 5, "Technical reference must reuse source-only evidence");
  assert.ok(await page.locator(".man-header").isVisible());
  await page.getByRole("tab", { name: "Steps & rules", exact: true }).click();
  await page
    .locator("[data-business-reading-view]")
    .getByText(/Live business rule 6/)
    .first()
    .waitFor();
  assert.equal(reads, 6, "Refreshing source must invalidate the old explanation");
  await page.getByRole("tab", { name: /Test cases/ }).click();
  await page
    .locator("[data-business-test]")
    .getByText("The limit is exceeded", { exact: true })
    .waitFor();
  assert.equal(reads, 7);
  await page.goto(`${process.env.DOCS_BASE_URL || "http://127.0.0.1:5178"}/tool-usage/#view:items`);
  await page.getByRole("tab", { name: "Source code", exact: true }).click();
  await page.locator("[data-direct-source]").waitFor();
  assert.equal(reads, 8, "A different entry must not reuse previous source evidence");
  assert.ok(requests[7].pathname.endsWith("/view/items"));
  assert.equal(requests[7].searchParams.get("interpret"), "false");
  assert.ok(
    !(await page.locator(".man-header").isVisible()),
    "Technical catalog belongs only in Technical details",
  );
  await page.screenshot({ path: "/tmp/business-blueprints-docs.png", fullPage: true });
  console.log("Live docs browser: freshness, escaping, tests, graph and retry passed.");
} finally {
  await browser.close();
}
