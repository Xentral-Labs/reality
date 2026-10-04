// Spec 351: exact outgoing review, original evidence/file navigation and safe HTML.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { reference } from "./action-discovery-fixture.mjs";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage();
const base = process.env.UNIFIED_BASE_URL || "http://localhost:5177";
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const message = {
  account: "support@example.test",
  sender: "support@example.test",
  to: ["customer@example.test"],
  cc: [],
  bcc: ["audit@example.test"],
  subject: "Delivery question",
  text: "We will confirm the delivery date.\nNo date is promised yet.",
  html: '<img src="bad" onerror="window.emailInjection=true">',
  attachments: [
    { part_id: "part1", filename: "Quote.pdf", artifact_id: "art-1", sha256: "a".repeat(64) },
  ],
};
const proposal = {
  id: "email-proposal",
  tool: "email_dispatch_authorize",
  label: "Authorize external email dispatch",
  purpose: "Authorize the exact email, without sending it.",
  review_kind: "common",
  status: "proposed",
  actor_type: "agent",
  created_at: "2026-10-03T10:00:00Z",
  input: {
    message,
    rationale: "Acknowledge the question",
    supporting_source_ids: ["incoming-source"],
    fingerprint: "b".repeat(64),
  },
  preview: {},
  receipt: {},
  confirmable: true,
  rejectable: true,
  message: "",
  next_step: {
    review_required: true,
    required_principal: "authenticated_active_member",
    reconciliation_read: "email_history",
    verification_reads: ["email_history"],
    decision_policy: {
      approval: { authority: "company_member", conditions: [], exceptions: [] },
      rejection: { authority: "action_context" },
      confirmation_channels: ["web"],
      built_in_chat_can_confirm: false,
      autonomous_agent_delegation: false,
      human_involvement_verified: false,
    },
  },
};
await page.route("**/api/**", async (route) => {
  const url = new URL(route.request().url());
  const path = url.pathname;
  const reply = (body) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
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
  if (path.endsWith("/application-reference")) return reply(reference);
  if (path.endsWith("/email/history")) {
    if (url.searchParams.has("source_id"))
      return reply({
        source: {
          id: "incoming-source",
          payload: {
            message: {
              text: "Please confirm delivery.",
              external_payload: { provider: "mail-agent" },
            },
          },
        },
        attachments: [
          {
            id: "attachment-source",
            payload: { filename: "Quote.pdf" },
            file: { download_url: "/api/tenants/company/email/files/art-1/download" },
          },
        ],
        supporting_sources: [],
        reports: [],
      });
    return reply({
      state: {
        proposed: "decision_pending",
        executed: "dispatch_authorized",
        rejected: "decision_rejected",
      }[proposal.status],
      source: null,
      attachments: [],
      supporting_sources: [
        { id: "incoming-source", payload: { message: { text: "Please confirm delivery." } } },
      ],
      reports: [],
    });
  }
  if (path.endsWith("/approve") || path.endsWith("/reject")) {
    proposal.status = path.endsWith("/approve") ? "executed" : "rejected";
    proposal.confirmable = false;
    proposal.rejectable = false;
    return reply({ status: proposal.status });
  }
  if (path.endsWith("/review")) return reply(proposal);
  if (path.endsWith("/change-proposals"))
    return reply({
      items: [],
      page: { number: 1, size: 50, total: 0, pages: 1, has_next: false, has_previous: false },
    });
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
  await page.goto(`${base}/app/decisions?tenant=company&proposal=email-proposal`);
  const dialog = page.getByRole("dialog");
  await dialog.getByText("audit@example.test", { exact: true }).first().waitFor();
  await dialog.getByText(message.text, { exact: true }).first().waitFor();
  assert.equal(await page.evaluate(() => Boolean(window.emailInjection)), false);
  assert.equal(await dialog.locator('img[src="bad"]').count(), 0);
  const history = dialog.locator("[data-email-evidence]");
  await history.getByText("incoming-source", { exact: true }).click();
  await history.getByRole("button", { name: "Open original evidence" }).click();
  await history.getByText("Quote.pdf", { exact: true }).waitFor();
  const link = history.getByRole("link", { name: "Download original file" });
  assert.equal(await link.getAttribute("href"), "/api/tenants/company/email/files/art-1/download");
  await history.getByRole("button", { name: "Return to email decision" }).click();
  await history.getByText("incoming-source", { exact: true }).waitFor();
  await history
    .locator("[data-email-outcome]")
    .getByText("Email decision pending", { exact: true })
    .waitFor();
  await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
  await history
    .locator("[data-email-outcome]")
    .getByText("Email dispatch authorized", { exact: true })
    .waitFor();
  proposal.status = "proposed";
  proposal.confirmable = true;
  proposal.rejectable = true;
  await page.reload();
  await history
    .locator("[data-email-outcome]")
    .getByText("Email decision pending", { exact: true })
    .waitFor();
  await dialog.getByRole("button", { name: "Do not approve", exact: true }).click();
  await history
    .locator("[data-email-outcome]")
    .getByText("Email decision rejected", { exact: true })
    .waitFor();
  assert.deepEqual(errors, []);
  console.log(
    "Email review, BCC, full text, safe HTML and original-file navigation and decision status refresh passed.",
  );
} finally {
  await browser.close();
}
