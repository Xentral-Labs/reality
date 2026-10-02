# Verification: Finance Reference Storage

Date: 2026-10-02. Status: accepted. Complete backend coverage proven through the frozen full run and targeted corrected/expanded checks. No live data migrated, no deployment or commit. Acceptance covers the approved consolidation source; it does not certify unrelated concurrent staged work.

## Pre-implementation gates
Owner approved exact two-catalog scope. Spec quality 7/7 and independent planning requirements review 6/6 passed. Kind-only physical identity design reviewed independently; no blocker. Analysis: 10 FR, 4 SC, 15 tasks, 100% requirement coverage; zero ambiguity, duplication or critical findings. All Constitution rows PASS. No extension hooks are configured. Feature context supplied explicitly to workflow scripts without changing another session's feature pointer.

## Red proof
- New physical two-to-one test failed as expected: missing `finance_reference_store`; 1 failed in 1.67s.
- Populated migration test failed because revision 0111 did not exist; 1 failed in 18.57s.
- First roundtrip restored equivalent CHECK expressions with different PostgreSQL array casts. Exact schema assertion correctly failed. Frozen DDL was corrected to preserve original expression form; assertions were not weakened.

## Current evidence
- Original references/target mappings and initial physical store test: 33 passed in 94.02s.
- Store metadata, ORM CRUD, family/tenant collisions, logical CHECK OPTION, widths and all eight incoming key shapes: 5 passed in 13.53s before the extra deletion/count proof.
- Populated migration now includes real received evidence, posted ledger, component split/case/group assignments, source mapping, target mapping with account/tax links and historical snapshots. It compares every original table row before/after and exact catalog/dependent schema on rollback, including subsequent changed labels/times.
- Extra proof checks rejection of missing references through all eight populated incoming constraints, and physical tenant count/purge without double counting logical views.
- Complete backend acceptance is running on `/private/tmp/reality-324-acceptance.0j147wxa` with isolated source PYTHONPATH and dedicated disposable PostgreSQL 17 (max_locks_per_transaction=256). The unchanged 10,000-source benchmark is run separately. Logs: `/private/tmp/reference-full-acceptance.log`, `/private/tmp/reference-benchmark.log`.
- Focused migration, source mapping, assignment, company deletion and index suite: **55 passed in 211.93s**.
- Expanded store and populated eight-FK rejection/rollback proofs: **7 passed in 76.45s**.
- Isolated docs build: **14 Python + 114 Node tests passed**, VitePress build passed (11.94s).
- Isolated web build: **451 Node tests passed**, i18n audit and TypeScript/Vite build passed (4.65s); existing bundle-size advisory only.
- Isolated `make docs-catalog-check` passed against a disposable snapshot Git index, with no user-workspace index changes or commits. Regeneration changed no frozen backend hashes.
- Predecessor/full-chain migration suite: **19 passed in 222.10s**.
- Complete backend acceptance is closed by the full run, corrected reporting module, additional storage proofs and final native PostgreSQL benchmark (results below).

## Documentation boundary
The public data-model explorer's selected `RECORDS` contains neither reference catalog. Its generator requires no new business resource or field; unchanged generation/build validates that selection. Storage is documented in DATA_MODEL and ARCHITECTURE instead of inventing a new public object. Generated command/resource vocabulary remains unchanged for this slice.

## Review
No domain/service/tool/API/UI changes. Shared store registration redirects exact typed FK shapes and adds view dependencies before index generation. Migration uses frozen DDL and eight named FK definitions; no live ORM imports, no CASCADE or data recalculation. Downgrade restores original structures and current values. Independent research/review inspected the concrete store, migration and tests: no blocker; original tenant/family namespaces, widths, target binding and timestamp shape remain intact. Final approval remains conditional on required suites. All remaining results are now recorded below; final review found no unresolved blocker.

## Benchmark first attempt
The separate benchmark process overlapped the full backend workers and both build suites. Its unchanged 60s assertion failed at 121.63s (182.31s test duration). This is a real red result; no threshold or algorithm was changed. Repeat only after other owned acceptance processes finish so the serial performance check has its intended resource isolation.

## Reporting coverage review
The explicit schema audit initially failed with only `finance_reference_store` undeclared (1 failed, 7 passed in 10.89s). The two logical Finance catalogs are already deliberately deferred from the original posting/allocation reporting slice. Their shared physical catalog is now explicitly named in that same Finance deferral, with a storage-specific reason. No general exclusion, production reporting rule or assertion was weakened. The full frozen run retains the earlier audit version; its expected static failure must be closed by rerunning the complete eight-test module against this one-line corrected declaration.

