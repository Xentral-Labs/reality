import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const recorder = readFileSync(
  new URL("../src/unified/FlightRecorder.tsx", import.meta.url),
  "utf8",
);

test("the recorder renders aggregate pulses and exposes members in the stacked record list", () => {
  assert.match(recorder, /data-recorder-pulse=/);
  assert.match(recorder, /pulseMembers\.map/);
  assert.match(recorder, /data-pulse-record-list/);
  assert.match(recorder, /data-pulse-record-label/);
  assert.match(recorder, /data-context-layout="stacked"/);
  assert.doesNotMatch(recorder, /previewOrbit/);
  assert.match(recorder, /data-close-focus-mode/);
  assert.match(recorder, /event\.key === "Escape"/);
  assert.doesNotMatch(recorder, /data-recorder-pulse-members/);
});

test("the relationship trace owns record-level links without duplicating them in the recorder", () => {
  assert.doesNotMatch(recorder, /data-flight-edge/);
  assert.doesNotMatch(recorder, /viewFocus\.edges\.map/);
  assert.doesNotMatch(recorder, /graph\.edges\.map/);
});
