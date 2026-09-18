import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";
import ts from "typescript";
const exports = {};
vm.runInNewContext(
  ts.transpileModule(
    readFileSync(new URL("../src/unified/analytics/catalog.ts", import.meta.url), "utf8"),
    { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } },
  ).outputText,
  { exports },
);
const nodes = [
  {
    key: "supplier_invoice",
    label: "Lieferantenrechnung",
    category: "Einkauf",
    aliases: ["Eingangsrechnung"],
    properties: [{ key: "number", label: "Nummer" }],
  },
  { key: "customer_credit_note", label: "Kundengutschrift", category: "Verkauf", properties: [] },
  {
    key: "supplier_credit_note",
    label: "Lieferantengutschrift",
    category: "Einkauf",
    properties: [],
  },
];
test("catalog groups preserve objects and search finds both credit kinds", () => {
  const groups = exports.catalogGroups(nodes, " GUTSCHRIFT ");
  assert.deepEqual(
    JSON.parse(JSON.stringify(groups.map(([name, items]) => [name, items.map((x) => x.key)]))),
    [
      ["Verkauf", ["customer_credit_note"]],
      ["Einkauf", ["supplier_credit_note"]],
    ],
  );
});
test("catalog search includes model synonyms, category and field labels", () => {
  assert.equal(exports.catalogGroups(nodes, "Eingangsrechnung")[0][1][0].key, "supplier_invoice");
  assert.equal(exports.catalogGroups(nodes, "Nummer")[0][1][0].key, "supplier_invoice");
  assert.equal(exports.catalogGroups(nodes, "Einkauf")[0][1].length, 2);
  assert.equal(exports.catalogGroups(nodes, "missing").length, 0);
});
