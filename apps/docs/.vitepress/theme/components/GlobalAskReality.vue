<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch } from "vue";
import { useRoute } from "vitepress";

declare const __APP_URL__: string;

const route = useRoute();
const dedicatedQuestionRoutes = new Set([
  "/getting-started/business-journeys",
  "/getting-started/business-journey-chat",
  "/de/getting-started/business-journeys",
  "/de/getting-started/business-journey-chat",
]);
let stopWatching: (() => void) | undefined;

function normalizedPath() {
  return route.path.replace(/\/$/u, "") || "/";
}

function updateVisibility() {
  const widget = document.querySelector<HTMLElement>("reality-journey-chat");
  if (!widget) return;
  const isDedicatedQuestionRoute = dedicatedQuestionRoutes.has(normalizedPath());
  widget.hidden = isDedicatedQuestionRoute;
}

onMounted(() => {
  const existingWidget = document.querySelector<HTMLElement>("reality-journey-chat");
  if (existingWidget) {
    updateVisibility();
  } else {
    const script = document.createElement("script");
    script.src = "/journey-guide-widget/widget.js";
    script.async = true;
    script.dataset.apiUrl = __APP_URL__;
    script.dataset.locale = route.path.startsWith("/de/") ? "de" : "en";
    script.dataset.guideUrl = route.path.startsWith("/de/")
      ? "/de/getting-started/business-journeys"
      : "/getting-started/business-journeys";
    script.addEventListener("load", updateVisibility, { once: true });
    document.body.append(script);
  }

  stopWatching = watch(() => route.path, updateVisibility);
});

onBeforeUnmount(() => stopWatching?.());
</script>

<template><span hidden aria-hidden="true"></span></template>
