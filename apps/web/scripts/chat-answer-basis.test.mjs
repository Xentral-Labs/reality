import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const evidence = fs.readFileSync(
  path.join(root, "src", "unified", "StorylineChatEvidence.tsx"),
  "utf8",
);
const api = fs.readFileSync(path.join(root, "src", "api.ts"), "utf8");

test("chat replies show a compact business basis and hide unavailable disclosure", () => {
  assert.match(evidence, /Basis for this answer/u);
  assert.match(evidence, /if \(!data\.basis\.available && !data\.available\) return null/u);
  assert.match(evidence, /data-basis-role/u);
  assert.match(evidence, /recordRoute\(row\.record_type!, row\.record_id!\)/u);
  assert.doesNotMatch(evidence, /Reality did not record which calls produced this reply/u);
});

test("business rows lead and technical activity remains secondary", () => {
  assert.ok(evidence.indexOf("basis.rows.map") < evidence.indexOf("data-technical-activity"));
  assert.match(evidence, /basis\.additional_count/u);
  assert.match(api, /export type ChatAnswerBasisRow/u);
  assert.match(api, /basis: ChatAnswerBasis/u);
});

test("basis quantities use compact localized number formatting", () => {
  assert.match(evidence, /formatExactDecimal/);
  assert.match(evidence, /currentLanguage\(\) === "de" \? "Stk\."/);
});
