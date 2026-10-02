# Verification: account-owned default selections

Date: 2026-10-02. Status: accepted for the isolated specs 316/319 source scope.
No production database was migrated, no deployment or commit performed.

## Outcome and acceptance scope

The physical `finance_role_destination` table becomes a read-only logical view of
selections held by `subledger_account`: one fewer physical table and no new generic
settings table. Combined with spec 316, ten physical tables are removed while logical
inspection resources and original financial authority remain available.

T013 is closed. Every backend test in the approved source scope has passing evidence,
including the unchanged timing benchmark and the complete specification-policy module.
Acceptance uses an isolated HEAD snapshot containing only specs 316/319 code, fixtures,
contracts and generated catalog changes. Unrelated concurrent proposal-decision work
is excluded; this is not a claim about CI for that separate feature or the combined
mutable worktree. The consolidation code/fixtures match the worktree byte-for-byte.
See [the source manifest](evidence/acceptance-source-manifest.json) for the baseline
commit, snapshot and hashes; all recorded snapshot hashes were checked at completion.

## Complete backend coverage

The final run used a task-owned disposable PostgreSQL 17 server on loopback, with
`max_locks_per_transaction=256` for migration-heavy setup and two pytest workers.
The existing PostgreSQL server and deployment settings were not changed.

| Check | Actual result | Disposition |
| --- | --- | --- |
| Complete functional/migration suite, excluding only the timing benchmark | 5334 passed, 10 skipped, one failed, one warning in 2524.13 seconds (42:04) | All runtime cases passed. The sole failure was the copied snapshot's missing coverage-matrix entries, not an implementation defect. |
| Complete spec-policy module plus serial 10,000-source benchmark | 24 passed in 27.55 seconds | Existing approved documents/specifications were copied into the snapshot; policy and benchmark pass. No runtime source or test assertion changed. |

Together the runs provide passing evidence for all 5336 unique non-skipped backend
cases, with ten skips preserved. Twenty-two already-passing spec-policy cases were
repeated with the corrected artifacts; they are not counted twice. The benchmark test
call took 25.97 seconds including preparation outside its measured loop, and its
unchanged 60-second assertion passed. The full run's red exit is recorded above rather
than rewritten as a zero-failure run. The only final failed check was re-executed through
its whole module and passed; no unchecked runtime failure remains.

Commands from the frozen `packages/reality-core` directory, with the task-owned admin
URL and the frozen `src` path supplied through the environment:

```sh
../../.venv/bin/pytest -n 2 -q --tb=short --durations=10 -k 'not test_reality_gap_replay_resumes_ten_thousand_sources_without_duplicates'
../../.venv/bin/pytest -q tests/test_spec_policy.py tests/test_postgresql_integration.py::test_reality_gap_replay_resumes_ten_thousand_sources_without_duplicates --tb=short --durations=5
```

The task-owned PostgreSQL container is removed after verification. No business timeout,
replay algorithm, demo behavior, assertion or skip was changed to obtain acceptance.

## Focused proofs and review

- Initial storage regression failed before implementation: the old physical table existed.
- Defaults/migration/admin-deletion suite: 12 passed in 53.34 seconds. Proves view-write
  refusal, tenant-local role/identity uniqueness, equal IDs across tenants, blocked
  defaults, read-only operations, competing/stale selections and partial/idempotent DDL.
- Populated migration preserves exact original account/destination IDs, authority values
  and rollback schema, including a default switched after upgrade. Source payload/hash/
  version and ledger comparisons are exact. Incompatible legacy roles abort without
  retirement or repair; account revisions and historical postings remain unchanged.
- Shared account-deletion regressions: 12 passed in 15.24 seconds. Physical storage is
  counted/purged once, views skipped, and confirmation/refusal/shared-company boundaries
  preserved. These tests do not prove purge of populated immutable cost histories;
  existing immutable DELETE guards remain outside spec 319.
- Migration/index/shared-cost regressions: 22 passed in 116.72 seconds, including pinned
  old revisions, downgrade/re-upgrade, exact cost-view behavior and schema checks.
- Corrected legacy cache migration and PostgreSQL modules: 17 passed in 44.12 seconds.
- Requirements analysis covered eight FRs and four success criteria, with no critical
  findings before implementation. Independent final read-only review found no actionable
  blocker in identity, tenant scope, atomic transfer, locking/revisions, migration/parity,
  rollback, shared view compilation, deletion integration or catalog alignment.

## Repository gates

- `make lint`, `make spec-check`, `git diff --check`: passed.
- `make docs-generate`: passed; field explanations and command storage writes match
  the account-owned marker and read-only view.
- `make docs-catalog-check`: passed against a disposable Git index/object directory
  containing the new generated artifacts. Regeneration produced no difference from
  that snapshot; the real Git index was not changed.
- `make docs-build`: passed (14 Python reference tests, 114 Node tests, VitePress build).
- `make web-build`: passed (451 Node tests, four i18n catalogs at 2492/2492 keys,
  TypeScript/Vite build). Existing bundle-size advisories remain.

## Earlier attempts retained as evidence

The initial complete run was interrupted at 165 passes/four failures; deletion-view
integration and an incorrect pre-switch rollback expectation were corrected. A later
run reported 5333 passed/three failed/ten skipped: two pinned legacy fixture bootstraps
were fixed through reflected test-only tables, and a parallel replay timing failure
passed isolated rerun. Original refusal/provenance assertions were retained.

A preliminary follow-up in the mutable worktree stopped at 93 passes/one unrelated
capability-guidance failure after concurrent proposal-decision edits. No files belonging
to that feature were changed by this consolidation task. A first isolated pass stopped
at 1054 passes/two skips to make frozen-source PYTHONPATH inheritance explicit for all
worker subprocesses. A shared-server pass then stopped at 2164 passes/six skips/five
failures/one setup error: four demo handler timeouts and two shared PostgreSQL lock-pool
exhaustions. The final dedicated-server run passed every one of those runtime cases.
The earlier spec 316 report also retains its unchanged-HEAD demo-failure evidence;
those demo cases passed in the final acceptance source scope.

## Final disposition

Implementation, complete backend coverage, populated migration/rollback, tenant and
concurrency proofs, retained finance authority, documentation/catalog, lint/spec,
web/i18n and independent review are complete for specs 316/319. No live data/settings,
production schema, deployment or commit changed. A further mapping/reference audit is
separate documentation-only work; it does not authorize another schema implementation.

## Current-main PR integration

Historical evidence above used local spec 319 and the former migration numbering.
The PR renumbers this feature to 329 and appends its migration after main 0114.
Combined current-main acceptance is recorded in spec 327 verification and hosted CI.

Combined current-main acceptance: PR #299, 5,564 backend cases passed, 10 skipped,
all 24 hosted gates passed. See spec 327 verification/ci-acceptance evidence; historical
local logs above retain their original source scope and former numbering.
