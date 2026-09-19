import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { parse, compileScript } from "@vue/compiler-sfc";
import { transform } from "esbuild";
import { createSSRApp } from "vue";
import { renderToString } from "vue/server-renderer";

const source = fs.readFileSync(
  new URL("../.vitepress/theme/components/AnalyticsModelExplorer.vue", import.meta.url),
  "utf8",
);
const { descriptor } = parse(source);
const compiled = compileScript(descriptor, { id: "analytics-model-test", inlineTemplate: true });
const { code } = await transform(compiled.content, { loader: "ts", format: "esm" });
const linked = code.replace(
  /from ["']vue["']/gu,
  `from ${JSON.stringify(import.meta.resolve("vue"))}`,
);
const { default: component } = await import(
  `data:text/javascript;base64,${Buffer.from(linked).toString("base64")}`
);
const catalogs = JSON.parse(
  fs.readFileSync(new URL("../.vitepress/data/tool-usage.json", import.meta.url), "utf8"),
).analyticsModel;
const render = (locale, selectedKey = "", query = "") =>
  renderToString(
    createSSRApp(component, { catalog: catalogs[locale], selectedKey, query, locale }),
  );

test("every declared analytics detail renders in both languages", async () => {
  for (const locale of ["en", "de"]) {
    const overview = await render(locale);
    assert.ok(overview.includes(catalogs[locale].model_version));
    for (const node of catalogs[locale].nodes) {
      const html = await render(locale, node.key);
      assert.ok(html.includes(node.key), node.key);
      for (const measure of node.measures) assert.ok(html.includes(measure.key), measure.key);
      for (const edge of [...node.edges, ...node.edges_in])
        assert.ok(html.includes(`#analytics:${edge.to || edge.from}`), edge.key);
    }
  }
});
test("search and unknown selection render safe empty states", async () => {
  assert.match(await render("en", "missing", "no-such-model-value-xyz"), /No matching objects/u);
  assert.match(
    await render("de", "missing", "no-such-model-value-xyz"),
    /Keine passenden Objekte/u,
  );
  const html = await render("en", "order", "stated_order_amount");
  assert.match(html, /aria-current="true"/u);
  assert.match(html, /href="#analytics:order"/u);
});
