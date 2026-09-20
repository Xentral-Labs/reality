# Restart handoff — spec 242

Checkpoint: 2026-09-19, after T193. The owner asked to record the exact remaining work
before restarting. This file is a documentation checkpoint, not new product scope.
Read this first, then the linked contract and the current code. Do not restart discovery
or reimplement completed historical reporting from the old convergence task descriptions.

## Resume here

**T194 is complete.** The fixed captured graph context, typed SQL relations,
saved-analysis/web question preservation and graph/tool/HTTP paths are implemented and
verified. The next bounded work is the still-open shared-worker/scale and full-company
financial-admission sequence described below; it requires its own refined plan and analysis
before implementation. Separate schema expansion or scope changes still follow governance.

First read:

1. [Captured report contract](contracts/captured-report-publication.md).
2. [Latest verification](verification-results.md), section “Approved captured report storage
   and services (T191–T193, 2026-09-19)”.
3. [Task history](tasks.md), T190–T194; [plan](plan.md) and [analysis](analysis.md).
4. Existing services/analytics/costing_relation.py, contribution_aggregates.py and the
   historical inventory/contribution graph integration and tests. Reuse these boundaries.
5. docs/WEB_SPEC.md before UI work; docs/features/scheduled-jobs.md before job integration.

Before coding T194, refine its graph context and tests in spec/plan/tasks and run the
required analysis. The concrete next acceptance is: a graph query and saved fixed analysis
reference one captured generation, return its verified known subtotals/coverage, and retain
that selection when a newer report is published. They must not resolve another latest
review or use the historical CompanyGenerationBasis for this captured context.

## What is already delivered

- Source-backed receipt acquisition cost, supported inventory calculation and confirmed
  whole-line commercial DB1/DB2, with source/decision traces and explicit missing costs.
- Cost-record and retained cost-query services plus existing tool/MCP/CLI/HTTP adapters.
- Selected historical inventory and contribution generations, SQL reporting relations,
  graph execution, saved contexts and Analysis Builder selectors. Selected contribution
  currentness has its own tested boundary. These are not full-company captured reports.
- Current source-backed company census, its immutable five-table retention, bounded review
  resolution, exact captured review vector and approved three-table retention (0072).
- Captured known subtotals, with independent acquisition/carrying/DB1/DB2 coverage.
- **Latest delivery:** migration 0079_captured_report, four approved disposable tables:
  cost_generation, cost_inventory_row, cost_contribution_row, cost_publication.
- Shared internal services in services/costing.py: build_captured_cost_generation,
  publish_captured_cost_generation, captured_cost_report, discard_captured_cost_generation.
  Build uses pinned canonical replay; reads use verified cached rows, not financial replay.
  Publication is tenant-serialized compare-and-swap; sealed outputs are immutable. Only a
  whole unpublished cache can be discarded; retained input history survives.

Key files under packages/reality-core/:

- src/reality/domain/captured_report.py — explicit captured context and publication rules.
- src/reality/db/captured_report.py — four typed tables.
- migrations/versions/0079_captured_report.py — static DDL and SQL guards.
- src/reality/services/captured_report.py — internal build/publish/read/discard.
- src/reality/services/cost_captured_summary.py — existing SQL aggregation reuse.
- tests/test_captured_report.py — 14 cases including one parametrized test.
- config/data_model.yaml, resource_catalog.yaml, tenant_isolation_catalog.yaml — registered
  tables and four new operations; the last verified operation count is 529.

## Open functionality, in practical continuation order

| Area / task | Actual remaining work |
|---|---|
| Captured report integration — T194, T195–T197 | Delivered: typed fixed relation/context, saved analyses, bounded discovery, graph/MCP/HTTP tool path and Analysis selector/explanation. Existing historical selectors retain their semantics. This remains a bounded known-subtotal diagnostic, not financial company publication. |
| Shared worker and scale — T080, T198–T203, T089 | Delivered: owner-authorized idempotent build and separate CAS publication of one sealed captured basis through the shared worker. Still open: census/basis orchestration, extension beyond ten subjects with an explicitly reviewed model and exact chunk closure, and fixture-J/reference-host qualification. Do not simply raise the bound or hold a database snapshot across worker children. |
| Full-company financial admission/context — T079/T080/T081 | Prove economic inclusion of all relevant subjects and source/header gaps, common supported financial input retention and historical knowledge semantics. Current captured selection does not satisfy this requirement. Only then specify when final company totals/rates are eligible. Do not substitute observed_at for knowledge_at or invent one common policy/profile from separate reviews. |
| Explainable operational UI/Inspector — T078, T088 | Complete the actual EK → inventory consumption → DB1/DB2 flow on operational pages and Analysis results, with shortest record/source links and exact/display precision. Extend record inspection for new census/basis/cache families as needed. Earlier cost.record.get/Inspector work exists; do not rebuild it. Run the specified user explanation/source-finding acceptance protocol. |
| Cost findings — T082 | Integrate missing acquisition evidence, unassigned components, stale review and supported negative actual DB1 with existing exception projection, queue and count contracts. Keep unknown/unevaluated distinct from cleared; preserve the old agreed-price exception. |
| Source-backed demo — T083 | Extend canonical demo profiles/intake through normal services: complete fixture A, missing-cost case and late-cost/return story. Preserve setup/source controls and confirmation authority; no fabricated financial approvals or second demo queue. |
| Broader inventory cases — T084 | Production admission/history for evidenced opening stock, specific identification, original-issue return matching, loss/corrections and consignment/transit ownership. Existing pure calculation capability is not proof these production flows are delivered. |
| Broader commercial matching — T085 | Split/partial billing and fulfilment, signed credits/returns, direct-service/shipping-only scopes, free goods and supported kit/production evidence; disjoint amount/quantity conservation and rematching/replacement history. Unsupported cases must remain explicit. |
| Acquisition-to-carrying-value bridge — T086 | Implement separately evidenced valuation assessments/write-downs/recoveries with ceiling, dates, owner confirmation and immutable history. Carrying-value slots and nulls are not this functionality. Verify primary HGB sources during that design; do not alter commercial DB definitions or claim statutory compliance. |
| Allocation/tax/conversion — T087 | Complete reviewed weighted allocation proposals and the remaining received nonrecoverable-tax, mixed source bucket, conversion and reduction scenarios. Retain original precision, residuals and deterministic rounding. Do not infer skonto from payment differences or double-count reductions. |
| Product qualification/release — T089/T090 | Required full backend/frontend/migration/catalog/docs/spec checks, actual integrated performance and usability evidence, review-owned acceptance, then separate merge/deployment authorization. A passing bounded backend slice does not close these gates. |

