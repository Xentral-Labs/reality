<script setup lang="ts">
import { computed, ref, watch, onUnmounted, useId } from "vue";
import { useData } from "vitepress";
import type { HighlighterCore } from "shiki/core";
import {
  diagram,
  sourceRanges,
  type BusinessBlueprint,
  type LogicSource,
} from "../../../../shared/businessBlueprint";
import SourceEvidence from "./SourceEvidence.vue";
const props = defineProps<{ kind: string; entryKey: string }>();
const { theme, lang } = useData();
const target = computed(() => String(theme.value.businessLogicUrl || ""));
const data = ref<BusinessBlueprint | null>(null);
const loading = ref(false);
const elapsed = ref(0);
const flowId = useId();
const activeTab = ref("");
const selectedTest = ref("");
const tabs = ["rules", "code", "tests", "technical"];
const cache = ref<{
  source?: BusinessBlueprint;
  rules?: BusinessBlueprint;
  full?: BusinessBlueprint;
}>({});
let controller: AbortController | undefined;
function selectTab(tab: string) {
  activeTab.value = tab;
  const cached =
    tab === "tests"
      ? cache.value.full
      : tab === "rules"
        ? cache.value.full || cache.value.rules
        : cache.value.full || cache.value.rules || cache.value.source;
  if (cached) {
    controller?.abort();
    sequence++;
    loading.value = false;
    error.value = "";
    data.value = cached;
  } else read(tab);
}
const codeSelection = ref("");
const codeSource = computed(
  () =>
    data.value?.sources.find((source) => source.id === codeSelection.value) ||
    data.value?.sources.find((source) => source.role === "builder") ||
    data.value?.sources[0],
);
const relatedSources = computed(
  () => data.value?.sources.filter((source) => source.id !== codeSource.value?.id) || [],
);
const directHelpers = computed(
  () =>
    data.value?.sources.filter((source) =>
      source.called_by?.includes(codeSource.value?.function || ""),
    ) || [],
);
type SourceToken = { content: string; htmlStyle?: Record<string, string> };
const coloredSources = ref<Record<string, SourceToken[][]>>({});
let highlighterPromise: Promise<HighlighterCore> | undefined;
let highlightEpoch = 0;
async function colorSource(source: LogicSource) {
  if (typeof window === "undefined" || coloredSources.value[source.id]) return;
  const epoch = highlightEpoch;
  try {
    highlighterPromise ||= Promise.all([
      import("shiki/core"),
      import("shiki/engine/javascript"),
      import("@shikijs/langs/python"),
      import("@shikijs/themes/github-light"),
      import("@shikijs/themes/github-dark"),
    ]).then(([core, engine, python, light, dark]) =>
      core.createHighlighterCore({
        langs: [python.default],
        themes: [light.default, dark.default],
        engine: engine.createJavaScriptRegexEngine(),
      }),
    );
    const highlighter = await highlighterPromise;
    if (epoch !== highlightEpoch) return;
    const tokens = highlighter.codeToTokens(source.code, {
      lang: "python",
      themes: { light: "github-light", dark: "github-dark" },
    }).tokens;
    coloredSources.value = { ...coloredSources.value, [source.id]: tokens };
  } catch {
    // Plain escaped source remains immediately readable if highlighting is unavailable.
    highlighterPromise = undefined;
  }
}
function helperToggle(event: Event, source: LogicSource) {
  if ((event.currentTarget as HTMLDetailsElement).open) colorSource(source);
}
const sourceLines = (source: LogicSource) =>
  source.code
    .replace(/\n$/u, "")
    .split("\n")
    .map((text, index) => ({
      number: source.start_line + index,
      text,
      tokens: coloredSources.value[source.id]?.[index] || [{ content: text || " " }],
    }));
