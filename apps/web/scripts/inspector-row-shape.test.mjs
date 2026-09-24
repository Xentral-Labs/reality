import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";
import React from "react";
import * as jsxRuntime from "react/jsx-runtime";
import { renderToStaticMarkup } from "react-dom/server";

/** Compile one source module against stubs, the way the Inspector tests already do. */
function load(file, requireImpl) {
  const exports = {};
  const wrapped = (name) => (name === "react/jsx-runtime" ? jsxRuntime : requireImpl(name));
  vm.runInNewContext(
    ts.transpileModule(readFileSync(new URL(`../src/${file}`, import.meta.url), "utf8"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText,
    { exports, require: wrapped, module: { exports }, console },
  );
  return exports;
}

const localization = {
  t: (key) => key,
  currentLanguage: () => "en",
  formatQuantity: (value) => String(Number(value)),
  formatMoney: (value, currency) => `${currency} ${value}`,
  formatDate: (value) => `day(${value})`,
  formatDateTime: (value) => `instant(${value})`,
};
const presentation = load("unified/inspectorPresentation.ts", () => ({}));
const format = load("unified/inspectorFormat.ts", (name) =>
  name === "../localization" ? localization : presentation,
);
const inspector = load("unified/Inspector.tsx", (name) => {
  if (name === "react")
    return {
      ...React,
      useEffect() {},
      useRef: () => ({ current: null }),
      useState: (i) => [i, () => {}],
    };
  if (name === "../localization") return localization;
  if (name === "./inspectorFormat") return format;
  if (name === "../api") return { api: {} };
  if (name === "./usePaletteHistory") return { recordOpened() {} };
  if (name === "./useCompanyContext") return { useRead: () => ({}) };
  if (name === "./ReadState") return { ReadState: () => null };
  if (name === "./WarehousePage") return { RegisterPager: () => null };
  return {};
});

const movement = {
  label: "Transfer",
  value: "-12 pcs",
  display_parts: [
    { type: "number", value: "-12" },
    { type: "text", value: " pcs" },
  ],
  meta: "2026-09-19T14:05:00+00:00",
  meta_parts: [{ type: "datetime", value: "2026-09-19T14:05:00+00:00" }],
  tone: "",
  link: { kind: "movement", id: "mov_1" },
};
const plain = { label: "Physical", value: "2 pcs", tone: "", link: null };

const panel = (rows, compact = false) =>
  inspector.InspectorContent({
    data: { title: "Beacon", subtitle: "—", sections: [{ title: "Movements here", rows }] },
    selectedKind: "stock",
    follow: () => {},
    compact,
  });

test("a measure and the qualifier beside it are separate elements, not one string", () => {
  const markup = renderToStaticMarkup(panel([movement]));
  assert.match(markup, /-12 pcs/);
  assert.match(markup, /instant\(2026-09-19T14:05:00\+00:00\)/);
  // The two never share an element, so neither can be read as part of the other.
  assert.doesNotMatch(markup, /-12 pcs\s*·\s*instant/);
  // Measures line up: the value carries tabular figures, the qualifier its own column.
  assert.match(markup, /tabular-nums/);
  assert.match(markup, /min-w-\[9\.5rem\] text-right/);
});

test("only the measure carries the link, and the whole row is the click target", () => {
  const markup = renderToStaticMarkup(panel([movement]));
  const button = markup.slice(markup.indexOf("<button"), markup.indexOf("</button>"));
  assert.match(button, /hover:bg-surface-muted/);
  // The qualifier is never underlined: the compound link was what made rows unreadable.
  const qualifier = markup.slice(markup.indexOf("instant(") - 200, markup.indexOf("instant("));
  assert.doesNotMatch(qualifier.slice(qualifier.lastIndexOf("<span")), /underline/);
});

test("a row without a qualifier renders exactly as it did before", () => {
  const markup = renderToStaticMarkup(panel([plain]));
  assert.match(markup, /max-w-\[65%\] break-words text-right/);
  assert.doesNotMatch(markup, /min-w-\[9\.5rem\]/);
});

test("a narrow preview stacks the qualifier under its measure", () => {
  const markup = renderToStaticMarkup(panel([movement], true));
  assert.match(markup, /flex min-w-0 flex-col items-end/);
  assert.doesNotMatch(markup, /min-w-\[9\.5rem\]/);
});

test("where there is room for one string only, value and qualifier recompose", () => {
  assert.equal(format.inspectorRowText(movement), "-12 pcs · instant(2026-09-19T14:05:00+00:00)");
  assert.equal(format.inspectorRowText(plain), "2 pcs");
  assert.equal(format.inspectorMeta(plain), "");
});
