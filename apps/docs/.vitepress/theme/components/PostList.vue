<script setup lang="ts">
import { computed } from "vue";
import { useData } from "vitepress";
import { data as allPosts, type PostLocale } from "../posts.data.mjs";

const copy: Record<PostLocale, { empty: string; by: string }> = {
  en: {
    empty: "No articles published yet.",
    by: "by",
  },
  de: {
    empty: "Noch keine Beiträge veröffentlicht.",
    by: "von",
  },
};

const { lang } = useData();
const locale = computed<PostLocale>(() => (lang.value.startsWith("de") ? "de" : "en"));
const labels = computed(() => copy[locale.value]);
const posts = computed(() => allPosts.filter((post) => post.locale === locale.value));
</script>

<template>
  <p v-if="posts.length === 0" class="post-list-empty">{{ labels.empty }}</p>

  <ul v-else class="post-list">
    <li v-for="post in posts" :key="post.url" class="post-list-item">
      <p class="post-list-meta">
        <time :datetime="post.date">{{ post.displayDate }}</time>
        <span v-if="post.author"> · {{ labels.by }} {{ post.author }}</span>
        <span v-for="tag in post.tags" :key="tag" class="post-list-tag">{{ tag }}</span>
      </p>
      <h3 class="post-list-title">
        <a :href="post.url">{{ post.title }}</a>
      </h3>
      <p class="post-list-description">{{ post.description }}</p>
    </li>
  </ul>
</template>

<style scoped>
.post-list {
  list-style: none;
  margin: 24px 0 0;
  padding: 0;
}

.post-list-item {
  border-top: 1px solid var(--vp-c-divider);
  padding: 24px 0;
}

.post-list-meta {
  margin: 0;
  color: var(--vp-c-text-2);
  font-size: 13px;
}

.post-list-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: 10px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-size: 12px;
}

.post-list-title {
  margin: 6px 0 0;
  border: 0;
  padding: 0;
  font-size: 20px;
  line-height: 1.4;
  letter-spacing: -0.02em;
}

.post-list-title a {
  color: var(--vp-c-text-1);
  font-weight: 600;
  text-decoration: none;
}

.post-list-title a:hover {
  color: var(--vp-c-brand-1);
}

.post-list-description {
  margin: 6px 0 0;
  color: var(--vp-c-text-2);
  max-width: 100%;
}

.post-list-empty {
  color: var(--vp-c-text-2);
}
</style>
