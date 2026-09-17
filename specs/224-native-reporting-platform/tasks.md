# Tasks: Graph-Native Reporting Platform

**Input**: spec.md, plan.md, data-model.md, contracts/native-reporting.md, research.md.
**Status**: Planning only. Every implementation and proof task is open.
**Gate**: Accepted product direction. Run cross-artifact analysis before implementation.
The fan-out, unit and additivity fixtures (T004) precede the compiler that satisfies them,
because they are the acceptance criterion for the whole design.
Paths are relative to the repository root. Tests precede the code they prove.

## Phase 1: The Declaration

- [ ] T001 [DR-003] Record the cross-artifact analysis and the withdrawal of the barrier-view, per-tenant-role and engine-gate design in `specs/224-native-reporting-platform/review.md`; confirm no unresolved critical finding and that ADR 0004 no longer constrains this feature through role provisioning.
- [ ] T002 [FR-001, FR-013, DR-002, DR-003] Add declaration validation tests in `packages/reality-core/tests/test_reporting_graph_declaration.py` — node without grain, node without correction semantics, measure without unit or additivity, edge without multiplicity, recursive edge without depth bound, declaration drift against the live schema — then implement the types and loader in `packages/reality-core/src/reality/domain/reporting_graph.py` and `src/reality/services/analytics/graph_model.py`. An invalid declaration must fail at load, not at query time.
- [ ] T003 [FR-001, FR-002, DR-001, DR-002] Write the first-slice declaration in `packages/reality-core/config/reporting_graph.yaml` for the eleven nodes, twelve edges and seven measures in `data-model.md`, and generate the discoverable catalog from it in `src/reality/services/analytics/graph_model.py`. Bind each measure to its canonical service where one exists; record each node's evidence route and temporal coverage.

## Phase 2: US1 and US2 — Traversal That Cannot Silently Double Count

Independent proof: a EUR 1,000 order with four lines returns 1,000; a two-currency sum
is refused; `open_balance` grouped over time is refused.

- [ ] T004 [US1, US2] [FR-003, FR-004, FR-005, DR-002] Add the correctness fixtures in `packages/reality-core/tests/test_reporting_graph_traversal.py` before any compiler code: order-grain measure along a 1:n edge, a measure reachable by two paths of different multiplicity, two sibling fan-out edges in one path, mixed currencies, missing amounts, NULL versus zero, non-additive measure over time, distinct counting after fan-out. Add the correction cases from `scale-and-updates.md`: a reversed posting group and a corrected movement must net out in a measure sum while a naive row count over the same rows is refused, and a `revise` node must resolve to its latest revision. Record the equivalent hand-written SQL returning the wrong total alongside each case, so the guarantee is visible rather than assumed. Assert the emitted statement count is exactly one per traversal — an eleven-thousand-query builder is the failure mode this compiler could most easily reproduce, and a correctness-only test would not catch it.
- [ ] T005 [US1, US2] [FR-003, FR-004, FR-004a, FR-005, FR-010, DR-001, DR-002] Implement the query form, effective-grain computation, fold-or-refuse rule, correction semantics, unit and additivity checks in `packages/reality-core/src/reality/services/analytics/traversal.py`, statement generation in `compile_sql.py`, and path-derived evidence in `lineage.py`. Add the prior-year customer comparison and monthly product ranking fixtures, including one-period customers and two currencies. A refusal must name the edge that caused it and offer the measure that lives at the traversed grain.

## Phase 3: US6 — The Boundary the Compiler Now Carries

Independent proof: no authoring input reaches SQL text; two tenants with overlapping
labels and foreign canaries stay separated under adversarial authoring.

- [ ] T006 [US6] [FR-006, FR-011] Add adversarial authoring tests in `packages/reality-core/tests/test_reporting_graph_isolation.py`: identifiers, labels, parameters, depth values and path elements crafted to escape; undeclared node, edge and measure references; a foreign tenant id supplied as a parameter; canary rows in a second tenant. Assert the tenant predicate is present on every node of every generated statement, including inside recursive common table expressions and independent branches.
- [ ] T007 [US6] [FR-006, FR-011] Implement tenant predicate emission, the reporting connection identity, depth bounds, cycle guards, admission limits, statement timeout, result-size limits and clean cancellation in `packages/reality-core/src/reality/services/analytics/compile_sql.py`, `execution.py` and `admission.py`. Reporting never uses the operational connection identity.

