import { test } from "node:test";
import assert from "node:assert/strict";
import { buildFlightGraph, connectedKeys } from "../src/unified/flightRecorderGraph.ts";
const event = (sequence, kind, id, payload = {}, source = "src1") => ({
  id: `e${sequence}`,
  sequence,
  subject_type: kind,
  subject_id: id,
  payload,
  source_record_id: source,
  recorded_at: "2026-09-08T10:00:00Z",
  business_context: {},
  type: `${kind}.created`,
  business_title: kind,
});
test("one record identity across events with explicit source and shortest payload links", () => {
  const graph = buildFlightGraph([
    event(4, "reservation", "r1", { commitment_id: "c1" }),
    event(3, "commitment", "c1", { document_line_id: "l1" }),
    event(2, "document", "d1"),
    event(1, "source_record", "src1"),
    event(5, "commitment", "c1"),
    event(6, "item", "unrelated", {}, null),
  ]);
  assert.equal(graph.nodes.filter((n) => n.key === "source_record:src1").length, 1);
  assert.equal(graph.nodes.filter((n) => n.key === "commitment:c1").length, 1);
  assert.equal(graph.nodes.filter((n) => n.kind === "business_event").length, 6);
  assert.deepEqual(
    graph.events.map((e) => e.sequence),
    [1, 2, 3, 4, 5, 6],
  );
  assert.ok(graph.edges.some((e) => e.from === "commitment:c1" && e.to === "reservation:r1"));
  assert.ok(graph.nodes.find((n) => n.key === "document_line:l1").referenceOnly);
  assert.equal(graph.nodes.find((n) => n.key === "document:d1").lane, 2);
  const keys = connectedKeys(graph, "reservation:r1");
  assert.ok(keys.has("source_record:src1"));
  assert.ok(!keys.has("item:unrelated"));
});
test("no edges inferred from correlation, names, unknown fields or invalid references", () => {
  const a = {
    ...event(1, "item", "a", { random_id: "b", party_id: { id: "b" } }, null),
    correlation_id: "same",
  };
  const b = { ...event(2, "item", "b", {}, null), correlation_id: "same" };
  const graph = buildFlightGraph([a, b]);
  assert.equal(graph.nodes.filter((n) => n.kind !== "business_event").length, 2);
  assert.ok(!connectedKeys(graph, "item:a").has("item:b"));
  assert.ok(graph.edges.every((e) => e.from !== e.to));
});
test("older history repositions first observations without duplicating records", () => {
  const recent = event(9, "movement", "m1");
  const before = buildFlightGraph([recent]);
  const after = buildFlightGraph([
    recent,
    event(1, "source_record", "src1"),
    event(2, "movement", "m1"),
  ]);
  assert.ok(before.nodes.find((n) => n.key === "source_record:src1").referenceOnly);
  assert.equal(after.nodes.find((n) => n.key === "source_record:src1").referenceOnly, false);
  assert.equal(after.nodes.find((n) => n.key === "movement:m1").column, 1);
  assert.equal(after.nodes.filter((n) => n.key === "movement:m1").length, 1);
});

test("dense earlier references stay in two rows in an untimed area", () => {
  const events = Array.from({ length: 100 }, (_, i) =>
    event(
      i + 1,
      "commitment",
      `c${i}`,
      {
        party_id: `p${i}`,
        item_id: `i${i}`,
        location_id: `l${i}`,
      },
      `src${i}`,
    ),
  );
  const graph = buildFlightGraph(events);
  const references = graph.nodes.filter((n) => n.referenceOnly);
  assert.equal(references.length, 400);
  assert.equal(graph.referenceColumns, 150);
  assert.equal(graph.slots[0], 2);
  const occupied = new Set();
  for (const node of references) {
    assert.ok(node.column < 0 && node.column >= -graph.referenceColumns);
    assert.ok(node.slot < 2);
    const cell = `${node.lane}:${node.column}:${node.slot}`;
    assert.ok(!occupied.has(cell));
    occupied.add(cell);
    assert.ok(graph.edges.some((edge) => edge.from === node.key));
  }
  assert.equal(graph.nodes.filter((n) => !n.referenceOnly).length, 200);
  assert.equal(graph.nodes.find((n) => n.key === "commitment:c99").column, 99);
  assert.ok(connectedKeys(graph, "item:i99").has("commitment:c99"));
});

test("older subject events move a reference out of the untimed area", () => {
  const recent = event(10, "commitment", "c1", { item_id: "i1" }, null);
  const before = buildFlightGraph([recent]);
  assert.equal(before.referenceColumns, 1);
  assert.equal(before.nodes.find((n) => n.key === "item:i1").column, -1);
  const after = buildFlightGraph([recent, event(1, "item", "i1", {}, null)]);
  assert.equal(after.referenceColumns, 0);
  assert.equal(after.nodes.find((n) => n.key === "item:i1").column, 0);
  assert.equal(after.nodes.filter((n) => n.key === "item:i1").length, 1);
  assert.ok(connectedKeys(after, "item:i1").has("commitment:c1"));
});

test("focus is one hop even when a shared reference connects hundreds of events", async () => {
  const { focusFlightGraph } = await import("../src/unified/flightRecorderGraph.ts");
  const graph = buildFlightGraph(
    Array.from({ length: 300 }, (_, i) =>
      event(i + 1, "document", `d${i}`, { party_id: "shared" }, null),
    ),
  );
  assert.equal(focusFlightGraph(graph, null).edges.length, 0);
  const focus = focusFlightGraph(graph, "document:d0");
  assert.deepEqual(
    [...focus.keys].sort(),
    ["business_event:e1", "document:d0", "party:shared"].sort(),
  );
  assert.equal(focus.edges.length, 2);
  assert.ok(!focus.keys.has("document:d1"));
  assert.equal(focusFlightGraph(graph, "party:shared").edges.length, 300);
});

test("off-screen hints count unique direct records and visible edges only", async () => {
  const { flightViewportFocus } = await import("../src/unified/flightRecorderGraph.ts");
  const graph = {
    nodes: ["a", "left", "right", "up", "down", "visible"].map((key) => ({ key })),
    edges: [
      ...["left", "right", "up", "down", "visible"].map((to) => ({ from: "a", to, label: "link" })),
      { from: "a", to: "left", label: "other" },
      { from: "visible", to: "right", label: "indirect" },
    ],
  };
  const positions = {
    a: { x: 40, y: 40 },
    left: { x: -40, y: 40 },
    right: { x: 120, y: 40 },
    up: { x: 40, y: -40 },
    down: { x: 40, y: 120 },
    visible: { x: 60, y: 60 },
  };
  const result = flightViewportFocus(
    graph,
    "a",
    (key) => positions[key],
    { left: 0, top: 0, right: 100, bottom: 100 },
    20,
    20,
  );
  assert.deepEqual(result.offscreen, {
    left: ["left"],
    right: ["right"],
    up: ["up"],
    down: ["down"],
  });
  assert.equal(result.edges.length, 1);
  assert.equal(result.edges[0].to, "visible");
});
