<script setup lang="ts">
import { computed, ref, watch, onUnmounted, useId } from "vue";
import { useData } from "vitepress";
import {
  diagram,
  sourceRanges,
  type BusinessBlueprint,
} from "../../../../shared/businessBlueprint";
import SourceEvidence from "./SourceEvidence.vue";
const props = defineProps<{ kind: string; entryKey: string }>();
const { theme, lang } = useData();
const target = computed(() => String(theme.value.businessLogicUrl || ""));
const data = ref<BusinessBlueprint | null>(null);
const loading = ref(false);
const elapsed = ref(0);
const flowId = useId();
const activeTab = ref("rules");
const selectedTest = ref("");
const tabs = ["code", "rules", "tests", "technical"];
const selectedCode = ref("");
const codeSource = computed(
  () =>
    data.value?.sources.find((source) => source.id === selectedCode.value) ||
    data.value?.sources[0],
);
function showCode() {
  if (data.value) activeTab.value = "code";
  else read(true, false);
}
function tabKey(event: KeyboardEvent, index: number) {
  let next = index;
  if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
  else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = tabs.length - 1;
  else return;
  event.preventDefault();
  activeTab.value = tabs[next];
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
watch(
  () => [props.kind, props.entryKey],
  () => {
    sequence++;
    data.value = null;
    activeTab.value = "rules";
    selectedTest.value = "";
    error.value = "";
    loading.value = false;
  },
);
async function read(brief = true, interpret = true) {
  const request = ++sequence;
  const previousTest = selectedTest.value;
  data.value = null;
  loading.value = true;
  error.value = "";
  try {
    if (!target.value) throw new Error("No configured target");
    const response = await fetch(
      `${target.value}/api/business-logic/entries/${encodeURIComponent(props.kind)}/${encodeURIComponent(props.entryKey)}?language=${de.value ? "de" : "en"}&brief=${brief}&interpret=${interpret}`,
      { cache: "no-store", credentials: "omit" },
    );
    if (!response.ok) throw new Error("Unavailable");
    const result = (await response.json()) as BusinessBlueprint;
    if (request !== sequence) return;
    data.value = result;
    activeTab.value = interpret ? "rules" : "code";
    selectedCode.value = result.sources[0]?.id || "";
    selectedTest.value = result.scenarios.some((test) => test.id === previousTest)
      ? previousTest
      : result.scenarios[0]?.id || "";
    selected.value =
      result.nodes.find((n) => n.durable)?.function || result.nodes[0]?.function || "";
  } catch {
    if (request === sequence)
      error.value = wording(
        "Live evidence is unavailable. Retry to read the configured system.",
        "Live-Nachweise sind nicht verfügbar. Erneut versuchen, um das konfigurierte System zu lesen.",
      );
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
    <h3 v-if="data?.business?.mode === 'llm'">
      {{ wording("Steps and rules", "Ablauf und Regeln") }}
    </h3>
    <p v-if="data" class="source-provenance">
      {{ wording("From the current source code", "Aus dem aktuellen Code") }}
    </p>
    <button
      type="button"
      class="explanation-start code-entry"
      :disabled="loading"
      @click="showCode"
    >
      {{ wording("View code →", "Code anschauen →") }}
    </button>
    <button
      type="button"
      :disabled="loading"
      :class="data?.business?.mode === 'llm' ? 'explanation-refresh' : 'explanation-start'"
      @click="read(true)"
    >
      {{
        data?.business?.mode === "llm"
          ? wording("Refresh explanation", "Erklärung aktualisieren")
          : wording("Explain steps and rules →", "Ablauf und Regeln erklären →")
      }}
    </button>
    <div v-if="loading" class="loading-panel" role="status" aria-live="polite">
      <span class="loading-spinner" aria-hidden="true"></span>
      <div>
        <strong>{{
          wording(
            "Reading current source and tests…",
            "Aktueller Quellcode und Tests werden gelesen…",
          )
        }}</strong>
        <p>
          {{
            wording(
              "The business explanation is created live. Complex logic can take longer.",
              "Die fachliche Erklärung wird jetzt live erstellt. Bei umfangreicher Logik kann das länger dauern.",
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
    <button
      v-if="data"
      type="button"
      :disabled="loading"
      class="detailed-read"
      @click="read(false)"
    >
      {{ wording("Detailed explanation and test cases", "Ausführliche Erklärung und Testfälle") }}
    </button>
    <p v-if="error" role="alert">{{ error }}</p>
    <template v-if="data">
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
          :tabindex="activeTab === tab ? 0 : -1"
          @click="activeTab = tab"
          @keydown="tabKey($event, index)"
        >
          {{
            tab === "code"
              ? wording("Source code", "Quelltext")
              : tab === "rules"
                ? wording("Steps", "Schritte")
                : tab === "tests"
                  ? wording("Test cases", "Testfälle")
                  : wording("Technical evidence", "Technische Nachweise")
          }}<span v-if="tab === 'tests'"> ({{ data.scenarios.length }})</span>
        </button>
      </div>
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
        <button type="button" :disabled="loading" @click="read(true, false)">
          {{ wording("Refresh code", "Code aktualisieren") }}
        </button>
        <label v-if="data.sources.length"
          >{{ wording("Function", "Funktion")
          }}<select v-model="selectedCode">
            <option v-for="source in data.sources" :key="source.id" :value="source.id">
              {{ source.function }}
            </option>
          </select></label
        >
        <template v-if="codeSource"
          ><p class="source-provenance">
            {{ codeSource.path }} · {{ wording("from line", "ab Zeile") }}
            {{ codeSource.start_line }}
          </p>
          <pre data-direct-source><code>{{ codeSource.code }}</code></pre>
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
            data.business?.mode === "llm"
              ? wording(
                  "Selected steps explained from current code; interpretation requires review.",
                  "Ausgewählte Schritte aus aktuellem Code erklärt; die Interpretation muss geprüft werden.",
                )
              : wording(
                  "The business explanation is unavailable. Technical evidence remains below.",
                  "Die fachliche Erklärung ist nicht verfügbar. Technische Nachweise stehen unten.",
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
                "This test was found in code but has not yet been explained in business language.",
                "Dieser Test wurde im Code gefunden, ist aber noch nicht fachlich erklärt.",
              )
            }}
          </p>
          <button
            v-if="!data.business?.scenarios.some((item) => item.id === test.id)"
            type="button"
            :disabled="loading"
            @click="read(false)"
          >
            {{ wording("Load business explanation", "Fachliche Erklärung laden") }}
          </button>
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
        <h4>{{ wording("Technical evidence", "Technische Nachweise") }}</h4>
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
</template>
<style scoped>
.live-blueprint {
  margin: 16px 0 24px;
  overflow-wrap: anywhere;
}
.live-blueprint-loaded {
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 16px;
  margin: 20px 0;
  overflow-wrap: anywhere;
}
.reading-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin: 24px 0;
  border-bottom: 1px solid var(--vp-c-divider);
  padding-bottom: 10px;
}
.reading-tabs button[aria-selected="true"] {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  font-weight: 600;
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
.explanation-start {
  color: var(--vp-c-brand-1);
  background: transparent;
  border: 0;
  padding: 0;
  font-weight: 600;
  cursor: pointer;
}
.code-entry {
  margin-right: 20px;
}
.code-panel {
  margin-top: 20px;
}
.code-panel select {
  width: 100%;
  margin: 12px 0;
}
.code-panel pre {
  white-space: pre;
  max-height: 500px;
  font-size: 13px;
}
.explanation-start:hover {
  text-decoration: underline;
}
.explanation-refresh {
  font-size: 13px;
  color: var(--vp-c-text-2);
  cursor: pointer;
}
.explanation-start:focus-visible,
.explanation-refresh:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 3px;
}
button:disabled {
  cursor: wait;
  opacity: 0.65;
}
.detailed-read {
  margin-left: 8px;
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
