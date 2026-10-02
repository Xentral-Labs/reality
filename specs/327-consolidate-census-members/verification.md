# Planning Verification: Census Membership

Status: foreign-currency main integration revalidation pending.

Requirements quality: 16/16 items passed, 11 FR/3 DR mapped to scenarios and planned
executable test paths. Constitution: all eight pre/post-design rows PASS. Independent
research and final design review by `/root/projection_research`: no planning blocker;
acceptance risks recorded in plan/research, not treated as passing runtime evidence.

Generated: plan.md, research.md, data-model.md, contracts/membership.md, quickstart.md.
No registered before/after planning hooks. Setup-plan used an explicit directory;
its automatic shared pointer write was restored to concurrent feature 325. No branch
switch, staging, commit, executable code, live database access or migration occurred.

FR-010/US3.4 was clarified against existing census immutability: count members once;
preserve permitted purge or retained-history refusal and rollback, with tenant isolation.
No bypass/new cleanup policy. This is original behavior preservation.

Validation: 14 distinct requirement IDs present in plan traceability; eight Constitution
PASS rows; all supporting artifacts exist with no unresolved clarification; shared
feature pointer preserved; make spec-check and git diff --check passed.

Next: dependency-ordered tasks, non-destructive analysis, then red-first PostgreSQL
proof and bounded implementation. The three-table saving is not accepted or implemented.

## Task generation

Generated 21 pending tasks: setup 1, foundational 2, US1 4, US2 6, US3 5, final review 3. Every FR/DR maps to tests and implementation/documentation; four SC map to acceptance tasks. Shared edits/fixtures make task mutations sequential; independent read-only searches may be batched. History is the first validation milestone, but the storage release remains atomic with typed protection and rollback. No additional agents are requested for task generation/analysis.

## PR integration baseline

Owner authorized implementation through a green PR. Isolated checkout is based on current main c55e0714. Historical local spec numbers 316/319/326 collided with already merged main features; consolidation artifacts are now 328/329/330 (Finance references remains 324, census remains 327). Migrations are renumbered 0115/0116/0117/0118 after main 0114; census candidate is 0119 with predecessor 0118. Prior logs are historical isolated acceptance, not proof against this new baseline. All required checks are rerun for the PR. Shared workspace and unrelated changes remain untouched.

## Implementation gate and initial proof

Read-only analysis found no critical issues, ambiguities or duplicate requirements.
All 18 FR/DR/SC requirements have task coverage; requirements checklist 16/16 passed
and all eight Constitution checks passed before implementation. Actual predecessor
DDL and incoming links were captured from an isolated revision-0118 database.
Initial proof failed as expected: 2 failures for absent physical store/revision.
The first complete targeted run found exact rollback constraint loss; separate ALTER
UNIQUE restoration fixes PostgreSQL's inline duplicate-key optimization. Corrected
focused proof passed 10 tests in 46.86 seconds. Expanded regression and final CI are
pending. PostgreSQL-18 catalog-only named NOT NULL clauses are omitted from frozen
DDL; original column NOT NULL declarations work on both PostgreSQL 17 and 18.

Unchanged census serializers and service interfaces preserve exact observed values,
IDs, source versions and hashes. No business derivation or public field was added.

## Corrected historical rollback and local quality

The expanded initial run passed 60 cases and failed 3 historical downgrade cases.
Restoring equivalent UNIQUE keys before the PK also preserves the original consumer
FK index binding, allowing old revision 0088 to replace its PK without CASCADE.
Corrected populated rollback, original census downgrade and full FK-index regression:
9 passed in 34.14 seconds (`rollback-corrected.log`). No assertion was weakened.

Unchanged serial 10,000-source benchmark: 1 passed in 35.62 seconds, normal durability
and the original elapsed <60 assertion. Docs: 14 Python and 114 Node tests passed,
format and production build passed. Web: 458 Node tests, four locales each 2550/2550
covered, format and production build passed. Generated catalog reproducibility and
lint/spec policy passed. Raw logs are retained under evidence.

Current integrated metadata: 149 physical tables, 25 exact logical views, 40 physical
cost tables. Census alone saves 3; all five PR slices save 18 from main's 167.
`integrated-storage-inventory.json` records exact names. Historical planning snapshots
remain dated evidence. No live database was accessed or migrated.

