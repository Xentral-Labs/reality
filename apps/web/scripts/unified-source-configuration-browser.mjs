// All API writes are intercepted; no shared company data is changed.
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
const out = "/private/tmp/reality-130-browser";
await mkdir(out, { recursive: true });
let releaseWrite;
let language = "en",
  mode = "ok",
  failRead = false;
const systems = [
  {
    id: "sys1",
    code: "shopify",
    name: "Main shop",
    description: "Original orders",
    is_active: true,
    record_count: 3,
  },
];
const capabilities = [
  {
    id: "cap1",
    system_id: "sys1",
    system: "Main shop",
    system_code: "shopify",
    source_type: "order",
    target_type: "sales_order",
    is_active: true,
    interpreter_available: true,
  },
];
const writes = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    p = u.pathname;
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (p === "/api/auth/me")
    return reply({
      id: "member",
      email: "member@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (p === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "main", name: "Main company", role: "member" },
        { id: "other", name: "Other company", role: "member" },
      ],
      default_tenant_id: "main",
    });
  if (p.endsWith("/copilot"))
    return reply({ sessions: [], messages: [], proposals: [], suggestions: [] });
  if (p.endsWith("/application-reference")) return reply({ workspaces: [] });
  const own = !p.includes("/other/");
  if (p.endsWith("/integrations"))
    return failRead
      ? reply({ detail: "Unavailable" }, 503)
      : reply({
          systems: own ? systems : [],
          capabilities: own ? capabilities : [],
          recent_records: [],
        });
  if (p.endsWith("/data-sources/systems"))
    return reply({
      items: own ? systems : [],
      page: { number: 1, size: 50, total: own ? systems.length : 0, pages: 1 },
    });
  if (p.endsWith("/evidence-documents"))
    return reply({ items: [], page: { number: 1, size: 50, total: 0, pages: 1 } });
  if (p.endsWith("/data-sources/records"))
    return reply({ items: [], page: { number: 1, size: 50, total: 0, pages: 1 } });
  if (req.method() !== "GET") {
    const body = req.postDataJSON();
    writes.push({ p, body });
    if (p.endsWith("/source-systems")) {
      if (systems.some((s) => s.code === body.code))
        return reply({ detail: "Source system code already exists: " + body.code }, 400);
      const row = { id: "sys" + (systems.length + 1), ...body, is_active: true, record_count: 0 };
      systems.push(row);
      if (mode === "held")
        await new Promise((resolve) => {
          releaseWrite = resolve;
        });
      return mode === "lost" ? route.abort("failed") : reply(row, 201);
    }
    if (p.endsWith("/active")) {
      const list = p.includes("source-capabilities") ? capabilities : systems;
      const row = list.find((x) => p.includes("/" + x.id + "/"));
      row.is_active = body.is_active;
      return mode === "lost" ? route.abort("failed") : reply(row);
    }
  }
  return reply({});
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const go = () => page.goto(base + "/app/data-sources?tenant=main");
const button = (name) => page.getByRole("button", { name, exact: true });
try {
  await go();
  await page.locator(".register-toolbar").waitFor();
  await page.getByRole("columnheader", { name: /^Source code/ }).waitFor();
  const surfaceBox = await page.locator(".register-surface").boundingBox();
  const tableBox = await page.locator("[data-source-table-inset] .erp-register").boundingBox();
  assert.ok(tableBox.x - surfaceBox.x >= 16);
  await page.screenshot({ path: out + "/systems-register.png", fullPage: true });
  await page
    .locator(".register-tabs")
    .getByRole("button", { name: "Received data", exact: true })
    .click();
  await page.getByRole("textbox", { name: "Exact system code", exact: true }).waitFor();

  await page.goto(base + "/app/data-sources?tenant=main&data_view=documents");
  await page.getByRole("textbox", { name: "Document type", exact: true }).waitFor();
  await page.screenshot({ path: out + "/documents-register.png", fullPage: true });
  await go();

  await page.locator(".register-actions > summary").waitFor();
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await button("Register source").click();
  await page.getByRole("dialog", { name: "Source configuration", exact: true }).waitFor();
  await page.getByRole("textbox", { name: "Source code", exact: true }).fill(" CATALOG ");
  await page.getByLabel("Source name", { exact: true }).fill("Catalog");
  await button("Review source").click();
  assert.equal(writes.length, 0);
  await button("Cancel").click();
  assert.equal(writes.length, 0);
  await button("Review source").click();
  await button("Confirm").click();
  await page.getByText("Source registered.", { exact: true }).waitFor();
  assert.equal(writes.length, 1);
  await page.getByText("No declared data types.", { exact: true }).waitFor();
  assert.equal(writes[0].body.code, "catalog");
  await button("Close").click();
  await page
    .locator("tbody")
    .getByRole("button", { name: "Settings", exact: true })
    .first()
    .click();
  await page.getByText("Declared data types", { exact: true }).waitFor();
  await button("Switch off this source").click();
  assert.equal(writes.length, 1);
  await button("Confirm").click();
  await page.getByText("Registry state saved.", { exact: true }).waitFor();
  assert.equal(systems[0].is_active, false);
  await button("Switch off this data type").click();
  await button("Confirm").click();
  assert.equal(capabilities[0].is_active, false);
  await page.getByText("Declared data types", { exact: true }).waitFor();
  await page.reload();
  await page.getByText("Declared data types", { exact: true }).waitFor();
  await page.screenshot({
    path: out + "/source-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await button("Close").click();
  await page.locator(".register-actions > summary").waitFor();
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await button("Register source").click();
  await page.getByRole("textbox", { name: "Source code", exact: true }).fill("catalog");
  await page.getByLabel("Source name", { exact: true }).fill("Duplicate");
  await button("Review source").click();
  await button("Confirm").click();
  await page.getByRole("alert").waitFor();
  await button("Cancel").click();
  await page.getByRole("textbox", { name: "Source code", exact: true }).fill("uncertain");
  await page.getByLabel("Source name", { exact: true }).fill("Uncertain source");
  await button("Review source").click();
  mode = "lost";
  await button("Confirm").click();
  await button("Check current configuration").waitFor();
  await page.waitForFunction(
    () => !document.querySelector("[data-source-review] button[data-check]")?.disabled,
  );
  const n = writes.length;
  await page.reload();
  await button("Check current configuration").waitFor();
  assert.equal(writes.length, n);
  failRead = true;
  await button("Check current configuration").click();
  await page.getByRole("alert").waitFor();
  assert.equal(await button("Confirm").isDisabled(), true);
  failRead = false;
  mode = "ok";
  await button("Check current configuration").click();
  await page
    .getByText("Current configuration loaded. This does not prove which request changed it.", {
      exact: true,
    })
    .waitFor();
  assert.equal(writes.length, n);
  await button("Close").click();
  await page
    .locator("tbody")
    .getByRole("button", { name: "Settings", exact: true })
    .first()
    .click();
  for (const lang of ["en", "de", "nl", "es"]) {
    language = lang;
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.reload();
      await page.locator("[data-source-configuration] article").waitFor();
      const headings = {
        en: "Declared data types",
        de: "Deklarierte Datentypen",
        nl: "Gedeclareerde gegevenstypen",
        es: "Tipos de datos declarados",
      };
      await page.getByText(headings[lang], { exact: true }).waitFor();
      await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
        true,
      );
      await page.screenshot({
        path: `${out}/${lang}-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
    }
  }
  language = "en";
  await page.setViewportSize({ width: 1440, height: 1000 });
  await go();
  await page
    .locator("tbody")
    .getByRole("button", { name: "Settings", exact: true })
    .first()
    .click();
  const panel = page.locator("[data-source-configuration]");
  // The dialog is settings only: it offers no navigation of its own.
  assert.equal(await panel.getByRole("button", { name: "View received records" }).count(), 0);
  await panel.getByRole("button", { name: "Close", exact: true }).click();
  await page
    .locator("tbody")
    .getByRole("button", { name: "Received data", exact: true })
    .first()
    .click();
  assert.equal(new URL(page.url()).searchParams.get("source_system"), "shopify");
  await go();
  capabilities.push(
    ...Array.from({ length: 29 }, (_, i) => ({
      ...capabilities[0],
      id: `extra${i}`,
      source_type: `type_${i}`,
      interpreter_available: false,
    })),
  );
  await page
    .locator("tbody")
    .getByRole("button", { name: "Settings", exact: true })
    .first()
    .click();
  await page.waitForFunction(
    () => document.querySelectorAll("[data-source-configuration] article").length === 25,
  );
  await panel.getByRole("button", { name: "Next", exact: true }).click();
  assert.equal(await panel.locator("article").count(), 5);
  await button("Close").click();
  await page.locator(".register-actions > summary").waitFor();
  if (await page.locator(".register-actions:not([open]) > summary").count())
    await page.locator(".register-actions > summary").click();
  await button("Register source").click();
  await page.getByRole("textbox", { name: "Source code", exact: true }).fill("delayed");
  await page.getByLabel("Source name", { exact: true }).fill("Delayed source");
  await button("Review source").click();
  const beforeHeld = writes.length;
  mode = "held";
  await button("Confirm").evaluate((button) => {
    button.click();
    button.click();
  });
  await page.waitForFunction(() => document.querySelector("[data-source-review] button")?.disabled);
  for (let i = 0; !releaseWrite && i < 100; i++) await page.waitForTimeout(20);
  assert.equal(writes.length, beforeHeld + 1);
  assert.ok(releaseWrite);
  await page.keyboard.press("Escape");
  assert.equal(await panel.isVisible(), true);
  assert.equal(await panel.getByRole("button", { name: "Close", exact: true }).isDisabled(), true);
  await page.goto(base + "/app/data-sources?tenant=other");
  releaseWrite();
  mode = "ok";
  await page.getByRole("heading", { name: "No matching records", exact: true }).waitFor();
  assert.equal(await page.locator("[data-source-configuration]").count(), 0);
  await page.waitForTimeout(100);
  assert.equal(new URL(page.url()).searchParams.get("tenant"), "other");
  assert.equal(writes.length, beforeHeld + 1);
  await page.goto(base + "/app/data-sources?tenant=other&entry=sys1");
  await page.getByText("Source definition not found.", { exact: true }).waitFor();
  assert.equal(await button("Switch off this source").count(), 0);
  failRead = true;
  await page.goto(base + "/app/data-sources?tenant=main&entry=sys1");
  await page.getByText("Could not load this view", { exact: true }).waitFor();
  assert.equal(await button("Switch on this source").count(), 0);
  failRead = false;
  await button("Retry").click();
  await button("Check current configuration").waitFor();
  assert.equal(await button("Confirm").isDisabled(), true);
  await button("Check current configuration").click();
  await page.getByText("Declared data types", { exact: true }).waitFor();
  assert.deepEqual(errors, []);
  console.log(
    "PASS source registration, review/cancel, normalized values, duplicate, flags, unknown response/reload/read failure, foreign context, type pagination, evidence navigation, single flight, in-flight company switch and 8 localized dark responsive views.",
  );
} catch (e) {
  console.error("Browser errors:", errors);
  await page.screenshot({ path: out + "/error.png", fullPage: true, animations: "disabled" });
  throw e;
} finally {
  await browser.close();
}
