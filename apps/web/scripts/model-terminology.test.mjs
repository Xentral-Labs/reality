import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";
import { parseCatalogs } from "./i18n-audit-lib.mjs";
import { invariantTerms } from "./i18n-invariants.mjs";

const catalogs = parseCatalogs(path.resolve(import.meta.dirname, "../src/localization.tsx"));
const types = {
  Fact: "Fact",
  Facts: "Facts",
  "Additional facts": "Facts",
  Commitment: "Commitment",
  Commitments: "Commitments",
  Reservation: "Reservation",
  Reservations: "Reservations",
  Movement: "Movement",
  Movements: "Movements",
  "Source record": "Source Record",
  "Source records": "Source Records",
  Document: "Document",
  Documents: "Documents",
  "Document line": "Document Line",
  "Document lines": "Document Lines",
  "Ledger entry": "Ledger Entry",
  "Ledger entries": "Ledger Entries",
  "Business event": "Business Event",
  "Business events": "Business Events",
  "Context Graph": "Context Graph",
};

for (const [language, catalog] of Object.entries(catalogs)) {
  test(`${language}: navigation and Inspector use canonical model names`, () => {
    for (const [source, label] of Object.entries(types)) {
      assert.equal(catalog.get(source), label, source);
      assert.ok(invariantTerms.has(label), `audit recognizes ${label}`);
    }
  });
  test(`${language}: related navigation keeps canonical model nouns`, () => {
    for (const [source, noun] of [
      ["Search commitments", "Commitments"],
      ["Back to commitments", "Commitments"],
      ["View commitments", "Commitments"],
      ["Open commitment", "Commitment"],
      ["Search reservations", "Reservations"],
      ["Select reservation", "Reservation"],
      ["Search movements", "Movements"],
      ["Select movement", "Movement"],
      ["Linked documents", "Documents"],
      ["Linked ledger entries", "Ledger Entries"],
      ["Linked movements", "Movements"],
      ["Existing facts", "Facts"],
    ]) {
      assert.ok(catalog.get(source)?.includes(noun), source);
      assert.notEqual(catalog.get(source), source, `control stays localized: ${source}`);
    }
  });
  test(`${language}: general business vocabulary and controls remain localized`, () => {
    for (const source of ["Save", "Business partners", "Items", "Locations", "All records"]) {
      assert.ok(catalog.get(source), source);
      assert.notEqual(catalog.get(source), source, source);
    }
  });
}

const localizedObjects = {
  de: ["Ausnahme", "Ausnahmen", "Entscheidung", "Entscheidungen"],
  nl: ["Uitzondering", "Uitzonderingen", "Beslissing", "Beslissingen"],
  es: ["Incidencia", "Incidencias", "Decisión", "Decisiones"],
};
for (const [language, expected] of Object.entries(localizedObjects)) {
  test(`${language}: Exceptions and Decisions use localized business names`, () => {
    const catalog = catalogs[language];
    ["Exception", "Exceptions", "Decision", "Decisions"].forEach((key, i) => {
      assert.equal(catalog.get(key), expected[i], key);
      assert.equal(invariantTerms.has(key), false, `${key} is no longer invariant`);
    });
    for (const [key, noun] of [
      ["Open in Exceptions", expected[1]],
      ["Search exceptions", expected[1]],
      ["Search decisions…", expected[3]],
      ["Current exceptions", expected[1]],
      ["Decision history", expected[2]],
      ["Exception catalog", expected[0]],
      ["Exception rules", expected[0]],
    ]) {
      // Compounds and inflected plural forms share their lexical stem.
      const stem = noun.toLocaleLowerCase().replace(/e$/, "").replace(/ión$/, "ion");
      const value = catalog.get(key)?.toLocaleLowerCase().replaceAll("ó", "o");
      assert.ok(value?.includes(stem.replaceAll("ó", "o")), key);
    }
    for (const [key, value] of catalog) {
      assert.doesNotMatch(value, /\b(?:Exceptions?|Decisions?)\b/, key);
    }
  });
}
