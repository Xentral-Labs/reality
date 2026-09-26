import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const source = (name) => fs.readFileSync(path.join(root, "src", "unified", name), "utf8");

test("Chat presents proposals as business decisions", () => {
  const chat = source("ChatPage.tsx");
  assert.match(chat, /data-chat-decision/u);
  assert.match(chat, /Decision required/u);
  assert.match(chat, /This proposed change has not changed your records yet\./u);
  assert.match(chat, /Review and decide/u);
  assert.match(chat, /proposalReviewLocation\(proposal\.id, proposal\.review_kind\)/u);
  assert.ok(!chat.includes('{t("Review proposed changes")} · {proposal.review_label}'));
});

test("common proposal review keeps a stable loading and failure dialog", () => {
  const review = source("ProposalReviewCard.tsx");
  assert.match(review, /aria-labelledby="proposal-review-title"/u);
  assert.match(review, /aria-busy=\{review\.loading\}/u);
  assert.match(review, /ReadState[\s\S]*retry=\{review\.refresh\}/u);
  assert.match(review, /min-h-72 w-\[min\(720px,calc\(100vw-2rem\)\)\]/u);
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
