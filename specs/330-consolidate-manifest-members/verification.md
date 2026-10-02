# Verification: Receipt Manifest Membership

Status: accepted in the repository; all required verification gates passed. No live migration or deployment performed.

## Requirements and planning gates

Owner selected the bounded five-to-one scope and continued into implementation.
Requirements checklist: 16/16 satisfied. Constitution: eight PASS rows. Read-only
analysis: 10 FR, three DR and four SC covered by 15 pending tasks; no critical,
ambiguity or duplication findings. Independent planning review accepted exact-column
INSERT-only routing and required physical insertion integrity/RETURNING/lifecycle proofs.
No extension hooks are registered. Shared feature pointer preserved for concurrent spec 325.

## Isolated predecessor and environment

Owned native PostgreSQL 18 cluster: `/private/tmp/reality-326-pg/data`, private Unix
socket `/private/tmp/reality-326-pg/socket`, socket port 55449, TCP disabled. Default
fsync, synchronous_commit and full_page_writes remain enabled. No live company rows
were accessed. Sandbox shared-memory/socket restrictions required narrow tool escalation
for local test execution; no live database access or global cleanup was performed.

At revision 0111, captured exact column/PK/unique/FK/index contracts for all five
members in `evidence/predecessor-schema.json`: zero incoming FKs and zero user triggers.
Migration parent/number is 0111 → 0112; existing three accepted consolidations are
preserved. Original business service/tool/adapter code remains unchanged.

## Chronological evidence before final acceptance

The following progress entries preserve the state and failures at the time they were
recorded. Pending statements below are historical; the final acceptance section
supersedes them.

## Red-first and focused proofs

Initial new physical store and populated migration tests: **2 failed in 12.54s**;
expected missing shared physical table and absent migration revision. Existing received
basis, replacement, correction and review services seed the populated fixtures.

First focused run: **6 passed in 25.26s**. It includes exact original view columns,
SQL/ORM mutations, independent namespaces, shape/FK/uniqueness refusal, partial metadata
lifecycle, populated all-family/two-tenant exact row/schema roundtrip and injected
parity failure with transactional rollback. Subsequent added explicit ORM insert/delete
and once-only physical counting/purge proofs require the expanded regression run below.

Full required gates and final review are pending. No task or acceptance criterion is
called complete merely because focused tests passed. No live migration/deployment/commit.

## First expanded regressions and resolved causes

First expanded run: **47 passed, 7 failed in 144.38s**. Two failures were explicit
classification/index inventories that needed the new physical membership store
named separately from its five logical inspection resources. Assertions remain
exact; no generic exclusion or production reporting rule was weakened. Three
captured-review failures came from the owned native cluster's initial local
Europe/Berlin timezone rather than UTC; two pinned Alembic tests rejected percent
escaping in a Unix-socket URL. The cluster now uses UTC and loopback-only TCP at
127.0.0.1:55449, preserving durability settings. No application timezone or
fixture assertions were changed. Expanded regressions are being rerun.

Independent concrete architecture/source/migration review found no blocker. It
confirmed original columns, fixed invoker insert routing, native mutations, all
seven FKs, closed shapes, ID collision behavior, exact rollback and owned function
lifecycle. Normal repeated/partial metadata lifecycle is covered; repairing a
manually deleted view with an orphaned function is outside the supported contract.

Catalog reproducibility passed in the disposable acceptance snapshot: generated paths staged only in that private Git index, then regeneration and unchanged diff. User Git index untouched. Docs build completed in 94.55s; complete gate exit/status is checked separately.

## Expanded regression acceptance

Corrected expanded run: **53 passed, 1 failed in 472.74s (07:52)**, passing new store/migration
proofs, receipt services/tools/inspection, schema/reporting assertions, pinned costing
migration and populated 0110/0111/0112 predecessor roundtrips. The remaining 0109
fixture failure is described below. Original historical
review, replacement, correction and corruption assertions remain intact. New count/purge
proof includes a neighboring tenant and exactly five added physical memberships.

Docs gate: 14 Python reference tests and 114 Node tests passed; VitePress build 94.55s.
Private-snapshot catalog reproducibility exited zero. Whole backend/web/benchmark gates
remain pending, so final acceptance tasks T014/T015 are not complete.

## Pinned predecessor fixture correction

The remaining expanded failure is the spec 316 migration fixture pinned to 0108,
which enumerated current cost metadata and attempted to query the new 0112 store
in that old database. Its authority inventory now intersects actual predecessor
physical tables. All original cost input/source/evidence/ledger authorities and
exact value/schema comparisons remain; this is not a production fallback or a
generic exclusion. A dedicated rerun is pending. The frozen whole-backend snapshot
contains the earlier fixture version; any resulting known failure must be closed
with the corrected complete migration module, never described as a green original
full command. No production code changed after the frozen run started.

