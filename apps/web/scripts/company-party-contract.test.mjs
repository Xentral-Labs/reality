import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

// Spec 289: the draft offers recording the company as its own business partner.
const dialog = readFileSync(
  new URL("../src/unified/CostReviewDraftDialog.tsx", import.meta.url),
  "utf8",
);
const api = readFileSync(new URL("../src/api.ts", import.meta.url), "utf8");

test("the button proposes through the shared prepare route without a name", () => {
  const prepare = api.match(/prepareCompanyParty:[\s\S]*?\),\n/)?.[0] || "";
  assert.match(prepare, /\/company-party\/prepare/);
  assert.match(prepare, /method: "POST"/);
  // FR-004/DR-003: the server names the partner; the client never sends a name.
  assert.doesNotMatch(prepare, /body:/);
  assert.match(dialog, /api\.prepareCompanyParty\(tenant\)/);
  assert.match(dialog, /t\("Record my company as a business partner"\)/);
});

test("a waiting proposal is named instead of offering another", () => {
  assert.match(dialog, /entry\.proposal_id/);
  assert.match(dialog, /\/app\/decisions\?/);
  assert.match(dialog, /data-company-party-action/);
});
