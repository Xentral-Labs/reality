import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parseCatalogs } from "./i18n-audit-lib.mjs";

const discovery = JSON.parse(
  fs.readFileSync(
    new URL("../../../packages/reality-core/config/action_discovery.json", import.meta.url),
    "utf8",
  ),
);
const catalogs = parseCatalogs(fileURLToPath(new URL("../src/localization.tsx", import.meta.url)));
const labels = [
  ...new Set([
    ...discovery.categories.flatMap((category) => [
      category.label,
      ...category.groups.map((group) => group.label),
    ]),
    ...discovery.entries.map((entry) => entry.label),
  ]),
];
for (const language of ["de", "nl", "es"])
  test(`dynamic action discovery labels have ${language} translations`, () => {
    assert.deepEqual(
      labels.filter((label) => !catalogs[language].get(label)?.trim()),
      [],
    );
  });
