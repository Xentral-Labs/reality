import { test } from "node:test";
import assert from "node:assert/strict";
import {
  journeyRange,
  layoutJourney,
  journeyLanes,
  mergeJourneyEvents,
  decisionTimelineEvents,
} from "../src/unified/orderJourneyLayout.ts";
const event = (id, kind, time, subject = id) => ({
  id,
  subject_type: kind,
  subject_id: subject,
  recorded_at: time,
  occurred_at: "2000-01-01T00:00:00Z",
  sequence: Number(id.slice(1)),
});
const events = [
  event("e1", "commitment", "2026-09-18T08:00:00Z", "c1"),
  event("e2", "reservation", "2026-09-18T08:01:00Z"),
  event("e3", "commitment", "2026-09-18T08:02:00Z", "c1"),
  event("e4", "document", "2026-09-17T08:00:00Z"),
];
test("fit uses eligible recording times, preserving repeated subject observations", () => {
  const range = journeyRange(events);
  assert.ok(range.start <= Date.parse(events[0].recorded_at));
  assert.ok(range.end >= Date.parse(events[2].recorded_at));
  assert.ok(range.start > Date.parse(events[3].recorded_at));
  const layout = layoutJourney(events, range, 800);
  assert.deepEqual(layout.flatMap((p) => p.events.map((e) => e.id)).sort(), ["e1", "e2", "e3"]);
  assert.equal(journeyLanes.length, 6);
});
test("only overlapping points in one lane group, with all members accessible", () => {
  const burst = Array.from({ length: 30 }, (_, i) =>
    event(`e${i}`, "movement", events[0].recorded_at),
  );
  const points = layoutJourney([...burst, events[0]], journeyRange(burst), 600);
  assert.equal(points.length, 2);
  assert.equal(points.find((p) => p.lane === 4).events.length, 30);
});
test("range excludes outside events and empty input has finite geometry", () => {
  const range = {
    start: Date.parse("2026-09-18T08:01:00Z"),
    end: Date.parse("2026-09-18T08:01:30Z"),
  };
  assert.deepEqual(
    layoutJourney(events, range, 600).flatMap((p) => p.events.map((e) => e.id)),
    ["e2"],
  );
  const empty = journeyRange([], 1000);
  assert.ok(Number.isFinite(empty.start) && empty.end > empty.start);
  assert.deepEqual(layoutJourney([], empty, 0), []);
});
test("refresh merges identity and sequence without dropping history", () => {
  assert.deepEqual(
    mergeJourneyEvents(events, [events[0]]).map((e) => e.id),
    ["e1", "e2", "e3", "e4"],
  );
});

test("posting group events share the ledger lane without becoming ledger entries", () => {
  const posting = event("e7", "posting_group", "2026-09-18T08:03:00Z", "group-1");
  const points = layoutJourney([posting], journeyRange([posting]), 600);
  assert.equal(points[0].lane, 5);
  assert.equal(points[0].events[0].subject_type, "posting_group");
});

test("decisions become unconnected raised and settled points", () => {
  const proposal = (id, status, decided_at = null) => ({
    id,
    status,
    created_at: "2026-09-18T08:00:00Z",
    decided_at,
    review_label: `Review ${id}`,
  });
  const markers = decisionTimelineEvents([
    proposal("pending", "proposed"),
    proposal("yes", "executed", "2026-09-18T08:02:00Z"),
    proposal("no", "rejected", "2026-09-18T08:03:00Z"),
  ]);
  assert.deepEqual(
    markers.map((marker) => marker.type),
    [
      "decision.raised",
      "decision.raised",
      "decision.accepted",
      "decision.raised",
      "decision.rejected",
    ],
  );
  assert.ok(markers.every((marker) => marker.subject_type === "decision"));
  assert.equal(layoutJourney(markers, journeyRange(markers), 600)[0].lane, 2);
});