Final bounded regression suite (two workers, worksteal): 142 passed in 321.45 seconds.
This includes all new census tests, original census and captured-basis migration
contracts, canonical company manifests/reads, previous four consolidation migrations,
cost records, schema/index/reporting coverage and account deletion. Source manifest
hashes were rechecked unchanged after the run.

Hosted run 37040134568: docs/frontend/spec, five live browser flows and Installer
passed. Business Journey first attempt reached invoice then exceeded its unchanged
30-second background projection poll; local real-browser reproduction is in progress.
Full backend and browser gates are not yet accepted; failures remain visible.

Local complete real Business Journey: 1 passed in 161.15 seconds, including
confirmed role-default changes, reference/mapping history and all financial forms.
The CI-only initial 30-second poll timeout remains recorded and will be rerun.

Current-main CI exposed one historical payment-return fixture that used current
account services against revision 0109, before `default_destination_id` exists.
Spec impact: none for this test adjustment: seed canonical history at head, restore
the actual predecessor, then keep original spec 322 FR-003 corruption/refusal and
exact rollback assertions. Dedicated regression passed: 1 case in 3.07 seconds.
Only this test's source hash changed since the 142-case acceptance run; runtime,
migrations and all other test hashes are unchanged. The final hosted run executes
the complete suite against the updated frozen manifest.

PR: https://github.com/Xentral-Labs/reality/pull/299. No merge, live migration or
deployment is authorized by this verification record.

## Final acceptance

All 24 hosted checks passed for commit 77004c5e, including all four PostgreSQL-17
shards, aggregate backend-quality, seven browser-script groups, all six live-browser
flows, docs/frontend/spec and both Installer jobs. Full backend: **5,564 passed,
10 skipped, zero failures**, 5,574 unique collected cases, verified from disjoint
JUnit identities. Targeted reruns and the separately passing serial benchmark are
not added again to that unique count. Source hashes match the frozen manifest.

Quality run: https://github.com/Xentral-Labs/reality/actions/runs/37041537774.
Installer run: https://github.com/Xentral-Labs/reality/actions/runs/37041537807.
`evidence/ci-acceptance.json` records every check and exact shard counts; compressed
raw passing/failed CI logs and JUnit files preserve evidence. The initial Journey
projection poll timeout passed unchanged on the corrected final-source full run,
as well as the complete local real-browser run. No timeout or assertion was weakened.

Main advanced to 88888570 with unrelated gateway/report-access changes. It adds no
new schema or conflicting IDs; the hosted merge validation includes those changes.
The backing application metadata remains 149 physical tables/25 views, exactly three
fewer for this slice and eighteen fewer across the PR. All 21 tasks are complete.
Final review is recorded in review.md; all eight Constitution checks remain PASS.

The closing documentation commit changes no frozen backend source. Its CI checks
are monitored to completion before delivery. Shared workspace, live schema, merge
and deployment remain outside this implementation.

## Concurrent main integration

Main 3330195a merged chat-scoped proposals during the closing CI event, allocating
spec 328 and migration 0115. Its actual CI merge tree caused duplicate spec numbers
and two migration heads. Main was merged conflict-free into the isolated branch.
Cost consolidation is now spec 331; the consolidation chain is 0116–0120, following
0115_chat_scoped_proposals. The original fully green run remains historical evidence;
T019–T021 are reopened for the new frozen source and complete CI validation.
The upstream change adds only a nullable chat FK to Action, no physical table, so
149 physical tables/25 views and the eighteen-table reduction remain unchanged.

Latest-main integration proof: 25 cases passed; the cost-output specimen initially
downgraded past its new immediate predecessor and correctly exposed the lost upstream
chat column. It now downgrades to 0115_chat_scoped_proposals; unchanged full authority
row/schema assertions passed in the dedicated rerun (1 case, 27.90 seconds). Alembic
reports exactly one head: 0120_census_members. Lint/spec and regenerated catalogs pass.
Remote-number inventory confirms no other active remote branch claims 331; the
331-consolidate-typed-storage alias makes this allocation visible to the shared helper.