## Phase 4: US1 — Authoring Surfaces

Independent proof: the same question authored as an object and as text produces one
identical internal query, fingerprint and result.

- [ ] T008 [US1] [FR-007] Add typed query object validation and round-trip tests in `packages/reality-core/tests/test_reporting_graph_surfaces.py`, then implement the object surface in `packages/reality-core/src/reality/domain/reporting_graph.py` and `services/analytics/traversal.py`.
- [ ] T009 [US1] [FR-002, FR-007, FR-009] Implement the Cypher-near text surface in `packages/reality-core/src/reality/services/analytics/cypher_surface.py` using the parse-then-admit shape of `sql_parser.py`; assert surface parity and sanitised errors in the same test module. Document the deliberate `RETURN` divergence in the generated catalog, and publish catalog and examples through `src/reality/tools/analytics.py`, `src/reality/mcp/catalog.py`, `src/reality/web/analytics_api.py` and `src/reality/cli/app.py`.

## Phase 5: US3 — Durable Reports and Compatibility

Independent proof: exact draft reload, confirmation, save and reopen, lost-response
retry, spec-222 parity, owner and tenant isolation.

- [ ] T010 [US3] [FR-008, FR-012] Add model-version envelope, immutable draft, pending proposal, exact decimal and retry tests in `packages/reality-core/tests/test_reporting_graph_lifecycle.py`; then implement them across `packages/reality-core/src/reality/domain/reporting.py` and `services/analytics/drafts.py`, `proposals.py`, `reports.py`. No compatibility mapping for earlier definitions is built — none shipped. The drafts table arrives with this feature's own migration.

## Phase 6: US4 — Time and Evidence

Independent proof: late corrections keep honest coverage; unsupported historical states
fail explicitly; example values navigate to their records.

- [ ] T011 [US4] [FR-009, DR-001] Audit the actual history fields and correction paths per node into `specs/224-native-reporting-platform/temporal-coverage.md`, then add current, activity-period, as-of-effective, as-of-knowledge and unavailable-contributor fixtures in `packages/reality-core/tests/test_reporting_graph_temporal.py` before publishing any capability.
- [ ] T012 [US4] [FR-009, FR-010, DR-001] Implement coverage and explanation contracts in `packages/reality-core/src/reality/domain/reporting.py` and `services/analytics/graph_model.py`, `lineage.py`; read `docs/WEB_SPEC.md`, add browser acceptance in `apps/web/scripts/reporting-browser.mjs`, then surface the traversal path, coverage and evidence through `apps/web/src/unified/analytics/`, `apps/web/src/api.ts` and `apps/web/src/localization.tsx`. Respect the register paragraph font rule: no `<p>` as a workbench first child.

## Phase 7: US5 and capacity

- [ ] T019 [FR-011] Measure the first-slice questions against the scale fixture tooling and add the covering indexes named in `scale-and-updates.md` — `(tenant_id, ordered_at) INCLUDE (gross_amount, currency, party_id)` on `document`, `(tenant_id, document_id) INCLUDE (item_id, gross_amount, quantity)` on `document_line`, `(tenant_id, party_id, ordered_at)` on `document` — in a migration under `packages/reality-core/migrations/versions/`. Record before and after on a quiet machine, baseline and change back to back. None of the node tables carries a composite index today, so this is measured work with a known shape, not speculation; add no index that a measurement does not justify.
- [ ] T013 [US6] [FR-011] Add cross-process admission, cancellation, timeout, oversized result and pool eviction fixtures in `packages/reality-core/tests/test_reporting_graph_budgets.py`; implement the remaining controls, then record measurements in `specs/224-native-reporting-platform/benchmark.md` including row width, skew, indexes, hardware, concurrency and ingestion impact. Measure on a quiet machine and compare baseline and change back to back. Expensive stages may stay unrun if recorded as unverified.
- [ ] T015 [US5] [FR-013] Prove declaration-only extension in `packages/reality-core/tests/test_reporting_graph_extension.py`: add one recursive edge, one node and one measure as configuration, answer a bounded variable-depth question, assert cycle termination and refusal of unbounded depth, and assert the change set contains no diff outside `config/` and its test. Include one `fact`-backed extension node with an explicit cast and a failing-cast case.

