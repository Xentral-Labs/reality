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
  ["lot_create", "payment_term_create", "graph.requests.create", "cost.change"].map(
    (tool, index) => [
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
        preview: { effect: `Review ${tool}`, requires_confirmation: true },
        receipt: {},
        next_step: {
          review_required: true,
          // Old payload keeps its owner summary; new policy takes precedence over it.
          required_principal: index > 0 ? "authorized_human" : "authenticated_active_owner",
          ...(index > 0
            ? {
                decision_policy: {
                  approval: {
                    authority:
                      index === 1
                        ? "company_member"
                        : index === 2
                          ? "private_report_author"
                          : "company_owner",
                    conditions: [],
                    exceptions: [],
                  },
                  rejection: { authority: "action_context" },
                  explicit_authorized_decision: true,
                  confirmation_channels: ["web", "external_mcp", "trusted_local_cli"],
                  built_in_chat_can_confirm: false,
                  autonomous_agent_delegation: false,
                  human_involvement_verified: false,
                },
              }
            : {}),
          reconciliation_read: "proposal_execution_status",
          verification_reads: [],
        },
        confirmable: true,
        rejectable: true,
        message: "",
      },
    ],
  ),
);
const deliveryProposals = new Map(
  ["credit_hold_release", "shipment_dispatch"].map((tool, index) => {
    const authority = index === 0 ? "company_owner" : "company_member";
    const nextStep = {
      review_required: true,
      required_principal: "authorized_human",
      decision_policy: {
        approval: { authority, conditions: [], exceptions: [] },
        rejection: { authority: "action_context" },
        explicit_authorized_decision: true,
        confirmation_channels: ["web", "external_mcp", "trusted_local_cli"],
        built_in_chat_can_confirm: false,
        autonomous_agent_delegation: false,
        human_involvement_verified: false,
      },
      reconciliation_read: "proposal_execution_status",
      verification_reads: [],
    };
    const id = `delivery-policy-${index}`;
    return [
      id,
      {
        id,
        tool,
        status: "proposed",
        review_kind: "delivery",
        label: tool,
        actor_type: "agent",
        created_at: "2026-10-02T08:00:00Z",
        next_step: nextStep,
        input: {},
        preview: {},
        receipt: {},
        confirmable: true,
        rejectable: true,
        message: "",
        review: {
          token: `review-${id}`,
          intent: {},
          effect: {},
          state: {
            number: "SO-323",
            holds: [],
            exposure: { currency: "EUR", credit_limit: "100", exposure: "200", excess: "100" },
          },
        },
        verification: "pending",
        links: [],
        observation: null,
        observation_error: null,
      },
    ];
  }),
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
  const deliveryId = [...deliveryProposals.keys()].find((candidate) => path.includes(candidate));
  if (deliveryId) {
    const delivery = deliveryProposals.get(deliveryId);
    if (path.endsWith("/approve")) {
      assert.equal(request.postDataJSON().confirmed, true);
      assert.equal(request.postDataJSON().review_token, delivery.review.token);
      Object.assign(delivery, {
        status: "executed",
        verification: "verified",
        confirmable: false,
        rejectable: false,
      });
      approvals++;
      return reply({ id: deliveryId, status: "executed", output: {} });
    }
    return reply(delivery);
  }
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
    // A tool with a business name in the catalog is titled by it, others by their label.
    const heading =
      proposal.tool === "payment_term_create" ? "Create payment term" : proposal.label;
    await dialog.getByRole("heading", { name: heading, exact: false }).waitFor();
    const authorityMessage =
      proposal.next_step.decision_policy?.approval.authority === "company_member"
        ? "For company operations, an active company member must approve this proposal."
        : proposal.next_step.decision_policy?.approval.authority === "private_report_author"
          ? "The original report author must approve this proposal."
          : "An authenticated company owner must approve this proposal.";
    await dialog.getByText(authorityMessage, { exact: false }).waitFor();
    assert.equal(await dialog.getByText("must approve or reject", { exact: false }).count(), 0);
    await dialog.getByText("Stated input", { exact: true }).waitFor();
    await dialog.getByText("Prepared preview", { exact: true }).waitFor();
    await dialog.getByRole("button", { name: "Confirm change", exact: true }).click();
    await dialog.getByText("Stored receipt", { exact: true }).waitFor();
    await page.reload();
    await page.getByRole("dialog").getByText("Stored receipt", { exact: true }).waitFor();
  }
  for (const proposal of deliveryProposals.values()) {
    await page.goto(`${base}/app/decisions?tenant=company&proposal=${proposal.id}`);
    const dialog = page.getByRole("dialog");
    const message =
      proposal.tool === "credit_hold_release"
        ? "An authenticated company owner must approve this proposal."
        : "For company operations, an active company member must approve this proposal.";
    await dialog.getByText(message, { exact: false }).waitFor();
    await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
    await page.waitForFunction(() => !document.querySelector("dialog[open]"));
    assert.equal(proposal.status, "executed");
    if (proposal.tool === "credit_hold_release") {
      await page.reload();
      await page.goto(`${base}/app/decisions?tenant=company&proposal=${proposal.id}`);
      await page
        .getByRole("dialog")
        .getByText("The credit hold is released; the order can be reserved and shipped.")
        .waitFor();
      assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).count(), 0);
      proposal.verification = "unresolved";
      await page.reload();
      await page
        .getByRole("dialog")
        .getByText("Execution outcome is being checked. Do not repeat the action.")
        .waitFor();
      assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).count(), 0);
      assert.equal(
        await page
          .getByText("The credit hold is released; the order can be reserved and shipped.")
          .count(),
        0,
      );
    }
  }
  assert.equal(approvals, proposals.size + deliveryProposals.size);
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
