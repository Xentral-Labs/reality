<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { sourceExcerpt, type LogicSource } from "../../../../shared/businessBlueprint";
const props = defineProps<{
  source: LogicSource;
  ranges: { start: number; end: number }[];
  language?: string;
}>();
const full = ref(false);
const code = ref<HTMLElement | null>(null);
const excerpt = computed(() => sourceExcerpt(props.source, props.ranges, full.value));
const wording = (en: string, de: string) => (props.language === "de" ? de : en);
async function toggle() {
  full.value = !full.value;
  await nextTick();
  if (full.value) {
    const focus = code.value?.querySelector<HTMLElement>("[data-source-highlight]");
    if (focus && code.value)
      code.value.scrollTop = Math.max(
        0,
        focus.getBoundingClientRect().top -
          code.value.getBoundingClientRect().top +
          code.value.scrollTop -
          40,
      );
  }
}
</script>
<template>
  <div class="source-evidence">
    <p class="source-location">{{ source.path }} · {{ source.function }}</p>
    <p class="source-caption">
      {{
        excerpt.focusAvailable
          ? wording(
              "Highlighted lines identify the cited source location.",
              "Markierte Zeilen zeigen die zitierte Quellstelle.",
            )
          : wording(
              "No exact line reference is available for this source.",
              "Für diesen Quelltext liegt kein genauer Zeilenverweis vor.",
            )
      }}
    </p>
    <button type="button" :aria-pressed="full" @click="toggle">
      {{
        full
          ? wording("Show excerpt", "Ausschnitt anzeigen")
          : wording("Full function", "Ganze Funktion anzeigen")
      }}
    </button>
    <pre
      ref="code"
      :aria-label="
        wording(
          'Source code with referenced lines highlighted',
          'Quellcode mit markierten Bezugszeilen',
        )
      "
    ><code><span v-for="line in excerpt.lines" :key="line.number" class="source-line" :class="{ highlighted: line.highlighted }" :data-source-highlight="line.highlighted ? '' : undefined"><span class="line-number" aria-hidden="true">{{ line.number }}</span><span class="line-text">{{ line.text || ' ' }}</span></span></code></pre>
  </div>
</template>
<style scoped>
.source-evidence {
  margin-top: 12px;
  min-width: 0;
}
.source-location {
  font-size: 12px;
  overflow-wrap: anywhere;
  margin: 8px 0;
}
.source-caption {
  color: var(--vp-c-text-2);
  font-size: 12px;
  margin: 6px 0;
}
button {
  border: 1px solid var(--vp-c-divider);
  border-radius: 5px;
  padding: 4px 9px;
  font-size: 12px;
}
pre {
  position: relative;
  max-height: 360px;
  overflow: auto;
  padding: 8px 0;
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  background: var(--vp-c-bg-soft);
  white-space: pre;
  font-size: 12px;
  line-height: 1.65;
}
.source-line {
  display: flex;
  min-width: max-content;
}
.highlighted {
  background: var(--vp-c-brand-soft);
  box-shadow: inset 3px 0 var(--vp-c-brand-1);
}
.line-number {
  flex: 0 0 56px;
  text-align: right;
  padding: 0 12px;
  color: var(--vp-c-text-2);
  user-select: none;
}
.line-text {
  padding-right: 14px;
}
</style>
