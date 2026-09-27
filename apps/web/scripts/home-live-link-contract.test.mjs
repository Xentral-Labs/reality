import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const homePulse = await readFile(new URL("../src/unified/HomePulse.tsx", import.meta.url), "utf8");
const activityGraph = await readFile(
  new URL("../src/unified/ActivityGraph.tsx", import.meta.url),
  "utf8",
);

test("the live-monitor action is separate from the period selector", () => {
  const period = homePulse.match(/const period = \(([\s\S]*?)\n  \);/)?.[1] ?? "";

  assert.match(period, /24 hours/);
  assert.doesNotMatch(period, /watchLive|Watch live|data-home-engine-room/);
  assert.match(homePulse, /liveAction=\{liveAction\}/);
});

test("the quiet action is supplied only when the live monitor is available", () => {
  assert.match(homePulse, /const liveAction = watchLive \? \(/);
  assert.match(homePulse, /data-home-engine-room/);
  assert.match(homePulse, /text-accent/);
  assert.doesNotMatch(homePulse, /className="br-btn"[^>]*data-home-engine-room/);
});

test("the graph groups the action with its live status, before independent controls", () => {
  assert.match(activityGraph, /liveAction\?: ReactNode/);
  assert.match(
    activityGraph,
    /data-activity-live=[\s\S]*?\{t\("Live"\)\}[\s\S]*?\{liveAction\}[\s\S]*?\{controls\}/,
  );
});
