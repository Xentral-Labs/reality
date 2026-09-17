import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { reference } from "./tool-catalog-fixture.mjs";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [],
  writes = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  fail = false,
  owner = true;
await page.route("**/api/**", (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  if (req.method() !== "GET") writes.push(path);
  const reply = (value, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(value) });
  if (path === "/api/auth/me")
    return reply({
      id: "u",
      email: "u@example.test",
      status: "active",
      language,
      locale: language === "de" ? "de-DE" : "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "a", name: "Northstar", role: owner ? "owner" : "member" },
        { id: "b", name: "Second company", role: "owner" },
      ],
      default_tenant_id: "a",
    });
  if (path.endsWith("application-reference"))
    return fail ? reply({ detail: "Catalog unavailable" }, 503) : reply(reference);
  if (path.endsWith("copilot"))
    return reply({
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
      active_session_id: null,
    });
  if (path.includes("projection"))
    return reply({
      items: [],
      page: { total: 0, number: 1, size: 50, pages: 1 },
      metadata: {
        state: "ready",
        completed_at: "2026-09-17T10:00:00Z",
        processed_event_sequence: 1,
        target_event_sequence: 1,
      },
    });
  return reply({
    items: [],
    parties: [],
    locations: [],
    commitments: [],
    page: { total: 0, number: 1, size: 50, pages: 1 },
  });
});
const base = process.env.WEB_BASE_URL || "http://localhost:5227";
try {
  for (const view of ["commands", "views"]) {
    await page.goto(`${base}/app/inspector?tenant=a&inspector_view=${view}`);
    await page.locator("[data-tool-capability]").first().waitFor();
    assert.equal(
      await page.locator("[data-tool-capability]").count(),
      reference.tool_catalog.entries.length,
    );
    assert.equal(await page.locator("[data-shell-header] .register-tabs").count(), 0);
    await page.getByRole("searchbox", { name: "Search capabilities" }).fill("inventory_read");
    assert.equal(await page.locator("[data-tool-capability]").count(), 1);
    await page.locator(".tool-capability").click();
    await page.locator(".tool-technical-details > summary").click();
    await page.locator('[data-tool-mcp="inventory_read"]').waitFor();
    await page.locator("[data-tool-report-open]").click();
    await page.getByRole("dialog").waitFor();
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: "Use in chat", exact: true }).click();
    const draft = page.locator("#global-chat textarea");
    await draft.waitFor();
    assert.match(await draft.inputValue(), /inventory_read/);
    await draft.fill("Keep my existing draft.");
    await page.getByRole("button", { name: "Use in chat", exact: true }).click();
    assert.match(await draft.inputValue(), /^Keep my existing draft\./);
    await page.getByRole("button", { name: "Reset filters", exact: true }).click();
    await page.getByRole("combobox", { name: "Topic", exact: true }).selectOption("stock");
    await page.getByRole("combobox", { name: "Purpose", exact: true }).selectOption("change");
    assert.ok((await page.locator("[data-tool-capability]").count()) > 0);
    assert.equal(await page.locator('[data-tool-capability="report:inventory"]').count(), 0);
    await page.locator('[data-tool-capability="form:reserve"] > button').click();
    await page.getByRole("button", { name: "Reserve stock", exact: true }).click();
    await page.getByRole("dialog").waitFor();
    await page.keyboard.press("Escape");
  }
  for (language of ["de", "nl", "es"]) {
    await page.goto(`${base}/app/inspector?tenant=a&inspector_view=commands`);
    await page.locator("[data-tool-capability]").first().waitFor();
    const search = page.locator("[data-tool-catalog] input[type=search]");
    await search.fill(language === "de" ? "reservieren" : "inventory_read");
    assert.ok((await page.locator("[data-tool-capability]").count()) > 0);
    if (language === "de") {
      await search.fill("");
      await page.screenshot({ path: "/private/tmp/reality-tools-de.png", animations: "disabled" });
      await page.setViewportSize({ width: 390, height: 844 });
      if (await page.locator("#global-chat").isVisible())
        await page
          .locator("#global-chat")
          .getByRole("button", { name: "Chat ausblenden", exact: true })
          .click();
      await page.screenshot({
        path: "/private/tmp/reality-tools-mobile.png",
        animations: "disabled",
      });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.evaluate(() => {
        localStorage.setItem("reality.theme", "dark");
        window.dispatchEvent(new Event("reality:theme-changed"));
      });
      await page.screenshot({
        path: "/private/tmp/reality-tools-dark.png",
        animations: "disabled",
      });
      await search.fill("order_explain");
      await page.locator(".tool-capability").click();
      await page.locator(".tool-technical-details > summary").click();
      await page.locator('[data-tool-mcp="order_explain"] summary').click();
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({
        path: "/private/tmp/reality-tools-detail-mobile.png",
        animations: "disabled",
      });
      await page.setViewportSize({ width: 1440, height: 1000 });
    }
  }
  language = "en";
  owner = false;
  await page.goto(`${base}/app/inspector?tenant=a&inspector_view=commands`);
  await page.locator('[data-tool-capability="command:create_invitation"] > button').click();
  assert.equal(await page.getByRole("button", { name: "Manage members", exact: true }).count(), 0);
  fail = true;
  await page.goto(`${base}/app/inspector?tenant=b&inspector_view=views`);
  await page.locator("main").getByText("Catalog unavailable", { exact: true }).waitFor();
  assert.equal(await page.locator("[data-tool-capability]").count(), 0);
  assert.deepEqual(writes, []);
  assert.deepEqual(errors, []);
  console.log(
    "PASS unified tools: complete metadata, legacy URLs, filters, MCP details, forms/reports, draft preservation, member eligibility, errors, languages and mobile",
  );
} finally {
  await browser.close();
}
