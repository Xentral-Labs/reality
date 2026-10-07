import assert from "node:assert/strict";
import test from "node:test";
import { instrumentTrend, miniTrendPath } from "../src/unified/instrumentMiniTrend.ts";
import { flows } from "./fixtures/operations-cockpit-data.mjs";

test("mini trends reuse held named flows and do not invent a stock-risk or Finance history", () => {
  const order = instrumentTrend("orders", flows);
  assert.deepEqual(
    order.series.map((s) => s.points.map((p) => p.value)),
    [flows.buckets.map((b) => b.orders_received), flows.buckets.map((b) => b.dispatch_movements)],
  );
  assert.deepEqual(
    order.series[0].points.map((p) => p.at),
    flows.buckets.map((b) => b.end),
  );
  assert.deepEqual(
    instrumentTrend("messages", flows).series[0].points,
    flows.messages.series.map((p) => ({ at: p.at, value: p.unanswered })),
  );
  assert.equal(instrumentTrend("messages", flows).level, true);
  assert.deepEqual(
    instrumentTrend("supply", flows).series[0].points.map((p) => p.value),
    flows.buckets.map((b) => b.receipts),
  );
  assert.deepEqual(
    instrumentTrend("stock", flows).series.map((s) => s.points.map((p) => p.value)),
    [flows.buckets.map((b) => b.receipts), flows.buckets.map((b) => b.dispatch_movements)],
  );
  assert.deepEqual(
    instrumentTrend("returns", flows).series.map((s) => s.points.map((p) => p.value)),
    [flows.buckets.map((b) => b.return_arrivals), flows.buckets.map((b) => b.return_dispositions)],
  );
  assert.equal(instrumentTrend("finance", flows).series.length, 0);
  assert.equal(instrumentTrend("orders", undefined).series.length, 0);
});

test("missing/uncovered values are gaps, while genuine zero values remain known", () => {
  const broken = structuredClone(flows);
  broken.buckets[1].known = false;
  broken.buckets[2].orders_received = null;
  broken.buckets[3].orders_received = Infinity;
  const points = instrumentTrend("orders", broken).series[0].points;
  assert.equal(points[0].value, 0);
  assert.equal(points[1].value, null);
  assert.equal(points[2].value, null);
  assert.equal(points[3].value, null);
});

test("mini paths honor actual elapsed time and never bridge missing history", () => {
  const at = (minute) => new Date(Date.UTC(2026, 9, 7, 10, minute)).toISOString();
  const options = { start: at(0), end: at(60), minimum: 0, maximum: 10 };
  const path = miniTrendPath(
    [
      { at: at(0), value: 0 },
      { at: at(15), value: 5 },
      { at: at(30), value: null },
      { at: at(60), value: 10 },
    ],
    options,
  );
  assert(path.startsWith("M2,34"));
  assert(
    path.includes("L41,18"),
    "quarter-hour is placed at quarter of the plot, not evenly spaced by index",
  );
  assert(path.includes("M158,2"), "missing history starts a new segment");
  assert.equal((path.match(/M/g) || []).length, 2);
  assert.equal(miniTrendPath([{ at: at(0), value: null }], options), "");
  assert.equal(miniTrendPath([{ at: "invalid", value: 1 }], options), "");
  assert.equal(miniTrendPath([{ at: at(0), value: 1 }], { ...options, end: options.start }), "");
  assert(
    !miniTrendPath(
      [
        { at: at(0), value: 0 },
        { at: at(60), value: 0 },
      ],
      { ...options, maximum: 0 },
    ).includes("NaN"),
  );
});
