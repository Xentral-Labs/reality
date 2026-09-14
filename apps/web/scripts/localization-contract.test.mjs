import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { pathToFileURL } from "node:url";

import ts from "typescript";

const frontendRoot = path.resolve(import.meta.dirname, "..");

async function loadCore() {
  const source = fs.readFileSync(path.join(frontendRoot, "src", "localization-core.ts"), "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ES2022, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const target = path.join(frontendRoot, ".localization-core.test.mjs");
  fs.writeFileSync(target, output);
  try {
    return await import(`${pathToFileURL(target).href}?v=${Date.now()}`);
  } finally {
    fs.unlinkSync(target);
  }
}

test("falls back to readable canonical English for missing or blank entries", async () => {
  const { resolveTranslation } = await loadCore();
  const catalogs = { de: { Save: "Speichern", Blank: " " }, nl: {}, es: {} };
  assert.equal(resolveTranslation(catalogs, "de", "Save"), "Speichern");
  assert.equal(resolveTranslation(catalogs, "nl", "Save"), "Save");
  assert.equal(resolveTranslation(catalogs, "de", "Blank"), "Blank");
  assert.equal(resolveTranslation(catalogs, "en", "Save"), "Save");
});

test("changing language preserves locale and timezone preferences", async () => {
  const { selectLanguage } = await loadCore();
  assert.deepEqual(
    selectLanguage({ language: "en", locale: "de-DE", timezone: "Europe/Berlin" }, "es"),
    { language: "es", locale: "de-DE", timezone: "Europe/Berlin" },
  );
});

test("the DOM boundary recognizes original content and trace containers", async () => {
  const { isOriginalContent } = await loadCore();
  const original = {
    closest: (selector) => (selector.includes('data-localization="original"') ? original : null),
  };
  const regular = { closest: () => null };
  assert.equal(isOriginalContent(original), true);
  assert.equal(isOriginalContent(regular), false);
  assert.equal(isOriginalContent(null), false);
});

test("public authentication keeps a supported landing-page language", async () => {
  const { resolvePublicLanguage } = await loadCore();
  assert.equal(resolvePublicLanguage("?lang=es", "de"), "es");
  assert.equal(resolvePublicLanguage("", "nl"), "nl");
  assert.equal(resolvePublicLanguage("?lang=unsupported", "de"), "de");
  assert.equal(resolvePublicLanguage("", null), "en");
});

test("reverse lookup preserves every real catalog value and first-match collisions", async () => {
  const { parseCatalogs } = await import("./i18n-audit-lib.mjs");
  const { createCanonicalSourceResolver } = await loadCore();
  const catalogs = Object.fromEntries(
    Object.entries(parseCatalogs(path.join(frontendRoot, "src", "localization.tsx"))).map(
      ([language, entries]) => [language, Object.fromEntries(entries)],
    ),
  );
  const previous = (value) => {
    for (const dictionary of Object.values(catalogs)) {
      const entry = Object.entries(dictionary).find(([, translated]) => translated === value);
      if (entry) return entry[0];
    }
    return value;
  };
  const resolve = createCanonicalSourceResolver(catalogs);
  const values = new Set([
    "",
    "  ",
    "untranslated-business-value-154",
    "__proto__",
    ...Object.values(catalogs).flatMap(Object.values),
  ]);
  for (const value of values) assert.equal(resolve(value), previous(value), value);
  const collision = createCanonicalSourceResolver({
    de: { First: "shared", Second: "shared", Blank: "" },
    nl: { Third: "shared" },
    es: {},
  });
  assert.equal(collision("shared"), "First");
  assert.equal(collision(""), "Blank");
  assert.equal(collision("First"), "First");
});

test("reverse lookup waits for initialization and never rescans for business values", async () => {
  const { createCanonicalSourceResolver } = await loadCore();
  let traversals = 0;
  const catalog = new Proxy(
    { Save: "Speichern" },
    {
      ownKeys(target) {
        traversals += 1;
        return Reflect.ownKeys(target);
      },
    },
  );
  const resolve = createCanonicalSourceResolver({ de: catalog, nl: {}, es: {} });
  assert.equal(traversals, 0);
  catalog.Late = "Spät";
  assert.equal(resolve("Spät"), "Late");
  const initial = traversals;
  assert.ok(initial > 0);
  for (let i = 0; i < 10000; i += 1) {
    assert.equal(resolve(`business-value-${i}`), `business-value-${i}`);
    assert.equal(resolve("Speichern"), "Save");
  }
  assert.equal(traversals, initial);
});
