import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { parseCatalogs } from "./i18n-audit-lib.mjs";
import { invariantTerms } from "./i18n-invariants.mjs";

const root = import.meta.dirname;
const catalogs = parseCatalogs(path.resolve(root, "../src/localization.tsx"));
const badge = readFileSync(path.resolve(root, "../src/unified/SourceBadge.tsx"), "utf8");
const inspection = readFileSync(
  path.resolve(root, "../../../packages/reality-core/src/reality/services/delivery_reads.py"),
  "utf8",
);

// Every label the origin badge renders, and the server rows the source inspection adds.
const labels = new Set([
  "Created here",
  "Show the original source",
  "A newer source version exists",
  "Open in source system",
  "Several systems contributed to this record",
  "Origin",
  "Address of the source system",
  "Address of the source system saved.",
  "Save address",
]);

test("the badge renders no label the catalogs do not carry", () => {
  const rendered = [...badge.matchAll(/t\(\s*"([^"]+)"/g)].map((match) => match[1]);
  assert.notEqual(rendered.length, 0, "the badge should render translated labels");
  assert.deepEqual(
    rendered.filter((label) => !labels.has(label)),
    [],
  );
});

test("the source inspection labels its interpretation and link rows", () => {
  for (const label of ["Interpretation", "Interpreter", "Open in source system"])
    assert.match(
      inspection,
      new RegExp(`value\\(\\s*"${label}"`),
      `missing inspection row: ${label}`,
    );
});

for (const [language, catalog] of Object.entries(catalogs)) {
  test(`${language}: provenance labels have translations`, () => {
    assert.deepEqual(
      [...labels].filter((label) => !catalog.has(label) && !invariantTerms.has(label)),
      [],
    );
  });
}

for (const [language, catalog] of Object.entries(catalogs)) {
  test(`${language}: data sources and received records have distinct labels`, () => {
    for (const key of ["Source", "Sources"]) {
      assert.equal(catalog.get(key), key);
      assert.ok(invariantTerms.has(key));
    }
    assert.ok(catalog.get("Original source").includes("Source Record"));
    assert.ok(catalog.get("Show the original source").includes("Source Record"));
  });
}

test("provenance columns use Source without renaming origin data", () => {
  for (const file of ["OrdersPage", "MasterDataPage", "DataSourcesPage"]) {
    const source = readFileSync(path.resolve(root, `../src/unified/${file}.tsx`), "utf8");
    assert.doesNotMatch(source, /"Origin"/);
    assert.match(source, /"Source"/);
    assert.match(source, /origin/);
  }
});