function sourceRole(source: LogicSource) {
  if (source.role === "builder") return wording("Build after changes", "Aufbau bei Änderungen");
  if (source.role === "reader")
    return wording("Read stored results", "Gespeicherte Ergebnisse lesen");
  if (source.role === "shared")
    return wording("Shared full derivation", "Gemeinsame vollständige Berechnung");
  return wording("Source function", "Quelltext-Funktion");
}
function tabKey(event: KeyboardEvent, index: number) {
  let next = index;
  if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
  else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = tabs.length - 1;
  else return;
  event.preventDefault();
  selectTab(tabs[next]);
  (event.currentTarget as HTMLElement).parentElement
    ?.querySelectorAll<HTMLButtonElement>("[role=tab]")
    [next]?.focus();
}
let timer: ReturnType<typeof setInterval> | undefined;
function stopTimer() {
  clearInterval(timer);
  timer = undefined;
}
watch(loading, (busy) => {
  stopTimer();
  if (busy) {
    const started = Date.now();
    elapsed.value = 0;
    timer = setInterval(() => {
      elapsed.value = Math.floor((Date.now() - started) / 1000);
    }, 1000);
  }
});
onUnmounted(() => {
  controller?.abort();
  sequence++;
  stopTimer();
});
const error = ref("");
const selected = ref("");
const de = computed(() => lang.value.startsWith("de"));
const wording = (en: string, german: string) => (de.value ? german : en);
const nodes = computed(() => data.value?.nodes.filter((n) => n.function === selected.value) || []);
const layout = computed(() => diagram(nodes.value, data.value?.edges || []));
const businessNodes = computed(() =>
  (data.value?.business?.steps || []).map((n) => ({
    ...n,
    expression: "",
    evidence_id: n.evidence_ids[0],
    context: [],
  })),
);
let sequence = 0;
watch(data, () => {
  highlightEpoch++;
  coloredSources.value = {};
});
watch([activeTab, codeSource], ([tab, source]) => {
  if (tab === "code" && source) colorSource(source);
});
watch(
  () => [props.kind, props.entryKey],
  () => {
    sequence++;
    data.value = null;
    activeTab.value = "";
    cache.value = {};
    controller?.abort();
    selectedTest.value = "";
    error.value = "";
    loading.value = false;
  },
);
async function read(tab = activeTab.value, refresh = false) {
  if (!tab) return;
  const brief = tab === "rules";
  const interpret = tab === "rules" || tab === "tests";
  activeTab.value = tab;
  controller?.abort();
  controller = new AbortController();
  if (refresh) cache.value = {};
  const request = ++sequence;
  const previousTest = selectedTest.value;
  data.value = null;
  loading.value = true;
  error.value = "";
  let failure = wording(
    "Cannot reach the configured system. Check that it is running and retry.",
    "Das konfigurierte System ist nicht erreichbar. Prüfe, ob es läuft, und versuche es erneut.",
  );
  try {
    if (!target.value) throw new Error("No configured target");
    const response = await fetch(
      `${target.value}/api/business-logic/entries/${encodeURIComponent(props.kind)}/${encodeURIComponent(props.entryKey)}?language=${de.value ? "de" : "en"}&brief=${brief}&interpret=${interpret}`,
      { cache: "no-store", credentials: "omit", signal: controller.signal },
    );
    if (!response.ok) {
      failure =
        response.status === 429
          ? wording(
              "The live source service is busy. Wait briefly and retry.",
              "Die Live-Quelltextabfrage ist ausgelastet. Warte kurz und versuche es erneut.",
            )
          : wording(
              `Source could not be loaded (HTTP ${response.status}). Retry or inspect the service.`,
              `Der Quelltext konnte nicht geladen werden (HTTP ${response.status}). Erneut versuchen oder den Dienst prüfen.`,
            );
      throw new Error("Unavailable");
    }
    failure = wording(
      "The system returned an unreadable source response. Retry or inspect the service.",
      "Das System hat eine nicht lesbare Quelltextantwort geliefert. Erneut versuchen oder den Dienst prüfen.",
    );
    const result = (await response.json()) as BusinessBlueprint;
    if (request !== sequence) return;
    if (
      Object.values(cache.value).some(
        (item) => item && item.evidence_digest !== result.evidence_digest,
      )
    )
      cache.value = {};
    cache.value = { ...cache.value, [interpret ? (brief ? "rules" : "full") : "source"]: result };
    data.value = result;
    activeTab.value = tab;
    codeSelection.value = "";
    selectedTest.value = result.scenarios.some((test) => test.id === previousTest)
      ? previousTest
      : result.scenarios[0]?.id || "";
    selected.value =
      result.nodes.find((n) => n.durable)?.function || result.nodes[0]?.function || "";
  } catch {
    if (request === sequence) error.value = failure;
  } finally {
    if (request === sequence) loading.value = false;
  }
}
</script>
<template>
  <section
    v-if="['command', 'tool', 'view', 'projection', 'action', 'exception'].includes(kind)"
    :class="['live-blueprint', { 'live-blueprint-loaded': data }]"
    data-live-blueprint
  >
    <div
      class="reading-tabs"
      role="tablist"
      :aria-label="wording('Explore business logic', 'Geschäftslogik erkunden')"
    >
      <button
        v-for="(tab, index) in tabs"
        :id="`${flowId}-tab-${tab}`"
        :key="tab"
        type="button"
        role="tab"
        :aria-selected="activeTab === tab"
        :aria-controls="`${flowId}-panel-${tab}`"
        :tabindex="activeTab === tab || (!activeTab && index === 0) ? 0 : -1"
        @click="selectTab(tab)"
        @keydown="tabKey($event, index)"
      >
        {{
          tab === "code"
            ? wording("Source code", "Quelltext")
            : tab === "rules"
              ? wording("Steps & rules", "Ablauf & Regeln")
              : tab === "tests"
                ? wording("Test cases", "Testfälle")
                : wording("Technical details", "Technische Details")
        }}<span v-if="tab === 'tests' && data"> ({{ data.scenarios.length }})</span>
      </button>
    </div>
    <div v-if="activeTab" class="section-tools">
      <button v-if="!error" type="button" :disabled="loading" @click="read(activeTab, true)">
        {{ wording("Refresh", "Aktualisieren") }}
      </button>
      <button v-else type="button" @click="read(activeTab, true)">
        {{ wording("Retry", "Erneut versuchen") }}
      </button>
    </div>
    <p v-if="!activeTab" class="section-hint">
      {{
        wording(
          "Choose a section to inspect this function.",
          "Wähle einen Bereich, um diese Funktion zu verstehen.",
        )
      }}
    </p>
    <div v-if="loading" class="loading-panel" role="status" aria-live="polite">
      <span class="loading-spinner" aria-hidden="true"></span>
      <div>
        <strong>{{
          wording(
            "Reading current source and tests…",
            "Aktueller Quellcode und Tests werden gelesen…",
          )
        }}</strong>
        <p v-if="activeTab === 'rules' || activeTab === 'tests'">
          {{
            wording(
              "Reading English descriptions directly from current source. No AI generation.",
              "Englische Beschreibungen werden direkt aus dem aktuellen Quelltext gelesen. Ohne KI-Generierung.",
            )
          }}
        </p>
        <small aria-live="off"
          >{{ elapsed }} {{ wording("seconds elapsed", "Sekunden vergangen") }}</small
        >
        <p v-if="elapsed >= 60">
          {{
            wording(
              "Still waiting for the live response. No result is available yet.",
              "Die Live-Antwort steht noch aus. Es liegt noch kein Ergebnis vor.",
            )
          }}
        </p>
      </div>
    </div>
    <p v-if="error" role="alert">{{ error }}</p>
    <div
      v-if="activeTab === 'technical' && !data"
      role="tabpanel"
      :id="`${flowId}-panel-technical`"
      :aria-labelledby="`${flowId}-tab-technical`"
    >
      <slot name="reference" />
    </div>
    <template v-if="data">
      <section
        v-show="activeTab === 'code'"
        role="tabpanel"
        :id="`${flowId}-panel-code`"
        :aria-labelledby="`${flowId}-tab-code`"
        class="code-panel"
      >
        <p v-if="kind === 'exception'">
          {{
            wording(
              "This exception uses a shared evaluator. The source is not isolated to this one exception class.",
              "Dieser Klärfall nutzt eine gemeinsame Auswertung. Der Quelltext ist nicht auf diesen einen Klärfall beschränkt.",
            )
          }}
        </p>
        <p v-if="data.sources.some((source) => source.role === 'reader')" class="source-scope">
          {{
            wording(
              "This projection reads stored results. The change builder below can use the shared full derivation as a fallback; shared functions contain branches for other projections too.",
              "Diese Projection liest gespeicherte Ergebnisse. Der Aufbau bei Änderungen kann auf die gemeinsame vollständige Berechnung zurückgreifen. Gemeinsame Funktionen enthalten auch Zweige anderer Projections.",
            )
          }}
        </p>
        <template v-if="codeSource"
          ><button v-if="codeSelection" type="button" @click="codeSelection = ''">
            {{ wording("Back to entry function", "Zur Startfunktion") }}
          </button>
          <h3>{{ sourceRole(codeSource) }}</h3>
          <p>
            <code>{{ codeSource.function }}</code>
          </p>
          <p class="source-provenance">
            {{ codeSource.path }} · {{ wording("from line", "ab Zeile") }}
            {{ codeSource.start_line }}
          </p>
          <pre
            data-direct-source
          ><code><span v-for="line in sourceLines(codeSource)" :key="line.number" class="direct-source-line"><span class="direct-line-number" aria-hidden="true">{{ line.number }}</span><span><span v-for="(token, index) in line.tokens" :key="index" class="source-token" :style="token.htmlStyle">{{ token.content }}</span></span></span></code></pre>
          <div v-if="directHelpers.length" class="source-next">
            <p>{{ wording("Continue into the called code", "Weiter im aufgerufenen Code") }}</p>
            <button
              v-for="helper in directHelpers"
              :key="helper.id"
              type="button"
              @click="codeSelection = helper.id"
            >
              {{ helper.function.split(".").at(-1) }} →
            </button>
          </div>
          <details v-if="relatedSources.length" class="called-functions" data-called-functions>
            <summary>
              {{ wording("Related source functions", "Weitere Quelltext-Funktionen") }}
            </summary>
            <details
              v-for="source in relatedSources"
              :key="source.id"
              @toggle="helperToggle($event, source)"
            >
              <summary>
                {{ sourceRole(source) }} · <code>{{ source.function }}</code>
              </summary>
              <p class="source-provenance">
                {{ source.path }} · {{ wording("from line", "ab Zeile") }} {{ source.start_line }}
              </p>
              <pre><code><span v-for="line in sourceLines(source)" :key="line.number" class="direct-source-line"><span class="direct-line-number" aria-hidden="true">{{ line.number }}</span><span><span v-for="(token, index) in line.tokens" :key="index" class="source-token" :style="token.htmlStyle">{{ token.content }}</span></span></span></code></pre>
            </details>
          </details>
        </template>
        <p v-else>
          {{
            wording(
              "Verified source is unavailable for this entry.",
              "Für diesen Eintrag ist kein verifizierter Quelltext verfügbar.",
            )
          }}
        </p>
      </section>
      <div
        v-show="activeTab === 'rules'"
        :id="`${flowId}-panel-rules`"
        role="tabpanel"
        :aria-labelledby="`${flowId}-tab-rules`"
        data-business-reading-view
      >
        <div v-if="data.business?.overview">
          <p>
            <strong>{{ data.business.overview.text }}</strong>
          </p>
          <details>
            <summary class="source-action">
              {{ wording("Show referenced source", "Markierte Quellstelle anzeigen") }}
            </summary>
            <template
              v-for="source in data.sources.filter((e) =>
                data?.business?.overview?.evidence_ids.includes(e.id),
              )"
              :key="source.id"
            >
              <SourceEvidence :source="source" :ranges="[]" :language="de ? 'de' : 'en'" />
            </template>
          </details>
        </div>
        <h4>
          {{ data.business?.heading || wording("Business explanation", "Fachliche Erklärung") }}
        </h4>
        <p>
          {{
            data.business?.mode === "authored"
              ? wording(
                  "English descriptions from current source. No AI generation; descriptions require code review.",
                  "Englische Beschreibungen aus dem aktuellen Quelltext. Ohne KI-Generierung; Beschreibungen gehören zur Code-Review.",
                )
              : data.business?.mode === "llm"
                ? wording(
                    "Selected steps explained from current code; interpretation requires review.",
                    "Ausgewählte Schritte aus aktuellem Code erklärt; die Interpretation muss geprüft werden.",
                  )
                : wording(
                    "No valid business description is present. Original source remains available in Source code.",
                    "Keine gültige fachliche Beschreibung vorhanden. Der Originalcode steht unter Quelltext.",
                  )
          }}
        </p>
        <ol class="rule-cards" :aria-label="wording('Business steps', 'Geschäftliche Schritte')">
          <li v-for="step in businessNodes" :key="step.id">
            <p style="white-space: pre-line">{{ step.text }}</p>
            <details>
              <summary class="source-action">
                {{ wording("Show referenced source", "Markierte Quellstelle anzeigen") }}
              </summary>
              <template
                v-for="source in data.sources.filter((e) => step.evidence_ids.includes(e.id))"
                :key="source.id"
              >
                <SourceEvidence
                  :source="source"
                  :ranges="sourceRanges(source, data.nodes, step.rule_ids, step.line)"
                  :language="de ? 'de' : 'en'"
                />
              </template>
            </details>
          </li>
        </ol>
      </div>
      <div
        v-show="activeTab === 'tests'"
        :id="`${flowId}-panel-tests`"
        role="tabpanel"
        :aria-labelledby="`${flowId}-tab-tests`"
      >
        <h4>
          {{ wording("Existing executable test cases", "Vorhandene ausführbare Testfälle") }} ({{
            data.scenarios.length
          }})
        </h4>
        <p v-if="!data.scenarios.length">
          {{
            wording(
              "No matching test evidence is available.",
              "Keine passenden Testnachweise verfügbar.",
            )
          }}
        </p>
        <div class="test-list" :aria-label="wording('Choose a test case', 'Testfall auswählen')">
          <button
            v-for="test in data.scenarios"
            :key="test.id"
            type="button"
            :aria-pressed="selectedTest === test.id"
            @click="selectedTest = test.id"
          >
            {{ data.business?.scenarios.find((item) => item.id === test.id)?.title || test.name }}
          </button>
        </div>
        <article
          v-for="test in data.scenarios.filter((item) => item.id === selectedTest)"
          :key="test.id"
          class="selected-test"
        >
          <h4>
            {{ data.business?.scenarios.find((item) => item.id === test.id)?.title || test.name }}
          </h4>
          <p v-if="!data.business?.scenarios.some((item) => item.id === test.id)">
            {{
              wording(
                "No authored business description is present in this test source.",
                "Dieser Test enthält noch keine fachliche Beschreibung im Quelltext.",
              )
            }}
          </p>
          <div
            v-for="item in data.business?.scenarios.filter((item) => item.id === test.id) || []"
            :key="item.id"
            data-business-test
          >
            <template
              v-for="section in [
                { label: wording('Given', 'Gegeben'), values: item.given },
                { label: wording('When', 'Wenn'), values: item.when },
                { label: wording('Then', 'Dann'), values: item.then },
              ]"
              :key="section.label"
            >
              <h5>{{ section.label }}</h5>
              <ul>
                <li v-for="value in section.values" :key="value">{{ value }}</li>
              </ul>
            </template>
            <p>{{ item.notice }}</p>
            <p v-if="item.unexplained_assertions > 0">
              {{
                wording(
                  "Additional test assertions not explained:",
                  "Weitere Testprüfungen noch nicht fachlich erklärt:",
                )
              }}
              {{ item.unexplained_assertions }}
            </p>
          </div>
          <details>
            <summary>{{ wording("Technical test evidence", "Technischer Testnachweis") }}</summary>
            <p>
              {{ test.id }} · {{ test.relationship }} · {{ test.run.outcome }} ·
              {{
                test.run.revision_match
                  ? wording("Matching release", "Passende Version")
                  : wording("Unverified for this release", "Für diese Version nicht nachgewiesen")
              }}
            </p>
            <template
              v-for="section in [
                { label: wording('Setup', 'Ausgangslage'), items: test.setup },
                { label: wording('Action', 'Aktion'), items: test.action },
                {
                  label: wording('Asserted expectations', 'Geprüfte Erwartungen'),
                  items: test.expectations,
                },
                {
                  label: wording('Unknown assumptions', 'Unbekannte Voraussetzungen'),
                  items: test.assumptions,
                },
              ]"
              :key="section.label"
              ><h5>{{ section.label }}</h5>
              <ul>
                <li v-for="item in section.items" :key="item">{{ item }}</li>
              </ul></template
            >
          </details>
          <details>
            <summary>{{ wording("Test source", "Test-Quelltext") }}</summary>
            <pre>{{ test.code }}</pre>
            <details v-for="helper in test.helpers" :key="helper.id">
              <summary>{{ helper.path }} · {{ helper.function }}</summary>
              <pre>{{ helper.code }}</pre>
            </details>
          </details>
        </article>
      </div>
      <div
        v-show="activeTab === 'technical'"
        :id="`${flowId}-panel-technical`"
        role="tabpanel"
        :aria-labelledby="`${flowId}-tab-technical`"
      >
        <slot name="reference" />
        <h4>{{ wording("Live technical evidence", "Live-Nachweise") }}</h4>
        <p>
          {{ wording("API server", "API-Server") }}: <code>{{ target }}</code>
        </p>
        <p v-if="data.business?.notice">{{ data.business.notice }}</p>
        <p>
          {{ data.release.version }} · {{ data.release.commit || data.release.source_digest }} ·
          {{ data.status }}
        </p>
        <p>{{ data.purpose }}</p>
        <p>
          {{
            wording(
              "English explanation; source identifiers remain exact.",
              "Englische Erklärung; Quelltext-Bezeichner bleiben exakt.",
            )
          }}
        </p>
        <details v-if="data.business?.annotation_gaps?.length">
          <summary>
            {{ wording("Descriptions still to prepare", "Noch aufzubereitende Beschreibungen") }}
            ({{ data.business.annotation_gaps.length }})
          </summary>
          <ul>
            <li v-for="gap in data.business.annotation_gaps" :key="gap">{{ gap }}</li>
          </ul>
        </details>
        <details v-if="data.limitations.length" open>
          <summary>{{ wording("Evidence limitations", "Grenzen der Nachweise") }}</summary>
          <ul>
            <li v-for="item in data.limitations" :key="item">{{ item }}</li>
          </ul>
        </details>
        <details>
          <summary>
            {{
              wording("Source constants and bindings", "Quelltext-Konstanten und gebundene Werte")
            }}
          </summary>
          <dl>
            <template v-for="(value, name) in data.runtime_values || {}" :key="name"
              ><dt>{{ name }}</dt>
              <dd>{{ value }}</dd></template
            >
          </dl>
        </details>
        <details>
          <summary>
            {{ wording("Inputs and prerequisites", "Eingaben und Voraussetzungen") }}
          </summary>
          <p>{{ [...data.inputs, ...data.prerequisites].join(" · ") }}</p>
        </details>
        <label v-if="data.nodes.length"
          >{{ wording("Logic section", "Abschnitt der Logik")
          }}<select v-model="selected">
            <option
              v-for="f in [...new Set(data.nodes.map((n) => n.function))]"
              :key="f"
              :value="f"
            >
              {{ f.split(".").at(-1)?.replaceAll("_", " ") }}
            </option>
          </select></label
        >
        <ol aria-label="Business steps">
          <li v-for="node in nodes" :key="node.id">
            <p>{{ node.text }}</p>
            <small>{{ node.context.join(" → ") }} · {{ node.id }} · {{ node.line }}</small>
            <details>
              <summary class="source-action">
                {{ wording("Show referenced source", "Markierte Quellstelle anzeigen") }}
              </summary>
              <template
                v-for="source in data.sources.filter((s) => s.id === node.evidence_id)"
                :key="source.id"
                ><SourceEvidence
                  :source="source"
                  :ranges="sourceRanges(source, data.nodes, [node.id], node.line)"
                  :language="de ? 'de' : 'en'"
                />
              </template>
            </details>
          </li>
        </ol>
        <details v-if="nodes.length">
          <summary>{{ wording("Flow diagram", "Flussdiagramm") }}</summary>
          <div class="graph">
            <svg
              role="img"
              aria-label="Flow diagram"
              :viewBox="`0 0 760 ${layout.height}`"
              width="760"
            >
              <g v-for="(edge, index) in layout.edges" :key="index">
                <path
                  :d="`M 700 ${edge.from} L 740 ${edge.from} L 740 ${edge.to} L 700 ${edge.to}`"
                  fill="none"
                  stroke="currentColor"
                />
                <text x="703" :y="(edge.from + edge.to) / 2" font-size="10">
                  {{ edge.outcome }}
                </text>
                <path
                  :d="`M 706 ${edge.to - 4} L 700 ${edge.to} L 706 ${edge.to + 4}`"
                  fill="none"
                  stroke="currentColor"
                />
              </g>
              <g v-for="node in layout.nodes" :key="node.id">
                <rect
                  x="5"
                  :y="node.y"
                  width="690"
                  height="55"
                  :rx="node.kind === 'decision' ? 20 : 5"
                  fill="none"
                  stroke="currentColor"
                />
                <text x="15" :y="node.y + 20" font-size="12">
                  {{ node.kind }} · {{ node.id.slice(-65) }}
                </text>
                <text x="15" :y="node.y + 40" font-size="11">{{ node.text.slice(0, 100) }}</text>
                <title>{{ node.text }}</title>
              </g>
            </svg>
          </div>
        </details>
        <details>
          <summary>
            {{ wording("Unproven branches", "Nicht nachgewiesene Zweige") }} ({{
              data.test_gaps.length
            }})
          </summary>
          <p>
            {{
              wording(
                "Related tests do not prove branch execution.",
                "Verwandte Tests beweisen keine Zweigausführung.",
              )
            }}
          </p>
          <ul>
            <li v-for="id in data.test_gaps" :key="id">{{ id }}</li>
          </ul>
        </details>
      </div>
    </template>
  </section>
  <slot v-else name="reference" />
