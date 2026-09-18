import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
const require = createRequire(import.meta.url);
const source = (name) => readFileSync(new URL(`../src/unified/${name}`, import.meta.url), "utf8");
test("off-page detail isolates its close action from table surface resets and preserves content", () => {
  const exports = {};
  vm.runInNewContext(
    ts.transpileModule(source("SelectedRecordPreview.tsx"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText,
    { exports, require: (name) => (name === "../localization" ? { t: (x) => x } : require(name)) },
  );
  let closed = false;
  const element = exports.SelectedRecordPreview({
    kind: "order",
    close: () => {
      closed = true;
    },
    children: React.createElement("p", null, "Exact selected record"),
  });
  const html = renderToStaticMarkup(element);
  assert.match(html, /data-selected-order-detail/);
  assert.match(html, /Exact selected record/);
  assert.doesNotMatch(html, /register-surface/);
  const toolbar = React.Children.toArray(element.props.children)[0];
  const button = React.Children.toArray(toolbar.props.children)[0];
  assert.equal(button.props["aria-label"], "Close");
  button.props.onClick();
  assert.equal(closed, true);
});
test("order and master off-page branches share the isolated detail surface", () => {
  for (const file of ["OrdersPage.tsx", "MasterDataPage.tsx"]) {
    const text = source(file);
    assert.match(text, /<SelectedRecordPreview/);
    assert.doesNotMatch(text, /className="register-surface" data-selected-/);
  }
});

test("exact selections reveal loaded details rather than only the loading placeholder", () => {
  assert.match(source("OrdersPage.tsx"), /<InlineInspector\s+reveal/);
  assert.match(
    source("InlinePreview.tsx"),
    /if \(reveal && ready\) content.current\?\.scrollIntoView/,
  );
  assert.match(source("InlinePreview.tsx"), /\[reveal, ready, target.id, target.kind\]/);
  assert.match(source("MasterDataPage.tsx"), /if \(readyId\) preview.current\?\.scrollIntoView/);
});
