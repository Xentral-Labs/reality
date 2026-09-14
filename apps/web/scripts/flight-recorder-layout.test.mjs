import { test } from "node:test";
import assert from "node:assert/strict";
import { buildFlightGraph } from "../src/unified/flightRecorderGraph.ts";
import {
  layoutRecorder,
  recorderInterval,
  DAY,
  HOUR,
  HOUR6,
  INTERVALS,
  MINUTE5,
  QUARTER,
  WEEK,
} from "../src/unified/flightRecorderLayout.ts";

const at = (iso, sequence, kind = "movement", id = `m${sequence}`, payload = {}) => ({
  id: `e${sequence}`,
  sequence,
  subject_type: kind,
  subject_id: id,
  payload,
  source_record_id: null,
  recorded_at: iso,
  occurred_at: "2026-01-01T00:00:00Z",
  business_context: {},
  type: `${kind}.recorded`,
  business_title: kind,
});
const options = { label: 100, header: 50, dot: 12, gap: 4, rows: 8, column: 40, pad: 4 };
const upTo = (iso, extra = {}) => ({ ...options, now: Date.parse(iso), ...extra });

test("interval follows the loaded recording range: 15 minutes, one hour, one day", () => {
  assert.equal(recorderInterval(0), QUARTER);
  assert.equal(recorderInterval(6 * HOUR), QUARTER);
  assert.equal(recorderInterval(6 * HOUR + 1), HOUR);
  assert.equal(recorderInterval(3 * DAY), HOUR);
  assert.equal(recorderInterval(3 * DAY + 1), DAY);
});

test("records land in the column of their earliest recording interval, never per event", () => {
  const graph = buildFlightGraph([
    at("2026-09-08T10:02:00Z", 1),
    at("2026-09-08T10:09:00Z", 2, "movement", "m1"),
    at("2026-09-08T10:31:00Z", 3, "document", "d1"),
    at("2026-09-08T11:50:00Z", 4, "commitment", "c1"),
  ]);
  const layout = layoutRecorder(graph, upTo("2026-09-08T11:59:00Z"));
  assert.equal(layout.interval, QUARTER);
  assert.equal(layout.columns.length, 8);
  assert.equal(layout.columns[0].start, Date.parse("2026-09-08T10:00:00Z"));
  const column = (key) => layout.nodes.get(key).column;
  assert.equal(column("movement:m1"), 0);
  assert.equal(column("business_event:e2"), 0);
  assert.equal(column("document:d1"), 2);
  assert.equal(column("commitment:c1"), 7);
  assert.equal(layout.nodes.size, graph.nodes.length);
  assert.ok(layout.width <= options.label + 8 * options.column + 64);
});

test("same interval and lane stack in rows; a burst widens its column instead of hiding records", () => {
  const events = Array.from({ length: 20 }, (_, i) =>
    at("2026-09-08T10:00:00Z", i + 1, "movement", `m${i}`),
  );
  const layout = layoutRecorder(buildFlightGraph(events), upTo("2026-09-08T10:05:00Z"));
  assert.equal(layout.columns.length, 1);
  const dots = [...layout.nodes.values()].filter((n) => n.kind === "movement");
  assert.equal(dots.length, 20);
  const rows = new Set(dots.map((n) => n.row)),
    subColumns = new Set(dots.map((n) => n.subColumn));
  assert.equal(rows.size, 8);
  assert.equal(subColumns.size, 3);
  assert.ok(layout.columns[0].width > options.column);
  const cells = new Set(dots.map((n) => `${n.lane}:${n.column}:${n.subColumn}:${n.row}`));
  assert.equal(cells.size, 20, "every record has its own cell");
  const laneHeight = layout.laneHeights[3];
  assert.equal(laneHeight, 2 * options.pad + 8 * (options.dot + options.gap) - options.gap);
  for (const node of dots) {
    const { x, y } = layout.position(node.key);
    assert.ok(
      x >= layout.columns[0].x && x + options.dot <= layout.columns[0].x + layout.columns[0].width,
    );
    assert.ok(y >= layout.laneTops[3] && y + options.dot <= layout.laneTops[3] + laneHeight);
  }
});

