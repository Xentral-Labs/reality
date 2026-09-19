import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
const read = (p) => fs.readFileSync(new URL(`../${p}`, import.meta.url), "utf8");
const model = JSON.parse(read(".vitepress/data/tool-usage.json")).analyticsModel;
test("analytics documentation includes all graph categories, templates and semantic rules", () => {
  for (const language of ["en", "de"]) {
    const catalog = model[language];
    const keys = new Set(catalog.nodes.map((n) => n.key));
    assert.ok(keys.has("order") && keys.has("item"));
    assert.ok(catalog.templates.length > 0);
    for (const node of catalog.nodes) {
      assert.ok(node.label && node.grain && node.definition);
      for (const edge of node.edges) assert.ok(keys.has(edge.to));
      for (const edge of node.edges_in) assert.ok(keys.has(edge.from));
      for (const property of node.properties) assert.ok(!("values" in property));
    }
    const amount = catalog.nodes
      .find((n) => n.key === "order")
      .measures.find((m) => m.key === "stated_order_amount");
    assert.ok(amount.never_across.includes("currency"));
    assert.equal(catalog.limits.max_path_length, 8);
  }
  assert.deepEqual(
    model.en.nodes.map((n) => n.key),
    model.de.nodes.map((n) => n.key),
  );
});
test("analytics explorer is a sibling tab with stable links and both guide entries", () => {
  const parent = read(".vitepress/theme/components/ToolUsage.vue");
  assert.match(parent, /'model', 'analytics', 'technical'/);
  assert.match(parent, /analytics:/);
  assert.match(parent, /AnalyticsModelExplorer/);
  for (const prefix of ["", "de/"])
    assert.match(read(`content/${prefix}analytics/index.md`), /tool-usage\/#analytics:/);
  const component = read(".vitepress/theme/components/AnalyticsModelExplorer.vue");
  assert.match(component, /overflow-wrap: anywhere/);
  assert.match(component, /edges_in/);
  assert.match(component, /never_across/);
  assert.doesNotMatch(component, /fetch\(|v-html/);
});

test("explorer uses English names while preserving localized explanatory text", () => {
  const parent = read(".vitepress/theme/components/ToolUsage.vue");
  assert.match(parent, /const name = .*e\?\.label/u);
  assert.match(parent, /canonical\(r.label\)/u);
  assert.match(parent, /loc\(r.subtitle\)/u);
  assert.match(parent, /canonical\(step.title\)/u);
  assert.match(parent, /e.label_de \|\|/u);
  const data = read(".vitepress/theme/components/DataModelExplorer.vue");
  assert.match(data, /return e \? e.label : id/u);
  assert.match(data, /loc\(selected.purpose\)/u);
  for (let i = 0; i < model.en.nodes.length; i++) {
    assert.equal(model.en.nodes[i].label, model.de.nodes[i].label);
    assert.equal(model.en.nodes[i].category, model.de.nodes[i].category);
  }
});
