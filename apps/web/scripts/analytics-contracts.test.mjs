import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const source = (name) => readFileSync(new URL(`../src/${name}`, import.meta.url), "utf8");
test("analytics navigation preserves the existing overview and isolates tenant drafts", () => {
  const page = source("unified/AnalyticsPage.tsx");
  assert.match(page, /function AnalyticsOverview/);
  assert.match(page, /AnalyticsPreview/);
  assert.match(page, /key=\{selection.tenant\}/);
  assert.match(source("unified/routing.ts"), /analytics_view/);
});
test("displayed results are tied to executed definitions and cancellation rejects stale responses", () => {
  const hook = source("unified/analytics/useAnalyticsExecution.ts");
  assert.match(hook, /current === generation.current/);
  assert.match(hook, /AbortController/);
  const explorer = source("unified/analytics/AnalyticsExplorer.tsx");
  assert.match(explorer, /result.executed_definition/);
  assert.match(explorer, /analyticsApi.export/);
});
test("private agent changes show their owner-only definition before explicit confirmation", () => {
  const proposal = source("unified/analytics/AnalyticsReportProposal.tsx");
  assert.match(proposal, /analyticsApi\.proposal/);
  assert.match(proposal, /proposal\.name/);
  assert.match(proposal, /JSON\.stringify\(proposal\.definition/);
  assert.match(proposal, /api\.approveProposal/);
  assert.match(source("api.ts"), /confirmed: true/);
});
