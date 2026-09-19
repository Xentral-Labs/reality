<script setup lang="ts">
import { computed, ref } from "vue";

type Definition = Record<string, unknown>;
interface Property {
  key: string;
  label: string;
  kind?: string;
  temporal?: string;
  input?: string;
  identity?: boolean;
}
interface Measure {
  key: string;
  label: string;
  unit: string;
  additive_over: string[];
  never_across: string[];
  note?: string;
  less?: { measure: string; over: { edge: string; direction: string }[] };
  definition: Definition;
}
interface Edge {
  key: string;
  label: string;
  to?: string;
  from?: string;
  to_label?: string;
  from_label?: string;
  multiplicity: string;
  definition: Definition;
}
interface Node {
  key: string;
  label: string;
  category: string | null;
  grain: string;
  backed_by: string | null;
  coverage: string[];
  corrections: string;
  evidence?: string;
  properties: Property[];
  measures: Measure[];
  edges: Edge[];
  edges_in: Edge[];
  definition: Definition;
}
interface Template {
  key: string;
  label: string;
  about: string;
  question: { from: string; follow?: { edge: string }[] };
  period?: unknown;
  snapshot?: unknown;
}
interface Catalog {
  model_version: string;
  nodes: Node[];
  templates: Template[];
  limits: Record<string, number>;
}
const props = defineProps<{
  catalog: Catalog;
  selectedKey: string;
  query: string;
  locale: "en" | "de";
}>();
const emit = defineEmits<{ select: [key: string] }>();
const de = computed(() => props.locale === "de");
const category = ref("");
const categories = computed(
  () => [...new Set(props.catalog.nodes.map((n) => n.category).filter(Boolean))] as string[],
);
const nodes = computed(() => {
  const tokens = props.query.toLocaleLowerCase().trim().split(/\s+/u).filter(Boolean);
  return props.catalog.nodes.filter(
    (n) =>
      (!category.value || n.category === category.value) &&
      tokens.every((token) => JSON.stringify(n).toLocaleLowerCase().includes(token)),
  );
});
const selected = computed(() => props.catalog.nodes.find((n) => n.key === props.selectedKey));
const templates = computed(() => {
  const node = selected.value;
  if (!node) return props.catalog.templates;
  const edges = new Set([...node.edges, ...node.edges_in].map((e) => e.key));
  return props.catalog.templates.filter(
    (t) => t.question.from === node.key || t.question.follow?.some((h) => edges.has(h.edge)),
  );
});
const total = (field: "properties" | "measures" | "edges") =>
  props.catalog.nodes.reduce((sum, n) => sum + n[field].length, 0);
const json = (value: unknown) => JSON.stringify(value, null, 2);
const go = (key: string) => {
  category.value = "";
  emit("select", key);
};
</script>

