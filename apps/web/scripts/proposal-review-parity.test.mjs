import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = (path) => readFileSync(new URL(`../src/unified/${path}`, import.meta.url), "utf8");

test("chat and decisions use the server-owned proposal review class", () => {
  const chat = source("ChatPage.tsx");
  const decisions = source("DecisionsPage.tsx");
  const app = source("UnifiedApp.tsx");
  const routing = source("proposalRouting.ts");

  assert.match(chat, /proposalReviewLocation\(proposal\.id, proposal\.review_kind\)/);
  assert.match(decisions, /select\(proposal\.id, proposal\.review_kind\)/);
  assert.match(app, /proposalReviewLocation\(proposal, reviewKind\)/);
  assert.match(routing, /reviewKind === "import"/);
  assert.match(routing, /reviewKind === "reference"/);
  assert.match(routing, /reviewKind === "analytics_report"/);
  assert.doesNotMatch(chat, /proposal\.tool === "lot_create"/);
  assert.doesNotMatch(decisions, /cannot be reviewed in this interface/);
});

test("the generic review delegates stronger delivery reviews", () => {
  const card = source("ProposalReviewCard.tsx");
  assert.match(card, /review\.data\.review_kind === "delivery"/);
  assert.match(card, /<ActionCard/);
  assert.match(card, /api\.proposalReview/);
  assert.match(card, /api\.approveProposal/);
  assert.match(card, /api\.rejectProposal/);
});
