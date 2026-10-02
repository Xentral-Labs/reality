import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
const read = (name) => readFileSync(new URL(`../src/unified/${name}`, import.meta.url), "utf8");
test("private review uses author-scoped details and a bounded fallback", () => {
  const source = read("ProposalReviewCard.tsx");
  assert.match(source, /private_review/);
  assert.match(source, /private_report_change/);
  assert.match(source, /This change is private/);
});
test("technical inspection is collapsed and omits sealed carriers", () => {
  const source = read("DecisionReview.tsx");
  assert.match(source, /export function TechnicalDetails/);
  assert.match(source, /<details/);
  assert.doesNotMatch(source, /<details[^>]*\bopen\b/);
  assert.match(source, /requested_analysis/);
});
test("shipment review defaults to structured fields", () => {
  const source = read("ShipmentActions.tsx");
  assert.match(source, /BusinessFieldList/);
  assert.match(source, /TechnicalDetails/);
  assert.doesNotMatch(source.slice(source.indexOf("{proposal && (")), /JSON\.stringify/);
});
