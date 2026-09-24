import assert from "node:assert/strict";
import test from "node:test";
import {
  emptyStream,
  engineRoomHref,
  groupByCorrelation,
  liveFilterFromParams,
  liveFilterQuery,
  liveFilterToParams,
  mergeRows,
  receive,
  resume,
  setPaused,
} from "../src/unified/engineRoomModel.ts";

const row = (cursor, extra = {}) => ({
  id: `int_${cursor}`,
  cursor,
  correlation_id: `c_${cursor}`,
  recorded_at: `2026-09-24T10:00:${String(cursor % 60).padStart(2, "0")}Z`,
  ...extra,
});

test("a poll that repeats rows and delivers a late commit merges once, in cursor order", () => {
  const first = mergeRows([], [row(1), row(2), row(3)]);
  // The server re-sends recent rows and one that took a lower cursor but committed late.
  const merged = mergeRows(first, [row(3), row(4), row(0)]);
  assert.deepEqual(
    merged.map((r) => r.cursor),
    [0, 1, 2, 3, 4],
  );
});

test("the merged list keeps only the newest rows past its cap", () => {
  const rows = Array.from({ length: 10 }, (_, i) => row(i + 1));
  assert.deepEqual(
    mergeRows([], rows, 3).map((r) => r.cursor),
    [8, 9, 10],
  );
});

test("while paused, arrivals wait and are counted; resume shows them", () => {
  let stream = receive(emptyStream(), [row(1)]);
  stream = setPaused(stream, true);
  stream = receive(stream, [row(2), row(3)]);
  stream = receive(stream, [row(3), row(4)]);
  assert.deepEqual(
    stream.visible.map((r) => r.cursor),
    [1],
  );
  assert.equal(stream.pending, 3);
  stream = resume(stream);
  assert.equal(stream.paused, false);
  assert.equal(stream.pending, 0);
  assert.deepEqual(
    stream.visible.map((r) => r.cursor),
    [1, 2, 3, 4],
  );
});

test("a paused stream does not count a row it already shows", () => {
  let stream = receive(emptyStream(), [row(1)]);
  stream = setPaused(stream, true);
  stream = receive(stream, [row(1)]);
  assert.equal(stream.pending, 0);
});

test("rows of one cause group together, newest cause first", () => {
  const rows = [
    row(1, { correlation_id: "click" }),
    row(2, { correlation_id: "turn" }),
    row(3, { correlation_id: "click" }),
  ];
  const groups = groupByCorrelation(rows);
  assert.deepEqual(
    groups.map((g) => [g.correlation, g.rows.map((r) => r.cursor)]),
    [
      ["click", [1, 3]],
      ["turn", [2]],
    ],
  );
});

test("a filter survives the URL and becomes the API query", () => {
  const filter = {
    channel: "mcp",
    mcpToken: "mcpt_1",
    correlation: "",
    subjectType: "party",
    subjectId: "par_1",
    refresh: true,
  };
  const params = liveFilterToParams(filter);
  assert.equal(params.get("live_channel"), "mcp");
  assert.equal(params.get("live_correlation"), null);
  const back = liveFilterFromParams(params);
  assert.deepEqual(back, { ...filter, actor: "", kind: "", outcome: "" });
  const query = liveFilterQuery(back);
  assert.equal(query.get("channel"), "mcp");
  assert.equal(query.get("mcp_token_id"), "mcpt_1");
  assert.equal(query.get("subject_type"), "party");
  assert.equal(query.get("include_refresh"), "true");
  assert.equal(query.get("correlation_id"), null);
});

test("an unknown channel in the URL is ignored rather than sent", () => {
  const filter = liveFilterFromParams(new URLSearchParams("live_channel=telepathy"));
  assert.equal(filter.channel, "");
});

test("an entry point links to the Live tab with its filter", () => {
  const href = new URL(engineRoomHref("ten_1", { mcpToken: "mcpt_9" }), "https://app.test");
  assert.equal(href.pathname, "/app/inspector");
  assert.equal(href.searchParams.get("inspector_view"), "live");
  assert.equal(href.searchParams.get("tenant"), "ten_1");
  assert.equal(href.searchParams.get("live_token"), "mcpt_9");
});
