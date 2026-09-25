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
  assert.deepEqual(back, {
    ...filter,
    actor: "",
    kind: "",
    outcome: "",
    own: false,
    period: "",
    search: "",
  });
  const query = liveFilterQuery(back);
  assert.equal(query.get("channel"), "mcp");
  assert.equal(query.get("mcp_token_id"), "mcpt_1");
  assert.equal(query.get("subject_type"), "party");
  assert.equal(query.get("include_refresh"), "true");
  assert.equal(query.get("correlation_id"), null);
  // The viewer's own interactions are hidden unless they ask for them.
  assert.equal(query.get("hide_own"), "true");
  assert.equal(liveFilterQuery({ ...back, own: true }).get("hide_own"), null);
  assert.equal(liveFilterToParams({ ...back, own: true }).get("live_own"), "1");
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

test("a period is a window ending now; live has none", async () => {
  const { periodWindow } = await import("../src/unified/engineRoomModel.ts");
  const now = Date.parse("2026-09-25T10:00:00Z");
  assert.equal(periodWindow("", now), null);
  const hour = periodWindow("1h", now);
  assert.equal(hour.to.toISOString(), "2026-09-25T10:00:00.000Z");
  assert.equal(hour.from.toISOString(), "2026-09-25T09:00:00.000Z");
  assert.equal(periodWindow("7d", now).from.toISOString(), "2026-09-18T10:00:00.000Z");
});

test("the search finds a row by its shown label, technical name or actor", async () => {
  const { matchesSearch } = await import("../src/unified/engineRoomModel.ts");
  const row = {
    label: "List physical shipments",
    operation: "shipments_list",
    actor: { kind: "mcp_token", id: "mcp_1", label: "Claude Desktop" },
  };
  const german = (text) => (text === "List physical shipments" ? "Sendungen anzeigen" : text);
  assert.equal(matchesSearch(row, "sendungen", german), true);
  assert.equal(matchesSearch(row, "shipments_", german), true);
  assert.equal(matchesSearch(row, "claude", german), true);
  assert.equal(matchesSearch(row, "", german), true);
  assert.equal(matchesSearch(row, "rechnung", german), false);
});

test("period and search travel in the URL but never reach the API query", () => {
  const filter = { ...liveFilterFromParams(new URLSearchParams()), period: "24h", search: "lager" };
  const params = liveFilterToParams(filter);
  assert.equal(params.get("live_period"), "24h");
  assert.equal(params.get("live_q"), "lager");
  const back = liveFilterFromParams(params);
  assert.equal(back.period, "24h");
  assert.equal(back.search, "lager");
  const query = liveFilterQuery(back);
  assert.equal(query.get("live_period"), null);
  assert.equal(query.get("q"), null);
  assert.equal(liveFilterFromParams(new URLSearchParams("live_period=forever")).period, "");
});

const at = (seconds, extra = {}) => ({
  id: `int_${seconds}_${extra.channel || "web"}_${extra.op || ""}`,
  cursor: 1000 + seconds,
  recorded_at: new Date(Date.parse("2026-09-25T10:00:00Z") + seconds * 1000).toISOString(),
  channel: "web",
  outcome: "ok",
  operation: extra.op || "GET /items",
  actor: { kind: "user", id: "usr_1", label: "Anna" },
  stages: { read: [], written: [] },
  ...extra,
});
const NOW = Date.parse("2026-09-25T10:01:00Z");

test("the cockpit only counts what happened in the last minute", async () => {
  const { cockpit } = await import("../src/unified/engineRoomModel.ts");
  // 65 s and a day before "now" are outside the minute; 30 s and 1 s before are inside.
  const rows = [at(-86_400), at(-5), at(30), at(59)];
  const view = cockpit(rows, NOW);
  assert.equal(view.total, 2);
  assert.equal(view.quiet, false);
  // Yesterday's row is gone; nothing old keeps a quiet company busy.
  assert.equal(cockpit([at(-86_400)], NOW).quiet, true);
  assert.equal(cockpit([], NOW).total, 0);
});

test("channels get a rate, a 12-bucket trace of five seconds each, and errors", async () => {
  const { cockpit } = await import("../src/unified/engineRoomModel.ts");
  const rows = [
    at(1, { channel: "mcp" }),
    at(2, { channel: "mcp", outcome: "failed" }),
    at(58, { channel: "mcp" }),
    at(58, { channel: "worker" }),
  ];
  const view = cockpit(rows, NOW);
  const mcp = view.channels.find((c) => c.channel === "mcp");
  assert.equal(mcp.count, 3);
  assert.equal(mcp.errors, 1);
  assert.equal(mcp.trace.length, 12);
  assert.equal(mcp.trace[0], 2); // seconds 0-5 of the minute
  assert.equal(mcp.trace[11], 1); // the newest five seconds
  assert.deepEqual(
    view.channels.map((c) => c.channel),
    ["web", "mcp", "chat", "cli", "worker"],
  );
});

test("stages count reads and writes; actors are the ones active now, busiest first", async () => {
  const { cockpit } = await import("../src/unified/engineRoomModel.ts");
  const token = { kind: "mcp_token", id: "mcp_1", label: "Claude Desktop" };
  const rows = [
    at(10, { actor: token, op: "inventory_read", stages: { read: ["movement"], written: [] } }),
    at(20, {
      actor: token,
      op: "fulfillment_queue",
      stages: { read: ["commitment"], written: [] },
    }),
    at(30, { stages: { read: [], written: ["master_data"] } }),
  ];
  const view = cockpit(rows, NOW);
  assert.deepEqual(view.stages.movement, { read: 1, written: 0 });
  assert.deepEqual(view.stages.master_data, { read: 0, written: 1 });
  assert.equal(view.actors[0].label, "Claude Desktop");
  assert.equal(view.actors[0].count, 2);
  assert.equal(view.actors[0].last, "fulfillment_queue");
  assert.equal(view.ticker[0].operation, "GET /items"); // newest first
});
