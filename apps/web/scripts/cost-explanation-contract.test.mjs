import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = (name) => readFile(new URL(`../src/${name}`, import.meta.url), "utf8");

test("cost query client preserves the shared read-only context", async () => {
  const api = await source("api.ts");
  assert.match(api, /export type CostQueryEnvelope/);
  assert.match(api, /costQuery:\s*\(/);
  assert.match(api, /\/cost-query\?/);
  assert.doesNotMatch(api.match(/costQuery:[\s\S]*?\n\s*},/)?.[0] || "", /method:\s*["']POST/);
});

test("one explanation component owns freshness, gaps, precision and trace", async () => {
  const component = await source("unified/CostExplanation.tsx");
  for (const contract of [
    "Acquisition value",
    "Carrying value",
    "Consumed acquisition cost",
    "DB1",
    "DB2",
    "Retained basis — not current",
    "Missing basis",
    "Exact retained value",
    "inspector_target_kind",
  ])
    assert.match(component, new RegExp(contract.replace(/[—]/g, "—")));
  assert.match(component, /formatMoney/);
  assert.match(component, /formatExactDecimal\(text\(value\)!, true\)/);
  assert.doesNotMatch(component, /Exact retained value"\)\}: \{text\(value\)\}/);
  assert.match(component, /className="mt-1 block text-fg-muted"/);
  assert.match(component, /shown\.unit_cost/);
  assert.match(component, /shown\.acquisition_value \?\? shown\.basis_acquisition_value/);
});

test("warehouse item preview uses the shared explanation", async () => {
  const warehouse = await source("unified/WarehousePage.tsx");
  assert.match(warehouse, /CostExplanation/);
  assert.match(warehouse, /kind="inventory"/);
  assert.match(warehouse, /scopeId=\{row\.id\}/);
});

test("Analysis reuses the operational explanation frame", async () => {
  const analysis = await source("unified/analytics/InventoryValuation.tsx");
  assert.match(analysis, /CostExplanationFrame/);
  assert.match(analysis, /title=\{t\("Historical valuation basis"\)\}/);
});

test("Orders and Finance use only exact invoice line identities", async () => {
  const component = await source("unified/DocumentContributionExplanations.tsx");
  const orders = await source("unified/OrdersPage.tsx");
  const finance = await source("unified/FinancePage.tsx");
  assert.match(component, /invoice\.invoice_line_id/);
  assert.match(component, /line\.id/);
  assert.match(component, /kind="contribution" scopeId=\{scope\.id\}/);
  assert.match(orders, /source="billed_invoice_lines"/);
  assert.match(finance, /row\.document_type === "sales_invoice"/);
  assert.match(finance, /source="document_lines"/);
  assert.doesNotMatch(component, /document\.number|scopeId=\{detail\.id\}/);
});
