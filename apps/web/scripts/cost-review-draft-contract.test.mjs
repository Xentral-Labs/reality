import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parseCatalogs } from "./i18n-audit-lib.mjs";

// Spec 282: the review dialog shows the draft in words and proposes only through the
// endpoint that re-drafts on the server; the browser never assembles review arguments.
const source = (name) => readFile(new URL(`../src/${name}`, import.meta.url), "utf8");

test("the dialog proposes through the draft endpoint only", async () => {
  const dialog = await source("unified/CostReviewDraftDialog.tsx");
  assert.match(dialog, /api\s*\.costReviewDraft\(/);
  assert.match(dialog, /api\.proposeCostReview\(/);
  assert.doesNotMatch(dialog, /createChangeProposal|cost\.change|cost_change_propose/);
  // What it sends is the scope, the draft's sequence and the answers, nothing else.
  assert.match(dialog, /event_sequence: draft\.event_sequence,\s*answers,/);
  // A drifted draft is re-drafted and explained, never proposed.
  assert.match(dialog, /reason\.code === "draft_changed"/);
});

test("identifiers stay inside the collapsed system details", async () => {
  const dialog = await source("unified/CostReviewDraftDialog.tsx");
  const beforeDetails = dialog.slice(0, dialog.indexOf("data-draft-system-details"));
  assert.doesNotMatch(beforeDetails, /\{draft\.arguments|\{draft\.basis|scope_id\}/);
  assert.match(dialog, /reasonText\(catalog, entry\.code\)/);
});

test("the review step opens the dialog for the host's cost scope", async () => {
  const guidance = await source("unified/ResolutionGuidance.tsx");
  assert.match(guidance, /action\.path === "review_draft" && openDraft/);
  assert.match(guidance, /<CostReviewDraftDialog/);
  const panel = await source("unified/CostExplanation.tsx");
  assert.match(
    panel,
    /scope=\{\{ kind: envelope\.requested\.kind, id: envelope\.requested\.scope_id \}\}/,
  );
});

test("the opening stock form states the total value with its evidence", async () => {
  const form = await source("unified/OpeningStockCard.tsx");
  assert.match(form, /opening_cost: \{\s*amount: costAmount\.trim\(\),/);
  assert.match(form, /required=\{!!costAmount\.trim\(\)\}/);
  // Never a unit price times quantity: the form sends the stated total only.
  assert.doesNotMatch(form, /costAmount[^\n]*\*|\*[^\n]*costAmount/);
});

test("labels from the dialog's lookup tables are translated", async () => {
  const dialog = await source("unified/CostReviewDraftDialog.tsx");
  const labels = [...dialog.matchAll(/^\s+[a-z_]+: "([^"]+)",$/gmu)].map((match) => match[1]);
  assert.ok(labels.length >= 9, `found ${labels.length}`);
  const catalogs = parseCatalogs(
    fileURLToPath(new URL("../src/localization.tsx", import.meta.url)),
  );
  for (const language of ["de", "nl", "es"])
    assert.deepEqual(
      labels.filter((label) => !catalogs[language].get(label)?.trim()),
      [],
      language,
    );
});
