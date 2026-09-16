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
  if (path.endsWith("/integrations"))
    return reply({
      systems: [{ id: "sys1", code: "sample-shop", name: "Sample shop", is_active: true }],
      capabilities: [],
      recent_records: [],
    });
  if (path.endsWith("/facts"))
    return reply({
      items: [],
      subject_types: [],
      subject_types_has_more: false,
      page: { number: 1, size: 50, total: 0, pages: 0 },
    });
  if (path.includes("/inspector/"))
    return reply({
      title: "Original source evidence",
      subtitle: "ORDER-1042",
      meaning: "One received version",
      sections: path.includes("source_record")
        ? [
            {
              title: "Linked items",
              rows: [
                { label: "Record", value: "Imported lamp", link: { kind: "item", id: "item1" } },
              ],
            },
          ]
        : [],
      technical_rows: [],
      source_payload: '{"untrusted":"<script>alert(1)</script>"}',
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
await mkdir(out, { recursive: true });
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
try {
  await page.goto(`${base}/app/data-sources?tenant=${tenant}`);
  await page
    .locator("[data-shell-header]")
    .getByRole("heading", { name: /^Integrations/ })
    .waitFor();

  assert.equal(await page.locator(".register-tabs button").count(), 2);
  async function assertVisibleActions(labels) {
    const cell = page.locator("[data-source-row] .erp-actions-cell").first();
    for (const label of labels) {
      const button = cell.getByRole("button", { name: label, exact: true });
      await button.waitFor();
      await button.scrollIntoViewIfNeeded();
      assert.ok(
        await button.evaluate((element) => {
          const box = element.getBoundingClientRect();
          return element.contains(
            document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2),
          );
        }),
        `action is not covered: ${label}`,
      );
      assert.equal(await button.innerText(), label, `visible action: ${label}`);
      assert.ok(
        await button.evaluate((element) => {
          const range = document.createRange();
          range.selectNodeContents(element);
          const text = range.getBoundingClientRect();
          const bounds = element.getBoundingClientRect();
          return (
            parseFloat(getComputedStyle(element).fontSize) >= 12 &&
            text.width > 20 &&
            text.left >= bounds.left &&
            text.right <= bounds.right
          );
        }),
        `unclipped action: ${label}`,
      );
      assert.equal(await button.locator(".sr-only, .lucide-external-link").count(), 0);
    }
  }
  await assertVisibleActions(["Settings", "Received data"]);
  await page.locator("tbody").getByRole("button", { name: "Settings", exact: true }).click();
  await page.getByRole("dialog", { name: "Source configuration", exact: true }).waitFor();
  assert.equal(new URL(page.url()).searchParams.get("entry"), "sys1");
  await page.keyboard.press("Escape");
  await page.locator("tbody").getByRole("button", { name: "Received data", exact: true }).click();
  await page.locator("tbody tr").waitFor();
  assert.ok(page.url().includes("source_system=sample-shop"));
  async function assertFooter() {
    const register = page.locator(".erp-register");
    assert.equal(await register.locator(".erp-register-footer").count(), 1);
    assert.equal(await register.locator(".erp-register-footer select").count(), 1);

    assert.equal(
      await register.evaluate(
        (el) =>
          !!(
            el
              .querySelector("table")
              .compareDocumentPosition(el.querySelector(".erp-register-footer")) &
            Node.DOCUMENT_POSITION_FOLLOWING
          ),
      ),
      true,
    );
  }
  await assertFooter();
  await assertVisibleActions(["Open details", "View observations"]);
  await page
    .locator("tbody")
    .getByRole("button", { name: "View observations", exact: true })
    .click();
  await page.waitForURL(/fact_source=src_2/);
  assert.equal(new URL(page.url()).pathname, "/app/facts");
  await page.goBack();
  await assertVisibleActions(["Open details", "View observations"]);
  const inspect = page.locator("tbody").getByRole("button", { name: "Open details", exact: true });
  await inspect.focus();
  await page.keyboard.press("Enter");
  await page.getByRole("dialog").waitFor();
  const itemRead = page.waitForResponse((response) =>
    response.url().includes("/inspector/item/item1"),
  );
  await page.getByRole("button", { name: "Imported lamp", exact: true }).click();
  await itemRead;
  assert.ok(requests.some((r) => r.path.includes("/inspector/item/item1")));
  await page.getByRole("dialog").getByRole("button", { name: "Back", exact: true }).click();
  await page.getByRole("button", { name: "Imported lamp", exact: true }).waitFor();
  await page.locator("dialog summary").last().click();
  assert.ok((await page.locator("pre[data-original-content]").innerText()).includes("<script>"));
  assert.equal(await page.locator("dialog script").count(), 0);
  await page.keyboard.press("Escape");
  assert.equal(await inspect.evaluate((n) => n === document.activeElement), true);
  await inspect.click();
  await page.reload();
  await page.getByRole("dialog").waitFor();
  await page.keyboard.press("Escape");
  await page.goto(
    `${base}/app/data-sources?tenant=${tenant}&data_view=documents&source_record=src_2&source_system=sample-shop`,
  );
  await page.locator("tbody tr").waitFor();
  await assertFooter();
  assert.ok(page.url().includes("source_record=src_2"));
  assert.ok(
    requests.some(
      (r) => r.path.endsWith("/evidence-documents") && r.query.includes("source_record_id=src_2"),
    ),
  );
  await page.getByRole("button", { name: "Explain", exact: true }).click();
  await page.getByRole("dialog").waitFor();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Clear source version", exact: true }).click();
  assert.equal(new URL(page.url()).searchParams.has("source_record"), false);
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.waitForURL(/page=2/);
  await page.getByRole("textbox", { name: "Search data", exact: true }).fill("missing");
  await page.getByRole("heading", { name: "No matching records", exact: true }).waitFor();
  fail = true;
  await page.reload();
  await page.getByRole("alert").waitFor();
  fail = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.getByRole("heading", { name: "No matching records", exact: true }).waitFor();
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="other"]').click();
  for (const key of ["entry", "source_system", "source_record", "q"])
    assert.equal(new URL(page.url()).searchParams.has(key), false);
  for (language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        for (const view of ["systems", "records", "documents"]) {
          await page.goto(`${base}/app/data-sources?tenant=${tenant}&data_view=${view}`);
          await page.locator("[data-source-row]").first().waitFor();
          assert.ok(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            `${language}/${theme}/${width}/${view}`,
          );
          if (view !== "documents") {
            const labels = {
              en: {
                systems: ["Settings", "Received data"],
                records: ["Open details", "View observations"],
              },
              de: {
                systems: ["Einstellungen", "Empfangene Daten"],
                records: ["Details öffnen", "Beobachtungen ansehen"],
              },
              nl: {
                systems: ["Instellingen", "Ontvangen gegevens"],
                records: ["Details openen", "Waarnemingen bekijken"],
              },
              es: {
                systems: ["Configuración", "Datos recibidos"],
                records: ["Abrir detalles", "Ver observaciones"],
              },
            }[language][view];
            for (const density of ["compact", "normal"]) {
              await page.locator(".erp-table-tools select").selectOption(density);
              await assertVisibleActions(labels);
            }
            await page
              .locator("[data-source-row] .erp-actions-cell button")
              .last()
              .scrollIntoViewIfNeeded();
          }
          await page.screenshot({
            path: `${out}/${language}-${theme}-${width}-${view}.png`,
            fullPage: true,
          });
        }
      }
  assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: systems → source version → exact evidence, escaped original, Inspector reload/focus, paging, filters, retry, company reset, no writes and 48 localized screenshots.",
  );
} catch (error) {
  console.error({ url: page.url(), body: await page.locator("body").innerText(), errors });
  throw error;
} finally {
  await browser.close();
}
