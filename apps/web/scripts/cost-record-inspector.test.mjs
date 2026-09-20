import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
const require = createRequire(import.meta.url);
function harness() {
  const state = [],
    requests = [];
  let cursor = 0,
    loaded;
  const exports = {};
  const Pager = () => null;
  const ReadState = () => React.createElement("p", null, "Loading record");
  vm.runInNewContext(
    ts.transpileModule(
      readFileSync(new URL("../src/unified/Inspector.tsx", import.meta.url), "utf8"),
      {
        compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
      },
    ).outputText,
    {
      exports,
      require(name) {
        if (name === "react")
          return {
            ...React,
            useEffect() {},
            useRef: () => ({ current: null }),
            useState(initial) {
              const i = cursor++;
              if (!(i in state)) state[i] = initial;
              return [
                state[i],
                (value) => {
                  state[i] = value;
                },
              ];
            },
          };
        if (name === "../api")
          return {
            api: {
              inspector: async (...args) => {
                requests.push(args);
                return payload;
              },
            },
          };
        if (name === "../localization") return { t: (x) => x, currentLanguage: () => "de" };
        if (name === "./WarehousePage") return { RegisterPager: Pager };
        if (name === "./ReadState") return { ReadState };
        if (name === "./inspectorFormat")
          return { inspectorValue: (v) => (v == null ? "—" : String(v)) };
        if (name === "./usePaletteHistory") return { recordOpened() {} };
        if (name === "./useCompanyContext")
          return {
            useRead(fn) {
              requests.fetch = fn;
              return { data: loaded, loading: !loaded, error: null, refresh() {} };
            },
          };
        return require(name);
      },
    },
  );
  const payload = {
    title: "Deckungsbeitragsprüfung",
    subtitle: "review-1",
    sections: [
      {
        title: "Recorded values",
        rows: [
          { label: "Exact amount", value: "114.0000" },
          { label: "Source", value: "Invoice", link: { kind: "document", id: "doc-1" } },
        ],
      },
    ],
    member_page: { number: 1, size: 25, total: 34, pages: 2, has_next: true, has_previous: false },
  };
  const props = {
    tenant: "tenant-1",
    target: { kind: "cost_contribution_review", id: "review-1" },
    close() {},
  };
  const render = () => {
    cursor = 0;
    return exports.Inspector(props);
  };
  const find = (node, predicate) => {
    if (!React.isValidElement(node)) return;
    if (predicate(node)) return node;
    for (const child of React.Children.toArray(node.props.children)) {
      const found = find(child, predicate);
      if (found) return found;
    }
  };
  return {
    exports,
    payload,
    props,
    render,
    find,
    Pager,
    requests,
    load: async () => {
      loaded = await requests.fetch();
    },
  };
}
test("retained inspection renders exact amounts and follows the source link", () => {
  const h = harness();
  let target;
  const element = h.exports.InspectorContent({
    data: h.payload,
    selectedKind: "cost_contribution_review",
    follow: (value) => {
      target = value;
    },
  });
  assert.match(renderToStaticMarkup(element), /114\.0000/);
  h.find(element, (node) => node.type === "button").props.onClick();
  assert.equal(target.kind, "document");
  assert.equal(target.id, "doc-1");
});
test("member paging hides the previous page and resets after follow/back", async () => {
  const h = harness();
  h.render();
  await h.load();
  let tree = h.render();
  h.find(tree, (node) => node.type === h.Pager).props.change(2);
  tree = h.render();
  assert.equal(
    h.find(tree, (node) => node.type === h.exports.InspectorContent),
    undefined,
  );
  await h.load();
  tree = h.render();
  assert.deepEqual(h.requests.at(-1), [
    "tenant-1",
    "cost_contribution_review",
    "review-1",
    false,
    2,
    "de",
  ]);
  h.find(tree, (node) => node.type === h.exports.InspectorContent).props.follow({
    kind: "document",
    id: "doc-1",
  });
  h.render();
  await h.load();
  tree = h.render();
  assert.equal(h.requests.at(-1)[4], 1);
  h.find(tree, (node) => node.type === "button" && node.props.children === "Back").props.onClick();
  h.render();
  await h.load();
  tree = h.render();
  assert.equal(h.requests.at(-1)[2], "review-1");
  assert.equal(h.requests.at(-1)[4], 1);
  h.props.tenant = "tenant-2";
  tree = h.render();
  assert.equal(
    h.find(tree, (node) => node.type === h.exports.InspectorContent),
    undefined,
  );
});
