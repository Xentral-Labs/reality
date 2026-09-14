import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";
const load = async (name) => {
  const code = ts.transpile(
    readFileSync(new URL(`../src/unified/${name}.ts`, import.meta.url), "utf8"),
    { module: ts.ModuleKind.ES2022, target: ts.ScriptTarget.ES2022 },
  );
  return import(`data:text/javascript;base64,${Buffer.from(code).toString("base64")}`);
};
test("table preferences validate untrusted storage and keep identity/actions visible", async () => {
  const { validateLayout, layoutKey } = await load("tablePreferences");
  assert.notEqual(layoutKey("user1", "facts"), layoutKey("user2", "facts"));
  assert.notEqual(layoutKey("user1", "facts"), layoutKey("user1", "warehouse"));
  const layout = validateLayout(
    { density: "compact", hidden: [0, 1, 3, 999], widths: { 0: 99999, 1: 2, 3: "bad" } },
    4,
  );
  assert.deepEqual(layout.hidden, [1]);
  assert.equal(layout.widths[0], 320);
  assert.equal(layout.widths[1], 70);
  assert.equal(validateLayout(null, 3).density, "normal");
});
test("table query roundtrips bounded size and rejects invalid direction/size", async () => {
  const { readSelection, selectionUrl, companySelection } = await load("routing");
  const s = readSelection(
    new URL("https://example.test/app/facts?table=facts&size=100&sort=value&sort_direction=desc"),
  );
  assert.equal(s.tableSize, 100);
  assert.equal(s.tableSort, "value");
  assert.equal(s.tableDirection, "desc");
  assert.match(selectionUrl(s), /size=100/);
  assert.equal(companySelection(s, "new").tableSort, "");
  assert.equal(
    readSelection(new URL(selectionUrl(companySelection(s, "new")), "https://example.test"))
      .tableSize,
    100,
  );
  const bad = readSelection(
    new URL("https://example.test/app/facts?size=10000&sort_direction=unsafe"),
  );
  assert.equal(bad.tableSize, 50);
  assert.equal(bad.tableDirection, "asc");
});
