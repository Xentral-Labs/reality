<script setup lang="ts">
import { computed, ref, watch } from "vue";
type Localized = { en: string; de: string };
interface Field {
  name: string;
  type: string;
  nullable: boolean;
  default: { kind: string; value: unknown };
  meaning: Localized;
  references: string[];
}
interface DataModel {
  group: string;
  groupLabel: Localized;
  key: string;
  name: string;
  purpose: Localized;
  note: Localized;
  derived: Localized;
  example: Record<string, unknown>;
  fields: Field[];
  actions: string[];
  related: string[];
}
const props = defineProps<{
  models: DataModel[];
  selectedKey: string;
  locale: "en" | "de";
  query: string;
  entries: { id: string; label: string; label_de?: string }[];
}>();
const emit = defineEmits<{ select: [key: string]; action: [id: string] }>();
const de = computed(() => props.locale === "de");
const loc = (value: Localized) => value[props.locale];
const t = computed(() =>
  de.value
    ? {
        heading: "Wenige Bausteine. Klare Zuständigkeiten.",
        intro:
          "Ein ERP verteilt einen Vorgang oft über viele Tabellen. Hier findest du die Bausteine für Stammdaten, Preise, Belege, operative Abläufe, Lager und Finanzen. Wähle einen Baustein: Du siehst, was er speichert, wie er mit anderen zusammenhängt und welche Tools ihn bearbeiten.",
        core: "Operativer Kern",
        coreText: "Zusage, Zuordnung, Bewegung und Buchung haben eigene, feste Felder.",
        facts: "Zusätzliche Facts",
        factsText:
          "Unterstützte Beobachtungen ergänzen Kontext zu einem Datensatz. Sie ersetzen keine operativen Felder.",
        source: "Original bleibt erhalten",
        sourceText:
          "Ungenutzte ERP-Felder bleiben im SourceRecord. Nicht jedes externe Feld muss ein eigenes Feld oder Fact werden.",
        example: "Beispiel aus Hubers Lampenauftrag",
        excerpt:
          "Vereinfachter Datensatzausschnitt – keine vollständige Tool-Eingabe. IDs und weitere Pflichtwerte sind hier ausgelassen.",
        derived: "Daraus gelesen – nicht zusätzlich hier gespeichert",
        related: "Zusammenhänge verstehen",
        fields: "Gespeicherte Felder",
        field: "Feld",
        meaning: "Bedeutung",
        requiredness: "Pflicht",
        scrollHint: "Auf kleinen Bildschirmen kannst du die Tabelle seitlich scrollen.",
        actions: "Passende Aktionen",
        actionHint:
          "Diese Tools schreiben diesen Datensatz direkt oder als Teil eines Geschäftsablaufs. Öffne eine Aktion für Eingaben, Voraussetzungen und Bestätigung.",
        storageHint:
          "„Wert nötig“ beschreibt den gespeicherten Datensatz. Es bedeutet nicht, dass du das Feld selbst eingeben musst: Tools ergänzen beispielsweise Identität und Unternehmenskontext. Die tatsächlich nötigen Eingaben stehen bei der jeweiligen Aktion.",
        required: "Wert nötig",
        optional: "Darf leer sein",
        technical: "Typ, Standardwert und Verknüpfungen",
        type: "Speichertyp",
        standard: "Standard",
        noDefault:
          "Kein Modellstandard – Wert kommt aus dem Tool oder bleibt bei optionalen Feldern leer.",
        generated: "Wird beim Anlegen erzeugt",
        utcNow: "Aktueller UTC-Zeitpunkt beim Anlegen",
        scalar: "Modellstandard",
        server: "Datenbankstandard",
        defaultHint:
          "Dies ist der Modellstandard, keine Zusicherung über Vorgabewerte aller Tools.",
        refs: "Bezüge",
        noFields: "Kein Feld passt zur Suche. Leere die Suche, um alle Felder zu sehen.",
        noModels: "Kein Baustein passt zur Suche.",
        all: "Alle Bausteine",
        searchAll: "Die Suche durchsucht alle Bereiche.",
        noActions:
          "Der Katalog nennt kein eigenes schreibendes Tool für diese Tabelle. Sie kann im Rahmen eines übergeordneten Geschäftsablaufs entstehen; die Verknüpfungen zeigen die beteiligten Objekte.",
        schema: "Aus den aktuellen Modellfeldern erzeugt; fachlich erläutert.",
        tableMap: "Vollständige Tabellenkarte",
        more: "Diese Übersicht erklärt das fachliche Grundgerüst. Weitere Tabellen für Integration, Administration und technische Abläufe findest du in der Tabellenkarte.",
      }
    : {
        heading: "Few building blocks. Clear responsibilities.",
        intro:
          "An ERP often spreads a business case across many tables. Explore the building blocks for master data, pricing, evidence, operations, warehouse and finance. Select one to see what it stores, how it relates to the others and which tools work with it.",
        core: "Operational core",
        coreText: "Promises, allocations, movements and postings have their own typed fields.",
        facts: "Additional Facts",
        factsText:
          "Supported observations add context to a record. They do not replace operational fields.",
        source: "Keep the original",
        sourceText:
          "Unused ERP fields stay in SourceRecord. Not every external field needs a dedicated field or Fact.",
        example: "Example from Huber's lamp order",
        excerpt:
          "Illustrative record excerpt, not a complete tool input. IDs and other required values are omitted here.",
        derived: "Read from records — not additionally stored here",
        related: "Understand the connections",
        fields: "Stored fields",
        field: "Field",
        meaning: "Meaning",
        requiredness: "Required",
        scrollHint: "On narrow screens, scroll the table sideways to see every column.",
        actions: "Relevant actions",
        actionHint:
          "These tools write this record directly or as part of a business flow. Open an action for inputs, prerequisites and confirmation.",
        storageHint:
          "“Value required” describes the stored record. It does not mean you must enter the field yourself: tools supply identity and company context, for example. Each action documents its actual required inputs.",
        required: "Value required",
        optional: "May be empty",
        technical: "Type, default and references",
        type: "Storage type",
        standard: "Default",
        noDefault: "No model default — supplied by the tool, or empty for optional fields.",
        generated: "Generated on creation",
        utcNow: "Current UTC time on creation",
        scalar: "Model default",
        server: "Database default",
        defaultHint: "This is the model default, not a promise about every tool's default inputs.",
        refs: "References",
        noFields: "No field matches. Clear the search to see all fields.",
        noModels: "No building block matches your search.",
        all: "All building blocks",
        searchAll: "Search covers all groups.",
        noActions:
          "The catalog lists no standalone writing tool for this table. It may be maintained within a broader business flow; follow its related objects for context.",
        schema: "Generated from current model fields, with business explanations.",
        tableMap: "Complete table map",
        more: "This reference explains the business foundation. The table map also lists integration, administration and infrastructure tables.",
      },
);
const selected = computed(() => props.models.find((m) => m.key === props.selectedKey));
const activeGroup = ref("core");
watch(
  () => props.selectedKey,
  () => {
    activeGroup.value = selected.value?.group || "core";
  },
  { immediate: true },
);
const groups = computed(() =>
  ["core", "master", "pricing", "warehouse", "finance"]
    .map((key) => {
      const members = props.models.filter((m) => m.group === key);
      return { key, label: members[0]?.groupLabel, count: members.length };
    })
    .filter((g) => g.label),
);
const q = computed(() => props.query.trim().toLocaleLowerCase());
const matches = (value: unknown) => JSON.stringify(value).toLocaleLowerCase().includes(q.value);
const visible = computed(() =>
  props.models.filter((m) =>
    q.value
      ? matches([m.key, m.name, m.purpose, m.fields.map((f) => [f.name, f.meaning])])
      : !activeGroup.value || m.group === activeGroup.value,
  ),
);
const fields = computed(
  () =>
    selected.value?.fields.filter(
      (f) =>
        !q.value ||
        matches([selected.value?.key, selected.value?.name, selected.value?.purpose]) ||
        matches([f.name, f.meaning]),
    ) || [],
);
const entriesById = computed(() => new Map(props.entries.map((e) => [e.id, e])));
const actionName = (id: string) => {
  const e = entriesById.value.get(id);
  return e ? e.label : id;
};
const modelName = (key: string) => props.models.find((m) => m.key === key)?.name || key;
const prefix = computed(() => (de.value ? "/de" : ""));
const relationUrl = (ref: string) =>
  props.models.some((m) => m.key === ref.split(".")[0])
    ? `#model:${ref.split(".")[0]}`
    : `${prefix.value}/reference/table-map`;
