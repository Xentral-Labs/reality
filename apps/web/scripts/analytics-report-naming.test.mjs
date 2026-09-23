import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

/** A report is named before it is saved, not after it is refused.
 *
 * The field used to open empty and the backend refuses an empty name, so the
 * one moment a question becomes a report asked the reader to invent a title.
 * Everything needed to propose one was already on screen: the records being
 * read, the measures being reported and the axes they are cut by, all in the
 * reader's own language because the catalog is served translated.
 */
function load(path, shims = {}) {
  const exports = {};
  vm.runInNewContext(
    ts.transpileModule(readFileSync(new URL(path, import.meta.url), "utf8"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText,
    { exports, console, Date, Intl, require: () => shims },
  );
  return exports;
}

const nodes = {
  order: {
    key: "order",
    label: "Kundenauftrag",
    properties: [
      { key: "id", label: "ID", kind: "text", identity: true },
      { key: "currency", label: "Währung", kind: "text" },
      { key: "ordered_at", label: "Bestelldatum", kind: "time" },
    ],
    measures: [
      { key: "stated_order_amount", label: "Auftragswert" },
      { key: "order_count", label: "Anzahl" },
    ],
    edges: [],
    edges_in: [],
  },
  party: {
    key: "party",
    label: "Geschäftspartner",
    properties: [{ key: "name", label: "Name", kind: "text" }],
    measures: [],
    edges: [],
    edges_in: [],
  },
};

const plan = (changes = {}) => ({
  blocks: [{ alias: "o", node: "order", filters: [] }],
  measures: [],
  groups: [],
  limit: 200,
  ...changes,
});

const { suggestedName, sameQuestion } = load("../src/unified/analytics/reportName.ts");

test("a name says what the analysis reads, reports and is cut by", () => {
  assert.equal(
    suggestedName(
      plan({
        measures: ["stated_order_amount"],
        groups: [{ field: "o.currency", label: "Währung" }],
      }),
      nodes,
      ["Währung"],
    ),
    "Kundenauftrag · Auftragswert · Währung",
  );
});

test("an analysis with nothing but its records is named after them", () => {
  assert.equal(suggestedName(plan(), nodes), "Kundenauftrag");
});

test("a name is composed in the catalog's language, because the catalog is served translated", () => {
  const english = { ...nodes, order: { ...nodes.order, label: "Customer order" } };
  assert.equal(
    suggestedName(plan({ measures: ["order_count"] }), english),
    "Customer order · Anzahl",
  );
});

test("a measure or an axis the catalog does not declare never reaches the name", () => {
  // A stored question can outlive a declaration. A raw key in the name would be
  // the one place a reader sees the model's own vocabulary.
  assert.equal(suggestedName(plan({ measures: ["retired_measure"] }), nodes), "Kundenauftrag");
});

test("a name never exceeds what the store accepts, and is never cut mid-word", () => {
  const long = {
    order: {
      ...nodes.order,
      label: "Kundenauftrag",
      measures: [{ key: "m", label: "W".repeat(200) }],
    },
  };
  const name = suggestedName(plan({ measures: ["m"] }), long);
  assert.ok(name.length <= 120, `expected at most 120 characters, got ${name.length}`);
  assert.equal(name, "Kundenauftrag", "a part that cannot fit is left out, not sliced");
});

test("an analysis with no records at all still yields something savable", () => {
  assert.equal(suggestedName({ blocks: [], measures: [], groups: [], limit: 200 }, nodes), "");
});

test("the same part is never repeated", () => {
  // Grouping by a party's name reads back as the party itself — the caption the
  // builder already shows — which on a party-rooted analysis is the records it
  // reads. Saying it twice is not a name, it is a stutter.
  const rooted = plan({
    blocks: [{ alias: "p", node: "party", filters: [] }],
    groups: [{ field: "p.name", label: "Geschäftspartner" }],
  });
  assert.equal(suggestedName(rooted, nodes, ["Geschäftspartner"]), "Geschäftspartner");
});

/** Whether the question on screen is still the one that was saved.
 *
 * The server returns the question canonicalized, so comparing the stored text
 * against the executed text reports a change that nobody made. What is compared
 * is two canonical answers, key order and absent-versus-empty aside.
 */
test("a question equals itself regardless of key order", () => {
  assert.equal(
    sameQuestion(
      { from: "order", as: "o", measures: ["a"], limit: 200 },
      { limit: 200, measures: ["a"], as: "o", from: "order" },
    ),
    true,
  );
});

test("an empty list and an absent one are the same question", () => {
  assert.equal(sameQuestion({ from: "order", filter: [], follow: [] }, { from: "order" }), true);
});

test("a changed filter is a changed question", () => {
  assert.equal(
    sameQuestion(
      { from: "order", filter: [{ field: "o.currency", op: "eq", value: "EUR" }] },
      { from: "order", filter: [{ field: "o.currency", op: "eq", value: "CHF" }] },
    ),
    false,
  );
});

test("order within a list is part of the question", () => {
  // Two axes swapped are two different tables, so this is a real change.
  assert.equal(
    sameQuestion({ from: "order", measures: ["a", "b"] }, { from: "order", measures: ["b", "a"] }),
    false,
  );
});

test("nothing saved yet is never equal to a question", () => {
  assert.equal(sameQuestion(null, { from: "order" }), false);
  assert.equal(sameQuestion(null, null), false);
});