This table describes outstanding implementation, not a promise that every old unchecked
line means a missing implementation. T078–T081 were written before many later deliveries;
their original “missing” evidence is historical. Follow the later completed subtasks and
actual code. No full-company/HGB-ready completion claim has been made.

## Non-negotiable boundaries for the next step

- Current captured basis/report maximum: ten combined inventory/contribution subjects.
  Census verification has its separate bounded full-capture limit; neither proves scale.
- Currency/base-unit partitions stay separate; inventory additionally partitions method
  and owner. Inventory cannot be summed across cutoffs.
- Captured reports expose known subtotals only. All final totals and rates remain null,
  including with full numeric member coverage. financial_publication_eligible is false.
- Unknown subjects remain in retained population coverage; available-only group coverage
  is explicitly labeled. Source/header gaps cannot disappear behind covered row counts.
- Fixed report reads never build, enqueue, replay financial history or flush writes.
  Rows/pages/totals/cursors stay bound to one generation. Later events may make current
  assessment pending, but do not rewrite the old report.
- No live financial policy activation, migration or deployment was performed/authorized by
  these implementation turns. All PostgreSQL proof ran on disposable databases.

## Open verification markers are not all missing features

The following earlier delivery gates remain unchecked, principally because shared release
checks or broader integration are not closed. Audit their acceptance/evidence before closing;
do not mark them all complete and do not reimplement their already delivered code:

T049, T050, T056, T060, T065, T071, T077, T095, T100, T108, T116, T120, T124,
T128, T132, T136, T140, T144, T148, T153, T157, T161, T165, T169, T173, T177, T185.
T078–T090 retain broader feature obligations; T194 is the immediate open integration task.
Reviewer-owned checklist markers are unchanged. Prior permission to continue despite
remaining checklist gates persists; do not repeatedly ask for the same permission.

## Last verified evidence and environment

- captured-report-regression.txt: 179 passing tests, including 13 new report cases.
- captured-report-publication.txt: one additional publication transition case passes.
- captured-report-generation-compatibility.txt: 58 passing existing generation/graph tests.
- 73 docs tests and eight reference tests pass; 15 generated references reproduce exactly.
- Scoped lint: eight files pass; seven files pass formatting. The shared db/core.py has an
  unrelated authentication-field formatting finding outside this import-only change.
- Last src/tests-wide lint: 12 unrelated import findings, recorded in
  evidence/captured-report-global-lint.txt. Recheck actual state after restart; do not
  assume an old count or apply global --fix to shared work.
- Spec policy and git diff --check passed. Test counts overlap and are not total coverage.
- Branch at checkpoint: 242-inventory-cost-contribution. Last observed sole migration head:
  0079_captured_report. Recheck heads before adding migrations; other work shares the tree.
- Working tree is intentionally dirty and contains unrelated parallel changes, including
  specs 225/235/238/239. No commit was created. Do not reset, clean, stage all or overwrite
  unrelated edits. Changes for 234 include untracked files and must be preserved.
- All test processes exited; the owned PostgreSQL container and temporary volume were
  removed. No database process from this feature needs resuming or cleaning up.
- Run Ruff from packages/reality-core, not repository root, to preserve import grouping.
  Existing make invocation was blocked by the local Xcode license; direct script equivalents
  were used. No extension hooks were present in .specify/extensions.yml at last inspection.
- If tests need PostgreSQL, create a new disposable instance and use TEST_POSTGRES_ADMIN_URL;
  local socket/TCP access required tool sandbox escalation in this environment. Never reuse
  a live company database for these migration/concurrency proofs.

Spec impact of this handoff: none. It records delivered behavior and existing unfinished
requirements; it does not add schema, change runtime behavior or close acceptance gates.
