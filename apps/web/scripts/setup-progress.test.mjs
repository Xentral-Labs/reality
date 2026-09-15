import assert from "node:assert/strict";
import test from "node:test";
import { followSetup, setupProgress } from "../src/unified/setupProgress.ts";

const receipt = (status) => ({
  tenant_id: "ten_1",
  run_id: "pgr_1",
  name: "My demo company",
  status,
  environment: "sandbox",
  destination: status === "ready" ? "/app?tenant=ten_1" : null,
  error_code: null,
  profile: null,
});

test("only a ready receipt opens, and only a settled failure stops", () => {
  assert.equal(setupProgress(null), "waiting");
  assert.equal(setupProgress(receipt("initializing")), "waiting");
  assert.equal(setupProgress(receipt("ready")), "ready");
  assert.equal(setupProgress(receipt("initialization_failed")), "failed");
  assert.equal(setupProgress(receipt("archived")), "failed");
});

test("following ends on the first settled receipt", async () => {
  const answers = [receipt("initializing"), receipt("initializing"), receipt("ready")];
  let reads = 0;
  const result = await followSetup(
    async () => answers[reads++],
    () => true,
    { delay: 0 },
  );
  assert.equal(result.status, "ready");
  assert.equal(reads, 3);
});

test("a failed read is retried; a setup that is still running is not abandoned", async () => {
  let reads = 0;
  const result = await followSetup(
    async () => {
      reads++;
      if (reads < 3) throw new Error("Failed to fetch");
      return receipt("ready");
    },
    () => true,
    { delay: 0 },
  );
  assert.equal(result.status, "ready");
  assert.equal(reads, 3);
});

test("a screen that left stops the loop and reports nothing", async () => {
  let reads = 0;
  let alive = true;
  const result = await followSetup(
    async () => {
      reads++;
      alive = false;
      return receipt("initializing");
    },
    () => alive,
    { delay: 0 },
  );
  assert.equal(result, null);
  assert.equal(reads, 1);
});

test("following gives up after its bound instead of polling forever", async () => {
  let reads = 0;
  const result = await followSetup(
    async () => {
      reads++;
      return receipt("initializing");
    },
    () => true,
    { delay: 0, attempts: 4 },
  );
  assert.equal(reads, 4);
  assert.equal(setupProgress(result), "waiting");
});