## Final Phase: Cutover, Documentation, Verification

- [ ] T014 [FR-012, DR-003] In the same change that makes the graph live in chat and web, remove the replaced generation: `packages/reality-core/src/reality/services/analytics/catalog.py`, `comparison.py`, `contributors.py`, `finance.py`, `operations.py`, and `apps/web/src/unified/analytics/AnalyticsExplorer.tsx`, `AnalyticsPivot.tsx`, `useAnalyticsExecution.ts` with their styles. Rewrite the tests that cover them against the graph rather than deleting the coverage. `orders.py` stays — measures bind to its canonical received values.
- [ ] T016 [FR-014, DR-003] Rewrite `specs/224-native-reporting-platform/engine-comparison.md` as a deferred measurement: the trigger condition, the three reference questions, the hard gates, and the statement that the stored query form carries no dialect. No cloud account, cost, tenant-data transfer or second engine is authorised. Re-check SQL/PGQ availability in PostgreSQL core at the same review.
- [ ] T017 [FR-001, FR-002, DR-003] Update `docs/features/analytics.md`, `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md` and `packages/reality-core/config/resource_catalog.yaml`; classify every new public core function in `tenant_isolation_catalog.yaml` and bump the pinned count; regenerate the public command and MCP reference via `apps/docs/scripts/generate-catalog-reference.py`. Use the agreed German ERP vocabulary in the German documentation.
- [ ] T018 [all] Run the full PostgreSQL backend, migration and isolation suites, package Ruff, web build, contracts, browser and locale checks, and the spec and reference checks; record results and actual runtime status in `specs/224-native-reporting-platform/verification.md`. Remember that CI runs in file order with no shuffling, so a green shuffled local run proves nothing on its own.

## Dependencies and Delivery

T001 → T002 → T003 establishes the declaration. T004 precedes T005; both precede
everything that consumes a result. T006 precedes T007, and T007 must pass before any
surface is exposed, even though capacity is a P2 story. T008 → T009 add the surfaces.
T010 follows T005. T011 may run independently after T003; T012 follows T005 and T011.
T013 follows correctness, and T019 follows T005 because an index is justified by a measurement, not by a guess. T015 may run any time after T005 and is the clearest single
demonstration that the design achieved its purpose. T014 follows T007, T009, T010 and
T012. T016 is documentation and may run at any time. T017 and T018 close the release.

Independent work is available on T004 and T011, or T008 and T013, but shared
implementation modules must not be edited concurrently without coordination — another
session is active in this working tree. Stage by path and verify from a clean checkout.

No task authorises a live provider replay, report deletion, cloud data transfer, a
second database engine, a database extension or a new business table.

## Requirement Coverage

| Requirement | Tests | Implementation and documentation | Status |
|---|---|---|---|
| FR-001 | T002 | T003, T017 | Pending |
| FR-002 | T002 | T003, T009, T017 | Pending |
| FR-003 | T004 | T005 | Pending |
| FR-004 | T004 | T005 | Pending |
| FR-004a | T004 | T005 | Pending |
| FR-005 | T004 | T005 | Pending |
| FR-006 | T006 | T007 | Pending |
| FR-007 | T008, T009 | T008, T009 | Pending |
| FR-008 | T010 | T010 | Pending |
| FR-009 | T011 | T012 | Pending |
| FR-010 | T004, T011 | T005, T012 | Pending |
| FR-011 | T006, T013 | T007, T013, T019 | Pending |
| FR-012 | T010, T014 | T014 | Pending |
| FR-013 | T002, T015 | T003 | Pending |
| FR-014 | — | T016 | Pending |
| DR-001 | T011 | T003, T005, T012 | Pending |
| DR-002 | T004 | T003, T005 | Pending |
| DR-003 | T002, T015 | T001, T014, T016 | Pending |

SC-001 maps to T004 and T005; SC-002 to T004; SC-003 to T010; SC-004 to T011 and T012;
SC-005 to T006 and T007; SC-006 to T015; SC-007 to T013. All execution evidence is
pending; no task is complete.
