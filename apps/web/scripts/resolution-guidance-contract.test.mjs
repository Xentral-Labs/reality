import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

// Spec 279: missing values explain themselves through one shared presentation.
const source = (name) => readFile(new URL(`../src/${name}`, import.meta.url), "utf8");

test("the shared component renders catalog wording, never codes", async () => {
  const component = await source("unified/ResolutionGuidance.tsx");
  const actions = await source("unified/guidanceActions.ts");
  // Wording comes from the application catalog and passes through t().
  assert.match(component, /resolution_guidance/);
  assert.match(component, /t\(entry\.label\)/);
  assert.match(actions, /t\(entry\.label\)/);
  assert.match(actions, /t\(entry\.explanation\)/);
  // An unknown code falls back to a generic sentence instead of showing itself.
  assert.match(actions, /Something this value needs is still missing/);
  // Codes may mark elements for tests (data-*), but never appear as visible text.
  assert.doesNotMatch(component, />\s*\{(?:step\.code|guidance\.reason_code)\}/);
});

test("each path type reuses an existing route and never acts on its own", async () => {
  const component = await source("unified/ResolutionGuidance.tsx");
  const actions = await source("unified/guidanceActions.ts");
  assert.match(component, /context\.open\(form\)/);
  assert.match(component, /route: "decisions", proposal/);
  assert.match(component, /route: "home"/);
  assert.match(component, /prepareChat\(/);
  // The chat handoff only fills the composer through the existing event.
  assert.match(actions, /new CustomEvent\(openChatEvent, \{ detail: \{ draft:/);
  assert.match(actions, /openChatEvent = "reality:open-chat"/);
  const chat = await source("unified/ChatPage.tsx");
  const handler = chat.match(/const prepare = [\s\S]*?\n {4}};/)?.[0] || "";
  assert.match(handler, /setQuestion\(draft\)/);
  assert.doesNotMatch(handler, /send|submit|post/i);
});

test("a viewer without the role sees who must act instead of a control", async () => {
  const actions = await source("unified/guidanceActions.ts");
  for (const sentence of [
    "A company owner must confirm this.",
    "An administrator takes care of this.",
    "This company is read-only. Nothing can be changed here.",
  ])
    assert.match(actions, new RegExp(sentence.replace(/\./g, "\\.")));
  const component = await source("unified/ResolutionGuidance.tsx");
  assert.match(component, /step\.state === "open" && !barrier/);
});

test("the service result is re-read after any write", async () => {
  const component = await source("unified/ResolutionGuidance.tsx");
  assert.match(component, /addEventListener\(recordsChanged/);
});
