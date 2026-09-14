import { test } from "node:test";
import assert from "node:assert/strict";
import { resumeStage, latestDraft, usesWizard } from "../src/unified/ruleWizardState.ts";
const gap = (destination = null, rules = []) => ({ gap: { destination }, entries: [], rules });
test("resume uses saved milestones and never assumes a draft has been tested", () => {
  assert.equal(resumeStage(null), 0);
  assert.equal(resumeStage(gap()), 1);
  assert.equal(resumeStage(gap("source_only")), 1);
  assert.equal(resumeStage(gap("fact")), 2);
  assert.equal(resumeStage(gap("fact", [{ id: "r", version: 1, status: "draft" }])), 3);
});
test("only never-activated setup uses wizard; highest draft version is selected", () => {
  assert.equal(usesWizard([]), true);
  assert.equal(usesWizard(["draft"]), true);
  assert.equal(usesWizard(["active", "draft"]), false);
  assert.equal(usesWizard(["disabled"]), false);
  const versions = [
    { id: "new", version: 3, status: "draft" },
    { id: "old", version: 1, status: "draft" },
  ];
  assert.equal(latestDraft(gap("fact", versions)).id, "new");
  assert.equal(versions[0].id, "new");
});
