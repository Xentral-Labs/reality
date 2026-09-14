<script setup lang="ts">
import { languageHref } from "../../../../shared/language";
import { useData } from "vitepress";
const { theme, lang } = useData();
</script>

<template>
  <a
    :href="languageHref(theme.productUrl, lang.startsWith('de') ? 'de' : 'en')"
    target="_blank"
    rel="noopener noreferrer"
    ><slot>Reality</slot> ↗</a
  >
</template>
