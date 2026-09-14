import assert from "node:assert/strict";
import test from "node:test";
import { financeLink, needsAttention, orderToCashRows } from "../src/components/demoDataSummary.ts";
import { reasonLabel, suggestedInvoices } from "../src/finance/settlementCandidates.ts";

const block = {
  invoices_issued: 12,
  payments_received: 11,
  payments_allocated: 10,
  invoices_settled: 9,
  open_residuals: 1,
  credit_created: "20.00",
  unmatched_payments: 1,
  failed: 0,
  last_settlement: "2026-09-10T08:12:00+00:00",
  next_settlement: "2026-09-10T08:13:00+00:00",
};

test("the order-to-cash block renders every observation in reading order", () => {
  const rows = orderToCashRows(block);
  assert.deepEqual(
    rows.map((row) => row.label),
    [
      "Invoices issued",
      "Payments received",
      "Payments allocated",
      "Invoices settled",
      "Open residuals",
      "Customer credit created",
      "Unmatched payments",
      "Settlement failures",
    ],
  );
  assert.equal(rows.find((row) => row.key === "credit_created").value, "20.00");
  assert.deepEqual(orderToCashRows(undefined), []);
});

test("attention is needed for residuals, credit, unmatched payments or failures only", () => {
  assert.equal(needsAttention(block), true);
  assert.equal(
    needsAttention({
      ...block,
      open_residuals: 0,
      unmatched_payments: 0,
      failed: 0,
      credit_created: "0",
    }),
    false,
  );
  assert.equal(needsAttention(undefined), false);
});

test("finance links stay inside the company and name the synthetic source", () => {
  const url = new URL(financeLink("company a", "payments"), "https://example.test");
  assert.equal(url.pathname, "/app/finance");
  assert.equal(url.searchParams.get("tenant"), "company a");
  assert.equal(url.searchParams.get("finance_view"), "payments");
  assert.equal(url.searchParams.get("source"), "demo_data");
});

test("suggested invoices are the choices with reasons, labels stay readable", () => {
  const choices = [
    { id: "a", number: "INV-1", open: "100", currency: "EUR", reasons: [] },
    {
      id: "b",
      number: "INV-2",
      open: "100",
      currency: "EUR",
      reasons: ["amount equals the open amount"],
    },
    { id: "c", number: "INV-3", open: "5", currency: "EUR" },
  ];
  assert.deepEqual(
    suggestedInvoices(choices).map((c) => c.id),
    ["b"],
  );
  assert.deepEqual(suggestedInvoices(undefined), []);
  assert.equal(reasonLabel("amount equals the open amount"), "Amount equals the open amount");
  assert.equal(reasonLabel("something new"), "something new");
});
