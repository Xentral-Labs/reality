import assert from "node:assert/strict";
import test from "node:test";
import { metricChange, newEventIds } from "../src/unified/cockpitLiveSignals.ts";

const metric = (value, context = "company-a") => ({ context, value });
const events = (rows, context = "company-a:15") => ({
  context,
  events: rows.map(([id, sequence]) => ({ id, sequence })),
});

test("count feedback requires two finite current observations in the same context", () => {
  assert.equal(metricChange(null, metric(7)), null);
  assert.equal(metricChange(metric(7), metric(7)), null);
  assert.equal(metricChange(metric(7), metric(5)), -2);
  assert.equal(metricChange(metric(0), metric(3)), 3);
  assert.equal(metricChange(metric(7), metric(5, "company-b")), null);
  assert.equal(metricChange(metric(7), null), null);
  assert.equal(metricChange(null, metric(5)), null);
  assert.equal(metricChange(metric(NaN), metric(5)), null);
  assert.equal(metricChange(metric(7), metric(Infinity)), null);
});

test("event feedback excludes initial, repeated, replayed and changed-context rows", () => {
  const baseline = events([
    ["a", 5],
    ["b", 4],
  ]);
  assert.deepEqual(newEventIds(null, baseline), []);
  assert.deepEqual(newEventIds(baseline, baseline), []);
  assert.deepEqual(
    newEventIds(
      baseline,
      events([
        ["c", 6],
        ["a", 5],
      ]),
    ),
    ["c"],
  );
  assert.deepEqual(newEventIds(baseline, events([["old", 3]])), []);
  assert.deepEqual(newEventIds(baseline, events([["c", 6]], "company-b:15")), []);
  assert.deepEqual(newEventIds(baseline, events([["c", 6]], "company-a:60")), []);
  assert.deepEqual(newEventIds(baseline, null), []);
  assert.deepEqual(newEventIds(null, events([["c", 6]])), []);
  assert.deepEqual(newEventIds(events([]), events([["c", 6]])), ["c"]);
  assert.deepEqual(newEventIds({ ...events([]), sequenceFloor: 6 }, events([["old", 3]])), []);
});
