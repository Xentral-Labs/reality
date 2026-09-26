import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { statedDetail, withStatedDetail } from "../src/unified/statedAmounts.ts";

const card = readFileSync(new URL("../src/unified/InvoiceCard.tsx", import.meta.url), "utf8");

// FR-001: the typed values travel as the position's received detail, unchanged.
test("a position sends only the net and tax the person stated", () => {
  const position = { order_line_id: "l1", quantity: "2", gross_amount: "59.50" };
  assert.deepEqual(
    withStatedDetail({ ...position, reality_finance_v1: { net: " 50.00 ", tax: "9.50" } }),
    { ...position, reality_finance_v1: { net: "50.00", tax: "9.50" } },
  );
  // Tax only stays tax only: nothing is derived from gross.
  assert.deepEqual(statedDetail({ net: "", tax: "9.50" }), { tax: "9.50" });
  // Empty fields send no detail at all, so a gross-only invoice is unchanged (FR-006).
  assert.deepEqual(withStatedDetail({ ...position, reality_finance_v1: { net: " " } }), position);
  assert.deepEqual(withStatedDetail(position), position);
});

test("the form sends each position through the stated detail helper", () => {
  assert.match(card, /lines: draft\.lines\?\.map\(withStatedDetail\)/);
  assert.match(card, /t\("Net \(as stated on the invoice\)"\)/);
  assert.match(card, /t\("Tax \(as stated on the invoice\)"\)/);
});

// DR-003: gross is what the person entered; the form never computes it.
test("gross is never filled from net and tax", () => {
  assert.doesNotMatch(card, /gross_amount:\s*[^,}\n]*\b(net|tax)\b/);
  assert.doesNotMatch(card, /Number\(|parseFloat\(/);
});

// FR-005: the review shows what the person is about to confirm.
test("the review reads the stated amounts from the reviewed creation", () => {
  assert.match(card, /row\.reality_finance_v1/);
  assert.match(card, /review\.state\.creation\.reality_finance_v1/);
});
