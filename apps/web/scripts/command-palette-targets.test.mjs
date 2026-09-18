import { test } from "node:test";
import assert from "node:assert/strict";
import { paletteTargetSelection, palettePages } from "../src/unified/commandPaletteTargets.ts";
import { readSelection, selectionUrl, companySelection } from "../src/unified/routing.ts";

test("palette routes open exact capability, report and template without stale record context", () => {
  const initial = readSelection(
    new URL("http://localhost/app/finance?tenant=one&entry=old&q=old&page=4"),
  );
  const next = paletteTargetSelection(initial, { kind: "capability", id: "reserve" });
  assert.equal(next.toolCapability, "reserve");
  assert.equal(next.entry, "");
  assert.equal(next.page, 1);
  assert.equal(next.tenant, "one");
  for (const [kind, field] of [
    ["saved_report", "analyticsReport"],
    ["template", "analyticsTemplate"],
    ["calculated_report", "calculatedReport"],
  ]) {
    const value = paletteTargetSelection(initial, { kind, id: "exact" });
    const restored = readSelection(new URL(selectionUrl(value), "http://localhost"));
    assert.equal(restored[field], "exact");
    assert.equal(companySelection(restored, "two")[field], "");
  }
});
test("owner and demo destinations stay eligible and include primary workspaces", () => {
  assert(!palettePages({ owner: false, demo: false }).some((x) => x.key === "members"));
  assert(palettePages({ owner: true, demo: true }).some((x) => x.key === "members"));
  assert(!palettePages({ owner: true, demo: false }).some((x) => x.key === "demo"));
  for (const key of [
    "home",
    "orders",
    "purchases",
    "warehouse",
    "finance",
    "master",
    "analytics",
    "tools",
    "chat",
  ])
    assert(palettePages({ owner: true, demo: true }).some((x) => x.key === key));
});
test("unknown targets do not become arbitrary routes or commands", () => {
  const initial = readSelection(new URL("http://localhost/app?tenant=one"));
  assert.throws(() => paletteTargetSelection(initial, { kind: "unknown", id: "x" }));
});

const { paletteEntries } = await import("../src/unified/commandPaletteEntries.ts");
const { reference } = await import("./tool-catalog-fixture.mjs");
test("catalog entries deduplicate canonical targets and never fabricate a mutation form", () => {
  const entries = paletteEntries(reference, { owner: true, demo: true }, (x) => x, "en");
  assert.equal(new Set(entries.map((x) => x.key)).size, entries.length);
  assert(entries.some((x) => x.target.kind === "action" && x.target.id === "movement_create"));
  const noForm = entries.find((x) => x.references.includes("state_lot_expiry"));
  assert.equal(noForm.target.kind, "capability");
  assert(
    entries.some(
      (x) =>
        x.target.kind === "calculated_report" &&
        x.target.id === "price_resolution" &&
        x.outcome === "Show details",
    ),
  );
});

const { paletteActionPrefill } = await import("../src/unified/commandPaletteTargets.ts");
test("prefills copy only the existing form target fields", () => {
  assert.deepEqual(paletteActionPrefill("receipt", { commitment: "c1", invoice: "wrong" }), {
    commitment: "c1",
  });
  assert.deepEqual(
    paletteActionPrefill("ledger_reverse", { postingGroup: "pg1", invoice: "wrong" }),
    { postingGroup: "pg1" },
  );
  assert.deepEqual(paletteActionPrefill("unsupported", { commitment: "c1" }), {});
});

test("report route targets are exclusive and inbound shipment direction survives reload", () => {
  const report = readSelection(
    new URL(
      "http://localhost/app/analytics?tenant=one&analytics_report=r1&analytics_template=t1&analysis_proposal=p1",
    ),
  );
  assert.equal(report.analyticsReport, "r1");
  assert.equal(report.analyticsTemplate, "");
  assert.equal(report.analyticsProposal, "");
  const shipment = {
    ...report,
    route: "orders-deliveries",
    ordersView: "shipments",
    deliveryType: "supplier_delivery",
  };
  assert.equal(
    readSelection(new URL(selectionUrl(shipment), "http://localhost")).deliveryType,
    "supplier_delivery",
  );
});

test("every record family round-trips into its exact supported detail renderer", () => {
  const base = readSelection(new URL("http://localhost/app?tenant=one"));
  const families = [
    ["party", "party", ["customer"], "customer"],
    ["party", "party", ["supplier"], "supplier"],
    ["item", "item", [], "item"],
    ["location", "location", [], "location"],
    ["customer_order", "document"],
    ["supplier_order", "document"],
    ["customer_invoice", "document"],
    ["supplier_invoice", "document"],
    ["customer_credit", "document"],
    ["supplier_credit", "document"],
    ["payment", "payment"],
    ["shipment", "shipment"],
    ["document", "document"],
    ["source_record", "source_record"],
    ["commitment", "commitment"],
    ["reservation", "reservation"],
    ["movement", "movement"],
    ["fact", "fact"],
    ["ledger_entry", "ledger_entry"],
  ];
  for (const [family, record_kind, roles, masterFamily] of families) {
    const target = { kind: "record", family, record_kind, roles, id: "exact-opaque-id" };
    const next = readSelection(
      new URL(selectionUrl(paletteTargetSelection(base, target)), "http://localhost"),
    );
    assert.equal(next.tenant, "one", family);
    if (masterFamily) {
      assert.equal(next.route, "master-data", family);
      assert.equal(next.family, masterFamily, family);
      assert.equal(next.record, target.id, family);
    } else if (family.endsWith("_order")) {
      assert.equal(next.route, "orders-deliveries", family);
      assert.equal(
        next.ordersView,
        family === "customer_order" ? "customer-orders" : "supplier-orders",
        family,
      );
      assert.equal(next.entry, target.id, family);
    } else {
      assert.equal(next.route, "inspector", family);
      assert.equal(next.inspectorView, "records", family);
      assert.equal(next.inspectorTargetKind, record_kind, family);
      assert.equal(next.inspectorTargetId, target.id, family);
    }
  }
});
