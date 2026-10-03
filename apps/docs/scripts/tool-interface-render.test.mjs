import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { parse, compileScript } from "@vue/compiler-sfc";
import { transform } from "esbuild";
import { createSSRApp } from "vue";
import { renderToString } from "vue/server-renderer";

const model = JSON.parse(
  fs.readFileSync(new URL("../.vitepress/data/tool-usage.json", import.meta.url), "utf8"),
);
// Supply the normally asynchronous catalog and route state for server rendering.
const source = fs
  .readFileSync(new URL("../.vitepress/theme/components/ToolUsage.vue", import.meta.url), "utf8")
  .replace(
    'import { useData } from "vitepress";',
    `
const props = defineProps<{ testLocale: string; testModel: Model; testSelection: string; testTab: string; testResource: string; testQuery: string }>();
`,
  )
  .replace(/import (DataModelExplorer|AnalyticsModelExplorer) from .*;/gu, "const $1 = {};")
  .replace(
    /import LiveBusinessBlueprint from .*;/u,
    "const LiveBusinessBlueprint = { inheritAttrs: false, setup(_props, { slots }) { return () => slots.reference?.(); } };",
  )
  .replace("const { lang } = useData();", "const lang = computed(() => props.testLocale);")
  .replace("shallowRef<Model | null>(null)", "shallowRef<Model | null>(props.testModel)")
  .replace('const tab = ref<Tab>("resources");', "const tab = ref<Tab>(props.testTab as Tab);")
  .replace('const selectedId = ref("");', "const selectedId = ref(props.testSelection);")
  .replace('const selectedResource = ref("");', "const selectedResource = ref(props.testResource);")
  .replace('const query = ref("");', "const query = ref(props.testQuery);");