<template>
  <section class="analytics-model" :aria-label="de ? 'Analytics-Modell' : 'Analytics model'">
    <p class="am-note">
      {{
        de
          ? "Welche Fragen sind möglich? Dieses Modell beschreibt vorhandene Geschäftsdaten und ihre Bedeutung. Es zeigt keine Unternehmensdaten und führt keine Abfragen aus."
          : "What can you ask? This model describes existing business records and their meaning. It shows no company data and executes no queries."
      }}
      <a :href="`${de ? '/de' : ''}/analytics/`">{{
        de ? "Analytics verstehen →" : "Understand Analytics →"
      }}</a>
    </p>
    <p class="am-counts">
      {{ catalog.nodes.length }} {{ de ? "Objekte" : "objects" }} · {{ total("properties") }}
      {{ de ? "Felder" : "fields" }} · {{ total("edges") }}
      {{ de ? "Beziehungen" : "relationships" }} · {{ total("measures") }}
      {{ de ? "Kennzahlen" : "measures" }} · {{ catalog.templates.length }}
      {{ de ? "Vorlagen" : "templates" }}
    </p>
    <div class="am-layout">
      <aside>
        <label class="am-category"
          >{{ de ? "Geschäftsbereich" : "Business area" }}
          <select v-model="category">
            <option value="">{{ de ? "Alle Bereiche" : "All areas" }}</option>
            <option v-for="name in categories" :key="name">{{ name }}</option>
          </select>
        </label>
        <p role="status">{{ nodes.length }} {{ de ? "Treffer" : "matches" }}</p>
        <p v-if="!nodes.length">
          {{
            de
              ? "Keine passenden Objekte. Ändere die Suche oder den Bereich."
              : "No matching objects. Change the search or area."
          }}
        </p>
        <nav :aria-label="de ? 'Analytics-Objekte' : 'Analytics objects'" class="am-picker">
          <a
            v-for="node in nodes"
            :key="node.key"
            :href="`#analytics:${node.key}`"
            :aria-current="selectedKey === node.key ? 'true' : undefined"
            @click.prevent="go(node.key)"
          >
            <strong>{{ node.label }}</strong
            ><code>{{ node.key }}</code
            ><small>{{ node.category }}</small>
          </a>
        </nav>
      </aside>
      <div class="am-detail" tabindex="-1">
        <template v-if="selected">
          <button type="button" @click="go('')">
            ← {{ de ? "Modellübersicht" : "Model overview" }}
          </button>
          <h3>{{ selected.label }}</h3>
          <code>{{ selected.key }}</code>
          <p>{{ selected.grain }}</p>
          <dl class="am-facts">
            <dt>{{ de ? "Datenbasis" : "Backing records" }}</dt>
            <dd>{{ selected.backed_by || "—" }}</dd>
            <dt>{{ de ? "Berechnung" : "Derivation" }}</dt>
            <dd>
              {{
                selected.definition.derivation ||
                (de ? "Vorhandene Datensätze" : "Existing records")
              }}
            </dd>
            <dt>{{ de ? "Zeitliche Abdeckung" : "Time coverage" }}</dt>
            <dd>{{ selected.coverage.join(", ") }}</dd>
            <dt>{{ de ? "Korrekturen" : "Corrections" }}</dt>
            <dd>{{ selected.corrections }}</dd>
            <dt>{{ de ? "Belegverweis" : "Evidence reference" }}</dt>
            <dd>{{ selected.evidence || "—" }}</dd>
          </dl>
          <h4>
            {{ de ? "Felder zum Filtern und Gruppieren" : "Fields for filtering and grouping" }}
          </h4>
          <ul class="am-fields">
            <li v-for="field in selected.properties" :key="field.key">
              <strong>{{ field.label }}</strong> <code>{{ field.key }}</code
              ><small
                >{{ field.kind }} {{ field.temporal }} {{ field.input }}
                {{ field.identity ? (de ? "Identität" : "Identity") : "" }}</small
              >
            </li>
          </ul>
          <h4>{{ de ? "Kennzahlen und ihre Regeln" : "Measures and their rules" }}</h4>
          <p v-if="!selected.measures.length">
            {{
              de
                ? "Keine eigene Kennzahl deklariert. Über Beziehungen erreichbare Kennzahlen hängen vom Abfragepfad ab."
                : "No own measure declared. Measures reached through relationships depend on the query path."
            }}
          </p>
          <article v-for="measure in selected.measures" :key="measure.key" class="am-measure">
            <strong>{{ measure.label }}</strong> <code>{{ measure.key }}</code>
            <p>
              {{ de ? "Einheit" : "Unit" }}: {{ measure.unit }}<br />{{
                de ? "Addierbar über" : "Additive over"
              }}: {{ measure.additive_over.join(", ") || "—" }}<br />{{
                de ? "Nicht zusammenfassen über" : "Never combine across"
              }}: {{ measure.never_across.join(", ") || "—" }}
            </p>
            <p v-if="measure.less">
              {{ de ? "Abzüglich" : "Less" }} <code>{{ measure.less.measure }}</code>
              {{ de ? "über" : "via" }} {{ measure.less.over.map((s) => s.edge).join(" → ") }}
            </p>
            <p v-if="measure.note">{{ measure.note }}</p>
            <details>
              <summary>{{ de ? "Technische Definition" : "Technical definition" }}</summary>
              <pre>{{ json(measure.definition) }}</pre>
            </details>
          </article>
          <h4>{{ de ? "Beziehungen" : "Relationships" }}</h4>
          <p>
            {{
              de
                ? "1:n erreicht mehrere Datensätze. Dadurch kann sich die erlaubte Aggregation ändern."
                : "1:n reaches many records. This can change which aggregations are valid."
            }}
          </p>
          <p v-if="!selected.edges.length && !selected.edges_in.length">
            {{ de ? "Keine Beziehung deklariert." : "No relationship declared." }}
          </p>
          <ul class="am-edges">
            <li v-for="edge in selected.edges" :key="`out:${edge.key}`">
              <a :href="`#analytics:${edge.to}`" @click.prevent="go(edge.to!)"
                >{{ selected.label }} → {{ edge.to_label }}</a
              ><br /><code>{{ edge.key }}</code> · {{ edge.multiplicity }}
              <details>
                <summary>{{ de ? "Definition" : "Definition" }}</summary>
                <pre>{{ json(edge.definition) }}</pre>
              </details>
            </li>
            <li v-for="edge in selected.edges_in" :key="`in:${edge.key}`">
              <a :href="`#analytics:${edge.from}`" @click.prevent="go(edge.from!)"
                >{{ edge.from_label }} → {{ selected.label }}</a
              ><br /><code>{{ edge.key }}</code> · {{ edge.multiplicity }}
              <details>
                <summary>Definition</summary>
                <pre>{{ json(edge.definition) }}</pre>
              </details>
            </li>
          </ul>
          <details>
            <summary>
              {{ de ? "Vollständige Objektdefinition" : "Complete object definition" }}
            </summary>
            <p>
              {{
                de
                  ? "Originaldefinition aus dem ausführbaren Modell; technische Schlüssel bleiben Englisch."
                  : "Original executable model definition; technical keys remain English."
              }}
            </p>
            <pre>{{ json(selected.definition) }}</pre>
          </details>
        </template>
        <template v-else>
          <h3>
            {{ de ? "Vom Datensatz zur Geschäftsfrage" : "From a record to a business question" }}
          </h3>
          <p>
            {{
              de
                ? "Wähle links ein Objekt. Felder bestimmen Filter und Gruppierungen, Beziehungen die möglichen Pfade und Kennzahlen die zulässigen Berechnungen."
                : "Choose an object on the left. Fields define filters and groupings, relationships define paths, and measures define permitted calculations."
            }}
          </p>
          <p>
            {{
              de
                ? "Beispiel: Auftrag → Kunde, gruppiert nach Kundenidentität und Währung, mit dem übernommenen Auftragsbetrag als Kennzahl. Auftragswert ist kein realisierter Umsatz."
                : "Example: order → customer, grouped by customer identity and currency, with the received order amount as a measure. Order value is not recognized revenue."
            }}
          </p>
          <p>
            {{
              de
                ? "Dies ist eine Graph-Abfrageschicht über PostgreSQL. Bestände und finanzielle Positionen verwenden die gemeinsamen operativen Services."
                : "This is a graph query layer over PostgreSQL. Stock and financial positions reuse the shared operational services."
            }}
          </p>
        </template>
        <h4>
          {{
            selected
              ? de
                ? "Vorlagen mit diesem Objekt"
                : "Templates involving this object"
              : de
                ? "Alle Startvorlagen"
                : "All starting templates"
          }}
        </h4>
        <p>
          {{
            de
              ? "Vorlagen sind bearbeitbare Fragen, keine vorberechneten Ergebnisse. Zeiträume werden beim Verwenden aufgelöst; Stichtage müssen explizit gewählt werden."
              : "Templates are editable questions, not precomputed results. Periods resolve when used; snapshot dates must be chosen explicitly."
          }}
        </p>
        <p v-if="!templates.length">
          {{
            de
              ? "Keine Startvorlage für dieses Objekt deklariert."
              : "No starting template declared for this object."
          }}
        </p>
        <details v-for="template in templates" :key="template.key" class="am-template">
          <summary>{{ template.label }}</summary>
          <p>{{ template.about }}</p>
          <code>{{ template.key }}</code>
          <pre>{{ json(template) }}</pre>
        </details>
        <details class="am-limits">
          <summary>
            {{ de ? "Modellversion und Ausführungsgrenzen" : "Model version and execution limits" }}
          </summary>
          <p>{{ catalog.model_version }}</p>
          <pre>{{ json(catalog.limits) }}</pre>
          <p>
            {{
              de
                ? "Servicebasierte Kennzahlen können mehrere begrenzte Lesezugriffe benötigen. Die Grenze einer gewöhnlichen SQL-Abfrage ist kein Geschwindigkeitsversprechen."
                : "Service-backed measures can require several bounded reads. The ordinary SQL-query limit is not a speed guarantee."
            }}
          </p>
        </details>
      </div>
    </div>
  </section>
