import assert from "node:assert/strict";
import test from "node:test";
import { historyRecord, shortId } from "../src/unified/historyRows.ts";

const event = (context, extra = {}) => ({
  subject_type: "item",
  subject_id: "itm_2d4b700073",
  business_context: context,
  ...extra,
});

test("an item reads by its name and SKU, never by its id", () => {
  assert.deepEqual(historyRecord(event({ name: "Desk lamp", sku: "LAMP-1" })), {
    name: "Desk lamp · LAMP-1",
    kind: "item",
    id: "itm_2d4b700073",
  });
});

test("a party, an item on a line, or a reference names the record", () => {
  assert.equal(
    historyRecord(event({ party: "Müller GmbH" }, { subject_type: "commitment" })).name,
    "Müller GmbH",
  );
  assert.equal(
    historyRecord(
      event({ party: "Müller GmbH", item: "Desk lamp" }, { subject_type: "reservation" }),
    ).name,
    "Müller GmbH · Desk lamp",
  );
  assert.equal(
    historyRecord(event({ reference: "SO-1001" }, { subject_type: "document" })).name,
    "SO-1001",
  );
});

test("an item created from its SKU alone reads by the SKU", () => {
  // item.created carries the SKU, not the name.
  assert.equal(historyRecord(event({ sku: "LAMP-1" })).name, "LAMP-1");
});

test("without a known name, the kind and a short id stand in", () => {
  const record = historyRecord(event({}));
  assert.equal(record.name, null);
  assert.equal(shortId("itm_2d4b700073"), "itm_…0073");
  assert.equal(shortId("abc"), "abc");
});
