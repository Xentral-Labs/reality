import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parseCatalogs } from "./i18n-audit-lib.mjs";

// Spec 279 FR-004: every text the resolution guidance catalog can put on screen has a
// translation in each supported language. The web translates the English wording.
const guidance = JSON.parse(
  fs.readFileSync(
    new URL("../../../packages/reality-core/config/resolution_guidance.json", import.meta.url),
    "utf8",
  ),
);
const catalogs = parseCatalogs(fileURLToPath(new URL("../src/localization.tsx", import.meta.url)));
const texts = [
  ...new Set([
    ...Object.values(guidance.reasons).flatMap((reason) => [reason.label, reason.explanation]),
    ...Object.values(guidance.steps).flatMap((step) =>
      [step.label, step.chat_prompt, step.alternative?.label, step.alternative?.chat_prompt].filter(
        Boolean,
      ),
    ),
  ]),
];

test("the catalog has wording to translate", () => {
  assert.ok(texts.length > 50);
});
for (const language of ["de", "nl", "es"])
  test(`resolution guidance wording has ${language} translations`, () => {
    assert.deepEqual(
      texts.filter((text) => !catalogs[language].get(text)?.trim()),
      [],
    );
  });
test("translated chat prompts keep their scope placeholder", () => {
  for (const language of ["de", "nl", "es"])
    for (const prompt of Object.values(guidance.steps).flatMap((entry) =>
      [entry.chat_prompt, entry.alternative?.chat_prompt].filter(Boolean),
    ))
      assert.match(catalogs[language].get(prompt) || "{scope}", /\{scope\}/u);
});