const { descriptor } = parse(source);
const compiled = compileScript(descriptor, { id: "tool-interface-test", inlineTemplate: true });
const { code } = await transform(compiled.content, { loader: "ts", format: "esm" });
const linked = code.replace(
  /from ["']vue["']/gu,
  `from ${JSON.stringify(import.meta.resolve("vue"))}`,
);
const { default: component } = await import(
  `data:text/javascript;base64,${Buffer.from(linked).toString("base64")}`
);
const render = (locale, selection = "", tab = "technical", resource = "", query = "") =>
  renderToString(
    createSSRApp(component, {
      testLocale: locale,
      testModel: model,
      testSelection: selection,
      testTab: tab,
      testResource: resource,
      testQuery: query,
    }),
  );

const escaped = (text) =>
  text
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

test("both technical editions render the shared guide and real example", async () => {
  for (const locale of ["en", "de"]) {
    const html = await render(locale);
    assert.ok(html.includes("data-interface-guide"));
    for (const definition of Object.values(model.interface_guide.kinds)) {
      assert.ok(html.includes(definition.label[locale]));
      assert.ok(html.includes(escaped(definition.description[locale])));
    }
    assert.ok(html.includes(model.interface_guide.counts_note[locale]));
    for (const kind of ["action", "tool", "command"])
      assert.ok(html.includes(model.interface_guide.example[kind].split(":")[1]));
  }
});

test("mapped entry details render explicit relationships and unmapped tools retain purpose", async () => {
  for (const locale of ["en", "de"]) {
    for (const kind of ["action", "tool", "command"]) {
      const html = await render(locale, model.interface_guide.example[kind]);
      assert.ok(html.includes("data-operation-relationships"), kind);
      assert.ok(html.includes(model.interface_guide.relationships_title[locale]), kind);
    }
    const tool = model.entries.find((entry) => entry.kind === "tool" && !entry.command);
    assert.ok((await render(locale, tool.id)).includes(escaped(tool.summary)));
  }
});

test("ERP object navigation localizes names and prioritizes familiar objects without hiding others", async () => {
  const html = await render("de", "", "resources");
  assert.ok(html.includes("Geschäftsobjekte"));
  assert.ok(html.indexOf("<strong>Auftrag</strong>") < html.indexOf("<strong>Artikel</strong>"));
  assert.ok(html.includes("<strong>Geschäftspartner</strong>"));
  assert.ok(!html.includes("<strong>Business partner</strong>"));
  assert.ok(html.includes("data-explorer-start"));
  assert.ok(html.includes("Kreditobligo prüfen"));
  for (const resource of model.resources)
    assert.ok(html.includes(escaped(resource.label.de || resource.label.en)));
  const english = await render("en", "", "resources");
  assert.ok(english.includes("Business partner"));
});

test("business function details lead with localized purpose before technical identity", async () => {
  const html = await render("de", "command:reorder_points", "resources");
  assert.ok(html.includes("Meldebestände anzeigen"));
  assert.ok(
    html.includes(
      "Zeigt die hinterlegten Meldebestände und Nachbestellmengen je Artikel und Lagerort.",
    ),
  );
  assert.ok(html.indexOf('class="function-intro"') < html.indexOf('class="man-header"'));
  assert.ok(html.includes("reorder_points [item_id] [location_id]"));
});

test("business object lists keep views and projections separately discoverable", async () => {
  for (const locale of ["en", "de"]) {
    const html = await render(locale, "", "resources", "order");
    const list = html.split('class="tool-usage-detail')[0];
    assert.equal((list.match(/>fulfillment_blockers<\/code>/gu) || []).length, 3);
    for (const key of ["orders", "warehouse_queue", "fulfillment_queue", "commitment_register"])
      assert.ok(list.includes(`>${key}</code>`), key);
    assert.ok(list.includes("badge-projection"));
    assert.ok(list.includes("badge-view"));
    const overview = await render(locale, "", "resources");
    assert.match(overview, /8 (lists|Listen)/u);
    const search = await render(locale, "", "resources", "order", "fulfillment_queue");
    assert.ok(search.split('class="tool-usage-detail')[0].includes(">fulfillment_queue</code>"));
  }
});

test("view details explain backing projections while technical entries remain independently available", async () => {
  for (const locale of ["en", "de"]) {
    const view = await render(locale, "view:fulfillment_blockers", "resources", "order");
    assert.ok(view.includes("data-read-relationships"));
    assert.ok(view.includes("fulfillment_blockers"));
    const projection = await render(locale, "projection:fulfillment_blockers");
    assert.ok(projection.includes("data-read-relationships"));
    assert.ok(projection.includes("badge-view"));
    const technical = await render(locale);
    assert.ok(technical.includes("badge-projection"));
  }
});

test("technical category labels are identical in both documentation languages", async () => {
  for (const locale of ["en", "de"]) {
    const html = await render(locale);
    for (const term of ["Views", "Projections", "Commands", "Agent Tools", "Web Actions"])
      assert.ok(html.includes(term), `${locale}: ${term}`);
    const view = await render(locale, "view:fulfillment_blockers", "resources", "order");
    assert.match(view, /badge-view[^>]*>View</u);
    assert.match(view, /badge-projection[^>]*>Projection</u);
  }
});

test("business objects list every related agent tool and Web action with typed command rows", async () => {
  for (const locale of ["en", "de"]) {
    const html = await render(locale, "", "resources", "order");
    const list = html.split('class="tool-usage-detail')[0];
    for (const entry of model.entries.filter(
      (e) => ["tool", "action"].includes(e.kind) && e.resources?.includes("order"),
    ))
      assert.ok(list.includes(`>${entry.key}</code>`), `${locale}: ${entry.id}`);
    for (const label of ["Command", "Agent Tool", "Web Action"])
      assert.ok(list.includes(`>${label}</span>`), label);
    const search = await render(locale, "", "resources", "order", "reservation_propose");
    assert.ok(search.split('class="tool-usage-detail')[0].includes(">reservation_propose</code>"));
    const globalSearch = await render(locale, "", "resources", "", "reservation_propose");
    assert.ok(
      globalSearch.split('class="tool-usage-detail')[0].includes(">reservation_propose</code>"),
    );
  }
});

test("shared type guide explains five categories and both examples at the existing destinations", async () => {
  for (const locale of ["en", "de"]) {
    const html = await render(locale);
    assert.match(html, /data-interface-guide open/u);
    assert.ok(html.includes(model.interface_guide.read_example.title[locale]));
    for (const id of model.interface_guide.read_example.entries)
      assert.ok(html.includes(id.split(":")[1]));
    const resource = await render(locale, "", "resources", "order");
    assert.ok(resource.includes("data-type-guide-link"));
  }
});
