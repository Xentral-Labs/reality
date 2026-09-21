import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../src/", import.meta.url);
const source = (path) => readFile(new URL(path, root), "utf8");

test("an open customer invoice exposes a confirmed dunning flow with a manual fee", async () => {
  const [page, dialog] = await Promise.all([
    source("unified/FinancePage.tsx"),
    source("finance/DunningNotice.tsx"),
  ]);
  assert.match(page, /row\.document_type === "sales_invoice"/);
  assert.match(page, /setDunningInvoice\(row\.document_id\)/);
  assert.match(dialog, /name="fee"/);
  assert.match(dialog, /finance\.dunning\.record/);
  assert.match(dialog, /change-proposals\/\$\{pending\.id\}/);
  assert.match(dialog, /No email is sent automatically/);
});
