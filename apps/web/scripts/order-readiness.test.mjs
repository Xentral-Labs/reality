import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = (path) => readFile(new URL(`../src/${path}`, import.meta.url), "utf8");

test("sales readiness reads the canonical projection without a mutation", async () => {
  const orders = await source("unified/OrdersPage.tsx");
  assert.match(orders, /specializedProjection<FulfillmentQueueRow>[\s\S]*"fulfillment_queue"/);
  assert.match(orders, /metadata\.state === "uninitialized"/);
  assert.match(orders, /target_event_sequence[\s\S]*processed_event_sequence/);
  assert.doesNotMatch(orders, /refreshProjection|method:\s*"POST"/);
});

test("readiness evidence preserves direct document and commitment traces", async () => {
  const orders = await source("unified/OrdersPage.tsx");
  assert.match(orders, /kind: "document", id: row\.document_id/);
  assert.match(orders, /kind: "commitment", id: line\.commitment_id/);
  assert.match(orders, /line\.fulfilled_quantity/);
  assert.match(orders, /payment\.received_amount[\s\S]*payment\.required_amount/);
});

test("readiness is a routable sales register", async () => {
  const routing = await source("unified/routing.ts");
  const table = await source("unified/RegisterTable.tsx");
  assert.match(routing, /\| "readiness"/);
  assert.match(table, /"orders-deliveries:readiness"/);
});

test("readiness actions hand exact identities to existing reviewed forms", async () => {
  const orders = await source("unified/OrdersPage.tsx");
  const app = await source("unified/UnifiedApp.tsx");
  assert.match(orders, /prepareInvoice\(row\.document_id/);
  assert.match(orders, /blocking_reasons\.includes\("prepayment_invoice_missing"\)/);
  assert.match(orders, /quantity: line\.shippable_quantity/);
  assert.match(orders, /commitment_id: line\.commitment_id/);
  assert.doesNotMatch(orders, /Math\.min/);
  assert.match(app, /setAction\("sales_invoice_record"\)/);
  assert.match(app, /setAction\("shipment_dispatch"\)/);
});

test("confirmed actions visibly reuse the shared automatic reload", async () => {
  const orders = await source("unified/OrdersPage.tsx");
  const reads = await source("unified/useCompanyContext.ts");
  assert.match(reads, /addEventListener\("reality:delivery-settled", changed\)/);
  assert.match(orders, /addEventListener\("reality:delivery-settled", settled\)/);
  assert.match(orders, /Readiness was reloaded/);
  assert.match(orders, /projection freshness/);
});

test("blockers render source quantities and payment evidence instead of raw codes", async () => {
  const orders = await source("unified/OrdersPage.tsx");
  assert.match(orders, /line\.reserved_quantity[\s\S]*line\.open_quantity/);
  assert.match(orders, /line\.physical_quantity[\s\S]*physically available/);
  assert.match(orders, /remaining_amount[\s\S]*prepayment remaining/);
  assert.match(orders, /Prepayment cannot be attributed unambiguously/);
  assert.doesNotMatch(orders, /row\.blocking_reasons\.map/);
});

test("stale or missing projections remain readable but cannot prefill actions", async () => {
  const orders = await source("unified/OrdersPage.tsx");
  assert.match(orders, /actionsCurrent=\{data\.metadata\?\.state === "ready"\}/);
  assert.match(orders, /Actions are unavailable until the readiness projection is current/);
  assert.match(orders, /actionsCurrent &&[\s\S]*prepareInvoice/);
  assert.match(orders, /actionsCurrent &&[\s\S]*prepareShipment/);
});
