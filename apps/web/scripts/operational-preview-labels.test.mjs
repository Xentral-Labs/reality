import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { parseCatalogs } from "./i18n-audit-lib.mjs";
import { invariantTerms } from "./i18n-invariants.mjs";

const catalogs = parseCatalogs(path.resolve(import.meta.dirname, "../src/localization.tsx"));
const service = readFileSync(
  path.resolve(
    import.meta.dirname,
    "../../../packages/reality-core/src/reality/services/operational_previews.py",
  ),
  "utf8",
);
const labels = new Set(
  [...service.matchAll(/(?:_row|_section|field)\(\s*"([^"]+)"/g)].map((match) => match[1]),
);
for (const label of [
  "Current item name",
  "Committed / reserved / fulfilled / open",
  "Customer",
  "Supplier",
  "Committed",
  "Reserved",
  "Fulfilled",
  "Open",
  "Requested delivery",
  "Incoming",
  "Outgoing",
  "Inbound",
  "Outbound",
  "Debit",
  "Credit",
  "Partially settled",
  "Settled",
  "Delivered",
  "Announced",
  "In transit",
  "Handed over",
  "Delivery exception",
])
  labels.add(label);
for (const [language, catalog] of Object.entries(catalogs)) {
  test(`${language}: server-produced preview labels have translations`, () => {
    assert.deepEqual(
      [...labels].filter((label) => !catalog.has(label) && !invariantTerms.has(label)),
      [],
    );
  });
}
