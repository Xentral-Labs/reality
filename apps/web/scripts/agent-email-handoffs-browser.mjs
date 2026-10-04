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
page.setDefaultTimeout(15000);
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
const businessReferences = [{ kind: "party", id: "supplier-1", label: "Bike Parts GmbH" }];
const fixturePage = (number = 1, total = 1, size = 25) => ({
  number,
  size,
  total,
  pages: Math.max(1, Math.ceil(total / size)),
  has_next: number * size < total,
  has_previous: number > 1,
});
let externalApproved = false;
const externalDecider = {
  kind: "external_grant",
  name: "Anna Buyer",
  subject: "person-42",
  issuer: "approval.example",
  approved_at: 1791093600,
  grant_source_id: "grant-source",
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
    business_references: businessReferences.map(({ kind, id }) => ({ kind, id })),
    rationale: "Acknowledge the question",
    supporting_source_ids: ["incoming-source"],
    fingerprint: "b".repeat(64),
    retry_acknowledgements: [
      {
        execution_id: "smtp-uncertain",
        report_source_ids: ["unknown-receipt"],
        reason: "Person explicitly accepts duplicate delivery",
        accept_duplicate_send_risk: true,
      },
    ],
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
  if (path.endsWith("/inspector-records")) return reply({ items: [], page: fixturePage(1, 0) });
  if (path.endsWith("/inspector/party/supplier-1"))
    return reply({
      kind: "party",
      id: "supplier-1",
      title: "Bike Parts GmbH",
      subtitle: "Supplier",
      sections: [],
      events: [],
      email_history_identity: { business_kind: "party", business_id: "supplier-1" },
    });
  if (path.endsWith("/email/history")) {
    if (url.searchParams.has("business_kind")) {
      assert.equal(url.searchParams.get("business_kind"), "party");
      assert.equal(url.searchParams.get("business_id"), "supplier-1");
      const number = Number(url.searchParams.get("page") || 1);
      return reply({
        business_references: businessReferences,
        items:
          number === 1
            ? Array.from({ length: 25 }, (_, index) => ({
                source_id: index === 0 ? "incoming-source" : `mail-${index}`,
                subject: index === 0 ? "Supplier delivery question" : `Supplier email ${index}`,
                sender: "supplier@example.test",
                direction: "inbound",
                received_at: "2026-10-03T10:00:00Z",
              }))
            : [
                {
                  source_id: "older-source",
                  subject: "Earlier supplier question",
                  sender: "supplier@example.test",
                  direction: "outbound",
                  authorization: "external_unverified",
                  received_at: "2026-10-02T10:00:00Z",
                },
              ],
        page: fixturePage(number, 26),
        related_decisions: [
          {
            proposal_id: proposal.id,
            subject: "Delivery question",
            status: proposal.status,
            review_url: "/app/decisions?tenant=company&proposal=email-proposal",
          },
        ],
        decision_page: fixturePage(),
      });
    }
    if (url.searchParams.has("execution_id"))
      return reply({
        source: null,
        attachments: [],
        supporting_sources: [],
        reports: [{ id: "unknown-receipt", payload: { outcome: "unknown" } }],
        state: "execution_uncertain",
      });
    if (url.searchParams.has("source_id"))
      return reply({
        business_references: businessReferences,
        authorization:
          url.searchParams.get("source_id") === "older-source"
            ? "external_unverified"
            : "inbound_evidence",
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
      business_references: businessReferences,
      decision: {
        proposal_id: proposal.id,
        status: proposal.status,
        decided_at: externalApproved ? "2026-10-04T06:00:00Z" : null,
        decider: externalApproved ? externalDecider : { kind: "unknown" },
        duplicate_send_risk: !externalApproved,
        retry_acknowledgements: externalApproved ? [] : proposal.input.retry_acknowledgements,
      },
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
  await history.getByRole("link", { name: "Bike Parts GmbH", exact: true }).click();
  const supplier = page.getByRole("dialog");
  await supplier.getByRole("heading", { name: "Bike Parts GmbH", exact: true }).waitFor();
  const correspondence = supplier.locator("[data-object-correspondence]");
  await correspondence.getByRole("button", { name: /Supplier delivery question/ }).click();
  await correspondence.getByText("Email evidence history", { exact: true }).waitFor();
  await correspondence.getByText("incoming-source", { exact: true }).click();
  await correspondence.getByText("Quote.pdf", { exact: true }).waitFor();
  assert.equal(
    await correspondence.getByRole("link", { name: "Download original file" }).getAttribute("href"),
    "/api/tenants/company/email/files/art-1/download",
  );
  await correspondence.getByRole("button", { name: "Back to linked correspondence" }).click();
  await correspondence.getByRole("button", { name: "Next", exact: true }).first().click();
  await correspondence.getByRole("button", { name: /Earlier supplier question/ }).waitFor();
  await correspondence
    .locator("[data-email-external-authorization]")
    .getByText("Externally sent; no Reality approval is documented.", { exact: true })
    .waitFor();
  await correspondence.getByRole("button", { name: /Earlier supplier question/ }).click();
  await correspondence
    .locator("[data-email-external-authorization]")
    .getByText("Externally sent; no Reality approval is documented.", { exact: true })
    .waitFor();
  await correspondence.getByRole("button", { name: "Back to linked correspondence" }).click();
  await correspondence.getByRole("link", { name: "Delivery question", exact: true }).click();
  await page
    .getByRole("dialog")
    .locator("[data-email-outcome]")
    .getByText("Email decision rejected", { exact: true })
    .waitFor();
  await page.getByRole("dialog").locator("[data-email-retry-risk]").waitFor();
  await page
    .getByRole("dialog")
    .getByText("Person explicitly accepts duplicate delivery", { exact: true })
    .waitFor();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Open previous execution evidence", exact: true })
    .click();
  await page.getByRole("dialog").getByText("Email execution uncertain", { exact: true }).waitFor();
  await page.getByRole("dialog").getByText("Stored receipt", { exact: true }).waitFor();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Return to email decision", exact: true })
    .click();
  await page.getByRole("dialog").locator("[data-email-retry-risk]").waitFor();
  externalApproved = true;
  proposal.status = "executed";
  proposal.confirmable = false;
  proposal.rejectable = false;
  proposal.input.retry_acknowledgements = [];
  await page.reload();
  const grantPanel = page.getByRole("dialog").locator("[data-email-external-grant]");
  await grantPanel
    .getByText("External approval by Anna Buyer, verified through approval.example", {
      exact: false,
    })
    .waitFor();
  const proof = grantPanel.getByRole("link", { name: "Open original approval proof" });
  assert.equal(
    await proof.getAttribute("href"),
    "/app/inspector?tenant=company&inspector_view=facts&inspector_target_kind=source_record&inspector_target_id=grant-source",
  );
  assert.equal(await page.getByRole("dialog").locator("[data-email-retry-risk]").count(), 0);
  assert.deepEqual(errors, []);
  console.log(
    "Email review, BCC, full text, safe HTML and original-file navigation, decision status refresh and paged supplier correspondence passed.",
  );
} finally {
  await browser.close();
}
