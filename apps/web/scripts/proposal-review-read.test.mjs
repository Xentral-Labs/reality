import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import ts from "typescript";

const source = fs.readFileSync(new URL("../src/inflightRead.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { shareInFlight } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);

test("simultaneous reads share one request and a later read is fresh", async () => {
  const reads = new Map();
  let calls = 0;
  let finish;
  const load = () => {
    calls += 1;
    return new Promise((resolve) => {
      finish = resolve;
    });
  };

  const first = shareInFlight(reads, "tenant:proposal", load);
  const second = shareInFlight(reads, "tenant:proposal", load);
  assert.strictEqual(first, second);
  assert.equal(calls, 1);

  finish({ id: "proposal" });
  await first;
  await Promise.resolve();
  await shareInFlight(reads, "tenant:proposal", async () => {
    calls += 1;
    return { id: "proposal" };
  });
  assert.equal(calls, 2);
});

test("a failed request is discarded before retry", async () => {
  const reads = new Map();
  const failure = new Error("offline");
  await assert.rejects(
    shareInFlight(reads, "tenant:proposal", async () => {
      throw failure;
    }),
    failure,
  );
  await Promise.resolve();
  assert.equal(await shareInFlight(reads, "tenant:proposal", async () => "retried"), "retried");
});

test("the API limits in-flight sharing to Proposal Review GETs", () => {
  const api = fs.readFileSync(new URL("../src/api.ts", import.meta.url), "utf8");
  assert.match(api, /const proposalReviewReads = new Map<string, Promise<ProposalReview>>/u);
  assert.match(api, /shareInFlight\(proposalReviewReads/u);
  assert.doesNotMatch(api, /shareInFlight\([^\n]*approveProposal/u);
  assert.doesNotMatch(api, /shareInFlight\([^\n]*rejectProposal/u);
});
