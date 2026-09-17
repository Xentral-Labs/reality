import { test } from "node:test";
import assert from "node:assert/strict";
import { buildReports, filterReports, groupReports } from "../src/unified/reportCatalogEntries.ts";
const projection = (key) => ({
  name: key,
  materialized_as: key,
  calculation: "Catalog explanation",
});
const view = (key, target) => ({
  key,
  label: key,
  description: "View explanation",
  projection: target,
  route: key,
});
const reference = {
  projections: [
    projection("fulfillment_queue"),
    projection("inventory"),
    projection("payments"),
    projection("price_resolution"),
    projection("future_report"),
  ],
  workspaces: [
    {
      views: [
        view("orders", "fulfillment_queue"),
        view("warehouse_queue", "fulfillment_queue"),
        view("inventory", "inventory"),
        view("payments"),
        view("future_view"),
      ],
    },
    { views: [view("orders", "fulfillment_queue")] },
  ],
};
test("identical report targets merge while live and stored readers stay distinct", () => {
  const reports = buildReports(reference);
  assert.equal(reports.filter((r) => r.target === "fulfillment_queue").length, 1);
  assert.equal(reports.find((r) => r.target === "fulfillment_queue").views.length, 2);
  assert.ok(reports.find((r) => r.target === "payments"));
  assert.ok(reports.find((r) => r.target === "view:payments"));
  assert.equal(reports.length, 7);
});
test("unknown catalog entries remain visible and price resolution remains details-only", () => {
  const reports = buildReports(reference);
  assert.equal(reports.find((r) => r.target === "future_report").title, "future_report");
  assert.equal(
    reports.find((r) => r.target === "view:future_view").description,
    "View explanation",
  );
  assert.equal(reports.find((r) => r.target === "price_resolution").dataAvailable, false);
});
test("report search uses localized names, descriptions and aliases together with workspace filter", () => {
  const reports = buildReports(reference);
  const translate = (key) => (key === "Dispatch readiness" ? "Versandbereitschaft" : key);
  assert.equal(filterReports(reports, "versand", "Sales", translate).length, 1);
  assert.equal(filterReports(reports, "versand", "Finance", translate).length, 0);
  assert.equal(filterReports(reports, "warehouse_queue", "All", translate).length, 1);
});

test("report directory has one home per target and retains unknown entries", () => {
  const reports = buildReports(reference);
  const groups = groupReports(reports);
  assert.equal(groups.flatMap((group) => group.reports).length, reports.length);
  assert.equal(
    groups
      .find((group) => group.key === "Sales")
      .reports.filter((report) => report.target === "fulfillment_queue").length,
    1,
  );
  assert.ok(
    groups
      .find((group) => group.key === "Company")
      .reports.some((report) => report.target === "future_report"),
  );
  assert.ok(groups.every((group) => group.reports.length > 0));
});
