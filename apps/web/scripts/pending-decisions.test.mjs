import assert from "node:assert/strict";
import test from "node:test";
import { decisionBadge } from "../src/unified/dailyWork.ts";

test("the Inbox badge states pending decisions and nothing when none wait", () => {
  assert.equal(decisionBadge(null), "");
  assert.equal(decisionBadge(undefined), "");
  assert.equal(decisionBadge(0), "");
  assert.equal(decisionBadge(1), "1");
  assert.equal(decisionBadge(99), "99");
  assert.equal(decisionBadge(100), "99+");
});
