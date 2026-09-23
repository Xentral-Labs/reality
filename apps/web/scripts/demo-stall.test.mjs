import assert from "node:assert/strict";
import test from "node:test";
import {
  sourceNeedsAttention,
  stallCause,
  stallHeadline,
} from "../src/components/demoDataSummary.ts";

const stall = (kind, code = null) => ({
  kind,
  code,
  stopped_at: null,
  attempts: 0,
  recovery_at: null,
  automatic: false,
});

test("every stall kind has a headline a person can act on", () => {
  for (const kind of ["suspended", "stopped", "unresolved", "overdue", "throttled"]) {
    const headline = stallHeadline(stall(kind));
    assert.ok(headline && headline.length > 10, `${kind} must say what happened`);
  }
});

test("an interrupted source says that it resumes itself, a stopped one that it does not", () => {
  assert.match(stallHeadline(stall("suspended")), /resume by itself/);
  assert.match(stallHeadline(stall("stopped")), /not resume by itself/);
});

test("the cause names the failure rather than repeating the code", () => {
  assert.match(stallCause("database_error"), /database/i);
  assert.match(stallCause("handler_timeout"), /time budget/i);
  assert.match(stallCause("incompatible_references"), /references/i);
  // An unknown code still produces a sentence instead of a raw identifier.
  assert.doesNotMatch(stallCause("something_new"), /something_new/);
  assert.equal(stallCause(null), "");
});

test("attention follows the derived state, and a healthy source is left alone", () => {
  for (const state of ["suspended", "overdue", "error", "throttled"])
    assert.equal(sourceNeedsAttention(state), true, state);
  for (const state of ["running", "paused", "stopped", "not_connected", undefined])
    assert.equal(sourceNeedsAttention(state), false, String(state));
});