The current-main backend suite (37044677694) passed all four shards and backend-quality;
all other checks passed except the Journey's recurring 30-second asynchronous poll.
The readiness-only fixture attempt also timed out after interactive writes, so it was
removed. Spec impact: none for this test-harness correction: the stored-projection
contract (spec 179) is asynchronous; use the existing live Finance rollout's bounded
120-second wait while continuing to require the exact invoice/payment values from
the real worker. No business assertion, benchmark limit or application queue changes.
The final-source Web app was rebuilt before the complete local Journey rerun.

Refreshed revision-0119 predecessor evidence matches all six original census-related
schemas, constraints, indexes, two incoming FKs and five triggers. Its shared function
is captured losslessly; the earlier revision-0118 artifact remains a historical copy.

Main advanced again to 10cd775d, adding platform-admin private-report access under
spec 329. Its documentation append conflicted with this PR, which prevented GitHub
from creating a CI merge tree. Both requirement-map sections were retained. Account
default consolidation is now spec 332; the migration chain remains 0116–0120. This
upstream change adds no table or migration. The numbered 332 branch alias reserves
the new maximum allocation for parallel feature work. Complete CI is resumed after
the conflict is resolved.

## Current-main acceptance

All 24 hosted checks passed for c76e5bfd: quality run 37047527891 and Installer
37047527980. PostgreSQL 17 collected **5,599 unique cases: 5,589 passed, 10 skipped,
zero failures**. All four JUnit identity sets are disjoint; native reruns are not
added to this count. Every browser-script group, six live browser flows, frontend,
docs, specification and Installer check passed. The prior 77004c5e acceptance JSON
is retained as `evidence/prior-770-ci-acceptance.json`; current exact shard counts,
checks, compressed raw logs and JUnit files are recorded alongside it.

The complete native Journey passed in 539.90 seconds. Its bounded asynchronous
projection poll is 120 seconds, matching the existing Finance rollout fixture;
all exact business assertions remain unchanged. The final-source serial 10,000-
source replay benchmark passed in **31.10 seconds**, below the unchanged 60-second
limit, on the owned disposable PostgreSQL cluster with normal durability. Lint,
specification, catalog regeneration/reproducibility and diff checks pass. All 926
frozen source hashes match; the final documentation/evidence commit changes none.

The final review confirms every FR/DR and all eight Constitution checks, exactly
one migration head (0120_census_members), populated rollback and immutable typed
relationships. The exact inventory still matches **149 physical tables and 25
views**, three fewer for census and eighteen fewer across the complete PR. Main's
chat scope and platform report-access changes are preserved. All 21 tasks are now
complete. No live migration, merge or deployment is performed. The closing commit
will be monitored until every hosted check is green before delivery.

## Rebase repair and concurrent currency integration

GitHub confirmed rebaseable after the exact verified tree was linearized onto
2cba5e20. During replacement CI, main integrated spec 309 through 0d485c12,
including migration 0116_company_currency. Generated knowledge conflicts were
resolved by regenerating both catalogs from merged inputs. Consolidation migrations
are now 0117–0121 after 0116_company_currency, with one head. The first cost
roundtrip specimen uses its new immediate predecessor, retaining all exact schema
and authority assertions. Upstream currency behavior and values are preserved.
T019–T021 are reopened; prior green evidence remains historical. The new source
manifest includes the merged currency implementation. The final integrated tree
will again be retained as one commit on latest main for GitHub rebaseability.

Currency integration: 39 targeted consolidation/currency cases passed in 29.55
seconds; exact revision-0120 predecessor member DDL, indexes, incoming FKs and
guards match the retained capture. The unchanged serial 10,000-source benchmark
passed in 12.33 seconds. Metadata has 150 physical tables/25 views; main added
company_currency, so the complete PR still reduces 168 to 150 physical tables.

CI 37053100983 exposed one new historical fixture mismatch: current canonical
tenant creation seeds the retained account default marker absent before spec 332.
The spec-309 currency specimen now seeds its canonical references at head, then
downgrades to the actual pre-currency schema before posting its original unconverted
EUR/USD entries. All original backfill values, positive rollback and refusal asserts
remain unchanged. Spec impact: none; this repairs test setup for already specified
FR-001/FR-005, SC-003 behavior. All ten company-currency tests passed in 3.18 seconds.
Failed/green raw evidence is retained; the new 931-file source manifest includes
this fixture correction. Complete CI acceptance remains pending.