</template>
<style scoped>
.live-blueprint {
  margin: 16px 0 24px;
  overflow-wrap: anywhere;
}
.live-blueprint-loaded {
  font-size: 14px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}
.reading-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
  overflow-x: auto;
  margin: 0;
  border-bottom: 1px solid var(--vp-c-divider);
  position: sticky;
  top: calc(var(--vp-nav-height, 64px) + 54px);
  background: var(--vp-c-bg);
  z-index: 2;
}
.reading-tabs button {
  border: 0;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  flex-shrink: 0;
  padding: 10px 8px;
  font-size: 13px;
}
.reading-tabs button[aria-selected="true"] {
  color: var(--vp-c-brand-1);
  border-bottom-color: var(--vp-c-brand-1);
  font-weight: 600;
}
.section-tools {
  display: flex;
  justify-content: flex-end;
  padding: 8px 0;
}
.section-tools button {
  font-size: 12px;
  color: var(--vp-c-text-2);
  padding: 4px 8px;
}
.section-hint {
  color: var(--vp-c-text-2);
  font-size: 14px;
}
.rule-cards {
  list-style: none;
  padding: 0;
  counter-reset: rule;
}
.rule-cards > li {
  counter-increment: rule;
  position: relative;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 14px 16px 14px 52px;
  background: var(--vp-c-bg-soft);
}
.rule-cards > li::before {
  content: counter(rule);
  position: absolute;
  left: 16px;
  top: 16px;
  color: var(--vp-c-brand-1);
  font-weight: 600;
}
.rule-cards > li > p {
  margin: 0 0 10px;
  line-height: 1.65;
}
.source-action {
  list-style: none;
  display: inline-block;
  border: 1px solid var(--vp-c-divider);
  border-radius: 5px;
  padding: 4px 9px;
  font-size: 12px;
  color: var(--vp-c-brand-1);
}
.source-action::-webkit-details-marker {
  display: none;
}
.test-list {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
  padding: 2px;
}
.test-list button {
  text-align: left;
  padding: 12px;
  background: var(--vp-c-bg-soft);
}
.test-list button[aria-pressed="true"] {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
}
.selected-test {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
}
.selected-test h4 {
  margin-top: 0;
}
.source-provenance {
  color: var(--vp-c-text-2);
  font-size: 13px;
  margin-top: -8px;
}
.code-panel {
  margin-top: 20px;
}
.dark .source-token {
  color: var(--shiki-dark) !important;
}
.source-next {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.source-next p {
  width: 100%;
  margin-bottom: 0;
}
.direct-source-line {
  display: flex;
  gap: 12px;
  min-height: 1.6em;
  width: max-content;
  min-width: 100%;
}
.direct-source-line > span:last-child {
  white-space: pre;
  overflow-wrap: normal;
  flex-shrink: 0;
}
.direct-line-number {
  min-width: 4ch;
  text-align: right;
  color: var(--vp-c-text-3);
  user-select: none;
  flex-shrink: 0;
}
.source-scope {
  color: var(--vp-c-text-2);
  font-size: 14px;
}
.called-functions {
  margin-top: 16px;
}
.called-functions details {
  margin: 12px 0;
}
.called-functions summary {
  cursor: pointer;
  overflow-wrap: anywhere;
}
.code-panel pre code {
  font-size: inherit;
  line-height: inherit;
}
.code-panel pre {
  white-space: pre;
  max-height: 500px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
}
.reading-tabs button:focus-visible,
.section-tools button:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 3px;
}
button:disabled {
  cursor: wait;
  opacity: 0.65;
}
button,
select {
  border: 1px solid var(--vp-c-divider);
  padding: 6px 12px;
  border-radius: 4px;
}
select {
  max-width: 100%;
  display: block;
}
summary {
  cursor: pointer;
}
pre {
  white-space: pre-wrap;
  max-height: 420px;
  overflow: auto;
  font-size: 12px;
}
.loading-panel {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  margin-top: 16px;
  background: var(--vp-c-bg-soft);
  border-radius: 8px;
}
.loading-panel p {
  margin: 8px 0;
}
.loading-spinner {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border: 3px solid var(--vp-c-divider);
  border-top-color: var(--vp-c-brand-1);
  border-radius: 50%;
  animation: blueprint-spin 1s linear infinite;
}
@keyframes blueprint-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .loading-spinner {
    animation: none;
  }
}
.graph {
  max-height: 480px;
  overflow: auto;
}
li {
  margin: 10px 0;
}
</style>

<style scoped>
.live-blueprint h3,
.live-blueprint h4 {
  font-size: 16px;
  line-height: 1.4;
  font-weight: 600;
  margin: 24px 0 10px;
  border: 0;
  padding: 0;
}
@media (max-width: 640px) {
  .reading-tabs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    overflow: visible;
    position: static;
  }
  .reading-tabs button {
    text-align: left;
  }
}
</style>
