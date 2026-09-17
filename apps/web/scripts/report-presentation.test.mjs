import { test } from "node:test";
import assert from "node:assert/strict";
import { reportColumns, reportFieldLabel } from "../src/unified/reportPresentation.ts";

test("dispatch places business fields before nested data and keeps opaque identity in the original row", () => {
  const row = {
    lines: [{ sku: "P01" }],
    party_id: "p1",
    order_key: "d1",
    party: "Acme",
    due_at: "2026-09-19T12:00:00Z",
    ship_ready: false,
    blocking_reasons: ["hold"],
    priority: "normal",
    external_order_id: "SO-1",
  };
  assert.deepEqual(reportColumns("fulfillment_queue", [row]), [
    "party",
    "external_order_id",
    "due_at",
    "ship_ready",
    "blocking_reasons",
    "priority",
    "lines",
  ]);
  assert.equal(row.party_id, "p1");
  assert.deepEqual(row.lines, [{ sku: "P01" }]);
});
test("unknown report fields survive and identity-only results remain readable", () => {
  assert.deepEqual(
    reportColumns("future", [{ id: "opaque", unfamiliar_metric: "999999999999999999.123456" }]),
    ["unfamiliar_metric"],
  );
  assert.deepEqual(reportColumns("future", [{ id: "opaque" }]), ["id"]);
  assert.equal(reportFieldLabel("unfamiliar_metric"), "unfamiliar_metric");
  assert.equal(reportFieldLabel("due_at"), "Due date");
});
test("columns include later sparse fields without changing data or decimal values", () => {
  const rows = [
    { item_id: "i1", available: "999999999999999999.123456" },
    { sku: "P2", physical: "8.100" },
  ];
  const before = JSON.stringify(rows);
  assert.deepEqual(reportColumns("inventory", rows), ["sku", "physical", "available"]);
  assert.equal(JSON.stringify(rows), before);
});

test("party labels do not misidentify suppliers as customers", () => {
  assert.equal(reportFieldLabel("party", "fulfillment_queue"), "Customer");
  assert.equal(reportFieldLabel("party", "open_financial_items"), "Business partner");
});
