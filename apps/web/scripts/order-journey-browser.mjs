import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const errors = [],
  writes = [];
page.on("pageerror", (e) => (errors.push(e.message), console.error("Page error:", e.stack)));
const at = (id, kind, minute, title, subject = id) => ({
  id,
  sequence: Number(id.slice(1)),
  subject_type: kind,
  subject_id: subject,
  recorded_at: `2026-09-18T10:${minute}:00Z`,
  occurred_at: `2026-09-17T09:${minute}:00Z`,
  type: `${kind}.recorded`,
  business_title: title,
  business_detail: "SO-10484 · Bike Light",
  business_context: { quantity: "3", unit: "pcs" },
  payload: {},
  source_record_id: null,
});
const events = [
  at("e1", "document", "40", "Sales order recorded", "d1"),
  at("e2", "commitment", "41", "Delivery commitment created", "c1"),
  at("e3", "reservation", "43", "Inventory reserved", "r1"),
  at("e4", "movement", "46", "Inventory movement recorded", "m1"),
  at("e5", "movement", "46", "Inventory movement recorded", "m2"),
];
let fail = false,
  older = false,
  delayed = false,
  language = "en",
  freshEvents = [];
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (req.method() !== "GET") writes.push(path);
  if (path === "/api/auth/me")
    return reply({
      id: "u1",
      email: "owner@example.test",
      status: "active",
      language,
      locale: { en: "en-GB", de: "de-DE", nl: "nl-NL", es: "es-ES" }[language],
      timezone: "UTC",
      platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "t1", name: "Demo company", role: "owner" },
        { id: "t2", name: "Other company", role: "owner" },
      ],
      default_tenant_id: "t1",
    });
  if (path.endsWith("/attention/summary"))
    return reply({ classes: [], total: 0, observed_at: "2026-09-18T10:00:00Z" });
  if (path.endsWith("/summary"))
    return reply({
      tenant: { id: "t1", name: "Demo company" },
      totals: {},
      capabilities: [],
      counts: {},
    });
  if (path.endsWith("/activity-signal"))
    return reply({ latest_sequence: 5, new_events: 0, attention_events: 0 });
  if (path.endsWith("/order-journeys"))
    return reply({
      orders: [
        { id: "d1", number: "SO-10484", party: "Klara Foods" },
        { id: "d2", number: "SO-10485", party: "Same customer" },
      ],
      has_more: false,
    });
  if (path.endsWith("/change-proposals")) {
    const history = url.searchParams.get("status") === "history";
    const items = history
      ? [
          {
            id: "p-accepted",
            tool: "reservation_create",
            actor_type: "human",
            status: "executed",
            input: {},
            created_at: "2026-09-18T10:42:00Z",
            decided_at: "2026-09-18T10:44:00Z",
            decided_by: "Owner",
            decider: { kind: "person", name: "Owner" },
            review_kind: "common",
            review_destination: "proposal-review",
            review_label: "Reserve inventory",
            review_purpose: "Review the exact change",
          },
          {
            id: "p-rejected",
            tool: "movement_create",
            actor_type: "agent",
            status: "rejected",
            input: {},
            created_at: "2026-09-18T10:44:00Z",
            decided_at: "2026-09-18T10:45:00Z",
            decided_by: "Owner",
            decider: { kind: "person", name: "Owner" },
            review_kind: "common",
            review_destination: "proposal-review",
            review_label: "Record movement",
            review_purpose: "Review the exact change",
          },
        ]
      : [];
    return reply({
      items,
      page: {
        number: 1,
        size: 100,
        total: items.length,
        pages: 1,
        has_previous: false,
        has_next: false,
      },
    });
  }
  if (path.endsWith("/timeline") || path.includes("/order-journeys/")) {
    if (fail) return reply({ detail: "Temporarily unavailable" }, 503);
    if (delayed && path.endsWith("/d1")) await new Promise((r) => setTimeout(r, 700));
    if (path.includes("/t2/") || path.endsWith("/d2"))
      return reply({
        events: [],
        edges: [],
        has_more: false,
        order: { id: "d2", number: "SO-10485", party: "Same customer" },
      });
    if (url.searchParams.has("after_sequence")) {
      const pending = [...events, ...freshEvents]
        .filter((event) => event.sequence > Number(url.searchParams.get("after_sequence")))
        .sort((a, b) => a.sequence - b.sequence);
      return reply({ events: pending.slice(0, 100), edges: [], has_more: pending.length > 100 });
    }
    if (url.searchParams.has("before_sequence")) {
      older = true;
      return reply({
        events: [at("e0", "fact", "39", "Fact observed", "f1")],
        edges: [],
        has_more: false,
      });
    }
    return reply({
      events: [...events].reverse(),
      has_more: true,
      edges: path.endsWith("/d1")
        ? [
            {
              from: { kind: "commitment", id: "c1" },
              to: { kind: "reservation", id: "r1" },
              label: "Commitment",
            },
            {
              from: { kind: "commitment", id: "c1" },
              to: { kind: "movement", id: "m1" },
              label: "Commitment",
            },
          ]
        : [],
      order: path.endsWith("/d1")
        ? { id: "d1", number: "SO-10484", party: "Klara Foods" }
        : undefined,
    });
  }
  if (path.includes("/inspector/"))
    return reply({
      kind: "reservation",
      id: "r1",
      title: "Reserved stock",
      subtitle: "SO-10484",
      sections: [],
      technical_rows: [],
      metrics: [],
      events: [],
      trail: [],
    });
  if (path.endsWith("/copilot"))
    return reply({ sessions: [], messages: [], proposals: [], suggestions: [] });
  return reply({ detail: "Fixture not provided" }, 404);
});
try {
  console.log("Opening journey page");
  await page.goto(
    `${process.env.WEB_BASE_URL || "http://localhost:5177"}/app/inspector?tenant=t1&inspector_view=overview`,
  );
  console.log("Page opened");
  await page.locator("[data-journey-timeline]").waitFor();
  console.log("Timeline ready");
  await page.getByRole("button", { name: "Hide chat", exact: true }).first().click();
  await page.locator('[data-journey-event="e3"]').waitFor();
  assert.equal(await page.locator("[data-journey-lane]").count(), 6);
  await page.locator('[data-journey-lane="decision"]').waitFor();
  assert.equal(await page.locator('[data-journey-event^="decision:"]').count(), 4);
  await page.getByRole("button", { name: "Choose sales order", exact: true }).click();
  await page.getByRole("button", { name: /SO-10484.*Klara Foods/ }).click();
  assert.equal(await page.locator('[data-journey-event^="decision:"]').count(), 0);
  await page.locator("[data-journey-edge]").first().waitFor();
  await page.locator('[data-journey-event="e3"]').click();
  await page.getByRole("button", { name: "Inspect record", exact: true }).click();
  await page.getByRole("dialog").waitFor();
  await page.keyboard.press("Escape");
  await page.locator("[data-journey-cluster]").click();
  assert.equal(await page.locator("[data-journey-cluster-member]").count(), 2);
  await page.locator('[data-journey-cluster-member="e5"]').click();
  await page.getByRole("button", { name: "Load older events", exact: true }).click();
  await page.locator('[data-journey-history="e0"]').waitFor();
  assert.ok(older);
  await page.getByRole("button", { name: "Today", exact: true }).click();
  // Today may or may not coincide with fixtures; fit always restores their points.
  await page.getByRole("button", { name: "Fit history", exact: true }).click();
  await page.locator('[data-journey-event="e3"]').waitFor();
  await mkdir("/tmp/reality-233-browser", { recursive: true });
  await page.screenshot({ path: "/tmp/reality-233-browser/desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  await page.screenshot({ path: "/tmp/reality-233-browser/mobile.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  fail = true;
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await page.getByRole("alert").filter({ hasText: "History could not be loaded." }).waitFor();
  assert.ok(await page.locator('[data-journey-history="e3"]').count());
  fail = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page
    .getByRole("alert")
    .filter({ hasText: "History could not be loaded." })
    .waitFor({ state: "hidden" });
  // A burst larger than one page is read forward without moving the pinned range.
  await page.locator('[data-journey-event="e3"]').click();
  const rangeBefore = await page.locator(".journey-chart-heading").innerText();
  freshEvents = Array.from({ length: 101 }, (_, i) =>
    at(`e${i + 6}`, "movement", "47", "Inventory movement recorded", `m${i + 6}`),
  );
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await page.getByRole("button", { name: "Load newer events", exact: true }).click();
  await page.locator('[data-journey-history="e106"]').waitFor();
  assert.equal(await page.locator(".journey-chart-heading").innerText(), rangeBefore);
  assert.ok(
    (await page.locator("[data-journey-selection]").innerText()).includes("Inventory reserved"),
  );
  freshEvents = [];
  await page.getByRole("button", { name: "Choose sales order", exact: true }).click();
  await page.getByRole("button", { name: /SO-10485/ }).click();
  await page.getByText("No recorded changes for this selection.", { exact: true }).waitFor();
  delayed = true;
  await page.getByRole("button", { name: "Choose sales order", exact: true }).click();
  await page.getByRole("button", { name: /SO-10484.*Klara Foods/ }).click();
  await page.getByRole("button", { name: "All activity", exact: true }).click();
  await page.locator('[data-journey-event="e3"]').waitFor();
  await page.waitForTimeout(850);
  assert.equal(await page.locator("[data-journey-edge]").count(), 0);
  // A company switch must discard a pending order read as well as pinned state.
  await page.getByRole("button", { name: "Choose sales order", exact: true }).click();
  const pending = page.waitForRequest((request) => request.url().includes("/order-journeys/d1"));
  await page.getByRole("button", { name: /SO-10484.*Klara Foods/ }).click();
  await pending;
  await page.evaluate(() => {
    history.pushState({}, "", "/app/inspector?tenant=t2&inspector_view=overview");
    dispatchEvent(new PopStateEvent("popstate"));
  });
  await page.getByText("No recorded changes for this selection.", { exact: true }).waitFor();
  await page.waitForTimeout(850);
  assert.equal(await page.locator("[data-journey-history]").count(), 0);
  delayed = false;
  for (language of ["de", "nl", "es"]) {
    await page.goto(
      `${process.env.WEB_BASE_URL || "http://localhost:5177"}/app/inspector?tenant=t1&inspector_view=overview&lang=${language}`,
    );
    await page.locator('[data-journey-event="e3"]').waitFor();
    await page.locator(".shell-chat-toggle").click();
    await page.locator(".journey-toolbar button").first().click();
    await page.getByRole("button", { name: /SO-10484.*Klara Foods/ }).click();
    await page.locator('[data-journey-event="e3"]').focus();
    await page.keyboard.press("Enter");
    await page.locator("[data-journey-selection]").waitFor();
    assert.ok(
      !(await page.locator(".journey-lane-label").first().innerText()).includes(
        "Recorded observations",
      ),
    );
    await page.evaluate(() => (document.documentElement.dataset.theme = "dark"));
    await page.screenshot({ path: `/tmp/reality-233-browser/${language}-dark.png` });
    await page.setViewportSize({ width: 390, height: 844 });
    await page
      .locator(".journey-chart-scroll")
      .evaluate((node) => (node.scrollLeft = node.scrollWidth));
    const label = await page.locator(".journey-lane-label").first().boundingBox();
    assert.ok(label.x >= 0 && label.x < 40, "lane labels remain visible after horizontal scroll");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.setViewportSize({ width: 1440, height: 1000 });
  }
  assert.deepEqual(errors, []);
  assert.deepEqual(writes, []);
  console.log("Order journey browser: passed; desktop and mobile screenshots saved.");
} catch (error) {
  console.error(errors, await page.locator("body").innerText());
  throw error;
} finally {
  await browser.close();
}
