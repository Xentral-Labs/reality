import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const card = fs.readFileSync(
  new URL("../src/unified/ProposalReviewCard.tsx", import.meta.url),
  "utf8",
);
const api = fs.readFileSync(new URL("../src/api.ts", import.meta.url), "utf8");

test("proposal review uses shared approval authority with rolling-deployment fallback", () => {
  const shared = fs.readFileSync(
    new URL("../src/unified/DecisionReview.tsx", import.meta.url),
    "utf8",
  );
  assert.ok(card.includes("ProposalApprovalRequirement"));
  assert.ok(shared.includes("decision_policy?.approval.authority"));
  assert.ok(shared.includes("authenticated_active_owner"));
  assert.ok(shared.includes("The original report author must approve this proposal."));
  assert.ok(shared.includes("An authenticated account user must approve this proposal."));
  assert.ok(
    shared.includes("For company operations, an active company member must approve this proposal."),
  );
  assert.ok(shared.includes("An authenticated company owner must approve this proposal."));
  assert.ok(!card.includes("must approve or reject this finance proposal"));
  assert.ok(api.includes("decision_policy?: ProposalDecisionPolicy"));
  const action = fs.readFileSync(new URL("../src/unified/ActionCard.tsx", import.meta.url), "utf8");
  const shipment = fs.readFileSync(
    new URL("../src/unified/ShipmentActions.tsx", import.meta.url),
    "utf8",
  );
  const credit = fs.readFileSync(
    new URL("../src/unified/CreditHoldRelease.tsx", import.meta.url),
    "utf8",
  );
  assert.ok(action.includes("nextStep={proposal.next_step}"));
  assert.ok(shipment.includes("nextStep={proposal.next_step}"));
  assert.ok(credit.includes("nextStep={prepared.next_step}"));
  assert.ok(action.includes('activeTool === "credit_hold_release"'));
});
