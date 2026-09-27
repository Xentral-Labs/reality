<script setup lang="ts">
import { computed, ref } from "vue";
import catalog from "../../data/business-journeys.json";

declare const __API_URL__: string;
type Journey = (typeof catalog.entries)[number];
type GuideAnswer = {
  status: string;
  text: string;
  citations: string[];
  matches: Journey[];
  outcome: string;
};

const props = withDefaults(defineProps<{ locale?: "en" | "de" }>(), { locale: "en" });
const query = ref("");
const status = ref("");
const section = ref("");
const question = ref("");
const answer = ref<GuideAnswer | null>(null);
const asking = ref(false);
const askFailed = ref(false);

const labels = computed(() =>
  props.locale === "de"
    ? {
        search: "Szenarien suchen",
        area: "Bereich",
        supportStatus: "Unterstützungsstatus",
        allStatuses: "Alle Status",
        allSections: "Alle Bereiche",
        ask: "Reality fragen",
        askTitle: "Passt Reality zu deinem Geschäftsablauf?",
        askIntro:
          "Beschreibe die Situation in deinen eigenen Worten. Reality antwortet ausschließlich aus dem veröffentlichten Guide und zeigt die verwendeten Szenarien.",
        question: "Zum Beispiel: Was passiert, wenn ein Lieferant zu wenig liefert?",
        evidence: "Nachweis",
        limitations: "Grenzen",
        noAnswer: "Diese Fähigkeit ist im veröffentlichten Guide nicht belegt.",
        unavailable:
          "Die KI-Antwort ist gerade nicht verfügbar. Diese lokalen Treffer können helfen:",
        sources: "Verwendete Szenarien",
        browse: "Alle Szenarien durchsuchen",
        browseIntro: "Filtere den vollständigen Katalog unabhängig von deiner Frage oben.",
        suggest: "Fehlendes Szenario vorschlagen",
        count: "Szenarien",
        waiting: "Reality prüft den veröffentlichten Guide …",
        examples: [
          "Was passiert bei einer Teillieferung?",
          "Kann Reality Retouren verwalten?",
          "Was passiert bei einer zu hohen Zahlung?",
        ],
      }
    : {
        search: "Search journeys",
        area: "Area",
        supportStatus: "Support status",
        allStatuses: "All statuses",
        allSections: "All areas",
        ask: "Ask Reality",
        askTitle: "Does Reality fit your business process?",
        askIntro:
          "Describe the situation in your own words. Reality answers only from the published Guide and shows the journeys it used.",
        question: "For example: What happens when a supplier delivers too little?",
        evidence: "Evidence",
        limitations: "Limitations",
        noAnswer: "This capability is not established by the published guide.",
        unavailable: "The AI answer is unavailable right now. These local matches may help:",
        sources: "Journeys used",
        browse: "Browse all journeys",
        browseIntro: "Filter the complete catalog independently of the question above.",
        suggest: "Suggest a missing journey",
        count: "journeys",
        waiting: "Reality is checking the published Guide …",
        examples: [
          "What happens with a partial delivery?",
          "Can Reality manage returns?",
          "What happens when a customer pays too much?",
        ],
      },
);

const statusLabels = computed<Record<string, string>>(() =>
  props.locale === "de"
    ? {
        supported: "Unterstützt",
        partial: "Teilweise",
        recognition_only: "Nur Erkennung",
        missing: "Fehlt",
        out_of_scope: "Nicht vorgesehen",
        not_established: "Nicht belegt",
      }
    : {
        supported: "Supported",
        partial: "Partial",
        recognition_only: "Recognition only",
        missing: "Missing",
        out_of_scope: "Out of scope",
        not_established: "Not established",
      },
);
const sections = [...new Set(catalog.entries.map((entry) => entry.section))];
const statuses = Object.keys(catalog.statuses);

function words(value: string) {
  return (
    value
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .match(/[\p{L}\p{N}]+/gu) || []
  );
}
function matches(entry: Journey, value: string) {
  const needle = words(value);
  if (!needle.length) return true;
  const haystack = words(
    [entry.id, entry.section, entry.title, entry.question, ...entry.question_examples].join(" "),
  );
  return needle.every((part) => haystack.some((word) => word.startsWith(part)));
}
const filtered = computed(() =>
  catalog.entries.filter(
    (entry) =>
      (!status.value || entry.status === status.value) &&
      (!section.value || entry.section === section.value) &&
      matches(entry, query.value),
  ),
);

function localFallback(value: string): GuideAnswer {
  const normalized = value
    .replace(/zu wenig|unterliefer\w*/giu, "under delivery remainder receipt")
    .replace(/lieferant/giu, "supplier receipt purchase");
  const found = catalog.entries
    .map((entry) => ({
      entry,
      score: words(normalized).filter((part) => matches(entry, part)).length,
    }))
    .filter((candidate) => candidate.score > 0)
    .sort((left, right) => right.score - left.score || left.entry.id.localeCompare(right.entry.id))
    .slice(0, 3)
    .map((candidate) => candidate.entry);
  return {
    status: found[0]?.status || "not_established",
    text: found.length ? labels.value.unavailable : labels.value.noAnswer,
    citations: found.map((entry) => entry.id),
    matches: found,
    outcome: "fallback",
  };
}

