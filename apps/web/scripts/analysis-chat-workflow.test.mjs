import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";
const source = (name) => readFileSync(new URL(`../src/unified/${name}`, import.meta.url), "utf8");
const compile = (text) =>
  ts.transpileModule(text, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
const exports = {};
vm.runInNewContext(compile(source("analytics/chatHandoff.ts")), { exports });
const query = {
  from: "order",
  as: "o",
  group_by: [{ field: "o.currency" }],
  measures: ["order.value"],
};
test("analysis context is tenant-bound, bounded and lossless", () => {
  const event = { kind: "analysis", tenant: "one", label: "Current analysis", question: query };
  assert.equal(exports.analysisContext(event, "two"), null);
  assert.equal(exports.analysisContext({ ...event, question: { bad: true } }, "one"), null);
  assert.equal(exports.analysisContext({ ...event, label: "x".repeat(3000) }, "one"), null);
  const context = exports.analysisContext(event, "one");
  assert.equal(JSON.stringify(context.question), JSON.stringify(query));
  const message = exports.analysisMessage("Only this year", context);
  assert.ok(message.includes(JSON.stringify(query)));
  assert.ok(message.includes("Do not save or confirm automatically"));
  assert.equal(exports.analysisMessageText(message), "Only this year");
  assert.equal(exports.analysisMessage("Plain question", null), "Plain question");
  assert.equal(exports.analysisMessageText("Plain question"), "Plain question");
  assert.equal(
    exports.analysisMessageText("text\n\n[Reality analysis context]\ninvalid"),
    "text\n\n[Reality analysis context]\ninvalid",
  );
});
test("templates open an unsaved question without calling a mutation", () => {
  const module = {};
  const jsx = (type, props) => ({ type, props });
  const template = { key: "orders", label: "Orders", about: "Orders by currency", question: query };
  vm.runInNewContext(compile(source("analytics/GraphTemplates.tsx")), {
    exports: module,
    require: (name) =>
      name === "react/jsx-runtime"
        ? { jsx, jsxs: jsx }
        : {
            useState: (value) => [value, () => {}],
            currentLanguage: () => "en",
            t: (key) => key,
            useRead: () => ({ data: { templates: [template] } }),
            graphApi: {
              change: () => {
                throw new Error("Templates must not save");
              },
            },
          },
  });
  let received;
  const walk = (e) =>
    !e || typeof e !== "object"
      ? []
      : Array.isArray(e)
        ? e.flatMap(walk)
        : [e, ...walk(e.props?.children)];
  const tree = module.GraphTemplates({
    tenant: "one",
    onAdopted: (value) => {
      received = value;
    },
  });
  walk(tree)
    .find((e) => e.type === "button")
    .props.onClick();
  assert.equal(received, query);
});
test("analysis proposal URLs retain the handoff only in the analysis workspace and clear on company switch", () => {
  const module = {};
  vm.runInNewContext(compile(source("routing.ts")), { exports: module, URL, URLSearchParams });
  const selection = module.readSelection(
    new URL(
      "https://example.test/app/analytics?tenant=one&analytics_view=graph&analysis_proposal=p1",
    ),
  );
  assert.equal(selection.analyticsProposal, "p1");
  assert.match(module.selectionUrl(selection), /analysis_proposal=p1/);
  assert.doesNotMatch(module.selectionUrl({ ...selection, route: "finance" }), /analysis_proposal/);
  assert.equal(module.companySelection(selection, "two").analyticsProposal, "");
});

test("proposal handoff opens the exact checked definition without approving or saving", () => {
  const proposal = { kind: "graph", operation: "create", definition: query };
  const module = {},
    effects = [];
  const jsx = (type, props) => ({ type, props });
  vm.runInNewContext(compile(source("AnalyticsPage.tsx") + "\nexport { ProposalAnalysis };"), {
    exports: module,
    require: (name) =>
      name === "react"
        ? { useEffect: (effect) => effects.push(effect) }
        : name === "react/jsx-runtime"
          ? { jsx, jsxs: jsx }
          : {
              useRead: () => ({ data: proposal }),
              t: (key) => key,
              graphApi: {
                change: () => {
                  throw new Error("Opening must not save");
                },
              },
            },
  });
  let opened;
  module.ProposalAnalysis({
    tenant: "one",
    id: "p1",
    open: (value) => {
      opened = value;
    },
  });
  effects.splice(0).forEach((effect) => effect());
  assert.equal(opened, query);
  opened = undefined;
  proposal.operation = "delete";
  module.ProposalAnalysis({
    tenant: "one",
    id: "p1",
    open: (value) => {
      opened = value;
    },
  });
  effects.splice(0).forEach((effect) => effect());
  assert.equal(opened, undefined);
});

test("global chat preserves typed text, isolates context and restores it after a failed send", async () => {
  const module = {},
    slots = [],
    effects = [],
    listeners = new Map(),
    sent = [];
  let cursor = 0,
    fail = true;
  const useState = (initial) => {
    const at = cursor++;
    if (!(at in slots)) slots[at] = typeof initial === "function" ? initial() : initial;
    return [
      slots[at],
      (value) => {
        slots[at] = typeof value === "function" ? value(slots[at]) : value;
      },
    ];
  };
  const data = {
    sessions: [],
    messages: [],
    proposals: [],
    active_session_id: "session",
    case: { counterparty: "Customer", item: "Item" },
  };
  const ChatComposer = function ChatComposer() {};
  const jsx = (type, props) => ({ type, props });
  const api = {
    copilot: async () => data,
    sendCopilotMessage: async (tenant, session, text, commitment) => {
      sent.push({ tenant, session, text, commitment });
      if (fail) throw new Error("Temporary failure");
      return { user: { id: "u", content: text }, assistant: { id: "a", content: "Prepared" } };
    },
  };
  vm.runInNewContext(compile(source("ChatPage.tsx")), {
    exports: module,
    requestAnimationFrame: () => {},
    window: {
      addEventListener: (name, fn) => listeners.set(name, fn),
      removeEventListener: (name) => listeners.delete(name),
    },
    document: { getElementById: () => null, querySelector: () => null },
    require: (name) =>
      name === "react"
        ? {
            useState,
            useRef: (initial) => useState({ current: initial })[0],
            useId: () => "composer",
            useEffect: (effect, deps = []) => {
              const at = cursor++,
                previous = slots[at];
              if (!previous || deps.some((value, index) => value !== previous.deps[index])) {
                slots[at] = { deps };
                effects.push(() => {
                  previous?.cleanup?.();
                  slots[at].cleanup = effect();
                });
              }
            },
          }
        : name === "react/jsx-runtime"
          ? { jsx, jsxs: jsx }
          : name.includes("chatHandoff")
            ? exports
            : {
                t: (key) => key,
                api,
                ChatComposer,
                useRead: () => ({ data, refresh: () => {} }),
                messageContext: (content) => ({ text: exports.analysisMessageText(content) }),
              },
  });
  const walk = (e) =>
    !e || typeof e !== "object"
      ? []
      : Array.isArray(e)
        ? e.flatMap(walk)
        : [e, ...walk(e.props?.children)];
  const navigate = () => {};
  const render = () => {
    cursor = 0;
    const tree = module.ChatPage({
      selection: { tenant: "one", session: "session", commitment: "delivery" },
      navigate,
      dock: true,
      initialDraft: "Only this year",
    });
    effects.splice(0).forEach((effect) => effect());
    return walk(tree);
  };
  const composer = (tree) => tree.find((e) => e.type === ChatComposer).props;
  render();
  listeners.get("reality:open-chat")({
    detail: { kind: "analysis", tenant: "two", label: "Wrong", question: query },
  });
  assert.equal(
    render().some((e) => e.props?.children === "Remove context"),
    false,
  );
  listeners.get("reality:open-chat")({
    detail: { kind: "analysis", tenant: "one", label: "Orders", question: query },
  });
  let tree = render();
  assert.equal(composer(tree).value, "Only this year");
  assert.equal(sent.length, 0);
  composer(tree).send();
  for (let i = 0; i < 8; i++) await Promise.resolve();
  tree = render();
  assert.equal(composer(tree).value, "Only this year");
  assert.equal(
    tree.some((e) => e.props?.children === "Remove context"),
    true,
  );
  assert.equal(sent[0].commitment, "");
  assert.ok(sent[0].text.includes(JSON.stringify(query)));
  fail = false;
  composer(tree).send();
  for (let i = 0; i < 8; i++) await Promise.resolve();
  tree = render();
  assert.equal(sent.length, 2);
  assert.equal(sent[1].text, sent[0].text);
  assert.equal(composer(tree).value, "");
  assert.equal(
    tree.some((e) => e.type === "button" && e.props?.children === "Remove context"),
    false,
  );
});
