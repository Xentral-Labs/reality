import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const source = (name) => fs.readFileSync(path.join(root, "src", "unified", name), "utf8");

test("Chat presents proposals as business decisions", () => {
  const chat = source("ChatPage.tsx");
  const presentation = source("proposalPresentation.ts");
  assert.match(chat, /data-chat-decision/u);
  assert.match(chat, /\{t\("Pending"\)\}/u);
  assert.match(chat, /\{t\("Review"\)\}/u);
  assert.match(presentation, /item_create: "Create item"/u);
  assert.match(presentation, /location_create: "Create location"/u);
  assert.match(presentation, /payment_term_create: "Create payment term"/u);
  assert.match(chat, /proposalBusinessLabel\(proposal\.tool, proposal\.review_label\)/u);
  assert.match(
    chat,
    /navigate\(\{ proposal: proposal\.id, importProposal: "", analyticsProposal: "" \}\)/u,
  );
  assert.ok(!chat.includes("proposalReviewLocation"));
  assert.ok(!chat.includes('t("Decision required")'));
  assert.ok(!chat.includes("proposal.review_purpose"));
  assert.ok(!chat.includes("proposal.actor_type"));
  assert.ok(!chat.includes('t("This proposed change has not changed your records yet.")'));
  assert.ok(!chat.includes('{t("Review proposed changes")} · {proposal.review_label}'));
});

test("Chat decisions stay compact in the main conversation and dock", () => {
  const chat = source("ChatPage.tsx");
  assert.match(chat, /data-chat-decision-list/u);
  assert.match(chat, /proposals\.length === 1/u);
  assert.match(chat, /divide-y divide-border-default/u);
  assert.match(chat, /data-chat-decision=\{proposal\.id\}/u);
  assert.match(chat, /className="br-btn min-h-9 shrink-0 px-3"/u);
  assert.match(chat, /max-w-\[680px\]/u);
  assert.doesNotMatch(chat, /function ChatDecisionCard/u);
  assert.doesNotMatch(chat, /br-btn br-btn-primary mt-3/u);
  assert.doesNotMatch(chat, /bg-accent-soft px-5 py-4/u);
});

test("common proposal review keeps a stable loading and failure dialog", () => {
  const review = source("ProposalReviewCard.tsx");
  assert.match(review, /aria-labelledby="proposal-review-title"/u);
  assert.match(review, /aria-busy=\{review\.loading\}/u);
  assert.match(review, /ReadState[\s\S]*retry=\{review\.refresh\}/u);
  assert.match(review, /min-h-72 w-\[min\(720px,calc\(100vw-2rem\)\)\]/u);
  assert.match(review, /proposalBusinessLabel\(data\.tool, data\.label\)/u);
});

test("order review leads with the business decision and one primary action", () => {
  const order = source("OrderCard.tsx");
  const kit = source("DecisionReview.tsx");
  assert.match(order, /Confirm customer order/u);
  assert.match(order, /What happens when you confirm\?/u);
  assert.match(kit, /Request changes/u);
  assert.match(kit, /Do not approve/u);
  assert.match(order, /System details/u);
  assert.match(order, /<DecisionActionBar/u);
});

test("decision reviews share chrome, structured values and action hierarchy", () => {
  const kit = source("DecisionReview.tsx");
  const common = source("ProposalReviewCard.tsx");
  const order = source("OrderCard.tsx");
  const master = source("MasterDataCard.tsx");
  assert.match(kit, /export function DecisionReviewHeader/u);
  assert.match(kit, /export function DecisionActionBar/u);
  assert.match(kit, /export function BusinessValue/u);
  assert.match(kit, /Array\.isArray\(value\)/u);
  assert.match(kit, /typeof value === "object"/u);
  for (const implementation of [common, order, master]) {
    assert.match(implementation, /DecisionReviewHeader/u);
    assert.match(implementation, /DecisionActionBar/u);
  }
  assert.match(master, /BusinessFieldList/u);
  assert.doesNotMatch(master, /typeof value === "object"\) return JSON\.stringify\(value\)/u);
  assert.doesNotMatch(master, /JSON\.stringify\(proposal\.output\.records/u);
  for (const name of [
    "ActionCard.tsx",
    "CommitmentActionCard.tsx",
    "CorrectionCard.tsx",
    "CreditCard.tsx",
    "FinancialReversalCard.tsx",
    "InvoiceCard.tsx",
    "PaymentCard.tsx",
    "RefundCard.tsx",
    "ShipmentActions.tsx",
  ])
    assert.match(source(name), /DecisionActionBar/u, `${name} bypasses the shared action bar`);
});

test("Chat shows only its own proposals, where they were made (spec 328)", () => {
  const chat = source("ChatPage.tsx");
  assert.match(chat, /proposal\.after_message_id/u);
  assert.match(chat, /renderProposals\(anchored\.get\(message\.id\)/u);
  assert.match(chat, /renderProposals\(unanchored\)/u);
  assert.match(chat, /<DecisionLine/u);
  assert.match(chat, /data-chat-pending-elsewhere/u);
  assert.match(chat, /route: "decisions", decisionsView: "pending"/u);
  assert.doesNotMatch(chat, /data\.proposals\.filter/u);
});
