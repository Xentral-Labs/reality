import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { parse, compileScript } from "@vue/compiler-sfc";
import { transform } from "esbuild";
import { createSSRApp, h } from "vue";
import { renderToString } from "vue/server-renderer";
const raw = fs.readFileSync(
  new URL("../.vitepress/theme/components/LiveBusinessBlueprint.vue", import.meta.url),
  "utf8",
);
const dataUrl = (code) => "data:text/javascript;base64," + Buffer.from(code).toString("base64");
async function compileVue(source) {
  const { descriptor } = parse(source);
  const compiled = compileScript(descriptor, { id: "business-logic-test", inlineTemplate: true });
  const { code } = await transform(compiled.content, { loader: "ts", format: "esm" });
  return dataUrl(
    code.replace(/from ["']vue["']/gu, `from ${JSON.stringify(import.meta.resolve("vue"))}`),
  );
}
async function component(initial = null, language = "en", section = initial ? "rules" : "") {
  const shared = fs.readFileSync(
    new URL("../../shared/businessBlueprint.ts", import.meta.url),
    "utf8",
  );
  const { code } = await transform(shared, { loader: "ts", format: "esm" });
  const sharedUrl = dataUrl(code);
  const rewriteShared = (source) =>
    source.replace(
      /from ["'][^"']*shared\/businessBlueprint["']/gu,
      `from ${JSON.stringify(sharedUrl)}`,
    );
  const child = await compileVue(
    rewriteShared(
      fs.readFileSync(
        new URL("../.vitepress/theme/components/SourceEvidence.vue", import.meta.url),
        "utf8",
      ),
    ),
  );
  let source = rewriteShared(raw)
    .replace('const activeTab = ref("");', `const activeTab = ref(${JSON.stringify(section)});`)
    .replace(
      'import { useData } from "vitepress";',
      `const useData = () => ({ theme: ref({businessLogicUrl:'https://running.example'}),lang:ref(${JSON.stringify(language)}) });`,
    )
    .replace('from "./SourceEvidence.vue"', `from ${JSON.stringify(child)}`)
    .replace(
      'const selectedTest = ref("");',
      `const selectedTest = ref(${JSON.stringify(initial?.scenarios?.[0]?.id || "")});`,
    )
    .replace(
      "ref<BusinessBlueprint | null>(null)",
      `ref<BusinessBlueprint | null>(${JSON.stringify(initial).replaceAll("<", "\\u003c")})`,
    );
  return (await import(await compileVue(source))).default;
}

test("docs read configured live target on demand with no tenant credentials or build-time answer", async () => {
  const html = await renderToString(
    createSSRApp(await component(), { kind: "tool", entryKey: "credit_exposure" }),
  );
  assert.ok(!html.includes("https://running.example"));
  assert.ok(!html.includes("Reads business logic from the currently running system."));
  assert.ok(!html.includes("How does this function work?"));
  for (const label of ["Steps &amp; rules", "Source code", "Test cases", "Technical details"])
    assert.ok(html.includes(label));
  assert.ok(!html.includes("Explain steps and rules →"));
  assert.ok(!html.includes("View code →"));
  assert.ok(!html.includes("Detailed explanation and test cases"));
  assert.ok(raw.includes('cache: "no-store"'));
  assert.ok(raw.includes('credentials: "omit"'));
  assert.ok(!raw.includes("v-html"));
});
test("source text is escaped and missing test execution remains explicit", async () => {
  const data = {
    release: { version: "current", commit: "abc" },
    purpose: "<script>alert(1)</script>",
    status: "partial",
    nodes: [],
    edges: [],
    sources: [],
    inputs: [],
    prerequisites: [],
    limitations: ["Unknown dependency"],
    test_gaps: ["guard"],
    scenarios: [
      {
        id: "test",
        name: "limit boundary",
        relationship: "candidate",
        run: { outcome: "unknown", revision_match: false },
        setup: [],
        action: [],
        expectations: ["exposure > limit"],
        assumptions: ["Unknown fixture"],
        code: "<img onerror=alert(1)>",
        helpers: [],
      },
    ],
  };
  const html = await renderToString(
    createSSRApp(await component(data), { kind: "tool", entryKey: "credit_exposure" }),
  );
  assert.ok(html.includes("&lt;script&gt;"));
  assert.ok(!html.includes("<script>alert"));
  assert.ok(html.includes("unknown"));
  assert.ok(html.includes("Unverified for this release"));
  assert.ok(html.includes("Unproven branches"));
});

test("business reading view uses live server interpretation and collapses technical evidence", async () => {
  const data = {
    release: { version: "dev", commit: "abc" },
    purpose: "Internal description",
    status: "partial",
    nodes: [],
    edges: [],
    sources: [],
    inputs: [],
    prerequisites: [],
    limitations: [],
    test_gaps: [],
    scenarios: [],
    business: {
      language: "de",
      mode: "llm",
      heading: "Fachliche Erklärung",
      notice: "KI-Interpretation aus Live-Code",
      steps: [
        {
          id: "rule",
          function: "unknown",
          kind: "calculation",
          text: "Neuer Betrag = Menge × aktueller Preis.",
          rule_ids: ["rule"],
          evidence_ids: [],
          line: 1,
        },
      ],
      edges: [],
      scenarios: [],
      unexplained_rules: 0,
    },
  };
  const html = await renderToString(
    createSSRApp(await component(data, "de"), { kind: "command", entryKey: "future_operation" }),
  );
  assert.ok(html.includes("Neuer Betrag = Menge × aktueller Preis."));
  assert.ok(html.includes("Ablauf &amp; Regeln"));
  assert.ok(html.includes("Aktualisieren"));
  assert.ok(!html.includes("Wie funktioniert diese Funktion?"));
  assert.ok(html.includes("KI-Interpretation"));
  assert.ok(html.includes("data-business-reading-view"));
  assert.ok(html.includes('role="tablist"'));
  assert.ok(html.includes('role="tabpanel"'));
});

test("primary steps retain multiline conditions without a duplicate business diagram", async () => {
  const sentence =
    "WENN die belegte Bedingung gilt:\nDANN gilt die belegte Folge.\nSONST gilt ausschließlich die belegte Alternative.";
  const data = {
    release: { version: "dev", commit: "abc" },
    purpose: "",
    status: "partial",
    nodes: [],
    edges: [],
    sources: [],
    inputs: [],
    prerequisites: [],
    limitations: [],
    test_gaps: [],
    scenarios: [],
    business: {
      heading: "Business explanation",
      notice: "Interpretation",
      steps: [
        {
          id: "one",
          function: "future",
          kind: "decision",
          text: sentence,
          evidence_ids: [],
          line: 1,
        },
        {
          id: "two",
          function: "future",
          kind: "effect",
          text: "Apply the effect",
          evidence_ids: [],
          line: 2,
        },
      ],
      edges: [{ source: "one", target: "two", outcome: "true" }],
      scenarios: [],
    },
  };
  const html = await renderToString(
    createSSRApp(await component(data), { kind: "command", entryKey: "future" }),
  );
  assert.ok(!html.includes("data-business-flow"));
  assert.ok(html.includes(sentence));
  assert.ok(html.includes("rule-cards"));
  assert.ok(html.includes("white-space:pre-line"));
  assert.ok(!html.includes('width="760"'));
});

test("shared flow groups original paths without adding connections between independent steps", async () => {
  const source = fs.readFileSync(
    new URL("../../shared/businessBlueprint.ts", import.meta.url),
    "utf8",
  );
  const { code } = await transform(source, { loader: "ts", format: "esm" });
  const { flowCards } = await import(
    "data:text/javascript;base64," + Buffer.from(code).toString("base64")
  );
  const cards = flowCards(
    [{ id: "a" }, { id: "b" }, { id: "independent" }],
    [
      { source: "a", target: "b", outcome: "yes / next" },
      { source: "a", target: "b", outcome: "no / next" },
      { source: "a", target: "absent", outcome: "unknown" },
    ],
  );
  assert.equal(cards[0].next.length, 1);
  assert.equal(cards[0].next[0].target, 2);
  assert.deepEqual(cards[0].next[0].outcomes, ["yes / next", "no / next"]);
  assert.equal(cards[0].next[0].outcome, "");
  assert.deepEqual(cards[1].next, []);
  assert.deepEqual(cards[2].next, []);
});

test("source excerpt focuses verified rule lines and never marks unrelated helper", async () => {
  const source = fs.readFileSync(
    new URL("../../shared/businessBlueprint.ts", import.meta.url),
    "utf8",
  );
  const { code } = await transform(source, { loader: "ts", format: "esm" });
  const { sourceRanges, sourceExcerpt } = await import(
    "data:text/javascript;base64," + Buffer.from(code).toString("base64")
  );
  const evidence = {
    id: "s",
    function: "current",
    start_line: 100,
    code: Array.from({ length: 80 }, (_, i) => `line ${i + 100}`).join("\n"),
  };
  const nodes = [
    {
      id: "r",
      evidence_id: "s",
      function: "current",
      kind: "calculation",
      line: 150,
      end_line: 152,
    },
  ];
  const ranges = sourceRanges(evidence, nodes, ["r"], 150);
  const view = sourceExcerpt(evidence, ranges);
  assert.deepEqual(
    view.lines.filter((line) => line.highlighted).map((line) => line.number),
    [150, 151, 152],
  );
  assert.equal(view.lines[0].number, 147);
  assert.equal(view.lines.at(-1).number, 155);
  assert.equal(
    sourceExcerpt(evidence, ranges, true)
      .lines.map((line) => line.text)
      .join("\n"),
    evidence.code,
  );
  assert.deepEqual(
    sourceRanges({ ...evidence, id: "other", function: "helper" }, nodes, ["r"], 150),
    [],
  );
  assert.equal(sourceExcerpt(evidence, []).focusAvailable, false);
  assert.equal(sourceExcerpt(evidence, [{ start: 999, end: 1000 }]).focusAvailable, false);
});

test("source tab opens main function without a selector and keeps helper code collapsed", async () => {
  const data = {
    release: { version: "current", commit: "abc" },
    purpose: "Change a commitment",
    status: "partial",
    nodes: [],
    edges: [],
    inputs: [],
    prerequisites: [],
    limitations: [],
    test_gaps: [],
    scenarios: [],
    sources: [
      {
        id: "main",
        function: "revise_commitment",
        path: "core.py",
        start_line: 10,
        code: "main_code()\nvalue = '<img src=x onerror=alert(1)>'",
      },
      {
        id: "helper",
        function: "positive",
        path: "core.py",
        start_line: 20,
        code: "helper_code()",
      },
    ],
  };
  for (const locale of ["en", "de"]) {
    const html = await renderToString(
      createSSRApp(await component(data, locale), {
        kind: "command",
        entryKey: "revise_commitment",
      }),
    );
    assert.ok(!html.includes("<select"));
    assert.match(html, /<pre data-direct-source>/u);
    assert.match(html, /direct-line-number[^>]*[^]*?>10<\/span>/u);
    assert.ok(html.includes("main_code()"));
    assert.ok(!html.includes("<img"), "Source tokens must remain escaped text");
    assert.ok(html.includes("&lt;img"));
    assert.match(html, /<details class="called-functions" data-called-functions>/u);
    assert.ok(
      html.includes(locale === "de" ? "Weitere Quelltext-Funktionen" : "Related source functions"),
    );
    assert.ok(html.includes("helper_code()"));
    assert.ok(!html.includes("Refresh code"));
    const projectionData = {
      ...data,
      sources: [
        { ...data.sources[0], role: "reader" },
        { ...data.sources[1], role: "builder", called_by: [data.sources[0].function] },
      ],
    };
    const projectionHtml = await renderToString(
      createSSRApp(await component(projectionData, locale), {
        kind: "projection",
        entryKey: "fulfillment_queue",
      }),
    );
    assert.ok(
      projectionHtml.indexOf("helper_code()") < projectionHtml.indexOf("main_code()"),
      "Actual registered builder opens before the shared stored reader",
    );
    assert.ok(
      projectionHtml.includes(locale === "de" ? "Aufbau bei Änderungen" : "Build after changes"),
    );
    assert.ok(projectionHtml.includes("Zur Startfunktion") === false);
    assert.ok(
      projectionHtml.includes("source-next") === false,
      "Reverse callers must not invent calls from the selected builder",
    );
  }
});

test("technical reference is contained in its section and remains available without live evidence", async () => {
  async function render(kind, section) {
    const Inspector = await component(null, "en", section);
    return renderToString(
      createSSRApp({
        render: () =>
          h(
            Inspector,
            { kind, entryKey: "example" },
            { reference: () => h("p", { "data-catalog-reference": "" }, "Catalog reference") },
          ),
      }),
    );
  }
  assert.ok(!(await render("view", "")).includes("Catalog reference"));
  assert.ok((await render("view", "technical")).includes("Catalog reference"));
  assert.ok((await render("event", "")).includes("Catalog reference"));
});

test("authored English descriptions are displayed without an AI or unavailable notice", async () => {
  const data = {
    release: { version: "dev" },
    purpose: "Current purpose",
    status: "partial",
    nodes: [],
    edges: [],
    sources: [],
    inputs: [],
    prerequisites: [],
    limitations: [],
    test_gaps: [],
    scenarios: [],
    business: {
      language: "en",
      mode: "authored",
      heading: "Steps from source",
      notice: "No AI generation",
      overview: null,
      steps: [
        {
          id: "rule",
          text: "IF the exact limit is exceeded:\n    Report a breach.",
          rule_ids: [],
          evidence_ids: [],
        },
      ],
      scenarios: [],
      annotation_gaps: ["Function description missing: helper"],
      unexplained_rules: 1,
    },
  };
  const html = await renderToString(
    createSSRApp(await component(data, "de", "rules"), { kind: "command", entryKey: "future" }),
  );
  assert.ok(html.includes("Englische Beschreibungen aus dem aktuellen Quelltext"));
  assert.ok(html.includes("IF the exact limit is exceeded:"));
  assert.ok(!html.includes("Keine gültige fachliche Beschreibung vorhanden"));
  assert.ok(html.includes("Noch aufzubereitende Beschreibungen"));
});
