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
const props = defineProps<{ testLocale: string; testModel: Model; testSelection: string; testTab: string }>();
`,
  )
  .replace(
    /import (DataModelExplorer|AnalyticsModelExplorer|LiveBusinessBlueprint) from .*;/gu,
    "const $1 = {};",
  )
  .replace("const { lang } = useData();", "const lang = computed(() => props.testLocale);")
  .replace("shallowRef<Model | null>(null)", "shallowRef<Model | null>(props.testModel)")
  .replace('const tab = ref<Tab>("resources");', "const tab = ref<Tab>(props.testTab as Tab);")
  .replace('const selectedId = ref("");', "const selectedId = ref(props.testSelection);");
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
const render = (locale, selection = "", tab = "technical") =>
  renderToString(
    createSSRApp(component, {
      testLocale: locale,
      testModel: model,
      testSelection: selection,
      testTab: tab,
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
