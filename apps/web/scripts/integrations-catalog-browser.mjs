// HTTP fixtures prove presentation; PostgreSQL tests prove scoped metadata and evidence queries.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const requests = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let userId = "operator";
let language = "en",
  fail = false;
const tenant = "source_fixture",
  source = "src_2",
  out = "/private/tmp/reality-111-browser";
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
      id: userId,
      email: "operator@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: tenant, name: "Northstar Commerce" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.includes("/data-sources/") || path.endsWith("/evidence-documents")) {
    if (fail) return reply({ detail: "Sources unavailable" }, 503);
    const empty = u.searchParams.get("q") === "missing",
      n = Number(u.searchParams.get("page") || 1);
    const view = path.endsWith("/systems")
      ? "systems"
      : path.endsWith("/records")
        ? "records"
        : "documents";
    const system = {
      id: "sys1",
      code: "sample-shop",
      name: "Sample shop",
      description: "Sales orders from the sample store",
      is_active: true,
      record_count: 51,
    };
    const record = {
      id: n === 1 ? source : "src_1",
      source_system: "sample-shop",
      source_type: "order",
      external_id: "ORDER-1042",
      version: n === 1 ? 2 : 1,
      received_at: "2026-09-07T10:00:00Z",
      supersedes_source_record_id: n === 1 ? "src_1" : null,
      job_status: n === 1 ? "completed" : null,
    };
    const doc = {
      id: "doc1",
      number: "ORDER-1042",
      date: "2026-09-07",
      type: "sales_order",
      party: "Müller",
      currency: "EUR",
      gross_amount: "600",
      line_count: 1,
      source: { system: "sample-shop", type: "order", external_id: "ORDER-1042" },
      status: "recorded",
    };
    return reply({
      items: empty ? [] : [view === "systems" ? system : view === "records" ? record : doc],
      page: {
        number: empty ? 1 : n,
        size: 50,
        total: empty ? 0 : 51,
        pages: empty ? 1 : 2,
        has_next: !empty && n === 1,
        has_previous: !empty && n > 1,
      },
    });
  }
  if (path.includes("/inspector/"))
    return reply({
      title: "Original source evidence",
      subtitle: "ORDER-1042",
      meaning: "One received version",
      sections: [],
      technical_rows: [],
      source_payload: '{"untrusted":"<script>alert(1)</script>"}',
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
await mkdir(out, { recursive: true });
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
try {
  await page.goto(`${base}/app/data-sources?tenant=${tenant}`);
  await page.getByRole("button", { name: "Add integration", exact: true }).click();
  await page.getByRole("textbox", { name: "Search providers" }).fill("Shopware");
  await page.getByRole("button", { name: "Prepare Shopware 6", exact: true }).click();
  await page.getByRole("textbox", { name: "Connection name", exact: true }).fill("DE Shop");
  await page.getByRole("dialog").getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("checkbox", { name: "Orders", exact: true }).check();
  await page.getByRole("button", { name: "Review", exact: true }).click();
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  assert.equal(await page.getByText("DE Shop", { exact: true }).count(), 1);
  await page.reload();
  await page.getByText("DE Shop", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Open preparation", exact: true }).click();
  await page.getByRole("textbox", { name: "Connection name", exact: true }).fill("Changed shop");
  await page.keyboard.press("Escape");
  assert.equal(await page.getByText("DE Shop", { exact: true }).count(), 1);
  await page.goto(`${base}/app/data-sources?tenant=other`);
  await page.getByRole("button", { name: "Add integration", exact: true }).waitFor();
  assert.equal(await page.getByText("DE Shop", { exact: true }).count(), 0);
  await page.goto(`${base}/app/data-sources?tenant=${tenant}`);
  await page.getByText("DE Shop", { exact: true }).waitFor();
  await page.screenshot({ path: "/private/tmp/integrations-desktop.png" });
  await page.getByRole("button", { name: "Remove draft", exact: true }).click();
  assert.equal(await page.getByText("DE Shop", { exact: true }).count(), 0);
  await page.getByRole("button", { name: "Add integration", exact: true }).click();
  const modal = page.getByRole("dialog");
  assert.equal(await modal.locator("input[type=password]").count(), 0);
  for (const name of [
    "Shopify",
    "Shopware 6",
    "Xentral",
    "Shopify Payments",
    "Stripe",
    "PayPal",
    "HubSpot",
    "Salesforce",
    "Akeneo",
    "Pimcore",
  ]) {
    assert.equal(
      await modal.getByRole("button", { name: `Prepare ${name}`, exact: true }).count(),
      1,
    );
  }
  await page.getByRole("combobox", { name: "Provider category" }).selectOption("CRM");
  assert.equal(await modal.getByRole("button", { name: /^Prepare / }).count(), 2);
  await page.getByRole("textbox", { name: "Search providers" }).fill("missing");
  await page.getByText("No providers match your search.").waitFor();
  await page.getByRole("textbox", { name: "Search providers" }).fill("");
  await page.getByRole("combobox", { name: "Provider category" }).selectOption("");
  await page.getByRole("button", { name: "Prepare Shopify Payments", exact: true }).click();
  assert.equal(await modal.getByRole("button", { name: "Next", exact: true }).isDisabled(), true);
  await page.getByRole("textbox", { name: "Related Shopify shop" }).fill("DE shop");
  await modal.getByRole("button", { name: "Next", exact: true }).click();
  assert.equal(await modal.getByRole("button", { name: "Review", exact: true }).isDisabled(), true);
  await page.getByRole("checkbox", { name: "Payments", exact: true }).check();
  await modal.getByRole("button", { name: "Review", exact: true }).click();
  await page.evaluate(() => {
    window.originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = () => {
      throw new Error("Blocked");
    };
  });
  await modal.getByRole("button", { name: "Save draft", exact: true }).click();
  await modal.getByRole("alert").waitFor();
  await page.evaluate(() => {
    Storage.prototype.setItem = window.originalSetItem;
  });
  await modal.getByRole("button", { name: "Save draft", exact: true }).click();
  await page.getByRole("button", { name: "Open preparation", exact: true }).waitFor();
  userId = "another-user";
  await page.reload();
  await page.getByRole("button", { name: "Add integration", exact: true }).waitFor();
  assert.equal(
    await page.getByRole("button", { name: "Open preparation", exact: true }).count(),
    0,
  );
  userId = "operator";
  await page.reload();
  await page.getByRole("button", { name: "Open preparation", exact: true }).click();
  await page.getByRole("textbox", { name: "Connection name", exact: true }).fill("Payment account");
  await modal.getByRole("button", { name: "Next", exact: true }).click();
  await modal.getByRole("button", { name: "Review", exact: true }).click();
  await modal.getByRole("button", { name: "Save draft", exact: true }).click();
  await page.getByText("Payment account", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Add integration", exact: true }).click();
  await modal.getByRole("button", { name: "Prepare Shopify Payments", exact: true }).click();
  await page.getByRole("textbox", { name: "Related Shopify shop" }).fill("Another shop");
  await modal.getByRole("button", { name: "Next", exact: true }).click();
  await modal.getByRole("checkbox", { name: "Payments", exact: true }).check();
  await modal.getByRole("button", { name: "Review", exact: true }).click();
  await modal.getByRole("button", { name: "Save draft", exact: true }).click();
  assert.equal(
    await page.getByRole("button", { name: "Open preparation", exact: true }).count(),
    2,
  );
  await page.evaluate(() => {
    sessionStorage.setItem(
      "reality.integration-preparations.v1:operator:source_fixture",
      "invalid JSON",
    );
  });
  await page.reload();
  await page
    .getByText("Saved preparations could not be loaded. You can start a new draft.")
    .waitFor();
  await page.evaluate(() =>
    sessionStorage.removeItem("reality.integration-preparations.v1:operator:source_fixture"),
  );
  fail = true;
  await page.reload();
  await page.getByRole("button", { name: "Add integration", exact: true }).click();
  await modal.getByRole("button", { name: "Prepare Shopware 6", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  fail = false;
  for (const [lang, add, prepare] of [
    ["en", "Add integration", "Prepare"],
    ["de", "Integration hinzufügen", "Vorbereiten"],
    ["nl", "Integratie toevoegen", "Voorbereiden"],
    ["es", "Añadir integración", "Preparar"],
  ]) {
    language = lang;
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.reload();
      await page.getByRole("button", { name: add, exact: true }).click();
      await modal.getByRole("button", { name: `${prepare} Shopware 6`, exact: true }).waitFor();
      await page.screenshot({ path: `/private/tmp/integrations-catalog-${lang}-${width}.png` });
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
        true,
      );
      await page.evaluate(() => (document.documentElement.dataset.theme = "dark"));
      await page.screenshot({
        path: `/private/tmp/integrations-catalog-${lang}-${width}-dark.png`,
      });
      await page.keyboard.press("Escape");
      assert.equal(
        await page
          .getByRole("button", { name: add, exact: true })
          .evaluate((el) => el === document.activeElement),
        true,
      );
    }
  }
  assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
  assert.deepEqual(errors, []);
  console.log(
    "Integration preparation: selection, save, reload, cancellation, tenant isolation and removal passed; no API mutations.",
  );
} finally {
  await browser.close();
}
