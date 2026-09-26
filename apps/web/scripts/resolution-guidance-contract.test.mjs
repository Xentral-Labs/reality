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

test("ordered guidance reads as a connected numbered stepper", async () => {
  const component = await source("unified/ResolutionGuidance.tsx");
  assert.match(component, /data-guidance-marker/);
  assert.match(component, /data-guidance-connector/);
  assert.match(component, /: index \+ 1\}/);
  assert.match(component, /size-8/);
  assert.doesNotMatch(component, /CircleDot/);
  assert.doesNotMatch(
    component,
    /data-\[guidance-first=true\]:ring-1|data-\[guidance-first=true\]:bg-surface/,
  );
});

test("each path type reuses an existing route and never acts on its own", async () => {
  const component = await source("unified/ResolutionGuidance.tsx");
  const actions = await source("unified/guidanceActions.ts");
  // Forms open through the shared launcher; only fields a form accepts are prefilled.
  assert.match(component, /context\.open\(form, prefill \? paletteActionPrefill\(form, prefill\)/);
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
    "Cost decisions cannot be confirmed in this company.",
  ])
    assert.match(actions, new RegExp(sentence.replace(/\./g, "\\.")));
  const component = await source("unified/ResolutionGuidance.tsx");
  assert.match(component, /step\.state === "open" && !barrier/);
});

test("the service result is re-read after any write", async () => {
  const component = await source("unified/ResolutionGuidance.tsx");
  assert.match(component, /addEventListener\(recordsChanged/);
});

test("delivery blockers read as words and offer the form that resolves them", async () => {
  const table = await source("unified/ReportDataTable.tsx");
  // Queue rows carry blocker_codes; the blocker report carries one blocker_type per row.
  assert.match(
    table,
    /blockerKeys = new Set\(\["blocker_codes", "blocking_reasons", "blocker_type"\]\)/,
  );
  assert.match(table, /typeof row\.blocker_type === "string"/);
  assert.match(table, /<BlockerGuidance/);
  const component = await source("unified/ResolutionGuidance.tsx");
  // A customer delivery is never prefilled into a receipt form.
  assert.match(component, /\["reserve", "commitment_hold_release"\]\.includes/);
});

test("storyline checks and the empty valuation list explain themselves", async () => {
  const narrator = await source("unified/StorylineNarrator.tsx");
  assert.doesNotMatch(narrator, /`\$\{check\.kind\}: \$\{check\.name\}`/);
  assert.match(narrator, /operational_exception_guidance/);
  const valuation = await source("unified/analytics/InventoryValuation.tsx");
  assert.match(valuation, /"inventory_valuation_unavailable"/);
});
