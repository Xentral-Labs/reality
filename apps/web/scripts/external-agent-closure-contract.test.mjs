import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = path.resolve(webRoot, "..", "..");
const read = (...parts) => fs.readFileSync(path.join(repositoryRoot, ...parts), "utf8");

test("web review and MCP catalogs retain the shared application identities", () => {
  const dunning = read("apps", "web", "src", "finance", "DunningNotice.tsx");
  const proposalReview = read("apps", "web", "src", "unified", "ProposalReviewCard.tsx");
  const application = read("packages", "reality-core", "src", "reality", "tools", "application.py");
  const mcp = read("packages", "reality-core", "src", "reality", "mcp", "catalog.py");
  const finance = read("packages", "reality-core", "src", "reality", "tools", "finance.py");
  const applicationRegistry = `${application}\n${finance}`;

  assert.ok(dunning.includes('tool: "finance.dunning.record"'));
  assert.ok(dunning.includes('/change-proposals/${pending.id}/${approve ? "approve" : "reject"}'));
  assert.ok(proposalReview.includes("api.proposalReview"));
  assert.ok(proposalReview.includes("api.approveProposal"));
  assert.ok(proposalReview.includes("api.rejectProposal"));
  assert.ok(proposalReview.includes("authenticated_active_owner"));
  assert.ok(proposalReview.includes("next_step.reconciliation_read"));
  assert.ok(dunning.includes("authenticated company owner"));
  assert.ok(dunning.includes("dunning notice read"));
  for (const identity of [
    "finance.dunning.context",
    "finance.dunning.notices",
    "finance.dunning.notice",
    "finance.dunning.record",
    "finance.dunning.reverse",
    "invoice_credit_context",
    "supplier_invoice_free_record",
  ]) {
    assert.ok(applicationRegistry.includes(identity), `application registry lacks ${identity}`);
    assert.ok(mcp.includes(identity), `MCP binding lacks ${identity}`);
  }
});
