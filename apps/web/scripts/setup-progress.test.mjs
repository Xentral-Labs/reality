import assert from "node:assert/strict";
import test from "node:test";
import {
  SETUP_READY_CURRENT_MS,
  SETUP_READY_DONE_MS,
  followSetup,
  presentReadySetup,
  setupProgress,
  setupStage,
  setupSteps,
} from "../src/unified/setupProgress.ts";

assert.ok(SETUP_READY_CURRENT_MS >= 2500, "the active final step must be readable");
assert.ok(SETUP_READY_DONE_MS >= 3000, "all four completed steps must remain readable");

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

test("the steps are taken from real state, never estimated", () => {
  // Feature 201: queued work is current but still truthfully says it is waiting.
  assert.equal(setupSteps(null), null);
  assert.equal(setupSteps(receipt("initialization_failed")), null);

  const queued = setupSteps({ ...receipt("initializing"), preparation: "queued" });
  assert.deepEqual(
    queued.map((step) => [step.key, step.state]),
    [
      ["created", "done"],
      ["data", "current"],
      ["calculation", "waiting"],
      ["ready", "waiting"],
    ],
  );
  assert.equal(queued[1].label, "Waiting to start");

  const preparing = setupSteps({ ...receipt("initializing"), preparation: "preparing" });
  assert.deepEqual(
    preparing.map((step) => [step.key, step.state]),
    [
      ["created", "done"],
      ["data", "current"],
      ["calculation", "waiting"],
      ["ready", "waiting"],
    ],
  );
  assert.equal(preparing[1].label, "Preparing orders, deliveries and invoices");

  const retrying = setupSteps({ ...receipt("initializing"), preparation: "retrying" });
  assert.deepEqual(
    retrying.map((step) => [step.key, step.state]),
    [
      ["created", "done"],
      ["data", "current"],
      ["calculation", "waiting"],
      ["ready", "waiting"],
    ],
  );
  assert.equal(retrying[1].label, "Trying preparation again automatically");

  const done = setupSteps(receipt("ready"));
  assert.deepEqual(
    done.map((step) => step.state),
    ["done", "done", "done", "done"],
  );
  assert.equal(
    done.filter((step) => step.state === "current").length,
    0,
    "a finished setup has no current step",
  );
  assert.equal(done[1].label, "Orders, deliveries and invoices prepared");
  assert.equal(done[2].label, "Finance and margins calculated");
  for (const steps of [queued, preparing, retrying]) {
    assert.equal(steps.filter((step) => step.state === "current").length <= 1, true);
  }
});

test("confirmed completion remains visible before automatic navigation", async () => {
  const seen = [];
  await presentReadySetup(
    (steps) => seen.push(steps),
    () => true,
    {
      currentDelay: 0,
      doneDelay: 0,
    },
  );
  assert.deepEqual(
    seen.map((steps) => steps.map((step) => step.state)),
    [
      ["done", "done", "done", "current"],
      ["done", "done", "done", "done"],
    ],
  );
  assert.equal(seen[0][2].label, "Finance and margins calculated");
});

test("a receipt that reports no preparation still shows its steps", () => {
  // The inline path (an empty company, or a retry) reports nothing to wait for.
  const stage = setupSteps(receipt("initializing"));
  assert.deepEqual(
    stage.map((step) => step.state),
    ["done", "current", "waiting", "waiting"],
  );
});

test("the first read happens immediately, without waiting out an interval", async () => {
  let reads = 0;
  const started = Date.now();
  const result = await followSetup(
    async () => {
      reads++;
      return receipt("ready");
    },
    () => true,
    { delay: 5000 },
  );
  assert.equal(result.status, "ready");
  assert.equal(reads, 1);
  assert.ok(Date.now() - started < 1000, "a ready company must not wait for a poll");
});

test("each read is observed, so the screen can follow the stage", async () => {
  const answers = [
    { ...receipt("initializing"), preparation: "queued" },
    { ...receipt("initializing"), preparation: "preparing" },
    receipt("ready"),
  ];
  let reads = 0;
  const seen = [];
  await followSetup(
    async () => answers[reads++],
    () => true,
    {
      delay: 0,
      observe: (value) => seen.push(setupStage(value)),
    },
  );
  assert.deepEqual(seen, ["queued", "preparing", "ready"]);
});