const followReference = (event: MouseEvent, ref: string) => {
  const table = ref.split(".")[0];
  if (
    props.models.some((m) => m.key === table) &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.shiftKey &&
    !event.altKey
  ) {
    event.preventDefault();
    emit("select", table);
  }
};
const defaultText = (field: Field) => {
  const d = field.default;
  if (d.kind === "none") return de.value ? "Kein Modellstandard" : "No model default";
  if (d.kind === "generated")
    return d.value === "now" ? t.value.utcNow : `${t.value.generated}: ${d.value}`;
  return `${d.kind === "server" ? t.value.server : t.value.scalar}: ${JSON.stringify(d.value)}`;
};
</script>

<template>
  <section class="data-model" aria-label="Data model">
    <details class="model-guidance">
      <summary>{{ de ? "Wo Informationen hingehören" : "Where information belongs" }}</summary>
      <div class="authority-cards">
        <div>
          <strong>{{ t.core }}</strong>
          <p>{{ t.coreText }}</p>
        </div>
        <div>
          <strong>{{ t.facts }}</strong>
          <p>{{ t.factsText }}</p>
        </div>
        <div>
          <strong>{{ t.source }}</strong>
          <p>{{ t.sourceText }}</p>
        </div>
      </div>
    </details>
    <nav class="model-groups" :aria-label="t.all">
      <button
        class="explorer-filter"
        type="button"
        :aria-pressed="activeGroup === ''"
        @click="activeGroup = ''"
      >
        {{ t.all }} <span>{{ models.length }}</span>
      </button>
      <button
        class="explorer-filter"
        v-for="group in groups"
        :key="group.key"
        type="button"
        :aria-pressed="activeGroup === group.key"
        @click="activeGroup = group.key"
      >
        {{ group.label!.en }} <span>{{ group.count }}</span>
      </button>
    </nav>
    <p class="metadata-note">{{ t.searchAll }}</p>
    <nav class="model-picker explorer-surface" :aria-label="t.all">
      <a
        class="explorer-card"
        v-for="model in visible"
        :key="model.key"
        :href="`#model:${model.key}`"
        :aria-current="selectedKey === model.key ? 'page' : undefined"
        @click.prevent="emit('select', model.key)"
        ><strong>{{ model.name }}</strong
        ><span>{{ loc(model.purpose) }}</span></a
      >
    </nav>
    <p v-if="!visible.length" role="status">{{ t.noModels }}</p>
    <article
      v-if="selected && (!activeGroup || selected.group === activeGroup || q)"
      class="model-detail explorer-panel"
      :aria-label="selected.name"
    >
      <header class="model-heading">
        <div>
          <span class="eyebrow">{{ selected.key }}</span>
          <h2>{{ selected.name }}</h2>
          <p class="model-purpose">{{ loc(selected.purpose) }}</p>
        </div>
        <a :href="`#model:${selected.key}`" :aria-label="selected.name + ' permalink'">#</a>
      </header>
      <p>{{ loc(selected.note) }}</p>
      <div class="model-explanation">
        <section class="model-example">
          <h3>{{ t.example }}</h3>
          <p>{{ t.excerpt }}</p>
          <pre><code>{{ JSON.stringify(selected.example, null, 2) }}</code></pre>
        </section>
        <section class="model-derived">
          <h3>{{ t.derived }}</h3>
          <p>{{ loc(selected.derived) }}</p>
        </section>
      </div>
      <h3>{{ t.related }}</h3>
      <nav class="related-models" :aria-label="t.related">
        <a
          v-for="key in selected.related"
          :key="key"
          :href="`#model:${key}`"
          @click.prevent="emit('select', key)"
          >{{ modelName(key) }} →</a
        >
      </nav>
      <h3>
        {{ t.fields }}
        <span class="field-count">{{ fields.length }} / {{ selected.fields.length }}</span>
      </h3>
      <p>{{ t.storageHint }}</p>
      <p class="metadata-note">{{ t.schema }}</p>
      <p v-if="!fields.length" role="status">{{ t.noFields }}</p>
      <p class="metadata-note">{{ t.defaultHint }} {{ t.noDefault }}</p>
      <p class="table-scroll-hint">{{ t.scrollHint }}</p>
      <div class="model-fields" role="region" :aria-label="t.fields" tabindex="0">
        <table class="model-fields-table">
          <colgroup>
            <col class="col-name" />
            <col class="col-meaning" />
            <col class="col-required" />
            <col class="col-type" />
            <col class="col-default" />
            <col class="col-refs" />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">{{ t.field }}</th>
              <th scope="col">{{ t.meaning }}</th>
              <th scope="col">{{ t.requiredness }}</th>
              <th scope="col">{{ t.type }}</th>
              <th scope="col">{{ t.standard }}</th>
              <th scope="col">{{ t.refs }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="field in fields" :key="field.name" class="model-field">
              <th scope="row">
                <code>{{ field.name }}</code>
              </th>
              <td>{{ loc(field.meaning) }}</td>
              <td>{{ field.nullable ? t.optional : t.required }}</td>
              <td>
                <code>{{ field.type }}</code>
              </td>
              <td>{{ defaultText(field) }}</td>
              <td>
                <template v-if="field.references.length"
                  ><a
                    v-for="reference in field.references"
                    :key="reference"
                    :href="relationUrl(reference)"
                    @click="followReference($event, reference)"
                    >{{ reference }}</a
                  ></template
                ><span v-else>—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <h3>{{ t.actions }}</h3>
      <p>{{ selected.actions.length ? t.actionHint : t.noActions }}</p>
      <ul class="model-actions">
        <li v-for="id in selected.actions" :key="id">
          <a :href="`#${id}`" @click.prevent="emit('action', id)"
            >{{ actionName(id) }}<code>{{ id.replace("command:", "") }}</code></a
          >
        </li>
      </ul>
    </article>
    <footer class="model-footer">
      <p>{{ t.more }}</p>
      <a :href="`${prefix}/reference/table-map`">{{ t.tableMap }} →</a>
    </footer>
  </section>
</template>

<style scoped>
.data-model {
  min-width: 0;
  overflow-wrap: anywhere;
}
.data-model h2 {
  margin: 0 0 12px;
  border: 0;
  padding: 0;
}
.data-model h3 {
  margin: 28px 0 12px;
}
.data-model p {
  margin: 8px 0 16px;
  line-height: 1.65;
}
.authority-cards,
.model-picker {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.authority-cards p {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--vp-c-text-2);
}
.model-groups {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 20px 0 8px;
}
.model-groups span {
  margin-left: 5px;
  font-size: 12px;
  color: var(--vp-c-text-2);
}
.model-picker {
  margin-bottom: 28px;
}
.model-detail {
  scroll-margin-top: 84px;
}
.model-heading {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
}
.eyebrow {
  font-family: var(--vp-font-family-mono);
  font-size: 13px;
  color: var(--vp-c-text-2);
}
.model-heading h2 {
  margin-top: 6px;
  font-size: 22px;
}
.model-purpose {
  font-size: 16px;
  color: var(--vp-c-text-2);
}
.model-explanation {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.model-explanation > section {
  min-width: 0;
  padding: 18px;
  background: var(--vp-c-bg-soft);
  border-radius: 10px;
}
.model-explanation h3 {
  margin-top: 0;
  font-size: 16px;
}
.model-example > p {
  font-size: 13px;
  color: var(--vp-c-text-2);
}
.model-example pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  margin: 0;
  font-size: 13px;
}
.model-example pre code {
  padding: 0;
  background: transparent;
}
.related-models {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.related-models a {
  padding: 6px 12px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  text-decoration: none;
}
.field-count,
.metadata-note {
  font-size: 13px;
  color: var(--vp-c-text-2);
  font-weight: 400;
}
.model-fields {
  max-width: 100%;
  overflow-x: auto;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
}
.model-fields-table {
  display: table;
  width: 100%;
  min-width: 820px;
  table-layout: fixed;
  border-collapse: collapse;
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
}
.model-fields-table .col-name {
  width: 16%;
}
.model-fields-table .col-meaning {
  width: 27%;
}
.model-fields-table .col-required {
  width: 11%;
}
.model-fields-table .col-type {
  width: 14%;
}
.model-fields-table .col-default {
  width: 16%;
}
.model-fields-table .col-refs {
  width: 16%;
}
.model-fields-table th,
.model-fields-table td {
  padding: 12px 14px;
  vertical-align: top;
  text-align: left;
  white-space: normal;
  overflow-wrap: anywhere;
  border: 0;
  border-bottom: 1px solid var(--vp-c-divider);
}
.model-fields-table thead th {
  background: var(--vp-c-bg-soft);
  font-weight: 600;
}
.model-fields-table tbody th {
  font-weight: 600;
}
.model-fields-table tbody tr:last-child > * {
  border-bottom: 0;
}
.model-fields-table tbody tr:nth-child(even) {
  background: var(--vp-c-bg-soft);
}
.model-fields-table code {
  color: var(--vp-c-text-1);
  font-size: 12px;
  white-space: normal;
}
.model-fields-table a {
  display: block;
}
.table-scroll-hint {
  font-size: 13px;
  color: var(--vp-c-text-2);
}
.model-actions {
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.model-actions li {
  margin: 0;
  min-width: 0;
}
.model-actions a {
  display: block;
  padding: 12px 0;
  border-bottom: 1px solid var(--vp-c-divider);
  text-decoration: none;
}
.model-actions code {
  display: block;
  padding: 0;
  background: none;
  color: var(--vp-c-text-2);
  font-size: 12px;
  margin-top: 5px;
}
.model-footer {
  margin-top: 24px;
  color: var(--vp-c-text-2);
}
a:focus-visible,
summary:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 4px;
}
@media (max-width: 1100px) {
  .model-picker {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .model-explanation {
    grid-template-columns: minmax(0, 1fr);
  }
}
@media (max-width: 600px) {
  .authority-cards,
  .model-picker,
  .model-actions {
    grid-template-columns: minmax(0, 1fr);
  }
  .model-detail {
  }
  .model-heading h2 {
    font-size: 24px;
  }
}
</style>
