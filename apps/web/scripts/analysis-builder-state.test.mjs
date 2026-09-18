import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const source = readFileSync(
  new URL("../src/unified/analytics/GraphSteps.tsx", import.meta.url),
  "utf8",
);
const node = {
  key: "order",
  label: "Order",
  properties: [{ key: "number", label: "Number", kind: "text" }],
  measures: [],
  edges: [],
  edges_in: [],
};
const catalog = { nodes: [node], limits: { result_rows: 500 } };
const query = { from: "order", as: "o", group_by: [{ field: "o.number" }], limit: 50 };
const answer = (question = query, marker = "current") => ({
  question,
  rows: [{ marker }],
  editor: { path: "MATCH (o:order) RETURN o.number", parameters: {} },
  columns: [],
});

// Render the real component with deterministic hooks and deferred network reads.
// Children stay shallow: assertions observe the props passed to the real controls.
function harness(initialQuestion = query) {
  const slots = [],
    effects = [],
    requests = [];
  let cursor = 0;
  const useState = (initial) => {
    const at = cursor++;
    if (!(at in slots)) slots[at] = typeof initial === "function" ? initial() : initial;
    return [
      slots[at],
      (next) => {
        slots[at] = typeof next === "function" ? next(slots[at]) : next;
      },
    ];
  };
  const useRef = (initial) => useState({ current: initial })[0];
  const useEffect = (effect) => {
    const at = cursor++;
    if (!(at in slots)) {
      slots[at] = true;
      effects.push(effect);
    }
  };
  const defer = (tenant, question, signal) =>
    new Promise((resolve, reject) => requests.push({ tenant, question, signal, resolve, reject }));
  const exports = {};
  const jsx = (type, props) => ({ type, props });
  vm.runInNewContext(
    ts.transpileModule(source + "\nexport { Builder };", {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText,
    {
      exports,
      AbortController,
      DOMException,
      Date,
      Intl,
      console,
      require: (name) =>
        name === "react"
          ? { useState, useRef, useEffect, useMemo: (fn) => fn() }
          : name === "react/jsx-runtime"
            ? { jsx, jsxs: jsx }
            : {
                t: (text) => text,
                currentLanguage: () => "en",
                formatDateTime: (value) => value,
                formatDate: (value) => value,
                graphApi: { ask: defer, askPath: defer },
                useRead: () => ({ data: { templates: [] } }),
                APIError: class {},
                analyticsError: (error) => error.message,
              },
    },
  );
  let tree;
  const render = () => {
    cursor = 0;
    tree = exports.Builder({ tenant: "tenant-a", catalog, report: null, initialQuestion });
    return tree;
  };
  const all = (entry) =>
    !entry || typeof entry !== "object"
      ? []
      : Array.isArray(entry)
        ? entry.flatMap(all)
        : [entry, ...all(entry.props?.children)];
  const find = (predicate) => all(tree).find(predicate);
  const component = (name) => find((entry) => entry.type?.name === name);
  const tab = (name) =>
    find((entry) => entry.props?.role === "tab" && entry.props.children === name).props.onClick();
  render();
  const cleanups = effects.splice(0).map((fn) => fn());
  render();
  return {
    requests,
    render,
    find,
    component,
    tab,
    unmount: () => cleanups.forEach((fn) => fn?.()),
  };
}
const settle = async () => {
  await Promise.resolve();
  await Promise.resolve();
};

test("late responses cannot overwrite a newer sentence or update an unmounted company", async () => {
  const ui = harness();
  const before = ui.requests[0];
  ui.component("Toolbar").props.change({
    blocks: [{ alias: "o", node: "order", filters: [] }],
    measures: [],
    groups: [{ field: "o.number" }],
    limit: 10,
  });
  ui.render();
  const newer = ui.requests[1];
  assert.equal(before.signal.aborted, true);
  newer.resolve(answer({ ...query, limit: 10 }, "newer"));
  await settle();
  ui.render();
  before.resolve(answer(query, "older"));
  await settle();
  ui.render();
  assert.equal(ui.component("Result").props.answer.rows[0].marker, "newer");
  ui.unmount();
  assert.equal(newer.signal.aborted, true);
});

test("expert drafts survive tab changes and failed execution and block saving", async () => {
  const ui = harness();
  ui.requests[0].resolve(answer());
  await settle();
  ui.render();
  ui.tab("Cypher");
  ui.render();
  ui.find((entry) => entry.props?.["aria-label"] === "Cypher query").props.onChange({
    target: { value: "bad query" },
  });
  ui.render();
  ui.tab("Connections");
  ui.render();
  ui.tab("Cypher");
  ui.render();
  assert.equal(
    ui.find((entry) => entry.props?.["aria-label"] === "Cypher query").props.value,
    "bad query",
  );
  ui.find(
    (entry) => entry.type === "button" && entry.props.children === "Execute query",
  ).props.onClick();
  ui.requests[1].reject(new Error("Unreadable query"));
  await settle();
  ui.render();
  assert.equal(
    ui.find((entry) => entry.props?.["aria-label"] === "Cypher query").props.value,
    "bad query",
  );
  assert.equal(ui.find((entry) => entry.type === "fieldset").props.disabled, true);
  ui.tab("Result");
  ui.render();
  assert.equal(ui.component("Result"), undefined);
});

test("expert execution passes the full checked definition to saving", async () => {
  const advanced = {
    ...query,
    having: [{ measure: "order_count", op: "gt", value: 2 }],
    measures: ["order_count"],
  };
  const ui = harness(advanced);
  ui.requests[0].resolve(answer(advanced));
  await settle();
  ui.render();
  assert.equal(ui.component("Toolbar"), undefined);
  assert.equal(ui.component("Save").props.definition, advanced);
  assert.equal(ui.find((entry) => entry.type === "fieldset").props.disabled, false);
});

test("catalog previews keep false values false and translate boolean labels", () => {
  const exports = {};
  const source = readFileSync(
    new URL("../src/unified/analytics/DataExplorer.tsx", import.meta.url),
    "utf8",
  );
  vm.runInNewContext(
    ts.transpileModule(source, {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText,
    {
      exports,
      require: () => ({
        t: (key) => ({ Yes: "Ja", No: "Nein", Unknown: "Unbekannt" })[key] ?? key,
        formatCalendarDate: (value) => `day:${value}`,
        formatDateTime: (value) => `instant:${value}`,
      }),
    },
  );
  assert.equal(exports.catalogValue(false, "boolean"), "Nein");
  assert.equal(exports.catalogValue("false", "boolean"), "Nein");
  assert.equal(exports.catalogValue(true, "boolean"), "Ja");
  assert.equal(exports.catalogValue(null, "boolean"), "Unbekannt");
  assert.equal(exports.catalogValue("2026-09-01", "time", "date"), "day:2026-09-01");
  assert.equal(
    exports.catalogValue("2026-09-01T00:00:00Z", "time"),
    "instant:2026-09-01T00:00:00Z",
  );
});

test("explicitly reopening the same report reloads it while catalog navigation retains the draft", () => {
  const source = readFileSync(new URL("../src/unified/AnalyticsPage.tsx", import.meta.url), "utf8");
  const exports = {},
    slots = [];
  let cursor = 0;
  const jsx = (type, props, key) => ({ type, props, key });
  const components = {
    GraphSteps: function GraphSteps() {},
    ReportLibrary: function ReportLibrary() {},
  };
  vm.runInNewContext(
    ts.transpileModule(source + "\nexport { AnalyticsWorkspace };", {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText,
    {
      exports,
      require: (name) =>
        name === "react"
          ? {
              useState: (initial) => {
                const at = cursor++;
                if (!(at in slots)) slots[at] = initial;
                return [
                  slots[at],
                  (value) => {
                    slots[at] = typeof value === "function" ? value(slots[at]) : value;
                  },
                ];
              },
            }
          : name === "react/jsx-runtime"
            ? { jsx, jsxs: jsx }
            : { ...components, t: (text) => text },
    },
  );
  const walk = (entry) =>
    !entry || typeof entry !== "object"
      ? []
      : Array.isArray(entry)
        ? entry.flatMap(walk)
        : [entry, ...walk(entry.props?.children)];
  const render = (view) => {
    cursor = 0;
    return walk(
      exports.AnalyticsWorkspace({
        selection: { tenant: "a", analyticsView: view },
        navigate: () => {},
      }),
    );
  };
  const report = { id: "saved", revision: 1, definition: query };
  render("reports")
    .find((entry) => entry.type === components.ReportLibrary)
    .props.open(report);
  assert.equal(
    render("graph").find((entry) => entry.type === components.GraphSteps).props.active,
    true,
  );
  assert.equal(
    render("explore").find((entry) => entry.type === components.GraphSteps).props.active,
    false,
  );
  const firstKey = render("graph").find((entry) => entry.type === components.GraphSteps).key;
  assert.equal(
    render("explore").find((entry) => entry.type === components.GraphSteps).key,
    firstKey,
  );
  render("reports")
    .find((entry) => entry.type === components.ReportLibrary)
    .props.open(report);
  assert.notEqual(
    render("graph").find((entry) => entry.type === components.GraphSteps).key,
    firstKey,
  );
});
