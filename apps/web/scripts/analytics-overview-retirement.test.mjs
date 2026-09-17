import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const source = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const compiled = ts.transpile(source("../src/unified/routing.ts"), {
  module: ts.ModuleKind.ES2022,
});
const { readSelection, selectionUrl, companySelection } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);
for (const view of ["", "overview", "invalid", "explore", "reports"]) {
  test(`analytics link ${view || "default"} opens a retained tab`, () => {
    const selection = readSelection(
      new URL(
        `https://example.test/app/analytics?tenant=one&analytics_view=${view}&days=90&metric=shipped&day=2026-09-17`,
      ),
    );
    assert.equal(selection.analyticsView, view === "reports" ? "reports" : "explore");
    const url = new URL(selectionUrl(selection), "https://example.test");
    assert.equal(url.searchParams.get("tenant"), "one");
    for (const key of ["days", "metric", "day"]) assert.equal(url.searchParams.has(key), false);
    assert.equal(companySelection(selection, "two").analyticsView, "explore");
  });
}
test("rendered analytics carries no retired overview", () => {
  const exports = {};
  const require = createRequire(import.meta.url);
  vm.runInNewContext(
    ts.transpileModule(source("../src/unified/AnalyticsPage.tsx"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText,
    {
      exports,
      require: (name) => {
        if (name === "../localization") return { t: (value) => value };
        if (name === "./RegisterWorkbench") return { RegisterHeader: ({ children }) => children };
        if (name === "./analytics/AnalyticsExplorer")
          return { AnalyticsExplorer: () => "Explorer content" };
        if (name === "./analytics/ReportLibrary") return { ReportLibrary: () => "Saved reports" };
        if (name === "./analytics/GraphSteps") return { GraphSteps: () => "Graph content" };
        if (name.startsWith(".")) return {};
        return require(name);
      },
    },
  );
  const html = renderToStaticMarkup(
    React.createElement(exports.AnalyticsPage, {
      selection: { tenant: "one" },
      navigate: () => {},
    }),
  );
  // What spec 221 retired was the overview, not the right to add a view. The tabs
  // are named rather than counted, so a new one does not read as a regression.
  assert.match(html, /aria-pressed="true">Explore/);
  assert.match(html, /Business graph/);
  assert.match(html, /My reports/);
  assert.doesNotMatch(html, /Overview|Recorded activity/);
});
test("Home and client no longer consume retired metrics", () => {
  assert.doesNotMatch(source("../src/unified/HomePage.tsx"), /AnalyticsPreview/);
  assert.doesNotMatch(source("../src/api.ts"), /export type Insights|insights:|InsightMetric/);
});
