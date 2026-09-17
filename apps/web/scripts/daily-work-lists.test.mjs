import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";
const source = (p) => readFileSync(new URL(p, import.meta.url), "utf8");
const load = async (p) =>
  import(
    "data:text/javascript;base64," +
      Buffer.from(
        ts.transpile(source(p), { module: ts.ModuleKind.ES2022, target: ts.ScriptTarget.ES2022 }),
      ).toString("base64")
  );
test("daily commitments preserve side across reload and cannot request history", async () => {
  const { readSelection, selectionUrl } = await load("../src/unified/routing.ts");
  const selection = readSelection(
    new URL(
      "https://example.test/app/orders-deliveries?tenant=one&orders_view=commitments&delivery_type=supplier_delivery&delivery_status=all",
    ),
  );
  assert.equal(selection.ordersView, "commitments");
  assert.equal(
    readSelection(new URL(selectionUrl(selection), "https://example.test")).deliveryType,
    "supplier_delivery",
  );
  const page = source("../src/unified/CommitmentsPage.tsx");
  assert.match(page, /"open"/);
  assert.match(page, /<RegisterHeader title="Commitments">[\s\S]*className="register-tabs"/);
  assert.doesNotMatch(page, /deliveryStatus|All delivery history|RegisterTable/);
});
test("incremental queue merge preserves identity without duplicate rows", async () => {
  const { mergeWorkRows } = await load("../src/unified/workRows.ts");
  assert.deepEqual(
    mergeWorkRows(
      [{ id: "a", v: 1 }],
      [
        { id: "a", v: 2 },
        { id: "b", v: 3 },
      ],
    ),
    [
      { id: "a", v: 2 },
      { id: "b", v: 3 },
    ],
  );
});
