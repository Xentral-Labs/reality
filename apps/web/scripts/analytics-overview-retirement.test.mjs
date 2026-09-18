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
// Spec 228 restores explore as the declared-model catalog. Retired overview
// and console links still open the builder.
for (const view of [
  "",
  "overview",
  "invalid",
  "explore",
  "console",
  "reports",
  "graph",
  "templates",
]) {
  test(`analytics link ${view || "default"} opens a retained tab`, () => {
    const selection = readSelection(
      new URL(
        `https://example.test/app/analytics?tenant=one&analytics_view=${view}&days=90&metric=shipped&day=2026-09-17`,
      ),
    );
    assert.equal(
      selection.analyticsView,
      ["reports", "graph", "templates", "explore"].includes(view)
        ? view
        : view
          ? "graph"
          : "reports",
    );
    const url = new URL(selectionUrl(selection), "https://example.test");
    assert.equal(url.searchParams.get("tenant"), "one");
    for (const key of ["days", "metric", "day"]) assert.equal(url.searchParams.has(key), false);
    assert.equal(companySelection(selection, "two").analyticsView, "reports");
    assert.equal(
      companySelection({ ...selection, analyticsProposal: "private" }, "two").analyticsProposal,
      "",
    );
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
        if (name === "./RegisterWorkbench")
          return {
            RegisterHeader: ({ children }) => children,
            RegisterWorkbench: ({ children }) => children,
          };
        if (name === "./analytics/ReportLibrary") return { ReportLibrary: () => "Saved reports" };
        if (name === "./analytics/GraphSteps") return { GraphSteps: () => "Graph content" };
        if (name === "./analytics/GraphTemplates") return { GraphTemplates: () => "Templates" };
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
  // Spec 221 retired the overview; spec 224 retired the configured explorer
  // with it. The tabs are named rather than counted, so adding one does not
  // read as a regression and removing one does.
  assert.match(html, /aria-pressed="true">My reports/);
  assert.match(html, />Analysis</);
  assert.match(html, /Explore data/);
  assert.doesNotMatch(html, />Templates</);
  assert.match(html, /My reports/);
  assert.doesNotMatch(html, /Overview|Recorded activity|Query console/);
});
test("Home and client no longer consume retired metrics", () => {
  assert.doesNotMatch(source("../src/unified/HomePage.tsx"), /AnalyticsPreview/);
  assert.doesNotMatch(source("../src/api.ts"), /export type Insights|insights:|InsightMetric/);
});
test("the configured generation is gone from the client, not merely unmounted", () => {
  const client = source("../src/api.ts");
  assert.doesNotMatch(client, /analyticsApi|AnalyticsDefinition|AnalyticsCatalog/);
  // A chat hand-off carried a definition into the copilot. There is no
  // definition any more, so the context kind goes with it.
  assert.doesNotMatch(client, /kind: "analytics"/);
  assert.doesNotMatch(source("../src/unified/context.ts"), /AnalyticsHandoff/);
});
