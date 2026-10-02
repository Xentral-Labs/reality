import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";
import { distributeByDuration, parseShard } from "./browser-suite-sharding.mjs";

const suite = JSON.parse(readFileSync(new URL("./browser-suite.json", import.meta.url), "utf8"));

test("the CI browser suite lists existing fixture scripts once, in order", () => {
  assert.ok(suite.scripts.length > 0);
  assert.deepEqual(suite.scripts, [...new Set(suite.scripts)].sort());
  for (const script of suite.scripts) {
    const url = new URL(`./${script}`, import.meta.url);
    assert.ok(existsSync(url), `${script} is missing`);
    // Real-server journeys need their Python harness, not the fixture runner.
    assert.doesNotMatch(readFileSync(url, "utf8"), /JOURNEY_BASE_URL/, script);
    assert.ok(Number.isFinite(suite.estimated_seconds[script]), `${script} needs a duration`);
    assert.ok(suite.estimated_seconds[script] > 0, `${script} duration must be positive`);
  }
  assert.deepEqual(Object.keys(suite.estimated_seconds).sort(), suite.scripts);
});

test("duration-weighted shards contain every script once and stay balanced", () => {
  const shards = distributeByDuration(suite.scripts, suite.estimated_seconds, 7);
  assert.deepEqual(shards.flatMap((shard) => shard.scripts).sort(), suite.scripts);
  // The additional ten-second fee proof adds at most two seconds per seven-way shard.
  assert.ok(Math.max(...shards.map((shard) => shard.seconds)) <= 332, JSON.stringify(shards));
});

test("shard selection rejects malformed and out-of-range values", () => {
  assert.deepEqual(parseShard("2/7"), { index: 2, count: 7 });
  for (const invalid of ["", "0/7", "8/7", "1/0", "one/seven", "1/2/3"]) {
    assert.throws(() => parseShard(invalid), /Invalid BROWSER_SUITE_SHARD/);
  }
});
