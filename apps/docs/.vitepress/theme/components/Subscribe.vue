<script setup lang="ts">
import { computed } from "vue";
import { useData } from "vitepress";

const copy = {
  en: {
    heading: "Follow the blog",
    lead: "New articles appear in the feed the moment they are published. No account, no email address, no tracking.",
    how: "Paste this address into any feed reader — NetNewsWire, Feedly, Inoreader, Thunderbird or the reader built into your browser:",
    open: "Open the feed",
    path: "/blog/feed.rss",
  },
  de: {
    heading: "Dem Blog folgen",
    lead: "Neue Beiträge erscheinen im Feed, sobald sie veröffentlicht sind. Ohne Konto, ohne E-Mail-Adresse, ohne Tracking.",
    how: "Diese Adresse in einen beliebigen Feed-Reader einfügen — NetNewsWire, Feedly, Inoreader, Thunderbird oder den Reader im Browser:",
    open: "Feed öffnen",
    path: "/de/blog/feed.rss",
  },
};

const { lang, theme } = useData();

const locale = computed<"en" | "de">(() => (lang.value.startsWith("de") ? "de" : "en"));
const labels = computed(() => copy[locale.value]);
const origin = computed(() => String(theme.value.docsUrl || "").replace(/\/+$/u, ""));
const feedUrl = computed(() => `${origin.value}${labels.value.path}`);
</script>

<template>
  <aside class="subscribe">
    <p class="subscribe-heading">{{ labels.heading }}</p>
    <p class="subscribe-lead">{{ labels.lead }}</p>
    <p class="subscribe-how">{{ labels.how }}</p>
    <p class="subscribe-url">
      <code>{{ feedUrl }}</code>
    </p>
    <p class="subscribe-open">
      <a :href="labels.path">{{ labels.open }}</a>
    </p>
  </aside>
</template>

<style scoped>
.subscribe {
  margin: 40px 0;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 20px 24px;
  background: var(--vp-c-bg-soft);
}

.subscribe-heading {
  margin: 0;
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.subscribe-lead,
.subscribe-how {
  margin: 8px 0 0;
  color: var(--vp-c-text-2);
  font-size: 14px;
  line-height: 1.6;
}

.subscribe-url {
  margin: 12px 0 0;
  overflow-x: auto;
  max-width: 100%;
}

.subscribe-url code {
  font-size: 13px;
  white-space: nowrap;
}

.subscribe-open {
  margin: 12px 0 0;
  font-size: 14px;
}
</style>