test("labels fall on fixed steps and note day changes; references keep a compact area at the left", () => {
  const graph = buildFlightGraph([
    at("2026-09-06T08:00:00Z", 1, "movement", "m1", { item_id: "i1", party_id: "p1" }),
    at("2026-09-08T10:00:00Z", 2, "movement", "m2", { item_id: "i2" }),
  ]);
  const layout = layoutRecorder(graph, upTo("2026-09-08T10:00:00Z"));
  assert.equal(layout.interval, HOUR);
  assert.equal(layout.columns.length, 51);
  const labelled = layout.columns.filter((c) => c.label);
  assert.ok(labelled.length >= 8);
  assert.ok(labelled.every((c) => new Date(c.start).getUTCHours() % 6 === 0));
  assert.ok(
    layout.columns.some((c) => c.dayStart && c.start === Date.parse("2026-09-07T00:00:00Z")),
  );
  const reference = layout.nodes.get("item:i1");
  assert.ok(reference.reference);
  assert.ok(layout.position("item:i1").x < layout.columns[0].x);
  assert.ok(layout.referenceWidth > 0);
  assert.equal(layout.position("movement:m2").x >= layout.columns[50].x, true);
});

test("a graph without events still yields one column and no crash", () => {
  const layout = layoutRecorder(buildFlightGraph([]), upTo("2026-09-08T10:00:00Z"));
  assert.equal(layout.columns.length, 1);
  assert.equal(layout.nodes.size, 0);
  assert.ok(layout.height > options.header);
});

test("the paper runs up to now and fills the visible width even when records sit in one burst", () => {
  const graph = buildFlightGraph(
    Array.from({ length: 5 }, (_, i) => at("2026-09-09T19:09:00Z", i + 1, "document", `d${i}`)),
  );
  const layout = layoutRecorder(graph, upTo("2026-09-10T08:30:00Z", { minColumns: 24 }));
  assert.equal(layout.interval, HOUR, "range to now picks the raster, not the burst alone");
  assert.equal(layout.columns.at(-1).start, Date.parse("2026-09-10T08:00:00Z"));
  assert.ok(layout.columns.length >= 24);
  assert.equal(
    layout.nodes.get("document:d0").column,
    layout.columns.findIndex((c) => c.start === Date.parse("2026-09-09T19:00:00Z")),
  );
  const nowX = layout.xAt(layout.now);
  const last = layout.columns.at(-1);
  assert.ok(nowX > last.x && nowX <= last.x + last.width, "now sits inside the last column");
  const probe = Date.parse("2026-09-09T19:30:00Z");
  assert.ok(Math.abs(layout.timeAt(layout.xAt(probe)) - probe) < 60_000, "x and time round-trip");
  const short = layoutRecorder(graph, upTo("2026-09-10T08:30:00Z", { minColumns: 60 }));
  assert.equal(short.columns.length, 60, "a short history still fills the requested columns");
  assert.ok(short.columns[0].start < Date.parse("2026-09-09T19:00:00Z"));
});

