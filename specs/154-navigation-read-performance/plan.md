# Plan: Navigation read performance

## Technical Context
Existing React/TypeScript localization core, shared Python/SQLAlchemy/PostgreSQL services. Depends on spec 153. No dependencies or schema changes.

## Constitution Check

| Principle | Result | Reason |
|---|---|---|
| Source → Evidence → Reality | PASS | Existing payloads, amounts and evidence paths preserved. |
| Reality authority | PASS | Only lookup cost and disposable projection work change. |
| Proven schema | PASS | No schema. |
| Tenant/service boundaries | PASS | Existing tenant-scoped payment_rows and refresh service reused. |
| Tests before implementation | PASS | Failing lookup and projection regressions precede edits. |
| Explainable web | PASS | No browser business rules or label/layout changes. |
| Simplicity/storage | PASS | One catalog-sized in-memory index; no business-value memoization or infrastructure. |
| Received values | PASS | Financial builder extracted unchanged; no new calculations. |

## Design
- apps/web/src/localization-core.ts: createCanonicalSourceResolver builds a reverse Map lazily on first use; insert only the first occurrence to retain Object.values/Object.entries ordering. The returned function never stores lookup arguments. Catalogs are immutable after module initialization.
- apps/web/src/localization.tsx: replace canonicalSource's repeated scan with that shared resolver; keep translateTree, original-content checks, language switching, text-update tracking and formatting unchanged.
- apps/web/scripts/localization-contract.test.mjs: every real dictionary translation plus unknown/blank/collision input parity; proxy ownKeys counters prove late initialization and bounded traversal. Existing DOM boundary and language tests retained. Synthetic before/after timing is diagnostic, not a flaky unit-test threshold.
- packages/reality-core/src/reality/services/projections.py: extract unchanged payment builder; extend selective refresh and read-only derive to PAYMENTS. Existing full refresh continues to build all views.
- packages/reality-core/tests/test_payment_projection_performance.py: canonical parity, no unrelated refresh, event freshness, reversal, complete filtered currency totals, empty/foreign tenant and checkpoint stability.
- docs/SPEC_COVERAGE_MATRIX.md records the new test family.

## Validation and rollout
Run focused tests first, then complete backend, frontend, lint and spec gates. Review the diff, transfer only these changes into the port-8080 integration worktree, build matching core services plus web, and repeat actual sidebar/tab clicks. No migrations or demo-control changes. Keep pre-edit local copies for a scoped rollback. Publish a stacked follow-up PR after verification, without merging either PR.

## Risks
Reverse lookup must preserve collisions rather than choosing a new canonical label. Lazy construction must happen after all module-level Object.assign calls. No invalidation mechanism is added because runtime catalog mutation is absent. The index holds catalog strings only. Payment refresh must not advance unrelated checkpoints. Do not change the already-direct journal API.
