// Fixtures prove UI navigation; PostgreSQL tests prove scoped observation semantics.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir, readFile } from "node:fs/promises";
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
              predicate: "=1+1",
              value: "standard",
              observed_at: "2026-09-06T12:00:00Z",
              source_record_id: null,
              source: null,
            },
          ].flatMap((row, index) =>
            Array.from({ length: 15 }, (_, i) => ({ ...row, id: row.id + "-" + i })),
          ),
      subject_types: ["commitment", "historical"],
      subject_types_has_more: false,
      page: {
        number: Number(u.searchParams.get("page") || 1),
        size: Number(u.searchParams.get("size") || 50),
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
  await mkdir("/private/tmp/reality-115-browser", { recursive: true });
  await go();
  await page.locator("[data-shell-header] h1").waitFor();
  assert.equal(await page.locator(".register-workbench > .register-heading").count(), 0);
  await page.locator(".register-filter-row .erp-table-tools").waitFor();
  const toolbarGeometry = await page.evaluate(() => ({
    search: document.querySelector(".register-toolbar").getBoundingClientRect().bottom,
    filters: document.querySelector(".register-filter-row").getBoundingClientRect().top,
    tools: document.querySelector(".register-filter-row .erp-table-tools") !== null,
  }));
  assert.ok(toolbarGeometry.search <= toolbarGeometry.filters);
  assert.equal(toolbarGeometry.tools, true);

  const rows = page.locator(".erp-table tbody tr");
  assert.equal(await rows.count(), 30);
  await page.locator(".erp-register-footer").waitFor();
  const selectAll = page.getByRole("checkbox", { name: "Select current page", exact: true });
  await selectAll.check();
  assert.equal(await rows.locator("input:checked").count(), 30);
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export selection", exact: true }).click();
  const exported = await download;
  assert.match(exported.suggestedFilename(), /\.csv$/);
  const csv = await readFile(await exported.path(), "utf8");
  assert.ok(csv.includes("'=1+1"));
  assert.ok(!csv.split("\r\n")[0].includes("Actions"));
  assert.equal(csv.split("\r\n").length, 31);
  await selectAll.uncheck();
  assert.equal(
    await page.getByRole("button", { name: "Export selection", exact: true }).isDisabled(),
    true,
  );
  assert.equal(await rows.first().evaluate((n) => n.getBoundingClientRect().height), 44);
  assert.equal(
    await page
      .locator(".erp-table th")
      .first()
      .evaluate((n) => n.getBoundingClientRect().height),
    44,
  );
  await page.getByRole("combobox", { name: "Row density", exact: true }).selectOption("compact");
  assert.equal(await rows.first().evaluate((n) => n.getBoundingClientRect().height), 36);
  await page.reload();
  await rows.first().waitFor();
  await page.waitForFunction(
    () => document.querySelector(".erp-register")?.dataset.density === "compact",
  );
  await page.getByText("Columns", { exact: true }).click();
  await page.getByRole("checkbox", { name: "Value", exact: true }).uncheck();
  assert.equal(await page.locator(".erp-table th").filter({ hasText: "Value" }).count(), 0);
  await page.reload();
  await rows.first().waitFor();
  assert.equal(await page.locator(".erp-table th").filter({ hasText: "Value" }).count(), 0);
  await page.getByText("Columns", { exact: true }).click();
  await page.getByRole("button", { name: "Reset table", exact: true }).click();
  await page.getByText("Columns", { exact: true }).click();
  const resize = page.getByRole("separator", { name: "Resize column: Observation", exact: true });
  await resize.focus();
  await page.keyboard.press("ArrowRight");
  assert.equal(await resize.getAttribute("aria-valuenow"), "230");
  await page.reload();
  await rows.first().waitFor();
  await page.waitForFunction(
    () => document.querySelector("[role=separator]")?.getAttribute("aria-valuenow") === "230",
  );
  await rows.first().getByRole("checkbox").check();
  await page.getByRole("combobox", { name: "Rows per page", exact: true }).selectOption("100");
  await page.waitForURL(/size=100/);
  assert.equal(await rows.locator("input:checked").count(), 0);
  await rows.first().waitFor();
  await page.getByRole("button", { name: "Value", exact: true }).click();
  await page.waitForURL(/sort=value/);
  await rows.first().waitFor();
  assert.ok(
    requests.some(
      (r) =>
        r.path.endsWith("/facts") && r.query.includes("sort=value") && r.query.includes("size=100"),
    ),
  );
  await rows.first().locator("td").nth(1).click();
  await page.getByRole("dialog").getByRole("heading").first().waitFor();
  await page.keyboard.press("Escape");
  await rows.first().focus();
  await page.keyboard.press("Enter");
  await page.getByRole("dialog").getByRole("heading").first().waitFor();
  await page.keyboard.press("Escape");
  const scroll = page.locator(".erp-table-scroll");
  await scroll.evaluate((n) => {
    n.scrollTop = 400;
    n.scrollLeft = 250;
  });
  const geometry = await scroll.evaluate((n) => ({
    top: n.getBoundingClientRect().top,
    header: n.querySelector("th").getBoundingClientRect().top,
    left: n.getBoundingClientRect().left,
    key: n.querySelector("tbody td").getBoundingClientRect().left,
  }));
  assert.ok(Math.abs(geometry.top - geometry.header) < 2);
  assert.ok(Math.abs(geometry.left - geometry.key) < 2);
  for (language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440, 1920]) {
        await page.setViewportSize({ width, height: 1080 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        await go();
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await page.screenshot({
          path: `/private/tmp/reality-115-browser/${language}-${theme}-${width}.png`,
          fullPage: true,
        });
      }
  assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS:44/36px rows,44px header, visibility/resize/density persistence, server sort/size, row/keyboard details, sticky scroll and24 localized viewport screenshots.",
  );
} finally {
  await browser.close();
}