async function ask() {
  const value = question.value.trim();
  if (!value || asking.value) return;
  asking.value = true;
  askFailed.value = false;
  answer.value = null;
  try {
    const response = await fetch(`${__API_URL__}/api/journey-guide/questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: value, locale: props.locale }),
    });
    if (!response.ok) throw new Error("journey question unavailable");
    answer.value = await response.json();
  } catch (_error) {
    askFailed.value = true;
    answer.value = localFallback(value);
  } finally {
    asking.value = false;
  }
}
</script>

<template>
  <section class="journey-ask" aria-labelledby="journey-ask-title">
    <div class="journey-ask-intro">
      <span class="journey-ask-mark" aria-hidden="true">✦</span>
      <div>
        <p class="journey-eyebrow">{{ labels.ask }}</p>
        <h2 id="journey-ask-title">{{ labels.askTitle }}</h2>
        <p>{{ labels.askIntro }}</p>
      </div>
    </div>
    <form @submit.prevent="ask">
      <label class="sr-only" for="journey-question">{{ labels.question }}</label>
      <div class="journey-ask-row">
        <input
          id="journey-question"
          v-model="question"
          maxlength="1000"
          required
          :placeholder="labels.question"
        />
        <button type="submit" :disabled="asking">{{ asking ? labels.waiting : labels.ask }}</button>
      </div>
    </form>
    <div class="journey-examples" aria-label="Example questions">
      <button
        v-for="example in labels.examples"
        :key="example"
        type="button"
        @click="question = example"
      >
        {{ example }}
      </button>
    </div>
    <div class="journey-answer" aria-live="polite" :aria-busy="asking">
      <div v-if="asking" class="journey-answer-loading">{{ labels.waiting }}</div>
      <article v-else-if="answer">
        <div class="journey-answer-head">
          <span class="journey-status" :data-status="answer.status">{{
            statusLabels[answer.status] || answer.status
          }}</span>
          <span v-if="askFailed" class="journey-fallback">{{ labels.unavailable }}</span>
        </div>
        <p class="journey-answer-text">{{ answer.text }}</p>
        <div v-if="answer.citations.length" class="journey-answer-sources">
          <strong>{{ labels.sources }}</strong>
          <div>
            <a v-for="id in answer.citations" :key="id" :href="`#${id}`">{{ id }}</a>
          </div>
        </div>
        <a
          v-if="answer.status === 'not_established'"
          class="journey-suggest"
          href="__APP_URL__/?route=settings&settingsView=personal#journey-suggestions"
          >{{ labels.suggest }}</a
        >
      </article>
    </div>
  </section>

  <section class="journey-guide" aria-labelledby="journey-catalog-title">
    <div class="journey-catalog-head">
      <div>
        <h2 id="journey-catalog-title">{{ labels.browse }}</h2>
        <p>{{ labels.browseIntro }}</p>
      </div>
      <strong>{{ filtered.length }} {{ labels.count }}</strong>
    </div>
    <div class="journey-filters">
      <label
        ><span>{{ labels.search }}</span
        ><input v-model="query" type="search"
      /></label>
      <label
        ><span>{{ labels.area }}</span
        ><select v-model="section">
          <option value="">{{ labels.allSections }}</option>
          <option v-for="item in sections" :key="item">{{ item }}</option>
        </select></label
      >
      <label
        ><span>{{ labels.supportStatus }}</span
        ><select v-model="status">
          <option value="">{{ labels.allStatuses }}</option>
          <option v-for="item in statuses" :key="item" :value="item">
            {{ statusLabels[item] || item }}
          </option>
        </select></label
      >
    </div>
    <p class="journey-suggest-row">
      <a href="__APP_URL__/?route=settings&settingsView=personal#journey-suggestions">{{
        labels.suggest
      }}</a>
    </p>
    <details v-for="entry in filtered" :id="entry.id" :key="entry.id" class="journey-entry">
      <summary>
        <code>{{ entry.id }}</code
        ><span>{{ entry.title }}</span
        ><span class="journey-status" :data-status="entry.status">{{
          statusLabels[entry.status] || entry.status
        }}</span>
      </summary>
      <div class="journey-entry-body">
        <p>
          <strong>{{ entry.question }}</strong>
        </p>
        <p>{{ entry.summary }}</p>
        <p>
          <b>{{ labels.evidence }}:</b> {{ entry.evidence_level }}
        </p>
        <p v-if="entry.limitations.length">
          <b>{{ labels.limitations }}:</b> {{ entry.limitations.join(" ") }}
        </p>
      </div>
    </details>
  </section>
</template>
