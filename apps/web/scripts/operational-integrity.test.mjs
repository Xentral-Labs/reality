import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");

test("commitment revision and cancellation use the shared reviewed web action", () => {
  const discovery = JSON.parse(read("../../packages/reality-core/config/action_discovery.json"));
  const entries = new Map(discovery.entries.map((entry) => [entry.key, entry]));
  assert.equal(entries.get("commitment_revise")?.form, "commitment_revise");
  assert.equal(entries.get("commitment_cancel")?.form, "commitment_cancel");
  assert.ok(entries.get("commitment_revise")?.placements.includes("global"));
  assert.ok(entries.get("commitment_cancel")?.placements.includes("commitment.supplier"));

  const discoverySource = read("src/unified/actionDiscovery.ts");
  assert.match(discoverySource, /"commitment_revise"/);
  assert.match(discoverySource, /"commitment_cancel"/);

  const router = read("src/unified/ActionCard.tsx");
  assert.match(router, /activeTool === "commitment_revise"/);
  assert.match(router, /<CommitmentActionCard/);

  const card = read("src/unified/CommitmentActionCard.tsx");
  assert.match(card, /deliveryActions\.prepare/);
  assert.match(card, /deliveryActions\.confirm/);
  assert.match(card, /eligible_retained_allocations/);
  assert.match(card, /selection_required/);
  assert.doesNotMatch(card, /reviseCommitment|cancelCommitment/);

  const app = read("src/unified/UnifiedApp.tsx");
  assert.match(app, /proposalId=\{selection\.proposal\}/);
  assert.doesNotMatch(app, /proposalId=""/);
});
