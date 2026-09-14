import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
const source = readFileSync(
  new URL("../src/unified/analytics/AnalyticsChart.tsx", import.meta.url),
  "utf8",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.CommonJS,
    jsx: ts.JsxEmit.ReactJSX,
  },
}).outputText;
const exports = {};
vm.runInNewContext(compiled, {
  exports,
  require: (name) => {
    if (name === "../../localization") return { t: (text) => text, formatNumber: String };
    if (name === "./AnalyticsTable") return { labels: { customer_id: "customer_name" } };
    return require(name);
  },
});
function render(rows, dimensions = ["customer_id"], kind = "bar") {
  return renderToStaticMarkup(
    React.createElement(exports.AnalyticsChart, {
      kind,
      result: {
        executed_definition: { measures: ["order_count"], dimensions },
        columns: [{ key: "order_count", label: "Order count" }],
        rows: rows.map((row) => ({ customer_id: "customer-1", order_count: 3, ...row })),
        page: { has_more: false },
      },
    }),
  );
}
for (const kind of ["bar", "line"]) {
  test(`${kind}: mixed currencies render immediately with a direct choice`, () => {
    const html = render(
      [
        { currency: "EUR", order_count: 4 },
        { currency: "USD", order_count: 99 },
      ],
      undefined,
      kind,
    );
    assert.match(html, /<svg/);
    assert.match(html, /aria-pressed="true"[^>]*>EUR/);
    assert.match(html, /aria-pressed="false"[^>]*>USD/);
    assert.doesNotMatch(html, /Filter by/);
    assert.doesNotMatch(html.match(/<svg[\s\S]*<\/svg>/)[0], /99/);
  });
  test(`${kind}: units and combined partitions are directly selectable`, () => {
    for (const rows of [
      [{ unit: "kg" }, { unit: "pcs" }],
      [
        { currency: "EUR", unit: "kg" },
        { currency: "USD", unit: "pcs" },
      ],
    ]) {
      const html = render(rows, undefined, kind);
      assert.match(html, /<svg/);
      assert.match(html, /kg/);
      assert.match(html, /pcs/);
      assert.equal((html.match(/aria-pressed=/g) || []).length, 2);
    }
  });
  test(`${kind}: unknown partitions and partitions beyond row 50 stay accessible`, () => {
    const html = render(
      [
        ...Array.from({ length: 50 }, () => ({ currency: "EUR" })),
        { currency: "USD" },
        { currency: null },
      ],
      undefined,
      kind,
    );
    assert.match(html, />USD<\/button>/);
    assert.match(html, />Unknown<\/button>/);
  });
  test(`${kind}: missing grouping requests grouping first`, () => {
    const html = render([{ currency: "EUR" }, { currency: "USD" }], ["currency", "unit"], kind);
    assert.match(html, /Choose a grouping, such as customer or month, and run the analysis again/);
    assert.doesNotMatch(html, /Filter by|<svg/);
  });
  test(`${kind}: compatible results still render`, () => {
    assert.match(
      render(
        [
          { currency: "EUR", unit: "kg" },
          { currency: "EUR", unit: "kg" },
        ],
        undefined,
        kind,
      ),
      /<svg/,
    );
    assert.match(render([{}, {}], undefined, kind), /<svg/);
  });
}