</template>

<style scoped>
.analytics-model {
  min-width: 0;
}
.am-note,
.am-counts {
  color: var(--vp-c-text-2);
}
.am-layout {
  display: grid;
  grid-template-columns: minmax(180px, 260px) minmax(0, 1fr);
  gap: 28px;
}
.am-layout > *,
.am-detail {
  min-width: 0;
}
.am-category {
  display: grid;
  gap: 8px;
  font-weight: 600;
}
select {
  padding: 8px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  max-width: 100%;
}
.am-picker {
  display: grid;
  max-height: 70vh;
  overflow-y: auto;
}
.am-picker a {
  display: grid;
  padding: 10px;
  border-bottom: 1px solid var(--vp-c-divider);
  text-decoration: none;
}
.am-picker a[aria-current] {
  background: var(--vp-c-bg-soft);
  border-left: 3px solid var(--vp-c-brand-1);
}
small {
  display: block;
  color: var(--vp-c-text-2);
}
.am-detail h3 {
  margin-top: 12px;
}
.am-detail h4 {
  margin: 28px 0 12px;
}
.am-detail pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: var(--vp-c-bg-soft);
  padding: 12px;
  font-size: 12px;
}
.am-detail code,
.am-picker code,
.am-facts dd {
  overflow-wrap: anywhere;
}
.am-facts {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px 16px;
}
.am-facts dt {
  color: var(--vp-c-text-2);
}
.am-facts dd {
  margin: 0;
}
.am-fields,
.am-edges {
  padding-left: 20px;
}
.am-fields li,
.am-edges li {
  margin-bottom: 12px;
}
.am-measure {
  padding: 16px 0;
  border-top: 1px solid var(--vp-c-divider);
}
details {
  margin: 12px 0;
}
summary {
  cursor: pointer;
  font-weight: 600;
}
button {
  cursor: pointer;
  color: var(--vp-c-brand-1);
}
@media (max-width: 760px) {
  .am-layout {
    grid-template-columns: 1fr;
  }
  .am-picker {
    max-height: 260px;
  }
  .am-facts {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
