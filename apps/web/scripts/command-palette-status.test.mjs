import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
const require = createRequire(import.meta.url);
const exports = {};
vm.runInNewContext(
  ts.transpileModule(
    readFileSync(new URL("../src/unified/CommandSearchStatus.tsx", import.meta.url), "utf8"),
    { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } },
  ).outputText,
  { exports, require: (name) => (name === "../localization" ? { t: (x) => x } : require(name)) },
);
const render = (providers) =>
  renderToStaticMarkup(
    React.createElement(exports.CommandSearchStatus, {
      providers,
      labels: { partners: "Business partners", orders: "Orders" },
      retry: () => {},
    }),
  );
test("pending providers share one loading status without failure or retry controls", () => {
  const html = render({ partners: { loading: true }, orders: { loading: true } });
  assert.equal((html.match(/data-search-loading/g) || []).length, 1);
  assert(html.includes("Searching…"));
  assert(!html.includes("Retry"));
  assert(!html.includes("unavailable"));
});
test("failures use a compact disclosure with independently labelled retries", () => {
  const html = render({
    partners: { loading: false, error: "failure" },
    orders: { loading: false, error: "failure" },
  });
  assert(html.includes("<details"));
  assert(!html.includes("<details open"));
  assert(html.includes('aria-label="Retry · Business partners"'));
  assert(html.includes('aria-label="Retry · Orders"'));
  assert.equal((html.match(/Some results are unavailable\./g) || []).length, 1);
});
test("mixed pending and failed providers retain both truthful states", () => {
  const html = render({
    partners: { loading: true },
    orders: { loading: false, error: "failure" },
  });
  assert(html.includes("Searching…"));
  assert(html.includes("Some results are unavailable."));
  assert(!render({ partners: { loading: false } }).includes("Searching…"));
});
