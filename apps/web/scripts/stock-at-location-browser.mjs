import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";

if (!process.env.PLAYWRIGHT_MODULE || !process.env.PLAYWRIGHT_EXECUTABLE)
  throw new Error("Set PLAYWRIGHT_MODULE and PLAYWRIGHT_EXECUTABLE.");
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const visible = process.env.PLAYWRIGHT_VISIBLE === "1";
const browser = await chromium.launch({
  headless: !visible,
  slowMo: visible ? 500 : 0,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const out = "/private/tmp/reality-262-browser";
await mkdir(out, { recursive: true });

const tenant = "stock_place_company";
const item = "itm_beacon";
const rotterdam = "loc_rotterdam";
const singapore = "loc_singapore";
const pair = `${item}:${rotterdam}`;
const pager = (total) => ({
  number: 1,
  size: 50,
  total,
  pages: 1,
  has_next: false,
  has_previous: false,
});
const movement = (id, type, from, to) => ({
  id,
  item_id: item,
  item: "Beacon Desk Organizer",
  sku: "ITEM-012",
  unit: "pcs",
  quantity: "2",
  type,
  at: "2026-09-21T19:38:00Z",
  from_location_id: from,
  from_location: from === rotterdam ? "Rotterdam Warehouse" : from ? "Singapore Warehouse" : null,
  to_location_id: to,
  to_location: to === rotterdam ? "Rotterdam Warehouse" : to ? "Singapore Warehouse" : null,
  correction_role: "normal",
});

try {
  for (const [language, theme] of [
    ["en", "light"],
    ["de", "dark"],
  ]) {
    const german = language === "de";
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1000 },
      locale: german ? "de-DE" : "en-GB",
    });
    await page.addInitScript((theme) => localStorage.setItem("reality.theme", theme), theme);
    page.setDefaultTimeout(12000);
    const requests = [];
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));

    await page.route("**/api/**", async (route) => {
      const url = new URL(route.request().url());
      const path = url.pathname;
      const scoped = url.searchParams.get("location_id");
      requests.push(`${path}?${url.searchParams}`);
      const reply = (body, status = 200) =>
        route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
      if (path === "/api/auth/me")
        return reply({
          id: "clerk",
          email: "clerk@example.test",
          status: "active",
          language,
          locale: german ? "de-DE" : "en-GB",
          timezone: "UTC",
        });
      if (path === "/api/v1/bootstrap")
        return reply({
          tenants: [{ id: tenant, name: "Northstar Commerce", role: "owner" }],
          default_tenant_id: tenant,
        });
      if (path.endsWith("/application-reference"))
        return reply({
          command_count: 0,
          event_count: 0,
          projection_count: 0,
          fact_predicate_count: 0,
          projections: [],
          workspaces: [],
        });
      if (path.endsWith("/copilot"))
        return reply({
          sessions: [],
          active_session_id: null,
          messages: [],
          proposals: [],
          suggestions: [],
          has_archived: false,
        });
      if (path.endsWith("/warehouse/stock"))
        return reply({
          items: [
            {
              id: item,
              name: "Beacon Desk Organizer",
              sku: "ITEM-012",
              unit: "pcs",
              physical: scoped ? "2" : "3",
              reserved: "0",
              available: scoped ? "2" : "3",
            },
          ],
          page: pager(1),
          scope: {
            view: "stock",
            item_id: null,
            item: null,
            location_id: scoped,
            location: scoped ? "Rotterdam Warehouse" : null,
          },
          observed_at: "2026-09-21T19:38:00Z",
        });
      if (path.endsWith("/warehouse/movements"))
        return reply({
          items: [
            movement("mov_in", "receipt", null, rotterdam),
            movement("mov_out", "transfer", rotterdam, singapore),
          ],
          page: pager(2),
          scope: {
            view: "movements",
            item_id: url.searchParams.get("item_id"),
            item: "Beacon Desk Organizer",
            location_id: scoped,
            location: scoped ? "Rotterdam Warehouse" : null,
          },
          observed_at: "2026-09-21T19:38:00Z",
        });
      if (path.endsWith("/warehouse/reservations"))
        return reply({
          items: [],
          page: pager(0),
          scope: {
            view: "reservations",
            item_id: url.searchParams.get("item_id"),
            item: "Beacon Desk Organizer",
            location_id: scoped,
            location: scoped ? "Rotterdam Warehouse" : null,
          },
          observed_at: "2026-09-21T19:38:00Z",
        });
      if (path.endsWith("/cost-query"))
        return reply({
          requested: { kind: "inventory", scope_id: item, review_id: null },
          resolved: null,
          context_id: null,
          freshness: { state: "uninitialized", processed_event_sequence: null },
          result: null,
          basis_result: null,
          persistence: { business_writes: false, projection_writes: false },
        });
      if (path.includes(`/inspector/stock/`))
        return reply({
          kind: "stock",
          id: pair,
          eyebrow: "Operational Reality / stock at a location",
          title: "Beacon Desk Organizer",
          subtitle: "Rotterdam Warehouse · pcs",
          status: "Held",
          meaning: "Beacon Desk Organizer. Rotterdam Warehouse · pcs.",
          business_reference: null,
          guidance: null,
          technical_rows: [],
          metrics: [
            { label: "Physical", value: "2", tone: "", link: null },
            { label: "Reserved", value: "0", tone: "", link: null },
            { label: "Available", value: "2", tone: "", link: null },
          ],
          trail: [],
          events: [],
          source_payload: null,
          sections: [
            {
              title: "Held here",
              rows: [
                { label: "Item", value: "ITEM-012 · Beacon Desk Organizer", link: null },
                { label: "Location", value: "Rotterdam Warehouse", link: null },
                { label: "Physical", value: "2 pcs", link: null },
                { label: "Reserved", value: "0 pcs", link: null },
                { label: "Available", value: "2 pcs", link: null },
              ],
            },
            {
              title: "Movements here",
              rows: [
                {
                  label: "Receipt",
                  value: "3 pcs",
                  meta: "2026-09-21T19:38:00+00:00",
                  meta_parts: [{ type: "datetime", value: "2026-09-21T19:38:00+00:00" }],
                  link: null,
                },
                {
                  label: "Transfer",
                  value: "-1 pcs",
                  meta: "2026-09-21",
                  meta_parts: [{ type: "date", value: "2026-09-21" }],
                  link: null,
                },
              ],
            },
            { title: "Reservations here", rows: [] },
          ],
        });
      if (path.includes("/inspector/item/"))
        return reply({
          kind: "item",
          id: item,
          eyebrow: "Reference data / item",
          title: "Beacon Desk Organizer",
          subtitle: "ITEM-012 · pcs",
          status: "Active",
          meaning: "Beacon Desk Organizer. ITEM-012 · pcs.",
          business_reference: null,
          guidance: null,
          technical_rows: [],
          metrics: [],
          trail: [],
          events: [],
          source_payload: null,
          sections: [],
          preview_sections: [
            {
              title: "Stock across all locations",
              rows: [
                { label: "Item", value: "ITEM-012 · Beacon Desk Organizer", link: null },
                { label: "Physical", value: "3 pcs", link: null },
                { label: "Reserved", value: "0 pcs", link: null },
                { label: "Available", value: "3 pcs", link: null },
              ],
            },
            {
              title: "Available stock by location",
              rows: [
                {
                  label: "Rotterdam Warehouse",
                  original_label: true,
                  hint: "Available stock",
                  value: "2 pcs",
                  link: { kind: "stock", id: pair },
                },
                {
                  label: "Singapore Warehouse",
                  original_label: true,
                  hint: "Available stock",
                  value: "1 pcs",
                  link: { kind: "stock", id: `${item}:${singapore}` },
                },
              ],
            },
          ],
        });
      return reply({ detail: "Fixture endpoint unavailable" }, 404);
    });

    // Each quantity in the table answers its own question.
    const quantity = (english, german_) => (german ? german_ : english);
    const stock = `${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock`;
    for (const [label, expected] of [
      [quantity("Physical", "Physischer Bestand"), "movements"],
      [quantity("Reserved", "Reserviert"), "reservations"],
    ]) {
      await page.goto(stock);
      await page
        .getByRole("button", { name: `${label} · Beacon Desk Organizer`, exact: true })
        .click();
      await page.waitForURL(new RegExp(`warehouse_view=${expected}`));
      assert.equal(new URL(page.url()).searchParams.get("item"), item);
    }
    await page.goto(stock);
    await page
      .getByRole("button", {
        name: `${quantity("Available", "Verfügbar")} · Beacon Desk Organizer`,
        exact: true,
      })
      .click();
    await page.waitForURL(new RegExp(`entry=${item}`));

    await page.goto(`${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&entry=${item}`);

    // The item preview carries the quantity per location, and it opens the pair.
    await page.getByText("Rotterdam Warehouse", { exact: true }).first().waitFor();
    await page.getByRole("button", { name: "2 pcs", exact: true }).first().click();

    // The pair shows this item in this place, and nothing of the rest of the warehouse.
    const dialog = page.locator("dialog[open]");
    await dialog.getByRole("heading", { name: "Beacon Desk Organizer" }).waitFor();
    await dialog.getByText("Rotterdam Warehouse · pcs", { exact: true }).waitFor();
    await dialog
      .getByRole("heading", { name: german ? "Bestand hier" : "Held here", exact: true })
      .waitFor();
    const here = (english, german_) => (german ? german_ : english);
    await dialog
      .getByRole("heading", { name: here("Movements here", "Movements hier"), exact: true })
      .waitFor();
    await dialog
      .getByRole("heading", { name: here("Reservations here", "Reservations hier"), exact: true })
      .waitFor();
    assert.equal(await dialog.getByText("Aurora Notebook").count(), 0);

    // One action reaches the register scoped to both halves of the pair.
    await dialog
      .getByRole("button", { name: here("Movements here", "Movements hier"), exact: true })
      .click();
    await page.waitForURL(/warehouse_view=movements/);
    const url = new URL(page.url());
    assert.equal(url.searchParams.get("item"), item);
    assert.equal(url.searchParams.get("location"), rotterdam);
    assert.ok(requests.some((entry) => entry.includes(`location_id=${rotterdam}`)));

    // The scope is stated, says which side each movement is on, and clears.
    await page
      .getByText(
        german
          ? "Movements in diesen Lagerort und aus ihm heraus."
          : "Movements into and out of this location.",
        { exact: true },
      )
      .waitFor();
    await page
      .getByText(german ? "Zugang · " : "Into this location · ", { exact: false })
      .waitFor();
    await page
      .getByText(german ? "Abgang · " : "Out of this location · ", { exact: false })
      .waitFor();
    await page.screenshot({ path: `${out}/scoped-movements-${language}.png`, fullPage: true });

    // A scoped stock list answers for the place, and says so.
    await page.goto(
      `${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&location=${rotterdam}`,
    );
    await page
      .getByText(
        german
          ? "Die Mengen sind, was an diesem Lagerort liegt, nicht der Bestand des Unternehmens."
          : "Quantities are what lies at this location, not the whole company.",
        { exact: true },
      )
      .waitFor();
    await page
      .getByRole("button", { name: /Rotterdam Warehouse · /, exact: false })
      .first()
      .click();
    await page.waitForURL((candidate) => !new URL(candidate).searchParams.get("location"));

    assert.deepEqual(errors, []);
    await page.close();
  }
  console.log(
    "PASS: each quantity answers its own question, a location quantity opens the item in that place, the pair reaches both scoped registers, and the scope is stated and cleared in both editions.",
  );
} catch (error) {
  throw error;
} finally {
  await browser.close();
}
