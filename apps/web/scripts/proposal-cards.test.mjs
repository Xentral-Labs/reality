import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

/** A proposal a person cannot dismiss is a proposal that never goes away.
 *
 * The graph report card shipped with only Confirm. When its change could never
 * succeed — a retry key the copilot had reused — the card sat in every chat the
 * reader opened, refusing on each press, with no way out. Every other card in
 * the application already had the second button.
 */
const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "src", "unified");

function sources(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? sources(path.join(directory, entry.name))
      : entry.name.endsWith(".tsx")
        ? [path.join(directory, entry.name)]
        : [],
  );
}

test("every card that can approve a proposal can also reject it", () => {
  const offenders = sources(root)
    .map((file) => [file, readFileSync(file, "utf8")])
    .filter(([, text]) => text.includes("api.approveProposal"))
    .filter(([, text]) => !text.includes("api.rejectProposal"))
    .map(([file]) => path.relative(root, file));
  assert.deepEqual(offenders, [], "these can only say yes");
});
