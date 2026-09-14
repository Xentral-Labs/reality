# Implementation Review

## Pre-implementation review — 2026-09-09

The owner approved spec 147 and then explicitly instructed implementation after the proposed technical-review → tests → implementation sequence. This authorizes proceeding with the prepared bounded schema and implementation. It does not authorize live deployment. The custom checklist markers remain unchanged as required by the implementation skill; the review findings below record the technical assessment instead of claiming an item-by-item owner review.

- Requirements checklist: 14 checked, 0 unchecked. Reliability checklist: 0 checked, 17 unchecked; proceeding under the explicit implementation instruction, with technical assessment recorded here.
- CHK001–005: separate materialization/consumption, strict UTC cron, revision/request replay, paused retries and queue-cap deferral are defined and testable.
- CHK006–010: token fencing is paired with atomic database effects/run completion; direct network handlers excluded. Tenant catalog discovery is separate from scoped queries. Actor authorization and business confirmation are preserved.
- CHK011–014: cleanup keeps 90-day policy and gains tenant/batch limits. Child-process bounds, retries, independent CLI bootstrap and release-owned migrations have concrete proofs planned.
- CHK015–017: canonical names are reality-scheduler work/tick and reality-worker work/once. Requirements map to tests/tasks; two infrastructure tables have field-level proof and no business schema expansion.
- Repository review found existing cleanup callers in test_email_delivery.py that need the required tenant argument; update that regression alongside new cleanup tests. Existing invitation dispatch remains unchanged.
- Constitution: all eight plan rows PASS. No additional fields or behavior beyond the approved model are required by this review.
- Cross-artifact analysis: 17 FR/DR, 32 tasks, no unresolved critical finding. Runtime proof still pending; no task/acceptance is marked complete based only on design review.

## Final cross-artifact analysis — 2026-09-09

Spec Kit analysis was repeated against spec.md, plan.md, tasks.md and the constitution. Feature prerequisite resolution selected `147-scheduled-jobs`. No extension hooks were configured. The analysis itself was read-only; this evidence is recorded by the implementation workflow.

| Finding | Severity | Disposition |
|---|---|---|
| Initial implementation-status wording differed between prepared docs and delivered code | Low | Reconciled spec, plan, data model, interface contract and canonical/discovery docs. |
| New tenant-aware cleanup and scheduler services required isolation-catalog coverage | High during verification | Registered 14 operations in four evidence-backed families; catalog now expects 340 classified operations. |
| Scheduler rejected-authority outcome was absent from sweep failures; updates accepted two timing sources | High during targeted verification | Regression tests observed failing; both corrected before final acceptance. |
| No unresolved requirement conflict, constitutional exception or critical analysis finding | None | Proceed to final verification; no scope clarification required. |

| Requirement | Test tasks | Implementation / documentation tasks |
|---|---|---|
| FR-001 | T006, T025 | T010 |
| FR-002 | T007 | T011, T012 |
| FR-003 | T004, T008, T016 | T005, T012, T018 |
| FR-004 | T004, T008, T016 | T005, T012, T018 |
| FR-005 | T007 | T011, T012 |
| FR-006 | T004, T015 | T005, T017 |
| FR-007 | T015 | T017 |
| FR-008 | T016 | T018 |
| FR-009 | T020 | T022 |
| FR-010 | T008, T020 | T012, T022 |
| FR-011 | T009 | T013 |
| FR-012 | T021 | T023, T024 |
| FR-013 | T025 | T026, T027 |
| DR-001 | T015 | T017 |
| DR-002 | T004, T008, T009, T016 | T005, T012, T013, T018 |
| DR-003 | T008 | T012 |
| DR-004 | T015 | T017 |

Metrics: 17 FR/DR, 32 tasks, 100% requirement-to-task coverage, no unmapped delivery task, no unresolved ambiguity/duplication and zero critical findings. SC-001 has an explicit ten-interval/two-worker committed-effect proof; SC-002–006 map to coalescing, crash/fencing, process bounds, scoped cleanup and executable documentation proofs respectively. All eight constitutional principles remain satisfied.

## Runtime review

- Additive migration has static SQL independent of runtime model imports, composite tenant FK, occurrence/manual request uniqueness and one unfinished run per schedule. It neither backfills nor activates schedules.
- Queue-cap checks serialize on the tenant row; schedule and run locks follow the documented order. Frozen input/run identity survives retries. Paused rows cannot consume the candidate page ahead of eligible work; tenant cursor survives a partial final catalog page.
- Child execution uses a fresh connection/session and bounded subprocess. Handler commit is rejected; database effect and success are committed atomically. Lost acknowledgement re-reads durable success; stale tokens cannot settle a later claim.
- Initial cleanup only calls the shared scoped retention service. No direct provider call, autonomous transaction or email delivery is registered. Existing delivery regressions remain part of verification.
- Dedicated CLIs bypass the general migration bootstrap. Missing schema fails without creating tables. Status output excludes configuration and claim tokens. Both apps have no public port, use the same shared core and remain optional in Compose.
- No business schema, generic Chat/MCP/web mutation, demo generator or live deployment was introduced. Existing unrelated working-tree edits were preserved.
- Local process/concurrency tests are bounded acceptance evidence, not a production load test or a claim of safety for future network-effect handlers. Each future handler needs its own reviewed effect/idempotency proof.

Final measured gate results are recorded in quickstart.md. Runtime checks do not constitute owner review of the unchanged custom reliability-checklist markers or a live deployment approval.

## Verification decision

Accepted locally on 2026-09-09: complete backend suite 1,500 passed / 8 skipped; final focused regressions 59 passed / 1 opt-in skip; both-image smoke 1 passed. Lint, specification/link checks, migration roundtrip/constraints, Compose validation, site/web/docs builds and i18n audits passed. Seven full-suite skips are retired server-rendered UI tests; the eighth is the separately executed container smoke. No required check remains red. All 32 implementation tasks are complete; live deployment and spec 146's demo integration remain separate work.

## Authorized local stack integration — 2026-09-09

The owner authorized combining this feature with the actual port-8080 checkout (acab690). Preserve the unified app and retired legacy browser routes. Port shared services and source controls into unified CompanySettings/DataSourcesPage; do not restore the old App. Active destinations use /app. Existing pending-admission presentation remains unchanged. Join migration branches with a no-DDL merge revision after the already-tested additive queue/setup migrations, retaining lot expiry. Back up the local database, rehearse upgrade on a restored disposable database, build matching services, and verify the actual localhost surface before replacing the running local containers. No remote deployment or Git merge/commit is implied. Constitution remains PASS; preservation of current domain changes and scoped service authorities are mandatory.
