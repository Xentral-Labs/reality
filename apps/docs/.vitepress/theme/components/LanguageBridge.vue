<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, nextTick } from "vue";
import { useData, useRoute } from "vitepress";
import {
  languageHref,
  readLanguage,
  rememberLanguage,
  validLanguage,
} from "../../../../shared/language";

const { theme } = useData();
const route = useRoute();
let previousLocale: string | undefined;
let observer: MutationObserver | undefined;
const pageLocale = () => (location.pathname.startsWith("/de/") ? "de" : "en");
function updateLinks() {
  const preference = readLanguage() ?? pageLocale();
  const origins = [theme.value.productUrl, theme.value.websiteUrl]
    .filter(Boolean)
    .map((href: string) => new URL(href).origin);
  for (const anchor of document.querySelectorAll<HTMLAnchorElement>("a[href]")) {
    const target = new URL(anchor.href);
    if (origins.includes(target.origin)) {
      anchor.href = languageHref(anchor.href, preference);
    } else if (target.origin === location.origin && !target.pathname.match(/\.[a-z0-9]+$/i)) {
      const targetLocale = target.pathname.startsWith("/de/") ? "de" : "en";
      const selection = anchor.closest(".VPNavBarTranslations, .VPNavScreenTranslations")
        ? targetLocale
        : preference;
      anchor.href = languageHref(anchor.href, selection, true);
    }
  }
}
onMounted(() => {
  const explicit = validLanguage(new URLSearchParams(location.search).get("lang"));
  const preference = explicit ?? (pageLocale() === "de" ? "de" : readLanguage()) ?? "en";
  if (explicit) rememberLanguage(preference);
  const destination = new URL(languageHref(location.href, preference, true));
  if (destination.pathname !== location.pathname) {
    location.replace(destination.href);
    return;
  }
  previousLocale = pageLocale();
  updateLinks();
  observer = new MutationObserver(updateLinks);
  observer.observe(document.body, { childList: true, subtree: true });
});
watch(
  () => route.path,
  async () => {
    if (!previousLocale) return;
    await nextTick();
    const current = pageLocale();
    if (
      current !== previousLocale &&
      !validLanguage(new URLSearchParams(location.search).get("lang"))
    )
      rememberLanguage(current);
    previousLocale = current;
    updateLinks();
  },
);
onBeforeUnmount(() => observer?.disconnect());
</script>

<template><span hidden aria-hidden="true"></span></template>
