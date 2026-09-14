import assert from "node:assert/strict";
import test from "node:test";
import {
  ARCHIVE_GUARD_MESSAGES,
  archiveGuard,
  archivedCompanies,
  archivedSandboxes,
  DELETE_CONFIRMATION_WORD,
  deleteConfirmationValid,
  isPracticeCompany,
  lifecycleKind,
  lossSummary,
} from "../src/unified/companyLifecycle.ts";

const owner = { id: "north", name: "Northstar Commerce", role: "owner" };
const other = { id: "south", name: "Southline Trading", role: "owner" };
const sandbox = {
  id: "box",
  name: "Practice",
  role: "owner",
  purpose: "playground",
  sandbox_run_id: "pgr_1",
};
const demo = {
  id: "demo",
  name: "Atlas",
  role: "owner",
  company_kind: "demo",
  sandbox_run_id: "pgr_2",
};

test("a business company is archived by an owner unless it is the last active one", () => {
  assert.deepEqual(archiveGuard(owner, [owner, other]), { allowed: true, kind: "company" });
  assert.deepEqual(archiveGuard(owner, [owner]), {
    allowed: false,
    kind: "company",
    reason: "last-active",
  });
  assert.deepEqual(archiveGuard(owner, [owner, sandbox, demo]), {
    allowed: false,
    kind: "company",
    reason: "last-active",
  });
  assert.deepEqual(archiveGuard({ ...owner, role: "member" }, [owner, other]), {
    allowed: false,
    kind: "company",
    reason: "not-owner",
  });
});

test("a sandbox or demo company is archived through its run while another entry remains", () => {
  assert.deepEqual(archiveGuard(sandbox, [owner, sandbox]), { allowed: true, kind: "sandbox" });
  assert.deepEqual(archiveGuard(demo, [demo, sandbox]), { allowed: true, kind: "sandbox" });
  assert.deepEqual(archiveGuard(sandbox, [sandbox]), {
    allowed: false,
    kind: "sandbox",
    reason: "last-active",
  });
  assert.deepEqual(archiveGuard({ ...demo, sandbox_run_id: undefined }, [owner, demo]), {
    allowed: false,
    kind: "sandbox",
    reason: "unavailable",
  });
});

test("practice companies are recognised by purpose, run or kind", () => {
  assert.equal(isPracticeCompany(owner), false);
  assert.equal(isPracticeCompany({ purpose: "playground" }), true);
  assert.equal(isPracticeCompany({ sandbox_run_id: "pgr_2" }), true);
  assert.equal(isPracticeCompany({ company_kind: "sandbox" }), true);
  assert.equal(isPracticeCompany({ company_kind: "company" }), false);
  assert.equal(lifecycleKind(owner), "company");
  assert.equal(lifecycleKind(demo), "sandbox");
});

test("every guard reason has a sentence to show in place", () => {
  for (const reason of ["not-owner", "last-active", "unavailable"])
    assert.ok(ARCHIVE_GUARD_MESSAGES[reason].length > 20, reason);
});

test("the archived company list keeps business companies only, newest first", () => {
  const rows = [
    { ...owner, archived_at: "2026-09-01T10:00:00Z" },
    { ...other, archived_at: null },
    { ...sandbox, archived_at: "2026-09-05T10:00:00Z" },
    { id: "west", name: "Westport", role: "member", archived_at: "2026-09-03T10:00:00Z" },
  ];
  assert.deepEqual(
    archivedCompanies(rows).map((row) => row.id),
    ["west", "north"],
  );
  assert.deepEqual(archivedCompanies([]), []);
});

test("the archived sandbox list keeps archived runs only, newest first", () => {
  const runs = [
    { id: "a", status: "active", archived_at: null },
    { id: "b", status: "archived", archived_at: "2026-09-02T00:00:00Z" },
    { id: "c", status: "archived", archived_at: "2026-09-04T00:00:00Z" },
    { id: "d", status: "initialization_failed", archived_at: null },
  ];
  assert.deepEqual(
    archivedSandboxes(runs).map((run) => run.id),
    ["c", "b"],
  );
});

test("deletion is confirmed only by the exact name and the literal word", () => {
  assert.equal(DELETE_CONFIRMATION_WORD, "DELETE");
  assert.equal(deleteConfirmationValid(owner, "Northstar Commerce", "DELETE"), true);
  assert.equal(deleteConfirmationValid(owner, "Northstar commerce", "DELETE"), false);
  assert.equal(deleteConfirmationValid(owner, "Northstar Commerce ", "DELETE"), false);
  assert.equal(deleteConfirmationValid(owner, "Northstar Commerce", "delete"), false);
  assert.equal(deleteConfirmationValid(owner, "", ""), false);
});

test("the loss summary names sources, evidence and reality counts in that order", () => {
  assert.deepEqual(lossSummary({ source_count: 3, evidence_count: 12, reality_count: 40 }), [
    { label: "Sources", count: 3 },
    { label: "Evidence documents", count: 12 },
    { label: "Reality records", count: 40 },
  ]);
});