test("a chosen zoom level overrides the automatic raster and keeps every record placed", () => {
  const graph = buildFlightGraph([
    at("2026-09-08T10:02:00Z", 1, "movement", "m1"),
    at("2026-09-09T19:09:00Z", 2, "document", "d1"),
  ]);
  assert.deepEqual(INTERVALS, [MINUTE5, QUARTER, HOUR, HOUR6, DAY, WEEK]);
  const fine = layoutRecorder(graph, upTo("2026-09-09T20:00:00Z", { interval: MINUTE5 }));
  assert.equal(fine.interval, MINUTE5);
  assert.equal(
    fine.nodes.get("document:d1").column,
    fine.columns.findIndex((c) => c.start === Date.parse("2026-09-09T19:05:00Z")),
  );
  assert.ok(
    fine.columns.filter((c) => c.label).every((c) => new Date(c.start).getUTCMinutes() % 15 === 0),
  );
  const coarse = layoutRecorder(
    graph,
    upTo("2026-09-09T20:00:00Z", { interval: WEEK, minColumns: 8 }),
  );
  assert.equal(coarse.interval, WEEK);
  assert.equal(coarse.columns.length, 8);
  assert.equal(
    coarse.nodes.get("movement:m1").column,
    coarse.nodes.get("document:d1").column,
    "both records fall into one week",
  );
  const six = layoutRecorder(graph, upTo("2026-09-09T20:00:00Z", { interval: HOUR6 }));
  assert.ok(six.columns.filter((c) => c.label).every((c) => new Date(c.start).getUTCHours() === 0));
});

test("one bounded logarithmic pulse groups every record in a lane and interval", () => {
  const events = Array.from({ length: 20 }, (_, i) =>
    at("2026-09-08T10:00:00Z", i + 1, "movement", `m${i}`),
  );
  const layout = layoutRecorder(buildFlightGraph(events), upTo("2026-09-08T10:05:00Z"));
  const movementPulse = layout.pulses.find(
    (pulse) => pulse.lane === 3 && pulse.column === 0 && !pulse.reference,
  );
  assert.ok(movementPulse);
  assert.equal(movementPulse.count, 20);
  assert.equal(movementPulse.members.length, 20);
  assert.equal(new Set(movementPulse.members).size, 20);
  assert.ok(movementPulse.diameter > options.dot);
  assert.ok(movementPulse.diameter <= 32);
  assert.ok(movementPulse.opacity > 0.5 && movementPulse.opacity <= 1);

  const eventPulse = layout.pulses.find(
    (pulse) => pulse.lane === 4 && pulse.column === 0 && !pulse.reference,
  );
  assert.equal(eventPulse.count, 20, "business events aggregate independently in their lane");
  assert.equal(
    layout.pulses.filter((pulse) => pulse.column === 0 && !pulse.reference).length,
    2,
    "the interval renders one pulse per non-empty lane",
  );
});

test("earlier references form one separate pulse for their lane", () => {
  const graph = buildFlightGraph([
    at("2026-09-08T10:00:00Z", 1, "movement", "m1", {
      item_id: "i1",
      party_id: "p1",
    }),
    at("2026-09-08T10:04:00Z", 2, "movement", "m2", {
      item_id: "i2",
      party_id: "p2",
    }),
  ]);
  const layout = layoutRecorder(graph, upTo("2026-09-08T10:05:00Z"));
  const referencePulses = layout.pulses.filter((pulse) => pulse.reference);
  assert.equal(referencePulses.length, 1);
  assert.deepEqual(
    referencePulses.map((pulse) => [pulse.lane, pulse.count]),
    [[0, 4]],
  );
});

test("aggregate mode keeps pulse columns fixed and gives all five lanes breathing room", () => {
  const events = Array.from({ length: 60 }, (_, i) =>
    at("2026-09-08T10:00:00Z", i + 1, "movement", `m${i}`),
  );
  const layout = layoutRecorder(
    buildFlightGraph(events),
    upTo("2026-09-08T10:05:00Z", { aggregate: true }),
  );
  assert.equal(layout.columns[0].width, options.column);
  assert.ok(layout.laneHeights.every((height) => height === 60));
  assert.equal(layout.height, options.header + 5 * 60);
});

test("aggregate lanes share an optional minimum work height", () => {
  const layout = layoutRecorder(buildFlightGraph([]), {
    ...options,
    aggregate: true,
    minHeight: 480,
  });
  assert.ok(layout.height >= 480);
  assert.ok(layout.laneHeights.every((height) => height >= 84));
});
