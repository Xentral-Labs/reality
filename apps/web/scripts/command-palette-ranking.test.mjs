import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { matchTier } from "../src/unified/commandPaletteRanking.ts";
const corpus = JSON.parse(
  readFileSync(
    new URL(
      "../../../packages/reality-core/tests/fixtures/global_search_matching.json",
      import.meta.url,
    ),
    "utf8",
  ),
);
for (const example of corpus)
  test(`shared matching: ${example.query}`, () =>
    assert.equal(matchTier(example.query, [example.label], example.references), example.tier));

const { comparePaletteEntries, palettePreview } =
  await import("../src/unified/commandPaletteRanking.ts");
test("raw references precede contextual metadata and each preview caps canonical groups", () => {
  const rows = Array.from({ length: 30 }, (_, i) => ({
    key: `item:${i}`,
    group: i % 2 ? "items_locations" : "orders",
    tier: 2,
    label: `Warehouse ${i}`,
  }));
  rows.push({ key: "item:exact", group: "items_locations", tier: 0, label: "ZZZ" });
  rows.sort(comparePaletteEntries);
  assert.equal(rows[0].key, "item:exact");
  const preview = palettePreview([...rows, ...rows]);
  assert.equal(preview.length, 8);
  assert.equal(new Set(preview.map((row) => row.key)).size, 8);
  assert.equal(preview.filter((row) => row.group === "orders").length, 4);
});

test("global preview caps at twelve across more than three populated groups", () => {
  const groups = ["partners", "items_locations", "orders", "finance", "shipping", "reports"];
  const rows = groups.flatMap((group) =>
    Array.from({ length: 8 }, (_, i) => ({
      key: `${group}:${i}`,
      group,
      label: `Result ${i}`,
      tier: 2,
    })),
  );
  const preview = palettePreview(rows);
  assert.equal(preview.length, 12);
  for (const group of groups) assert(preview.filter((row) => row.group === group).length <= 4);
});
