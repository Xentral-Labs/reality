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
      ["Business Graph", "overview"],
      ["Business Facts", "facts"],
      ["Event history", "history"],
      ["Available actions", "commands"],
    ],
  );
  assert.deepEqual(
    inspectorTabs("history").map((t) => t[0]),
    ["history"],
  );
  assert.deepEqual(
    inspectorTabs("rules").map((t) => t[1]),
    ["All records", "Calculated views", "Fact rules"],
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
    ["rules", "Fact rules"],
  ]);
  assert.equal(inspectorSection("views").label, "Business Facts");
  assert.equal(inspectorSection("commands").label, "Available actions");
});

test("legacy URLs retain tenant, search and record-type filters", async () => {
  const { readSelection, selectionUrl } = await import("../src/unified/routing.ts");
  const selection = readSelection(
    new URL(
      "https://example.test/app/inspector?tenant=t%26one&inspector_view=records&q=00123&inspector_record_kind=document&page=3",
    ),
  );
  assert.equal(inspectorSection(selection.inspectorView).label, "Business Facts");
  const url = new URL(selectionUrl(selection), "https://example.test");
  for (const [key, value] of [
    ["tenant", "t&one"],
    ["q", "00123"],
    ["inspector_record_kind", "document"],
    ["page", "3"],
  ])
    assert.equal(url.searchParams.get(key), value);
});

test("exception rules legacy links normalize without losing company or finding context", async () => {
  const { readSelection, selectionUrl, navigationSelection } =
    await import("../src/unified/routing.ts");
  const old = readSelection(
    new URL(
      "https://example.test/app/inspector?tenant=t1&inspector_view=exceptions&q=stock&exception=e1",
    ),
  );
  assert.equal(old.route, "attention");
  assert.equal(old.attentionView, "rules");
  assert.equal(old.tenant, "t1");
  assert.equal(old.q, "stock");
  assert.equal(old.exception, "e1");
  const restored = readSelection(new URL(selectionUrl(old), "https://example.test"));
  assert.equal(restored.attentionView, "rules");
  assert.equal(restored.route, "attention");
  const finding = navigationSelection(old, { route: "attention", exception: "e2" });
  assert.equal(finding.attentionView, "findings");
  assert.equal(finding.exception, "e2");
  assert.equal(finding.tenant, "t1");
  const internal = navigationSelection(finding, {
    route: "inspector",
    inspectorView: "exceptions",
  });
  assert.equal(internal.route, "attention");
  assert.equal(internal.attentionView, "rules");
  const invalid = readSelection(
    new URL("https://example.test/app/attention?attention_view=unknown"),
  );
  assert.equal(invalid.attentionView, "findings");
});
