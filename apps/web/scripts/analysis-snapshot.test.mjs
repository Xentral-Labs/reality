import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const require = createRequire(import.meta.url);
const exported = {};
const source = readFileSync(
  new URL("../src/unified/analytics/GraphSteps.tsx", import.meta.url),
  "utf8",
);
vm.runInNewContext(
  ts.transpileModule(source + "\nexport { Toolbar, withFilter };", {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText,
  {
    exports: exported,
    Date,
    require: (name) =>
      name.startsWith(".")
        ? {
            t: (value) => value,
            catalogGroups: (items) => [["", items]],
            APIError: class {},
            formatCalendarDate: (value) => value,
          }
        : require(name),
  },
);
const node = {
  key: "stock_history",
  label: "Historical stock",
  properties: [
    {
      key: "snapshot_date",
      label: "Snapshot date (UTC)",
      kind: "time",
      temporal: "date",
      input: "date",
    },
    { key: "unit", label: "Unit", kind: "text" },
  ],
  measures: [],
  edges: [],
  edges_in: [],
};
const nodes = { stock_history: node };
const catalog = { nodes: [node] };
const query = {
  from: "stock_history",
  as: "s",
  group_by: [{ field: "s.unit" }],
  filter: [
    { field: "s.snapshot_date", op: "eq", value: "2026-01-05" },
    { field: "s.unit", op: "eq", value: "pcs" },
  ],
};
const plain = (value) => JSON.parse(JSON.stringify(value));

test("snapshot input is visible and is not an activity period", () => {
  const plan = exported.planOf(query, nodes);
  assert.equal(exported.questionPeriod(plan, nodes), undefined);
  const { createElement } = require("react");
  const { renderToStaticMarkup } = require("react-dom/server");
  const html = renderToStaticMarkup(
    createElement(exported.Toolbar, { catalog, nodes, plan, change() {} }),
  );
  assert.match(html, /type="date"/);
  assert.match(html, /value="2026-01-05"/);
  assert.match(html, /Snapshot date \(UTC\)/);
  assert.doesNotMatch(html, /Choose a period/);
});

test("editing a snapshot replaces its date and preserves unrelated conditions", () => {
  const plan = exported.planOf(query, nodes);
  const changed = exported.withFilter(plan, {
    shown: "Snapshot date = 2026-01-06",
    conditions: [{ field: "s.snapshot_date", op: "eq", value: "2026-01-06" }],
  });
  const saved = exported.question(changed);
  assert.deepEqual(plain(saved.filter), [
    { field: "s.unit", op: "eq", value: "pcs" },
    { field: "s.snapshot_date", op: "eq", value: "2026-01-06" },
  ]);
  assert.deepEqual(plain(exported.question(exported.planOf(saved, nodes))), plain(saved));
});

test("sentence groups describe business dimensions without changing identity axes", () => {
  const stock = {
    ...node,
    properties: [
      ...node.properties,
      { key: "item_id", label: "Article identity", kind: "text" },
      { key: "sku", label: "Article number", kind: "text" },
      { key: "name", label: "Article", kind: "text" },
      { key: "location_id", label: "Location identity", kind: "text" },
      { key: "location_name", label: "Location", kind: "text" },
    ],
  };
  const catalog = { stock_history: stock };
  const query = {
    from: "stock_history",
    as: "s",
    group_by: ["item_id", "sku", "name", "location_id", "location_name", "unit"].map((key) => ({
      field: `s.${key}`,
    })),
  };
  const plan = exported.planOf(query, catalog);
  const before = plain(exported.question(plan));
  assert.deepEqual(plain(exported.groupCaptions(plan, catalog)), ["Article", "Location"]);
  assert.deepEqual(plain(exported.question(plan)), before);
});
