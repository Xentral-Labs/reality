import { test } from "node:test";
import assert from "node:assert/strict";
import {
  inspectorSections,
  inspectorSection,
  inspectorTabs,
} from "../src/unified/inspectorSections.ts";

test("Inspector sections match their contents and default destinations", () => {
  assert.deepEqual(
    inspectorSections.map((s) => [s.label, s.tabs[0]]),
    [
      ["Context Graph", "overview"],
      ["Facts", "facts"],
      ["Rules", "rules"],
      ["Actions", "history"],
    ],
  );
  assert.deepEqual(
    inspectorTabs("history").map((t) => t[0]),
    ["history", "commands"],
  );
  assert.deepEqual(
    inspectorTabs("rules").map((t) => t[1]),
    ["Additional fact rules", "Exception rules"],
  );
  assert.deepEqual(
    inspectorTabs("overview").map((t) => t[1]),
    ["Timeline", "Record graph"],
  );
});
test("legacy records links share the single primary register", () => {
  assert.equal(inspectorSection("records"), inspectorSection("facts"));
  assert.deepEqual(inspectorTabs("records"), [
    ["facts", "All records"],
    ["views", "Calculated views"],
  ]);
  assert.equal(inspectorSection("views").label, "Facts");
  assert.equal(inspectorSection("commands").label, "Actions");
});

test("legacy URLs retain tenant, search and record-type filters", async () => {
  const { readSelection, selectionUrl } = await import("../src/unified/routing.ts");
  const selection = readSelection(
    new URL(
      "https://example.test/app/inspector?tenant=t%26one&inspector_view=records&q=00123&inspector_record_kind=document&page=3",
    ),
  );
  assert.equal(inspectorSection(selection.inspectorView).label, "Facts");
  const url = new URL(selectionUrl(selection), "https://example.test");
  for (const [key, value] of [
    ["tenant", "t&one"],
    ["q", "00123"],
    ["inspector_record_kind", "document"],
    ["page", "3"],
  ])
    assert.equal(url.searchParams.get(key), value);
});
