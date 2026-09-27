import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { parseCatalogs } from "./i18n-audit-lib.mjs";
import { invariantTerms } from "./i18n-invariants.mjs";

// Spec 286 FR-006: every coded refusal and every translated term reads in each language,
// with the placeholders the service fills and the protected domain terms kept.
const catalog = JSON.parse(
  fs.readFileSync(
    new URL("../../../packages/reality-core/config/service_refusals.json", import.meta.url),
    "utf8",
  ),
);
const catalogs = parseCatalogs(fileURLToPath(new URL("../src/localization.tsx", import.meta.url)));
const protectedTerms =
  /\b(?:Reality|SourceRecords?|Evidence|Commitments?|Reservations?|Movements?)\b/gu;
const placeholders = (text) =>
  [...text.matchAll(/\{([a-z][a-z0-9_]*)\}/g)]
    .map((match) => match[1])
    .sort()
    .join();
const texts = [
  ...new Set([...Object.values(catalog.refusals).map((entry) => entry.message), ...catalog.terms]),
];

test("the catalog has refusals to translate", () => {
  assert.ok(texts.length > 0);
});

for (const language of ["de", "nl", "es"])
  test(`every refusal and term has a ${language} translation with its placeholders`, () => {
    const problems = [];
    for (const source of texts) {
      const value = catalogs[language].get(source);
      if (!value?.trim()) problems.push(`missing: ${source}`);
      else if (value === source && !invariantTerms.has(source))
        problems.push(`untranslated: ${source}`);
      else if (placeholders(value) !== placeholders(source))
        problems.push(`placeholders differ: ${source} → ${value}`);
      else if ((source.match(protectedTerms) || []).some((term) => !value.includes(term)))
        problems.push(`protected term dropped: ${source} → ${value}`);
    }
    assert.deepEqual(problems, []);
  });
