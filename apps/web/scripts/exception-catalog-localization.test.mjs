import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parseCatalogs } from "./i18n-audit-lib.mjs";

// Spec 279 FR-012: every exception class title and resolution text reads in the
// viewer's language. Read the catalog's plain `label:`/`clears_through:` lines.
const catalog = readFileSync(
  new URL(
    "../../../packages/reality-core/config/operational_exception_catalog.yaml",
    import.meta.url,
  ),
  "utf8",
);
const texts = [
  ...new Set(
    [...catalog.matchAll(/^ {4}(?:label|clears_through): (.+)$/gmu)].map((match) =>
      match[1].trim(),
    ),
  ),
];
const catalogs = parseCatalogs(fileURLToPath(new URL("../src/localization.tsx", import.meta.url)));

test("the catalog lists every class title and resolution", () => {
  assert.ok(texts.length >= 70, `found ${texts.length}`);
  assert.ok(texts.includes("Missing acquisition cost"));
});
for (const language of ["de", "nl", "es"])
  test(`exception titles and resolutions have ${language} translations`, () => {
    assert.deepEqual(
      texts.filter((text) => !catalogs[language].get(text)?.trim()),
      [],
    );
  });
test("the Exceptions page renders titles and resolutions through t()", () => {
  const page = readFileSync(new URL("../src/unified/AttentionPage.tsx", import.meta.url), "utf8");
  assert.match(page, /operational_exception_guidance/);
  assert.match(page, /t\(selected\.guidance\)/);
  assert.match(page, /<ResolutionGuidance/);
});
