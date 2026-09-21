import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const guides = [
  new URL("../content/getting-started/demo-data.md", import.meta.url),
  new URL("../content/de/getting-started/demo-data.md", import.meta.url),
];

const requiredReferences = [
  "SO-005",
  "DEMO-14-2",
  "wrong-location",
  "shipment-cancelled-remainder",
  "COST-LATE-CLEANUP",
  "correction-original",
  "COST-A-SELLING",
  "COST-PORTFOLIO-SELLING",
  "atlas-execution",
  "normal-month",
  "Rotterdam Warehouse",
  "Singapore Warehouse",
];

const items = [
  "Summit Bottle",
  "Trail Lantern",
  "Ridge Backpack",
  "Cedar Desk Lamp",
  "Coast Storage Box",
  "Harbor Travel Mug",
  "Aurora Notebook",
  "Vista Monitor Stand",
  "Maple Serving Tray",
  "Orbit Cable Kit",
  "Meadow Picnic Set",
  "Beacon Desk Organizer",
  "Drift Cushion",
  "Cove Glass Set",
  "Meridian Fabric",
  "Alpine Wax Pellets",
  "Willow Batch Balm",
  "Atlas Field Scanner",
];

const parties = [
  "Northstar Outdoor",
  "Maple Retail",
  "Solstice Living",
  "Pacific Outfitters",
  "Brightwater Home",
  "Juniper Trading Co.",
  "Lakeside Provisions",
  "Fjord Outfitters",
  "Harlow Interiors",
  "Tidewater Sports",
  "Evergreen Studio",
  "Copperline Goods",
  "Granite Peak Gear",
  "Willow & Finch",
  "Northbridge Office Supply",
  "Blue Heron Living",
  "Marlow Home Goods",
  "Silverbirch Design",
  "Cascade Trail Company",
  "Amber Coast Retail",
  "Alpine Components",
  "Meridian Textiles",
  "Seabright Goods",
];

for (const guide of guides) {
  test(`${guide.pathname} inventories the canonical demo`, async () => {
    const content = await readFile(guide, "utf8");
    for (const expected of [...requiredReferences, ...items, ...parties]) {
      assert.ok(content.includes(expected), `missing ${expected}`);
    }
    assert.match(content, /91 %|91%/);
    assert.match(content, /zero to six|null bis sechs/);
    assert.match(content, /pageClass: demo-data-page/);
    assert.match(content, /<details class="demo-data-inventory">/);
    assert.doesNotMatch(content, /\| (Enthalten|Included)\s+\|/);
    assert.match(content, /### (Bewusste Lücken|Deliberate gaps)/);
  });
}

test("the demo catalog uses one compact responsive table grid", async () => {
  const styles = await readFile(new URL("../.vitepress/theme/custom.css", import.meta.url), "utf8");
  assert.match(styles, /\.demo-data-page \.vp-doc table/);
  assert.match(styles, /table:has\(th:nth-child\(3\):last-child\)/);
  assert.match(styles, /table:has\(th:nth-child\(4\):last-child\)/);
  assert.match(styles, /table:has\(th:nth-child\(5\):last-child\)/);
  assert.match(styles, /@media \(max-width: 959px\)/);
});
