<script setup lang="ts">
import { computed } from "vue";
import { useData } from "vitepress";

const { frontmatter, lang } = useData();

const locale = computed(() => (lang.value.startsWith("de") ? "de" : "en"));
const byLabel = computed(() => (locale.value === "de" ? "von" : "by"));

const isoDate = computed(() => new Date(frontmatter.value.date).toISOString());

const displayDate = computed(() =>
  new Intl.DateTimeFormat(locale.value === "de" ? "de-DE" : "en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(frontmatter.value.date)),
);

const tags = computed<string[]>(() => frontmatter.value.tags || []);
</script>

<template>
  <p class="post-meta">
    <time :datetime="isoDate">{{ displayDate }}</time>
    <span v-if="frontmatter.author"> · {{ byLabel }} {{ frontmatter.author }}</span>
    <span v-for="tag in tags" :key="tag" class="post-meta-tag">{{ tag }}</span>
  </p>
</template>

<style scoped>
.post-meta {
  margin: -8px 0 32px;
  color: var(--vp-c-text-2);
  font-size: 13px;
}

.post-meta-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: 10px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-size: 12px;
}
</style>
