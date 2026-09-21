import { test } from "node:test";
import assert from "node:assert/strict";
import { reference } from "./action-discovery-fixture.mjs";
import {
  directoryEntries,
  groupDirectory,
  menuEntries,
  formKeys,
} from "../src/unified/actionDiscovery.ts";
const entries = directoryEntries(reference);
test("all catalog identities occur once and share reviewed categories", () => {
  assert.equal(entries.length, reference.commands.length + 13);
  assert.equal(new Set(entries.map((e) => e.id)).size, entries.length);
  assert.ok(entries.every((e) => e.group !== "unclassified"));
  const reserve = entries.filter((e) => e.command === "reserve");
  assert.equal(reserve.length, 2);
  assert.ok(reserve.every((e) => e.group === "reservations"));
});
test("search reveals exact hidden command, category descendants, and translated labels", () => {
  const all = groupDirectory(reference, entries, "", (s) => s);
  const hit = groupDirectory(reference, entries, "state_lot_expiry", (s) => s);
  assert.equal(hit.length, 1);
  assert.equal(hit[0].groups[0].entries[0].command, "state_lot_expiry");
  assert.ok(groupDirectory(reference, entries, "Warehouse", (s) => s)[0].groups.length >= 3);
  assert.equal(groupDirectory(reference, entries, "never-found-8490", (s) => s).length, 0);
  assert.deepEqual(
    groupDirectory(reference, entries, "", (s) => s),
    all,
  );
  assert.equal(
    groupDirectory(reference, entries, "Lager", (s) => (s === "Warehouse" ? "Lager" : s))[0].key,
    "warehouse",
  );
});
test("unknown future capabilities stay visible", () => {
  const next = {
    ...reference,
    commands: [...reference.commands, { service: "future", name: "Future", mode: "read" }],
  };
  assert.equal(directoryEntries(next).at(-1).group, "unclassified");
  assert.ok(
    groupDirectory(next, directoryEntries(next), "future", (s) => s).some(
      (c) => c.key === "unclassified",
    ),
  );
});
test("every supported form is registered and Warehouse placement is specific", () => {
  assert.deepEqual(
    reference.discovery.entries
      .filter((e) => e.form)
      .map((e) => e.form)
      .sort(),
    [...formKeys].sort(),
  );
  assert.deepEqual(
    menuEntries(reference, "global")
      .filter((e) => e.form)
      .map((e) => e.form)
      .sort(),
    [...formKeys].sort(),
  );
  const forms = (c) => menuEntries(reference, c).map((e) => e.form);
  assert.deepEqual(forms("warehouse.stock"), []);
  assert.deepEqual(forms("warehouse.reservations"), ["reserve", "reservation_release"]);
  assert.deepEqual(forms("warehouse.movements"), [
    "opening_stock",
    "receipt",
    "movement_create",
    "return_disposition",
    "shipment_dispatch",
    "shipment_receive",
    "movement_correct",
  ]);
});
test("Finance context never offers customer-only actions to suppliers", () => {
  for (const flow of ["payable", "supplier-balance"])
    for (const tab of ["open-items", "payments", "journal"]) {
      const forms = menuEntries(reference, `finance.${tab}.${flow}`).map((e) => e.form);
      assert.ok(!forms.includes("sales_credit_record"));
      assert.ok(!forms.includes("customer_refund_post"));
      assert.ok(!forms.includes("customer_payment_post"));
      if (tab === "journal") assert.deepEqual(forms, ["ledger_reverse"]);
    }
});
test("management entries honor owner and demo visibility and unknown handlers never launch", () => {
  const entries = menuEntries(reference, "global", { owner: false, demo: false });
  assert.ok(
    !entries.some((e) =>
      ["navigate_members", "navigate_accounts", "navigate_demo"].includes(e.key),
    ),
  );
  const broken = structuredClone(reference);
  broken.discovery.entries.push({
    key: "unknown",
    label: "unknown",
    form: "unknown",
    command: "reserve",
    placements: ["global"],
  });
  assert.ok(!menuEntries(broken, "global").some((e) => e.key === "unknown"));
});

test("explicit payment direction selects the correct payment form context", async () => {
  const { financeContext } = await import("../src/unified/actionDiscovery.ts");
  assert.equal(
    financeContext({ financeView: "payments", flow: "receivable", direction: "outgoing" }),
    "finance.payments.payable",
  );
  assert.equal(
    financeContext({ financeView: "payments", flow: "payable", direction: "incoming" }),
    "finance.payments.receivable",
  );
  assert.equal(
    financeContext({ financeView: "open-items", flow: "payable", direction: "incoming" }),
    "finance.open-items.payable",
  );
});