Pinned predecessor rerun: complete `test_cost_projection_migration.py` **1 passed
in 63.83s**, closing the remaining expanded-regression failure without production
changes. Expanded coverage is 54 unique passing cases by composition (53 plus the
corrected historical migration case). The original expanded command remains recorded
as failing; it is not represented as a single all-green run.

Web gate exited zero: **455 Node tests passed**, four locale audits each
**2499/2499** covered, TypeScript/Vite build **17.36s**. The frozen shared source
includes unrelated accepted/in-progress presentation work; this consolidation itself
changes no Web behavior. Docs and Web emitted only their existing large-bundle
advisory. Backend hash manifest remains unchanged after generation/build.

## Complete-key index correction before final freeze

Final review identified that family-partial uniqueness cannot supply an
unconditional tenant/manifest FK lookup. A global `(tenant_id,manifest_id)` index
is now explicit. New tests require unconditional full-key index coverage for all
seven FKs in both metadata and the actual migrated PostgreSQL schema. The DDL
freezing helper also must initialize `db/core.py` first so its index-registration
pass is complete before compiling the new store; the first helper's import order
omitted five target indexes from migration DDL even though normal runtime metadata
had them. These gaps are corrected and retested before the final source freeze.

The first whole run was deliberately interrupted for the index correction:
**499 passed, 2 skipped in 784.71s**, exit 2/KeyboardInterrupt. It is partial
historical evidence only and will not count as complete acceptance. Final full
acceptance will use refreshed immutable source including the corrected predecessor
fixture and complete physical index DDL.

Actual migrated-index proof observed red (**1 failed in 89.75s**) for the first
frozen DDL missing target indexes, then DDL regenerated after normal core-first
registration. Independent follow-up confirmed the unconditional parent and all five
target indexes; tenant-only FK is covered by the PK prefix. Final targeted run is pending.

Final index/lifecycle/migration regressions: **12 passed in 302.55s**. Both runtime metadata and migrated SQL indexes cover every complete FK unconditionally; populated rollback and the pinned projection predecessor are green. The final frozen full backend run has started.

## Final acceptance and review

The final frozen PostgreSQL backend command (`pytest -n 2 -q --tb=short
--durations=10 -k 'not test_reality_gap_replay_resumes_ten_thousand_sources_without_duplicates'`)
passed: **5,382 passed, 10 skipped, one transaction-cleanup warning in 3,253.88s**.
The unchanged 10,000-source benchmark then ran serially: **1 passed in 21.62s**.
Combined unique backend coverage is **5,383 passing cases and 10 skips**; targeted
reruns are not added to that count. Raw final logs are in `evidence/`.

The acceptance snapshot contains 894 hashed backend files. A post-run comparison
found no changed frozen files and no difference in any of the nine consolidation
implementation/test files between the workspace and the acceptance snapshot.
Concurrent unrelated work is not represented as part of this change.

Other required gates passed: core lint, specification checks, whitespace/diff check;
docs generation and a final catalog regeneration with zero generated diff;
docs build (14 Python reference tests, 114 Node tests); Web build (455 Node tests,
four locale audits at 2499/2499, TypeScript and Vite). Existing bundle-size advisories
remain advisory. The backend warning is SQLAlchemy transaction cleanup in an
existing storyline API test; it does not fail acceptance.

Final review reconciles all FR/DR with the linked tests and frozen predecessor
contracts: five original four-column interfaces; independent family/tenant IDs;
seven tenant-qualified physical FKs with unconditional complete-key indexes;
closed target shape and original selection uniqueness; SQL/ORM CRUD and RETURNING;
unchanged service digest serialization and historical amounts; exact populated
upgrade/downgrade/re-upgrade, transaction abort, metadata lifecycle and once-only
physical count/purge. No generic identities, new source authority, altered sealed
member contract or unrelated lifecycle repair was introduced.

Model metadata is **147 physical tables and 21 compatibility views**, down from
151/16 before this slice. Costing physical storage is 43 rather than the historical
47-table audit snapshot. This slice saves four physical tables; the four accepted
consolidations together save **15**. Census/captured/company-input candidates remain
unimplemented. No company database, live migration, commit or deployment is part
of this acceptance.

Final repository checks after audit updates: lint/spec/diff checks passed; all 15 tasks complete. Both physical/view name sets in the overview reconcile exactly with current metadata (147/21). The owned PostgreSQL cluster on port 55449 was stopped after testing; other database instances were untouched.

## Current-main PR integration

Historical evidence above used local spec 326 and the former migration numbering.
The PR renumbers this feature to 330 and appends its migration after main 0114.
Combined current-main acceptance is recorded in spec 327 verification and hosted CI.

Combined current-main acceptance: PR #299, 5,564 backend cases passed, 10 skipped,
all 24 hosted gates passed. See spec 327 verification/ci-acceptance evidence; historical
local logs above retain their original source scope and former numbering.
