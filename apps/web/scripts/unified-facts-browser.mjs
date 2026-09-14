// Fixtures prove UI navigation; PostgreSQL tests prove scoped observation semantics.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const requests = [],
  errors = [];
let language = "en",
  fail = false;
page.on("pageerror", (e) => errors.push(e.message));
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    path = u.pathname;
  requests.push({ path, query: u.search, method: req.method() });
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      display_name: "Operator",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "facts", name: "Northstar Commerce" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: "facts",
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.endsWith("/facts")) {
    if (fail) return reply({ detail: "Register unavailable" }, 503);
    const empty = u.searchParams.get("q") === "missing";
    return reply({
      items: empty
        ? []
        : [
            {
              id: "fact1",
              subject_type: "commitment",
              subject_id: "com/1",
              predicate: "order.shipping_priority",
              value: "Open <script>original</script>",
              observed_at: "2026-09-07T12:00:00Z",
              source_record_id: "source-v2",
              source_version: 2,
              source: { system: "sample", type: "order", external_id: "SAME" },
              interpretation_rule: { id: "rule1", logical_name: "Original rule", version: 1 },
            },
            {
              id: "fact2",
              subject_type: "historical",
              subject_id: "legacy1",
              predicate: "legacy.literal",
              value: "standard",
              observed_at: "2026-09-06T12:00:00Z",
              source_record_id: null,
              source: null,
            },
          ],
      subject_types: ["commitment", "historical"],
      subject_types_has_more: false,
      page: {
        number: Number(u.searchParams.get("page") || 1),
        size: 50,
        total: empty ? 0 : 51,
        pages: empty ? 0 : 2,
        has_previous: u.searchParams.get("page") === "2",
        has_next: !empty && u.searchParams.get("page") !== "2",
      },
    });
  }
  if (path.includes("/inspector/"))
    return path.endsWith("/foreign")
      ? reply({ detail: "Not found" }, 404)
      : reply({
          title: "Recorded observation",
          subtitle: "Exact record",
          meaning: "This is a recorded observation, not a current-state guarantee.",
          sections: [
            {
              title: "Context and source",
              rows: [
                { label: "Subject", value: "com/1", link: { kind: "commitment", id: "com/1" } },
                {
                  label: "Source",
                  value: "SAME",
                  link: { kind: "source_record", id: "source-v2" },
                },
                { label: "Value", value: "Open <script>original</script>" },
              ],
            },
          ],
          metrics: [],
          technical_rows: [],
          source_payload: JSON.stringify({ priority: "Open <script>original</script>" }),
        });
  return reply({ detail: "Fixture unavailable" }, 404);
});
const go = async (extra = "") => {
  await page.goto(`${base}/app/facts?tenant=facts${extra}`);
  await page.locator("[data-fact-row]").first().waitFor();
};
try {
  await mkdir("/private/tmp/reality-114-browser", { recursive: true });
  await go();
  const explain = page.getByRole("button", { name: "Explain observation", exact: true }).first();
  await explain.focus();
  await page.keyboard.press("Enter");
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Recorded observation", exact: true })
    .waitFor();
  await page.keyboard.press("Escape");
  assert.equal(await explain.evaluate((n) => n === document.activeElement), true);
  await explain.click();
  await page.reload();
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Recorded observation", exact: true })
    .waitFor();
  await Promise.all([
    page.waitForResponse((r) => r.url().includes("/inspector/commitment/com%2F1")),
    page.getByRole("dialog").getByRole("button", { name: "com/1", exact: true }).click(),
  ]);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Related observations", exact: true }).first().click();
  await page.waitForURL(/fact_subject=com%2F1/);
  assert.ok(requests.some((r) => r.query.includes("subject_id=com%2F1")));
  await page.getByRole("button", { name: "Open original", exact: true }).click();
  await page.waitForURL(/fact_target=source_record/);
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Recorded observation", exact: true })
    .waitFor();
  await page.keyboard.press("Escape");
  await go("&fact_source=source-v2");
  assert.ok(requests.some((r) => r.query.includes("source_record_id=source-v2")));
  await page.getByRole("button", { name: "Related observations", exact: true }).first().click();
  assert.ok(!new URL(page.url()).searchParams.has("fact_source"));
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await page.getByLabel("Subject type", { exact: true }).selectOption("historical");
  await page.waitForURL(/fact_subject_type=historical/);
  await page.getByLabel("Search observations", { exact: true }).fill("missing");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByRole("heading", { name: "No observations found", exact: true }).waitFor();
  fail = true;
  await page.reload();
  await page.getByRole("button", { name: "Retry", exact: true }).waitFor();
  fail = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.getByRole("heading", { name: "No observations found", exact: true }).waitFor();
  await go();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.waitForURL(/page=2/);
  await page.locator("[data-fact-row]").first().waitFor();
  assert.ok(requests.some((r) => r.query.includes("page=2")));
  await go("&fact_source=source-v2&fact_subject=com%2F1&fact_subject_type=commitment&q=Open");
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="other"]').click();
  for (const key of ["fact_source", "fact_subject", "fact_subject_type", "q", "entry"])
    assert.equal(new URL(page.url()).searchParams.has(key), false);
  await page.goto(`${base}/app/facts?tenant=facts&entry=foreign`);
  await page.getByRole("dialog").getByRole("alert").waitFor();
  await page.keyboard.press("Escape");
  for (const lang of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [1440, 390]) {
        language = lang;
        await page.setViewportSize({ width, height: 1000 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        await go();
        assert.ok(
          await page
            .locator("[data-fact-row] [data-original-content]")
            .allTextContents()
            .then((rows) => rows.includes("Open <script>original</script>")),
        );
        assert.equal(await page.locator("[data-fact-row] script").count(), 0);
        assert.ok(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
        );
        if (theme === "light" && width === 1440) {
          await page.locator("[data-fact-row]").first().getByRole("button").first().click();
          await page
            .getByRole("dialog")
            .locator("span[data-original-content]")
            .filter({ hasText: "Open <script>original</script>" })
            .waitFor();
          assert.equal(await page.getByRole("dialog").locator("script").count(), 0);
          await page.keyboard.press("Escape");
        }
        await page.screenshot({
          path: `/private/tmp/reality-114-browser/${lang}-${theme}-${width}.png`,
          fullPage: true,
        });
      }
  assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: exact subject/source navigation, keyboard and reload, raw values, filters, empty/retry, no writes and 16 localized screenshots.",
  );
} finally {
  await browser.close();
}
