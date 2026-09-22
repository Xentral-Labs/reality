import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { reference as discoveryReference } from "./action-discovery-fixture.mjs";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
const proposals = new Map(
  ["lot_create", "payment_term_create", "price_list_create", "cost.change"].map((tool, index) => [
    `proposal-${index}`,
    {
      id: `proposal-${index}`,
      tool,
      label: tool.replaceAll("_", " ").replaceAll(".", " "),
      purpose: `Review ${tool}`,
      review_kind: "common",
      status: "proposed",
      actor_type: "agent",
      created_at: "2026-09-22T08:00:00Z",
      decided_at: null,
      input: { reference: `TEST-${index}`, amount: "125.50" },
      preview: { effect: `Review ${tool}`, requires_human_confirmation: true },
      receipt: {},
      confirmable: true,
      rejectable: true,
      message: "",
    },
  ]),
);
let approvals = 0;
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
await page.route("**/api/**", async (route) => {
  const request = route.request();
  const path = new URL(request.url()).pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "company", name: "Northstar" }], default_tenant_id: "company" });
  const id = [...proposals.keys()].find((candidate) => path.includes(candidate));
  if (id && path.endsWith("/review")) return reply(proposals.get(id));
  if (id && path.endsWith("/approve")) {
    const proposal = proposals.get(id);
    assert.equal(request.postDataJSON().confirmed, true);
    approvals++;
    Object.assign(proposal, {
      status: "executed",
      receipt: { proposal_id: id, status: "executed" },
      preview: {},
      confirmable: false,
      rejectable: false,
    });
    return reply({ id, status: "executed", output: proposal.receipt });
  }
  if (path.endsWith("/change-proposals"))
    return reply({
      items: [],
      page: { number: 1, size: 50, total: 0, pages: 1, has_next: false, has_previous: false },
    });
  if (path.endsWith("/application-reference")) return reply(discoveryReference);
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  return reply({ items: [] });
});

try {
  for (const proposal of proposals.values()) {
    await page.goto(`${base}/app/decisions?tenant=company&proposal=${proposal.id}`);
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("heading", { name: proposal.label, exact: false }).waitFor();
    await dialog.getByText("Stated input", { exact: true }).waitFor();
    await dialog.getByText("Prepared preview", { exact: true }).waitFor();
    await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
    await dialog.getByText("Stored receipt", { exact: true }).waitFor();
    await page.reload();
    await page.getByRole("dialog").getByText("Stored receipt", { exact: true }).waitFor();
  }
  assert.equal(approvals, proposals.size);
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
