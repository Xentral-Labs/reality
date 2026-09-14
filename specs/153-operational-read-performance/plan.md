# Implementation Plan: Operational read performance

## Technical Context
Python 3.12, SQLAlchemy 2, PostgreSQL; shared service reads and existing disposable projection cache. No frontend change is initially required. Active worktree deployment per docs/LOCAL_STACK.md.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Preserve complete outputs and trace links; input loading only. |
| Reality authority | PASS | No document status or derived authority added. |
| Proven schema | PASS | No schema changes. |
| Tenant/service boundaries | PASS | Every batch query scoped; evaluation checks session and tenant; adapters call shared services. |
| Specification and tests | PASS | Approved scope; tests precede implementation; full required gates before completion. |
| Explainable Web | PASS | Existing payloads and links unchanged. |
| Simplicity/storage | PASS | No dependency, persistent cache, job or transport business rule. |
| Received values | PASS | Existing canonical commitment and correction rules reused; no recomputation of stated money. |

## Design and files
1. Add a shared movement aggregation query in services/core.py; scalar and batch readers use the same correction subtraction.
2. Add services/exception_inputs.py with invocation-scoped, tenant/session-bound bulk inputs. Extract the existing pure latest-stated-value rule from core commitment readers and reuse it with identically ordered revisions; read revision counts, movement sums, documents, lines, items and active reservations once. Fall back to canonical per-record reads if READ COMMITTED exposes a new identity after the batch load; do not fail on concurrent intake. Keep input context in a ContextVar with token reset in finally. It is used only by exception helpers, never by mutations or future requests.
3. Adapt services/exceptions.py input helpers to those inputs when inside operational_exceptions; retain uncached helper paths as parity reference and for direct calls. Evaluate the three commitment classes once per complete evaluation, retaining class registry and final ordering.
4. Extract the existing financial projection builder in services/projections.py. Add targeted refresh for OPEN_FINANCIAL_ITEMS with its own checkpoint while retaining full refresh behavior for existing explicit refresh callers. Register the shared refresh service in config/tenant_isolation_catalog.yaml with existing mutation/relationship classification. Update web/read_models.py and projection_rows to call the scoped service refresh.
5. Add tests/test_operational_read_performance.py for parity, bounded input queries, cleanup/freshness/isolation and targeted finance refresh/page/totals. Reuse business fixture and canonical mutating services in test databases.

## Test strategy
Observe failing query-budget and finance unrelated-refresh tests first. Compare a complete exception evaluation with individually invoked existing derivators at fixed as_of, including revisions and corrections. Run all existing exception, movement, finance, materialized projection, read-model, API and tenant tests, then full backend suite, lint, spec policy and frontend/site gates required by the repository. Record baseline and final local browser/resource and service query measurements.

## Rollout and rollback
No migration. Save pre-edit versions of touched dirty files outside the repository. Build and recreate matching local code services without restarting database/storage or touching demo controls. Roll back by restoring only this change and rebuilding those images. Existing full refresh repairs disposable projections without changing facts.

## Risks and review
Batch inputs retain tenant data during one exception evaluation; this improves query cost, not a claim of constant memory at arbitrary company size. Concurrent intake remains governed by existing read/refresh transaction semantics. Avoid adding TTLs or advancing unrelated checkpoints. Review output parity, correction semantics, nested context cleanup and same-session freshness.

## Complexity Tracking
No constitutional exceptions. Scope acceptance is the user's optimization approval; no schema or business decision requires separate approval.
