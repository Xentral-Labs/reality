import assert from "node:assert/strict";
import test from "node:test";
import { starterSelection, resultCompletesTask, promptKey } from "../src/unified/trialJourney.ts";

test("starter routes clear stale company filters and never propose writes", () => {
  const attention = starterSelection("attention", "tenant-a");
  assert.equal(attention.route, "attention");
  assert.equal(attention.tenant, "tenant-a");
  assert.equal(attention.severity, "");
  assert.equal(attention.proposal, "");
  const delivery = starterSelection("delivery", "tenant-a");
  assert.equal(delivery.deliveryStatus, "open");
  assert.equal(delivery.commitment, "");
  const invoices = starterSelection("invoices", "tenant-a");
  assert.equal(invoices.financeView, "open-items");
  assert.equal(invoices.flow, "receivable");
  assert.equal(invoices.financeStatus, "outstanding");
  assert.equal(invoices.partyId, "");
});
test("only successful matching current-company results complete a starter", () => {
  const active = { task: "delivery", tenant: "a" };
  assert.equal(resultCompletesTask(active, "delivery", "a", true), true);
  assert.equal(resultCompletesTask(active, "delivery", "b", true), false);
  assert.equal(resultCompletesTask(active, "invoices", "a", true), false);
  assert.equal(resultCompletesTask(active, "delivery", "a", false), false);
  assert.equal(resultCompletesTask(null, "delivery", "a", true), false);
});
test("voluntary prompt preferences are account-scoped", () => {
  assert.notEqual(promptKey("a"), promptKey("b"));
  assert.equal(promptKey("a"), promptKey("a"));
});
