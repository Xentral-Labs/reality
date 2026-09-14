import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
const root = new URL("../", import.meta.url);
const read = (p) => fs.readFileSync(new URL(p, root), "utf8");
const catalog = JSON.parse(read(".vitepress/data/tool-usage.json"));
test("data model covers core records with bilingual meanings and valid actions", () => {
  assert.deepEqual(
    catalog.dataModels.slice(0, 9).map((m) => m.key),
    [
      "source_record",
      "document",
      "document_line",
      "commitment",
      "commitment_revision",
      "reservation",
      "movement",
      "ledger_entry",
      "fact",
    ],
  );
  for (const m of catalog.dataModels) {
    for (const lang of ["en", "de"]) {
      assert.ok(m.purpose[lang]);
      assert.ok(m.note[lang]);
      assert.ok(m.derived[lang]);
    }
    assert.ok(Object.keys(m.example).length);
    for (const action of m.actions) assert.ok(catalog.entries.some((e) => e.id === action));
    assert.ok(m.fields.every((f) => f.meaning.en && f.meaning.de));
  }
});
test("model preserves semantic boundaries and exact authority links", () => {
  const get = (key) => catalog.dataModels.find((m) => m.key === key);
  assert.match(get("commitment").derived.en, /revision/i);
  assert.match(get("commitment_revision").note.en, /revise_commitment/);
  assert.match(get("fact").note.en, /supported/i);
  assert.match(get("source_record").note.en, /unused/i);
  assert.ok(!get("reservation").fields.some((f) => f.name === "document_id"));
});
test("model entry is linked in both handbooks and supports readable navigation", () => {
  for (const prefix of ["", "de/"])
    assert.match(
      read(`content/${prefix}concepts/business-reality-guide.md`),
      /tool-usage\/#model:commitment/,
    );
  const parent = read(".vitepress/theme/components/ToolUsage.vue");
  assert.match(parent, /DataModelExplorer/);
  assert.match(parent, /model:/);
  const component = read(".vitepress/theme/components/DataModelExplorer.vue");
  assert.match(component, /overflow-wrap: anywhere/);
  assert.doesNotMatch(component, /text-overflow:\s*ellipsis/);
});

test("Fact example preserves the actual text value and composite account scope is explained", () => {
  const fact = catalog.dataModels.find((m) => m.key === "fact");
  assert.equal(fact.example.value, "Side entrance");
  assert.doesNotMatch(fact.fields.find((f) => f.name === "value").meaning.en, /JSON/);
  const ledger = catalog.dataModels.find((m) => m.key === "ledger_entry");
  assert.match(ledger.fields.find((f) => f.name === "tenant_id").meaning.en, /composite/);
});

test("ERP reference covers master data, pricing, shipping and finance with valid groups", () => {
  assert.equal(catalog.dataModels.length, 35);
  for (const key of [
    "party",
    "item",
    "shipment",
    "shipment_package",
    "payment_term",
    "price_list_entry",
    "settlement_allocation",
    "subledger_account",
  ])
    assert.ok(
      catalog.dataModels.some((m) => m.key === key),
      key,
    );
  for (const m of catalog.dataModels) {
    assert.ok(m.group);
    assert.ok(m.groupLabel.en && m.groupLabel.de);
    for (const key of m.related)
      assert.ok(
        catalog.dataModels.some((r) => r.key === key),
        key,
      );
  }
  assert.match(catalog.dataModels.find((m) => m.key === "shipment").derived.en, /Movement/);
  assert.match(catalog.dataModels.find((m) => m.key === "item").derived.en, /stock/i);
});

test("stored fields use a semantic table with visible metadata and local scrolling", () => {
  const component = read(".vitepress/theme/components/DataModelExplorer.vue");
  assert.match(component, /<table class="model-fields-table">/);
  assert.match(component, /scope="col"/);
  assert.match(component, /scope="row"/);
  assert.match(component, /tabindex="0"/);
  assert.doesNotMatch(
    component.split('<table class="model-fields-table">')[1].split("</table>")[0],
    /<details>/,
  );
});

test("all explorer tabs share visual primitives and a consistent header", () => {
  const parent = read(".vitepress/theme/components/ToolUsage.vue");
  const model = read(".vitepress/theme/components/DataModelExplorer.vue");
  for (const text of [parent, model]) {
    assert.match(text, /explorer-card/);
    assert.match(text, /explorer-filter/);
    assert.match(text, /explorer-panel/);
  }
  assert.match(parent, /explorer-intro/);
  assert.match(model, /model-guidance/);
  assert.match(read(".vitepress/theme/index.ts"), /tool-usage.css/);
});
