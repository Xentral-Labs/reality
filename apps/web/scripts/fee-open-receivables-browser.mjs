// Read-only browser fixtures; PostgreSQL tests prove claim and confirmation semantics.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(15000);
const writes = [],
  errors = [];
let kind = "dunning_fee_charge";
page.on("pageerror", (error) => errors.push(error.message));
await page.route("**/api/**", async (route) => {
  const request = route.request(),
    path = new URL(request.url()).pathname;
  const reply = (data) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(data) });
  if (request.method() !== "GET" && !path.endsWith("/search/resolve")) writes.push(path);
  if (path === "/api/auth/me")
    return reply({
      id: "owner",
      email: "owner@example.test",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: "fee_fixture", name: "Fee company", role: "owner" }],
      default_tenant_id: "fee_fixture",
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      active_session_id: null,
      has_archived: false,
    });
  if (path.includes("/finance/settlements/context/"))
    return reply({
      document_id: "fee_1",
      number: "FEE-1",
      kind: "invoice",
      side: "customer",
      currency: "EUR",
      open: "5",
      revision: 1,
      control_account_code: "AR",
      counterpart: { state: "active" },
      reduction_allowed: false,
    });
  if (path.endsWith("/finance/open-items"))
    return reply({
      metadata: {
        projection: "open_financial_items",
        calculation_mode: "stored",
        state: "ready",
        completed_at: "2026-10-02T12:00:00Z",
        processed_event_sequence: 1,
        target_event_sequence: 1,
        projection_version: 6,
        consistency: "completed_snapshot",
        upstream_freshness: "unknown",
      },
      items: [
        {
          document_id: "fee_1",
          number: "FEE-1",
          document_type: kind,
          origin: "fee",
          document_date: "2026-10-02",
          party: "Customer",
          party_id: "customer_1",
          gross: "5",
          settled: "0",
          open: "5",
          currency: "EUR",
          status: "open",
        },
      ],
      page: { number: 1, size: 50, total: 1, pages: 1, has_next: false, has_previous: false },
      totals: [{ currency: "EUR", gross: "5", settled: "0", open: "5" }],
    });
  if (path.includes("/inspector/"))
    return reply({
      title: "Fee evidence",
      subtitle: "Customer",
      meaning: "Recorded charge",
      sections: [],
      technical_rows: [],
      source_payload: "{}",
    });
  return route.fulfill({
    status: 404,
    contentType: "application/json",
    body: '{"detail":"Fixture unavailable"}',
  });
});
try {
  for (kind of ["dunning_fee_charge", "payment_return_fee_charge"]) {
    await page.goto(
      `${process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5193"}/app/finance?tenant=fee_fixture`,
    );
    await page.getByText("FEE-1", { exact: true }).waitFor();
    await page.locator("tbody tr").first().click();
    await page.getByRole("button", { name: "Record payment and allocation", exact: true }).click();
    await page
      .getByRole("heading", { name: "Record payment and allocation", exact: true })
      .waitFor();
    assert.equal(
      await page.getByText("Also accept a stated reduction", { exact: true }).count(),
      0,
    );
    assert.equal(
      await page.getByRole("button", { name: "Accept settlement reduction", exact: true }).count(),
      0,
    );
    assert.equal(
      await page.getByRole("button", { name: "Create dunning notice", exact: true }).count(),
      0,
    );
  }
  assert.deepEqual(writes, []);
  assert.deepEqual(errors, []);
  console.log("Fee open-item payment browser checks passed for both charge types.");
} finally {
  await browser.close();
}
