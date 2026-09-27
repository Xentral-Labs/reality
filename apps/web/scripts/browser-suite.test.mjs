import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const suite = JSON.parse(readFileSync(new URL("./browser-suite.json", import.meta.url), "utf8"));

test("the CI browser suite lists existing fixture scripts once, in order", () => {
  assert.ok(suite.scripts.length > 0);
  assert.deepEqual(suite.scripts, [...new Set(suite.scripts)].sort());
  for (const script of suite.scripts) {
    const url = new URL(`./${script}`, import.meta.url);
    assert.ok(existsSync(url), `${script} is missing`);
    // Real-server journeys need their Python harness, not the fixture runner.
    assert.doesNotMatch(readFileSync(url, "utf8"), /JOURNEY_BASE_URL/, script);
  }
});
