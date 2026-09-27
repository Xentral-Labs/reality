import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const root = new URL("../../../", import.meta.url);
const data = JSON.parse(
  fs.readFileSync(new URL("apps/docs/.vitepress/data/business-journeys.json", root), "utf8"),
);
const component = fs.readFileSync(
  new URL("apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue", root),
  "utf8",
);
const english = fs.readFileSync(
  new URL("apps/docs/content/getting-started/business-journeys.md", root),
  "utf8",
);
const german = fs.readFileSync(
  new URL("apps/docs/content/de/getting-started/business-journeys.md", root),
  "utf8",
);

test("generated guide accounts for all canonical journeys without internal evidence", () => {
  assert.equal(data.entries.length, 228);
  assert.equal(new Set(data.entries.map((entry) => entry.id)).size, 228);
  assert.equal(data.entries[0].id, "A01");
  assert.equal(data.entries.at(-1).id, "R08");
  assert.doesNotMatch(JSON.stringify(data), /internal_evidence|packages\/reality-core\/tests/u);
});

test("guide provides filters, expandable details and a deterministic question fallback", () => {
  assert.match(component, /v-model="query"/u);
  assert.match(component, /v-model="section"/u);
  assert.match(component, /v-model="status"/u);
  assert.match(component, /<details v-for="entry in filtered"/u);
  assert.match(component, /Reality fragen/u);
  assert.match(component, /Ask Reality/u);
});

test("Docs Ask Reality uses the same public answer service as the website widget", () => {
  assert.match(component, /fetch\(`\$\{__API_URL__\}\/api\/journey-guide\/questions`/u);
  assert.match(component, /body: JSON\.stringify\(\{ question: value, locale: props\.locale \}\)/u);
  assert.match(component, /answer\.value = await response\.json\(\)/u);
  assert.match(component, /answer\.value\.text/u);
  assert.match(component, /answer\.citations/u);
  assert.match(component, /aria-busy/u);
});

test("Docs Ask Reality clears submitted questions and renders readable structured answers", () => {
  assert.match(component, /question\.value = ""/u);
  assert.match(component, /structuredAnswer/u);
  assert.match(component, /journey-answer-section/u);
  assert.match(component, /journey-answer-list/u);
  assert.doesNotMatch(component, /\{\{ answer\.text \}\}/u);
});

test("Docs Ask Reality shows cited journey IDs and titles in a compact table", () => {
  assert.match(component, /class="journey-citations"/u);
  assert.match(component, /citationTitle\(id\)/u);
  assert.match(component, /<table/u);
});

test("question answering and catalog browsing are presented as separate tasks", () => {
  assert.match(component, /class="journey-ask-intro"/u);
  assert.match(component, /class="journey-examples"/u);
  assert.match(component, /class="journey-catalog-head"/u);
  assert.match(component, /Browse all journeys/u);
  assert.match(component, /Alle Szenarien durchsuchen/u);
});

test("both editions distinguish capability coverage from demo cases", () => {
  assert.match(english, /broader than the \[Demo data guide\]/u);
  assert.match(german, /breiter als der \[Demo-Datensatz\]/u);
  assert.match(english, /Public questions are read-only/u);
  assert.match(german, /Öffentliche Fragen sind read-only/u);
});