## Completed full backend run
Frozen full run: **5340 passed, 10 skipped, 1 failed, 1 existing SAWarning in 3247.74s (54:07)**. Its sole failure is exactly the explicit Reporting schema deferral identified above. The entire corrected reporting module passed **8/8 in 8.66s**; no production source or business assertion changed. All runtime cases in the full run passed. This is a composite acceptance proof, not a claim that the historical full command exited green. Final serial benchmark passed on a native PostgreSQL instance (below).

Additional valid-physical-row family transition proof passed **1/1 in 6.99s**: clearing target/timestamps would satisfy internal storage shape, but the external view CHECK OPTION rejects the move.

## Serial benchmark infrastructure interruption
The first post-suite serial attempt lost its PostgreSQL connection and failed cleanup with `server closed the connection unexpectedly`. The dedicated auto-removed container was no longer present when inspected; its termination cause cannot be reconstructed from retained logs. This is not a passing benchmark. Retry on a fresh isolated instance, retaining container metadata until cleanup. No runtime code or threshold changed.

Fresh-instance diagnosis: PostgreSQL initdb failed with `No space left on device` in Docker storage (exit 1, not OOM). Only the owned failed test container/volume is removed. A PostgreSQL 17 instance with a 512MiB temporary-memory data directory avoids disk pressure for the final single benchmark; no other Docker resources are pruned and the test/threshold remain unchanged.

First RAM-backed serial benchmark completed all 20 pages / 10,000 not-applicable outcomes but exceeded the unchanged 60s threshold at **61.325s** (78.32s total). This remains a red performance gate; repeat once alone to check reproducibility.

RAM-backed standalone repeat also failed the unchanged threshold: **107.074s** replay, **131.08s** total. A same-instance comparison with the previously accepted spec-319 source snapshot is required before attributing this timing failure to the new catalog consolidation. Performance gate was still open at this stage; final native proof below closes it.

## Final accepted benchmark and coverage

The prior accepted spec-319 source also failed on the same RAM-backed Docker instance
(**93.764s** replay; **113.48s** total). Resource inspection showed concurrent external
test/browser workloads. No catalog regression was established by those measurements.

Final benchmark used the already-installed **PostgreSQL 18.4 (Postgres.app)** on an
owned temporary cluster under `/private/tmp/reality-324-native-pg-c47`, with a private
Unix socket and ordinary **fsync=on, synchronous_commit=on, full_page_writes=on**.
The frozen consolidation source, dataset, assertions and **60s** limit were unchanged.
Result: **1 passed in 40.76s**, including **37.50s** whole test call (preparation,
measured replay and idempotent repeat). The measured replay therefore satisfies 60s.
The complete backend run and populated migrations used PostgreSQL 17; only the final
standalone performance proof used the installed native PostgreSQL 18.4.

Unique accepted coverage: **5,343 passing cases and 10 existing skips**, without
counting repeated tests twice: 5,340 full-run passes, the one corrected reporting case,
the separately executed benchmark, and the one additional physical count/purge case.
The other seven reporting reruns and expanded existing store/migration/family-boundary
proofs overlap already counted cases. No unresolved runtime or required check failure
remains. The full historical command exited 1 because it contained the older explicit
reporting deferral; its complete corrected module passed independently.

Logs retained in `evidence/backend-full.log`, `evidence/reporting-rerun.log`, and
`evidence/benchmark-native.log`. The source manifest records all changes relative to
baseline 99043eb3, immutable frozen hashes and additional tested files. Frozen runtime
and migration files match the current consolidation files byte-for-byte.

Final lint, spec policy and diff whitespace checks passed. Isolated generated docs,
catalog reproducibility, web build and all four locale audits passed. Independent
review found no schema, identity, tenant, view-write or rollback blocker. No user Git
index, branch or unrelated staged work was changed by acceptance setup.

## Outcome and cleanup

Two physical Finance reference catalogs become one typed store with the same two
logical resources. Net reduction: **one physical table**, or **eleven across specs
316, 319 and 324**. No generic settings table or new business authority is introduced.
No live data, deployment or commit is performed. All owned remaining temporary
PostgreSQL instances are stopped after validation; unrelated Docker data is retained.
The Docker storage exhaustion remains an external environment condition, not a global
cleanup authorization. Snapshot sources/logs remain available for review.

Combined current-main acceptance: PR #299, 5,564 backend cases passed, 10 skipped,
all 24 hosted gates passed. See spec 327 verification/ci-acceptance evidence; historical
local logs above retain their original source scope and former numbering.
