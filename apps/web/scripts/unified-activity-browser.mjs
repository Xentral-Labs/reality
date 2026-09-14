// Intercepted read-only transport; existing PostgreSQL tests prove timeline semantics.
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
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
let language = "en",
  failOlder = false,
  failFirst = false,
  delayed;
const errors = [],
  requests = [],
  inspections = [],
  writes = [];
page.on("pageerror", (e) => errors.push(e.message));
const event = (id, sequence, extra = {}) => ({
  id,
  sequence,
  type: "reservation.created",
  subject_type: "reservation",
  subject_id: "reservation-1",
  occurred_at: "2026-09-01T10:00:00Z",
  recorded_at: "2026-09-08T08:00:00Z",
  payload: { note: "<script>window.injected = true</script>" },
  source_record_id: null,
  action_id: "action-1",
  correlation_id: "split-action",
  causation_id: null,
  area: "operations",
  status: "completed",
  business_title: "Inventory reserved",
  business_detail: "Müller · Desk lamp",
  business_context: { party: "Müller", item: "Desk lamp", quantity: "4.0000", unit: "pcs" },
  ...extra,
});
const newest = [
  event("newest", 105),
  event("second", 104, {
    type: "party.delivery_hold_placed",
    subject_type: "party",
    subject_id: "customer",
    status: "attention",
  }),
];
const older = [
  newest[1],
  event("oldest", 100, {
    type: "future.unknown",
    subject_type: "posting_group",
    business_title: "Future original action",
    business_context: { name: "Open <script>original</script>" },
  }),
];
const data = (events, has_more = false) => ({ events, activities: [], has_more });
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    p = u.pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (req.method() !== "GET") {
    writes.push(p);
    return reply({ detail: "No writes allowed" }, 400);
  }
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
        { id: "company", name: "Northstar Commerce" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: "company",
    });
  if (p.endsWith("/application-reference")) return reply({ workspaces: [], commands: [] });
  if (p.endsWith("/facts"))
    return reply({
      items: [],
      subject_types: [],
      subject_types_has_more: false,
      page: { number: 1, size: 50, total: 0, pages: 0, has_previous: false, has_next: false },
    });
  if (p.endsWith("/delivery-work"))
    return reply({
      items: [],
      page: { number: 1, size: 50, total: 0, pages: 0, has_previous: false, has_next: false },
    });
  if (p.endsWith("/timeline")) {
    requests.push({
      tenant: p.includes("/other/") ? "other" : "company",
      query: Object.fromEntries(u.searchParams),
    });
    if (u.searchParams.get("q") === "slow") {
      delayed = () => reply(data([event("stale", 500)]));
      return;
    }
    if (p.includes("/other/"))
      return reply(
        data([event("other-event", 200, { business_context: { name: "Other company only" } })]),
      );
    if (failFirst && !u.searchParams.has("before_sequence"))
      return reply({ detail: "History unavailable" }, 503);
    if (u.searchParams.get("q") === "missing") return reply(data([]));
    if (u.searchParams.has("before_sequence"))
      return failOlder ? reply({ detail: "Older history unavailable" }, 503) : reply(data(older));
    return reply(data(newest, true));
  }
  if (p.includes("/inspector/")) {
    inspections.push(p);
    return reply({
      title: "Exact recorded event",
      subtitle: "Evidence",
      meaning: "Original event",
      sections: [],
      technical_rows: [],
      metrics: [],
      source_payload: null,
    });
  }
  return reply({ detail: "Fixture unavailable" }, 404);
});
const drawer = () => page.getByRole("dialog", { name: "Activity", exact: true });
const rows = () => drawer().locator("[data-activity-event]");
const open = async () => {
  await page.getByRole("button", { name: "Activity", exact: true }).click();
  await rows().first().waitFor();
};
const search = async (value) => {
  await drawer().getByRole("textbox", { name: "Search activity", exact: true }).fill(value);
  await drawer().getByRole("button", { name: "Search", exact: true }).click();
};
const waitRows = async (count) => {
  await page.waitForFunction(
    (n) => document.querySelectorAll("[data-activity-event]").length === n,
    count,
  );
};
try {
  await page.goto(`${base}/app/facts?tenant=company`);
  await page.getByRole("textbox", { name: "Search observations", exact: true }).waitFor();
  const originalUrl = page.url();
  const workspaceSearch = page.getByRole("textbox", { name: "Search observations", exact: true });
  await workspaceSearch.fill("unfinished input");
  await open();
  assert.equal(requests.at(-1).query.hours, "24");
  assert.equal(await rows().count(), 2);
  assert.ok(await drawer().getByText("Müller", { exact: false }).count());
  assert.equal(await drawer().getByText("Completed", { exact: true }).count(), 0);
  await rows().first().getByText("Technical details", { exact: true }).click();
  assert.ok((await rows().first().innerText()).includes("<script>window.injected = true</script>"));
  assert.equal(await page.evaluate(() => window.injected), undefined);
  await rows().first().getByRole("button", { name: "Inspect event", exact: true }).click();
  await page.getByRole("heading", { name: "Exact recorded event", exact: true }).waitFor();
  assert.ok(inspections.at(-1).endsWith("/business_event/newest"));
  await page.keyboard.press("Escape");
  assert.equal(await drawer().isVisible(), true);
  await rows().first().getByRole("button", { name: "Open related record", exact: true }).click();
  await page.getByRole("heading", { name: "Exact recorded event", exact: true }).waitFor();
  assert.ok(inspections.at(-1).endsWith("/reservation/reservation-1"));
  await page.keyboard.press("Escape");
  failOlder = true;
  await drawer().getByRole("button", { name: "Load older events", exact: true }).click();
  await drawer().getByText("Older activity could not be loaded.", { exact: true }).waitFor();
  assert.equal(await rows().count(), 2);
  failOlder = false;
  await drawer().getByRole("button", { name: "Load older events", exact: true }).click();
  await waitRows(3);
  assert.equal(requests.at(-1).query.before_sequence, "104");
  assert.equal(
    await rows().last().getByRole("button", { name: "Open related record", exact: true }).count(),
    0,
  );
  await drawer().getByText("Future original action", { exact: true }).waitFor();
  await drawer().getByText("End of matching activity.", { exact: true }).waitFor();
  for (const hours of ["168", "720", "0"]) {
    await Promise.all([
      page.waitForResponse(
        (r) =>
          r.url().includes(`/timeline?`) && new URL(r.url()).searchParams.get("hours") === hours,
      ),
      drawer().getByLabel("Period", { exact: true }).selectOption(hours),
    ]);
    await waitRows(2);
    assert.equal(requests.at(-1).query.hours, hours);
    assert.equal(requests.at(-1).query.before_sequence, undefined);
  }
  await Promise.all([
    page.waitForResponse((r) => r.url().includes("event_status=attention")),
    drawer().getByLabel("Attention events only", { exact: true }).check(),
  ]);
  await search("slow");
  await page.waitForFunction(
    () => document.querySelector('dialog input[aria-label="Search activity"]').value === "slow",
  );
  while (!delayed) await new Promise((resolve) => setTimeout(resolve, 10));
  await search("missing");
  await drawer().getByText("No matching events.", { exact: true }).waitFor();
  await delayed();
  delayed = undefined;
  await page.waitForTimeout(100);
  assert.equal(await rows().count(), 0);
  await search("");
  await waitRows(2);
  failFirst = true;
  await drawer().getByRole("button", { name: "Refresh", exact: true }).click();
  await drawer().getByText("Activity could not be loaded.", { exact: true }).waitFor();
  failFirst = false;
  await drawer().getByRole("button", { name: "Retry", exact: true }).click();
  await waitRows(2);
  await page.keyboard.press("Escape");
  assert.equal(page.url(), originalUrl);
  assert.equal(await workspaceSearch.inputValue(), "unfinished input");
  assert.equal(
    await page
      .getByRole("button", { name: "Activity", exact: true })
      .evaluate((n) => n === document.activeElement),
    true,
  );
  await open();
  await page.mouse.click(30, 300);
  await drawer().waitFor({ state: "hidden" });
  await open();
  await drawer().getByRole("button", { name: "Close", exact: true }).focus();
  await page.keyboard.press("Tab");
  await workspaceSearch.evaluate((n) => n.focus());
  assert.equal(await drawer().evaluate((n) => n.contains(document.activeElement)), true);
  await drawer().getByRole("button", { name: "Close", exact: true }).click();
  await open();
  // A browser history tenant change can happen while a modal request is in flight.
  await search("slow");
  while (!delayed) await new Promise((resolve) => setTimeout(resolve, 10));
  await page.evaluate(() => {
    history.pushState({}, "", "/app/facts?tenant=other");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await drawer().waitFor({ state: "hidden" });
  await delayed();
  delayed = undefined;
  await open();
  await drawer().getByText("Other company only", { exact: true }).waitFor();
  assert.equal(await drawer().locator('[data-activity-event="stale"]').count(), 0);
  await page.keyboard.press("Escape");
  await page.goto(`${base}/app/work?tenant=company`);
  await open();
  await page.keyboard.press("Escape");
  await mkdir("/private/tmp/reality-134-browser", { recursive: true });
  const names = { en: "Activity", de: "Aktivität", nl: "Activiteit", es: "Actividad" };
  for (const lang of Object.keys(names))
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        language = lang;
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.goto(`${base}/app/facts?tenant=company`);
        await page.getByRole("button", { name: names[lang], exact: true }).waitFor();
        await page.evaluate(
          (theme) => document.documentElement.setAttribute("data-theme", theme),
          theme,
        );
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
          `header overflow ${lang}/${width}`,
        );
        await page.getByRole("button", { name: names[lang], exact: true }).click();
        await page.locator("[data-activity-event]").first().waitFor();
        assert.equal(
          await page.locator("dialog").evaluate((n) => n.scrollWidth <= n.clientWidth),
          true,
          `drawer overflow ${lang}/${width}`,
        );
        const translated = {
          en: "Search activity",
          de: "Verlauf durchsuchen",
          nl: "Activiteit doorzoeken",
          es: "Buscar actividad",
        };
        await page.getByRole("textbox", { name: translated[lang], exact: true }).waitFor();
        await page.screenshot({
          path: `/private/tmp/reality-134-browser/${lang}-${theme}-${width}.png`,
          animations: "disabled",
        });
        await page.keyboard.press("Escape");
      }
  assert.deepEqual(errors, []);
  assert.deepEqual(writes, []);
  console.log(
    "Activity browser passed: paging/retry/races/tenant isolation/inspection/focus/read-only and 16 localized layouts.",
  );
} finally {
  await browser.close();
}
