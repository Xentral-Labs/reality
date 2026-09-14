// Browser interactions use HTTP fixtures; PostgreSQL tests prove shared business rules.
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
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
let language = "en",
  confirmed = 0,
  loseResponse = false,
  failRead = false;
const proposals = new Map(),
  records = new Map();
const tenant = "workspace_fixture";
const pager = (total) => ({
  number: 1,
  size: 50,
  total,
  pages: 1,
  has_next: false,
  has_previous: false,
});
const series = Array.from({ length: 30 }, (_, i) => ({
  date: `2026-08-${String(i + 1).padStart(2, "0")}`,
  created: [7, 8, 4, 3, 6][i % 5],
  shipped: [5, 3, 7, 0, 4][i % 5],
}));
const insights = {
  position: {
    open: 12,
    fully_reserved: 8,
    needs_reservation: 4,
    overdue: 2,
    unknown_due: 1,
    coverage_percent: "66.7",
  },
  series,
  window: { days: 30, start: "2026-08-01T00:00:00Z", end: "2026-08-30T12:00:00Z", timezone: "UTC" },
  observed_at: "2026-08-30T12:00:00Z",
};
for (const family of ["customer", "supplier", "item", "location"])
  records.set(family, {
    id: `${family}_one`,
    family,
    name: family === "item" ? "Desk lamp" : family === "location" ? "Main warehouse" : "Müller",
    sku: family === "item" ? "LAMP" : undefined,
    unit: family === "item" ? "pcs" : undefined,
    is_active: true,
    expected_revision: "rev1",
    source_record_id: "source_one",
  });
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
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
  if (path.endsWith("/analytics")) return reply(insights);
  if (path.endsWith("/analytics/contributors"))
    return reply({
      items: [{ id: "movement_one", kind: "movement", at: "2026-08-30T10:00:00Z" }],
      page: pager(1),
    });
  if (path.endsWith("/dashboard"))
    return reply({
      totals: { open_deliveries: 12, exceptions: 2, pending_decisions: 1 },
      exceptions: [],
      inventory: [],
      facts: [],
      capabilities: {},
    });
  if (path.endsWith("/master-data") && url.searchParams.get("q") === "paging") {
    const number = Math.min(Number(url.searchParams.get("page") || 1), 2);
    return reply({
      items: [records.get(url.searchParams.get("family"))],
      page: {
        number,
        size: 50,
        total: 51,
        pages: 2,
        has_next: number < 2,
        has_previous: number > 1,
      },
    });
  }
  if (path.endsWith("/master-data"))
    return reply({
      items:
        url.searchParams.get("q") === "missing"
          ? []
          : [records.get(url.searchParams.get("family"))],
      page: pager(url.searchParams.get("q") === "missing" ? 0 : 1),
    });
  if (path.includes("/inspector/"))
    return reply({
      title: "Original source",
      subtitle: "External reference",
      sections: [],
      technical_rows: [],
      source_payload: '{"name":"<script>unsafe</script>"}',
    });
  if (path.endsWith("/master-data/prepare")) {
    const body = req.postDataJSON();
    let proposal = proposals.get(body.request_id);
    if (!proposal) {
      proposal = {
        id: body.request_id,
        tool: `${["customer", "supplier"].includes(body.family) ? "party" : body.family}_${body.operation}`,
        status: "proposed",
        input: {
          records: [
            {
              ...body.record,
              ...(["customer", "supplier"].includes(body.family) ? { type: body.family } : {}),
            },
          ],
        },
        output: { records: [] },
        links: [],
      };
      proposals.set(proposal.id, proposal);
    }
    return reply(proposal);
  }
  if (path.includes("/master-data/proposals/")) {
    const id = path.split("/proposals/")[1].split("/")[0],
      proposal = proposals.get(id);
    if (path.endsWith("/confirm")) {
      assert.deepEqual(req.postDataJSON(), { confirmed: true });
      if (proposal.status === "proposed") {
        proposal.status = "executed";
        proposal.links = [{ family: proposal.tool.split("_")[0], id: "record_created" }];
        confirmed++;
      }
      if (loseResponse) {
        loseResponse = false;
        return route.abort("failed");
      }
    }
    if (failRead && req.method() === "GET") return reply({ detail: "Reference unavailable" }, 503);
    return proposal ? reply(proposal) : reply({ detail: "Not found" }, 404);
  }
  if (path.includes("/master-data/"))
    return reply(records.get(path.split("/master-data/")[1].split("/")[0]));
  if (path.endsWith("/change-proposals"))
    return reply({
      items: [...proposals.values()].map((p) => ({ ...p, created_at: "2026-08-30T12:00:00Z" })),
      page: pager(proposals.size),
    });
  if (path.includes("/suggestions/")) return reply({ items: [], allow_custom: true });
  return reply({ detail: "Fixture endpoint unavailable" }, 404);
});
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const out = process.env.UNIFIED_WORKSPACE_SCREENSHOTS || "/private/tmp/reality-108-browser";
await mkdir(out, { recursive: true });
try {
  await page.goto(`${base}/app?tenant=${tenant}`);
  await page.getByRole("button", { name: "Open analytics", exact: true }).click();
  await page.getByRole("heading", { name: "Understand the flow of your business." }).waitFor();
  await page.getByRole("button", { name: "90 days", exact: true }).click();
  assert.ok(page.url().includes("days=90"));
  await page.getByText("Daily values and supporting records", { exact: true }).click();
  await page.getByRole("button", { name: "Shipment movements 2026-08-01: 5", exact: true }).click();
  assert.ok(page.url().includes("metric=shipped"));
  await page.getByRole("button").filter({ hasText: "movement_one" }).click();
  await page.getByRole("dialog").waitFor();
  await page.keyboard.press("Escape");
  await page.goto(`${base}/app/warehouse?tenant=${tenant}&warehouse_view=movements`);
  const menu = page.locator(".register-actions > summary");
  await menu.click();
  await page.keyboard.press("Escape");
  assert.equal(await menu.evaluate((node) => node === document.activeElement), true);
  assert.equal(await page.locator(".register-actions[open]").count(), 0);
  const createLabels = {
    customer: "New customer",
    supplier: "New supplier",
    item: "New item",
    location: "New location",
  };
  for (const family of ["customer", "supplier", "item", "location"]) {
    await page.goto(`${base}/app/master-data?tenant=${tenant}&family=${family}`);
    assert.equal(await page.locator(".register-actions").count(), 0);
    const create = page.getByRole("button", { name: createLabels[family], exact: true });
    await create.focus();
    await page.keyboard.press("Enter");
    await page.getByRole("dialog").waitFor();
    await page.keyboard.press("Escape");
    assert.equal(await create.evaluate((node) => node === document.activeElement), true);
    await create.click();
    let dialog = page.getByRole("dialog");
    await dialog.getByRole("textbox", { name: "Name", exact: true }).fill(`New ${family}`);
    if (family === "item")
      await dialog.getByRole("textbox", { name: "SKU", exact: true }).fill("NEW");
    const before = confirmed;
    await dialog.getByRole("button", { name: "Prepare change", exact: true }).click();
    await dialog.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
    assert.equal(confirmed, before);
    const original = page.url();
    await page.reload();
    assert.equal(page.url(), original);
    dialog = page.getByRole("dialog");
    if (family === "item") loseResponse = true;
    await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
    if (family === "item") {
      await dialog.getByRole("button", { name: "Check outcome", exact: true }).click();
    }
    await dialog.getByText("Change recorded", { exact: true }).waitFor();
    assert.equal(confirmed, before + 1);
    await page.reload();
    await page.getByText("Change recorded", { exact: true }).waitFor();
    assert.equal(confirmed, before + 1);
  }
  await page.goto(`${base}/app/master-data?tenant=${tenant}&family=item&record=item_one`);
  await page.getByRole("button", { name: "Edit details", exact: true }).click();
  let dialog = page.getByRole("dialog");
  assert.equal(
    await dialog.getByRole("textbox", { name: "SKU", exact: true }).inputValue(),
    "LAMP",
  );
  // Every service field is editable now; the unit is a code input with tenant choices.
  assert.equal(
    await dialog.getByRole("combobox", { name: "Unit", exact: true }).inputValue(),
    "pcs",
  );
  await dialog.getByRole("textbox", { name: "Name", exact: true }).fill("New label");
  await dialog.getByRole("button", { name: "Prepare change", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  assert.ok(
    [...proposals.values()].some(
      (p) =>
        p.input.records[0].id === "item_one" && p.input.records[0].expected_revision === "rev1",
    ),
  );
  await page.reload();
  failRead = true;
  await page.reload();
  await page.getByRole("alert").waitFor();
  failRead = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  await page.getByRole("textbox", { name: "Search master data", exact: true }).fill("missing");
  await page.getByText("No matching records", { exact: true }).waitFor();
  await page.goto(`${base}/app/master-data?tenant=${tenant}&family=item&q=paging&page=99`);
  await page.getByRole("button", { name: "Previous", exact: true }).click();
  assert.equal(new URL(page.url()).searchParams.get("page"), null);
  for (language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        for (const workspace of ["analytics", "master-data"]) {
          await page.goto(`${base}/app/${workspace}?tenant=${tenant}&family=item&record=item_one`);
          await page.locator("h1").waitFor();
          if (workspace === "analytics") await page.locator('svg[role="img"]').waitFor();
          else await page.getByRole("heading", { name: "Desk lamp", exact: true }).waitFor();
          assert.ok(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            `${language}/${theme}/${width}/${workspace} overflow`,
          );
          await page.screenshot({
            path: `${out}/${language}-${theme}-${width}-${workspace}.png`,
            fullPage: true,
          });
          if (workspace === "master-data") {
            const copy = {
              en: ["Edit details", "Prepare change", "Confirm change"],
              de: ["Details bearbeiten", "Änderung vorbereiten", "Änderung bestätigen"],
              nl: ["Details bewerken", "Wijziging voorbereiden", "Wijziging bevestigen"],
              es: ["Editar detalles", "Preparar cambio", "Confirmar cambio"],
            }[language];
            await page.getByRole("button", { name: copy[0], exact: true }).click();
            await page.getByRole("dialog").waitFor();
            await page.screenshot({
              path: `${out}/${language}-${theme}-${width}-form.png`,
              fullPage: true,
            });
            await page
              .getByRole("dialog")
              .getByRole("button", { name: copy[1], exact: true })
              .click();
            await page
              .getByRole("dialog")
              .getByRole("button", { name: copy[2], exact: true })
              .waitFor();
            assert.ok(
              await page
                .getByRole("dialog")
                .evaluate((node) => node.scrollWidth <= node.clientWidth),
            );
            await page.screenshot({
              path: `${out}/${language}-${theme}-${width}-review.png`,
              fullPage: true,
            });
            await page.keyboard.press("Escape");
          }
        }
      }
  assert.deepEqual(errors, []);
  console.log(
    "PASS: analytics drill-down, four-family review/reload/confirm, lost response recovery without replay, edit snapshot, read retry, empty search, keyboard focus and 64 localized workspace/form/review screenshots.",
  );
} finally {
  await browser.close();
}
