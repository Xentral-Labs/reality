import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("fee claims expose payment but not reduction or renewed dunning actions", async () => {
  const page = await readFile(new URL("../src/unified/FinancePage.tsx", import.meta.url), "utf8");
  const payment = page
    .split('{t("Record payment and allocation")}')[0]
    .split("canAcceptReduction &&")
    .at(-1);
  for (const kind of ["dunning_fee_charge", "payment_return_fee_charge"])
    assert.ok(payment.includes(`"${kind}"`));
  const reduction = page
    .split('{t("Accept settlement reduction")}')[0]
    .split("canAcceptReduction &&")
    .at(-1);
  assert.ok(!reduction.includes("fee_charge"));
  assert.match(page, /row\.document_type === "sales_invoice"[\s\S]*?Create dunning notice/);
});

test("the payment form respects service-provided reduction eligibility", async () => {
  const flow = await readFile(
    new URL("../src/finance/SettlementFlow.tsx", import.meta.url),
    "utf8",
  );
  assert.match(flow, /reduction_allowed\?: boolean;/);
  assert.match(flow, /data\.reduction_allowed !== false &&/);
});
