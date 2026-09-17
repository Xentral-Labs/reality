import { test } from "node:test";
import assert from "node:assert/strict";
import { filterCapabilities } from "../src/unified/toolCatalogEntries.ts";
const rows = [
  {
    id: "reserve",
    title: "Reserve stock",
    topic: "stock",
    purpose: "change",
    mcp: ["reservation_propose"],
    commands: ["reserve"],
    description: "",
    labels: { de: "Bestand reservieren" },
  },
  {
    id: "inventory",
    title: "Stock overview",
    topic: "stock",
    purpose: "read",
    mcp: ["inventory_read"],
    commands: [],
    description: "",
    labels: {},
  },
];
test("capability search combines translated and technical names with independent filters", () => {
  assert.equal(
    filterCapabilities(rows, "reservieren", "stock", "change", (x) => x, "de").length,
    1,
  );
  assert.equal(
    filterCapabilities(rows, "inventory_read", "", "read", (x) => x, "en")[0].id,
    "inventory",
  );
  assert.equal(filterCapabilities(rows, "reserve", "stock", "read", (x) => x, "en").length, 0);
  assert.equal(filterCapabilities(rows, "", "payments", "", (x) => x, "en").length, 0);
});
