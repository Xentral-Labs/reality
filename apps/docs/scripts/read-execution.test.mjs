import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const model = JSON.parse(
  fs.readFileSync(new URL("../.vitepress/data/tool-usage.json", import.meta.url)),
);
const entry = (id) => model.entries.find((row) => row.id === id);

test("every catalog read describes its actual execution mode", () => {
  for (const row of model.entries.filter(
    (e) => ["view", "projection"].includes(e.kind) || (e.kind === "tool" && e.access === "read"),
  )) {
    assert.ok(row.read_modes?.length, row.id);
    for (const read of row.read_modes) {
      assert.ok(read.query, row.id);
      assert.ok(model.read_mode_definitions[read.mode], row.id);
    }
  }
  assert.equal(entry("projection:price_resolution").read_modes[0].mode, "parameterized");
  assert.equal(
    model.entries.filter((e) => e.kind === "projection" && e.read_modes[0].mode === "stored")
      .length,
    12,
  );
});

test("inventory modes follow the adapter and response format, not the business name", () => {
  const inventory = entry("tool:inventory_read");
  assert.equal(
    inventory.read_modes.find((r) => r.query.includes("response_format=page")).mode,
    "live",
  );
  assert.equal(
    inventory.read_modes.find((r) => r.query.includes("response_format=legacy")).mode,
    "stored",
  );
  assert.equal(inventory.read_modes.find((r) => r.default).mode, "live");
  assert.equal(
    entry("view:inventory").read_modes.find((r) => r.query.includes("/warehouse/stock")).mode,
    "live",
  );
  assert.equal(
    entry("view:inventory").read_modes.find((r) => r.query.includes("/projection-snapshots/")).mode,
    "stored",
  );
  assert.ok(entry("tool:business_records_discover").read_modes.every((r) => r.mode === "live"));
  const openItems = entry("view:open_items").read_modes;
  assert.equal(openItems.find((r) => r.query.includes("flow=receivable")).mode, "stored");
  assert.equal(openItems.find((r) => r.query.includes("flow=customer-credit")).mode, "live");
  assert.equal(entry("view:payments").read_modes[0].mode, "live");
  assert.equal(entry("projection:payments").read_modes[0].mode, "stored");
});

test("both published languages explain modes, freshness and concrete query variants", () => {
  for (const language of ["en", "de"]) {
    const prefix = language === "de" ? "de/" : "";
    const views = fs.readFileSync(
      new URL(`../content/${prefix}tool-usage/views.md`, import.meta.url),
      "utf8",
    );
    const commands = fs.readFileSync(
      new URL(`../content/${prefix}tool-usage/commands.md`, import.meta.url),
      "utf8",
    );
    for (const definition of Object.values(model.read_mode_definitions)) {
      assert.ok(views.includes(definition.label[language]));
      assert.ok(views.replace(/\s+/gu, " ").includes(definition.description[language]));
    }
    for (const state of ["uninitialized", "pending", "failed", "ready"])
      assert.ok(views.includes(state));
    assert.ok(commands.includes("response_format=legacy"));
    assert.ok(commands.includes("response_format=page"));
    assert.ok(views.includes("/warehouse/stock"));
  }
});
