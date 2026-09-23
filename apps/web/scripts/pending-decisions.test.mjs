import assert from "node:assert/strict";
import test from "node:test";
import { workCountBadge } from "../src/unified/dailyWork.ts";

test("the Inbox badge states pending decisions and nothing when none wait", () => {
  assert.equal(workCountBadge(null), "");
  assert.equal(workCountBadge(undefined), "");
  assert.equal(workCountBadge(0), "");
  assert.equal(workCountBadge(1), "1");
  assert.equal(workCountBadge(99), "99");
  assert.equal(workCountBadge(100), "99+");
});
