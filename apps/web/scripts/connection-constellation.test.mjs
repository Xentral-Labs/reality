import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { connectionTraceLayout } from "../src/unified/connectionTraceLayout.ts";

test("directed trace separates origin and operational links around the selected record", () => {
  const layout = connectionTraceLayout(
    ["source_record", "document", "commitment", "movement", "business_event"],
    680,
  );
  assert.deepEqual(
    layout.nodes.map((node) => node.side),
    ["left", "left", "right", "right", "right"],
  );
  assert.ok(layout.nodes.slice(0, 2).every((node) => node.x < layout.root.x));
  assert.ok(layout.nodes.slice(2).every((node) => node.x > layout.root.x));
});

test("Timeline mounts the directed trace only for an individual record", () => {
  const recorder = readFileSync(
    new URL("../src/unified/FlightRecorder.tsx", import.meta.url),
    "utf8",
  );
  assert.match(recorder, /graphRecord && \(/);
  assert.match(recorder, /pulseMembers\.map/);
  assert.match(recorder, /<ObjectGraph[^>]*variant="trace"/s);
  assert.match(recorder, /data-context-detail-shell/);
  assert.match(recorder, /scrollIntoView\(\{ behavior: "smooth", block: "nearest" \}\)/);
  const graph = readFileSync(new URL("../src/unified/ObjectGraph.tsx", import.meta.url), "utf8");
  assert.match(graph, /variant\?: "standard" \| "trace"/);
  assert.match(graph, /data-connection-trace/);
});

test("pulse and pinned graph state stay in one stacked reading flow", () => {
  const recorder = readFileSync(
    new URL("../src/unified/FlightRecorder.tsx", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(recorder, /const \[preview, setPreview\]/);
  assert.match(recorder, /const graphKey = selected/);
  assert.match(recorder, /data-context-layout="stacked"/);
  assert.match(recorder, /data-recorder-pane/);
  assert.match(recorder, /data-relationship-pane/);
  assert.doesNotMatch(recorder, /data-context-split/);
  assert.doesNotMatch(recorder, /selected\s*&&\s*viewFocus\.edges\.map/);
});

test("the stacked inspector renders pulse members in an ERP-readable table", () => {
  const recorder = readFileSync(
    new URL("../src/unified/FlightRecorder.tsx", import.meta.url),
    "utf8",
  );
  const graph = readFileSync(new URL("../src/unified/ObjectGraph.tsx", import.meta.url), "utf8");
  assert.match(recorder, /data-pulse-record-list/);
  assert.match(recorder, /<table/);
  assert.match(recorder, /t\("Record type"\)/);
  assert.match(recorder, /t\("Business record"\)/);
  assert.match(recorder, /data-open-relationship-trace/);
  assert.doesNotMatch(recorder, /data-recorder-pulse-orbit/);
  assert.match(graph, /new Map\(/);
  assert.match(graph, /`\$\{row\.link!\.kind\}:\$\{row\.link!\.id\}`/);
});

test("the detail header follows the recorder instead of competing beside it", () => {
  const recorder = readFileSync(
    new URL("../src/unified/FlightRecorder.tsx", import.meta.url),
    "utf8",
  );
  assert.match(recorder, /data-recorder-header/);
  assert.match(recorder, /data-relationship-header/);
  assert.doesNotMatch(recorder, /context-pane-header/);
});

test("the recorder stays compact above the directed trace", () => {
  const recorder = readFileSync(
    new URL("../src/unified/FlightRecorder.tsx", import.meta.url),
    "utf8",
  );
  const graph = readFileSync(new URL("../src/unified/ObjectGraph.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(recorder, /minHeight: selectedPulse/);
  assert.match(graph, /connectionTraceLayout/);
  assert.match(graph, /data-trace-side/);
  assert.doesNotMatch(graph, /<ellipse/);
});
