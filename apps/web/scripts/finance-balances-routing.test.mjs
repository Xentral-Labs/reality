import assert from "node:assert/strict";
import test from "node:test";
import { readSelection, selectionUrl, companySelection } from "../src/unified/routing.ts";

test("Finance balances is a bookmarkable view with side, credit filter and party", () => {
  const held = readSelection(
    new URL(
      "https://example.test/app/finance?tenant=company-a&finance_view=balances&balance_side=supplier&credit_only=1",
    ),
  );
  assert.equal(held.financeView, "balances");
  assert.equal(held.balanceSide, "supplier");
  assert.equal(held.creditOnly, true);
  const reopened = readSelection(new URL(selectionUrl(held), "https://example.test"));
  assert.equal(reopened.financeView, "balances");
  assert.equal(reopened.balanceSide, "supplier");
  assert.equal(reopened.creditOnly, true);
  assert.equal(companySelection(held, "company-b").financeView, "balances");
});

test("a party filter travels into the open items and credit flows and falls back cleanly", () => {
  const filtered = readSelection(
    new URL(
      "https://example.test/app/finance?finance_view=open-items&flow=customer-balance&party_id=party_1",
    ),
  );
  assert.equal(filtered.partyId, "party_1");
  assert.equal(filtered.flow, "customer-balance");
  const url = new URL(selectionUrl(filtered), "https://example.test");
  assert.equal(url.searchParams.get("party_id"), "party_1");
  assert.equal(url.searchParams.has("balance_side"), false);
  const plain = readSelection(new URL("https://example.test/app/finance?balance_side=nonsense"));
  assert.equal(plain.balanceSide, "customer");
  assert.equal(plain.creditOnly, false);
  assert.equal(plain.partyId, "");
});
