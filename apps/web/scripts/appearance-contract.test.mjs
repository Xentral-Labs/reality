import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import test from "node:test";

const src = new URL("../src/", import.meta.url);
const read = (name) => readFileSync(new URL(name, src), "utf8");
const stylesheets = readdirSync(src).filter((name) => name.endsWith(".css"));

const tailwind = read("tailwind.css");
const block = (selector) => {
  const match = tailwind.match(new RegExp(`${selector}\\s*\\{([\\s\\S]*?)\\n\\}`));
  assert.ok(match, `missing_block:${selector}`);
  return match[1];
};
const tokens = (body) =>
  Object.fromEntries(
    [...body.matchAll(/--([a-z-]+):\s*(#[0-9a-fA-F]{3,8});/g)].map((m) => [m[1], m[2]]),
  );

const light = tokens(block(":root"));
const dark = tokens(block('\\[data-theme="dark"\\]'));

// FR-006: one vocabulary, defined for both appearances.
test("every semantic token is defined in both appearances", () => {
  for (const name of Object.keys(light)) {
    assert.ok(name in dark, `token_missing_in_dark:${name}`);
  }
  assert.ok(Object.keys(light).length >= 20, "token_vocabulary_too_small");
});

// DR-004: the bug this contract exists for. A second declaration of a shared
// variable silently shadows the first and pins it to one appearance.
test("shared variables are declared exactly once", () => {
  for (const name of ["brand", "brand-soft", "border", "muted", "quiet"]) {
    const declarations = stylesheets.flatMap((file) =>
      [...read(file).matchAll(new RegExp(`^\\s*--${name}:`, "gm"))].map(() => file),
    );
    assert.equal(
      declarations.length,
      1,
      `shadowed_variable:--${name} declared in ${declarations.join(", ")}`,
    );
  }
});

// FR-006: a single-theme scale must not carry a colour that has to switch.
test("no single-theme scale carries a theme colour", () => {
  const rules = tailwind.slice(tailwind.indexOf("@theme inline"));
  const utilities = [...rules.matchAll(/@apply([^;]*);/g)].map((m) => m[1]).join(" ");
  const stuck = utilities.match(
    /\b(?:[a-z-]+:)?(?:bg|text|border|divide|placeholder)-(?:white|gray|slate|zinc|neutral|stone|indigo)-?[0-9]*\b/g,
  );
  // The modal scrim stays dark on either ground and is the one allowed case.
  assert.deepEqual([...new Set(stuck ?? [])], ["bg-gray-950"]);

  for (const file of stylesheets) {
    const leaked = read(file).match(
      /(?:color|background|fill|stroke|border-color):\s*var\(--color-gray-/g,
    );
    assert.equal(leaked, null, `single_theme_scale_in:${file}`);
  }
});

// FR-008 and FR-005: the browser is told, and the answer arrives before paint.
test("appearance is declared to the browser and resolved before first paint", () => {
  assert.match(block(":root"), /color-scheme:\s*light/);
  assert.match(block('\\[data-theme="dark"\\]'), /color-scheme:\s*dark/);
  const main = read("main.tsx");
  assert.ok(
    main.indexOf("applyTheme(") < main.indexOf("createRoot("),
    "theme_resolved_after_first_paint",
  );
});

// DR-005: dark is held to the standard, over the pairings actually composed.
test("dark meets AA on every foreground and ground the stylesheets compose", () => {
  const channel = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  const luminance = (hex) => {
    const [r, g, b] = [1, 3, 5].map((i) => channel(parseInt(hex.slice(i, i + 2), 16) / 255));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const contrast = (a, b) => {
    const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (hi + 0.05) / (lo + 0.05);
  };

  const foregrounds = {
    "fg-strong": "text-strong",
    "fg-default": "text-default",
    "fg-secondary": "text-secondary",
    "fg-muted": "text-muted",
    "fg-quiet": "text-quiet",
    accent: "accent",
    "positive-text": "positive-text",
    "caution-text": "caution-text",
    "critical-text": "critical-text",
  };
  const grounds = [
    "surface",
    "surface-muted",
    "surface-sunken",
    "bg",
    "accent-soft",
    "positive-bg",
    "caution-bg",
    "critical-bg",
  ];

  let checked = 0;
  for (const [, rule] of tailwind.matchAll(/@apply([^;]*);/g)) {
    for (const [utility, token] of Object.entries(foregrounds)) {
      if (!new RegExp(`\\btext-${utility}\\b`).test(rule)) continue;
      for (const ground of grounds) {
        if (!new RegExp(`\\bbg-${ground}\\b`).test(rule)) continue;
        const ratio = contrast(dark[token], dark[ground]);
        assert.ok(ratio >= 4.5, `dark_below_aa:${utility}_on_${ground}=${ratio.toFixed(2)}`);
        checked += 1;
      }
    }
  }
  assert.ok(checked >= 20, `too_few_pairs_checked:${checked}`);
});
