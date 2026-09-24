// Spec 263: a settled decision stays findable and says who settled it, and how.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const pager = (size, total) => ({
  number: 1,
  size,
  total,
  pages: Math.max(1, Math.ceil(total / size)),
  has_previous: false,
  has_next: size < total,
});
const token = {
  kind: "mcp_token",
  token_name: "Claude Desktop",
  token_prefix: "ros_mcp_abc",
  revoked: false,
  issuer: "Olga Owner",
};
const proposal = (id, status, decider, tool = "item_create") => ({
  id,
  tool,
  actor_type: "agent",
  status,
  input: { records: [{ sku: "DOG-1", name: "Dog food" }] },
  output: {},
  created_at: "2026-09-24T05:42:10Z",
  decided_at: status === "proposed" ? null : "2026-09-24T05:42:13Z",
  decided_by: decider.kind === "person" ? decider.name : null,
  decider,
  review_kind: "common",
  review_destination: "proposal-review",
  review_label: "Create item",
  review_purpose: "",
});
const settled = [
  proposal("act_token", "executed", token),
  proposal("act_person", "rejected", { kind: "person", name: "Anna Owner" }),
];
const pending = [proposal("act_open", "proposed", { kind: "unknown" })];
const expected = {
  en: {
    token: "Confirmed through token Claude Desktop, issued by Olga Owner",
    person: "Rejected by Anna Owner",
    history: "History",
  },
  de: {
    token: "Bestätigt über MCP-Token Claude Desktop, ausgestellt von Olga Owner",
    person: "Abgelehnt von Anna Owner",
    history: "Verlauf",
  },
};
try {
  for (const language of ["en", "de"]) {
    const words = expected[language];
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.setDefaultTimeout(12000);
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const reads = [];
    await page.route("**/api/**", async (route) => {
      const url = new URL(route.request().url());
      const path = url.pathname;
      const reply = (data) =>
        route.fulfill({ contentType: "application/json", body: JSON.stringify(data) });
      if (path === "/api/auth/me")
        return reply({
          id: "owner",
          email: "owner@example.test",
          status: "active",
          language,
          locale: language === "de" ? "de-DE" : "en-GB",
          timezone: "UTC",
        });
      if (path === "/api/v1/bootstrap")
        return reply({
          tenants: [{ id: "demo", name: "CanisPro", role: "owner" }],
          default_tenant_id: "demo",
        });
      const review = path.match(/^\/api\/tenants\/demo\/change-proposals\/([^/]+)\/review$/);
      if (review) {
        const row = [...settled, ...pending].find((item) => item.id === review[1]);
        return reply({
          id: row.id,
          tool: row.tool,
          label: "Create item",
          purpose: "",
          review_kind: "common",
          status: row.status,
          actor_type: row.actor_type,
          created_at: row.created_at,
          decided_at: row.decided_at,
          decider: row.decider,
          input: row.input,
          preview: {},
          receipt: { records: [{ family: "item", id: "itm_1" }] },
          next_step: {
            review_required: true,
            required_principal: "authorized_human",
            reconciliation_read: "proposal_execution_status",
            verification_reads: [],
          },
          confirmable: row.status === "proposed",
          rejectable: row.status === "proposed",
          message: "",
        });
      }
      if (path === "/api/tenants/demo/change-proposals") {
        const status = url.searchParams.get("status");
        const size = Number(url.searchParams.get("size") || 50);
        reads.push({ status, size });
        const items = status === "history" ? settled : pending;
        return reply({ items, page: pager(size, items.length) });
      }
      if (path.endsWith("/dashboard"))
        return reply({ totals: { open_deliveries: 0, exceptions: 0, pending_decisions: 1 } });
      if (path.endsWith("/activity-volume") || path.endsWith("/readiness"))
        return route.fulfill({ status: 503, body: "Unavailable in decision fixture" });
      if (path.endsWith("/copilot"))
        return reply({
          sessions: [],
          active_session_id: null,
          messages: [],
          proposals: [],
          suggestions: [],
          has_archived: false,
        });
      return reply({ items: [], workspaces: [], commands: [], page: pager(50, 0) });
    });

    // The queue still opens on what waits; history is one tab away.
    await page.goto(`${base}/app/decisions?tenant=demo`);
    const historyTab = page.getByRole("button", { name: words.history, exact: true });
    await historyTab.waitFor();
    assert.equal(await historyTab.getAttribute("aria-pressed"), "false");
    await historyTab.click();
    await page.waitForURL(/decisions_view=history/);
    const tokenRow = page.locator("[data-work-row]").filter({ hasText: words.token });
    await tokenRow.waitFor();
    assert.ok(
      await page.locator("[data-work-row]").filter({ hasText: words.person }).count(),
      "a rejection is attributed like an approval",
    );
    const historyRead = reads.find((read) => read.status === "history");
    assert.equal(historyRead.size, 25, "history is read 25 rows at a time");

    // Opening a settled decision states who settled it and how.
    await tokenRow.click();
    await page
      .getByRole("button", {
        name: language === "de" ? "Entscheidung öffnen" : "Open the decision",
      })
      .click();
    const dialog = page.locator("dialog[open]");
    await dialog.waitFor();
    await dialog.locator("[data-decision-attribution]").filter({ hasText: words.token }).waitFor();
    assert.equal(
      await dialog
        .getByRole("button", { name: language === "de" ? "Bestätigen" : "Confirm" })
        .count(),
      0,
      "a settled decision cannot be confirmed again",
    );

    // The link a record or an activity carries opens the same decision directly.
    await page.goto(`${base}/app/decisions?tenant=demo&decisions_view=history&proposal=act_token`);
    await page
      .locator("dialog[open] [data-decision-attribution]")
      .filter({ hasText: words.token })
      .waitFor();
    assert.equal(
      await page
        .getByRole("button", { name: words.history, exact: true })
        .getAttribute("aria-pressed"),
      "true",
    );
    assert.doesNotMatch(
      await page.locator("body").innerText(),
      language === "de" ? /Bestätigt von Olga/ : /Confirmed by Olga/,
      "the issuer is never presented as the one who confirmed",
    );
    assert.deepEqual(errors, []);
    await page.screenshot({ path: `/private/tmp/decision-trail-${language}.png` });
    await page.close();
  }
  console.log("PASS: pending and history tabs, decider sentences, settled decision by link, de/en");
} finally {
  await browser.close();
}
