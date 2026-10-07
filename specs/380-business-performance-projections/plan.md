# Implementation Plan: Incremental Business performance
**Branch**: `feat/business-performance-projections` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary and Technical Context
Python 3.12+, SQLAlchemy 2, PostgreSQL, Alembic, React/TypeScript. Add typed disposable cache rows for orders and correspondence because cohort filtering, deadlines and keyset ordering require indexes. Retain summary/generation progress in the existing `ProjectionRow` and `ProjectionCheckpoint`. No new scheduler, queue or business authority.

## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Opaque document/source/commitment links retained | PASS |
| Reality owns operational state | Worker recomputes derived caches; booking services never read caches | PASS |
| Proven schema only | Indexed flags, ordering, transitions and tenant/generation uniqueness serve FR-003/005/007 | PASS |
| Tenant + shared service boundaries | Every query scoped; owner API unchanged; shared projection jobs | PASS |
| Spec/test traceability | Requirements map to tests and tasks below | PASS |
| Explainable web behavior | Existing metrics and Inspector links retained, freshness added | PASS |
| Received values not recomputed | Received dates/values retained, operational observations disposable | PASS |
| Smallest coherent design | Existing queue/checkpoints; two indexed cache tables instead of new broker | PASS |

## Repository Structure and Layer Changes
`db/business_projection.py`, additive Alembic migration, `services/business_projection.py`, `services/business_projection_derivation.py`, `services/projections.py`, `services/projection_jobs.py`, `web/interactions_api.py`, `apps/web/src/unified/BusinessLive.tsx`, `apps/web/src/api.ts`, `tests/test_business_projection.py`, `scripts/benchmark_business_projection.py`. The existing `services/business_performance.py` is unchanged and serves as the oracle. No new domain booking rules or agent tools.

## Design
### Reality and service flow
Business event subject → recorded related document/commitment/movement/reservation/payment → bounded affected-order selection → canonical `core.commitment_terms` and `projections._open_work_rows` → replace cache row and subtract/add its summary contribution in one transaction. Stock/item/party fan-out is keyset-paged; corrections follow original, compensating and replacement movements. Unknown subjects conservatively rebuild rather than lose changes.
Correspondence sources resolve exact namespace/message identities and acknowledgements; cached summaries separate unread from unanswered and unknown completion.

### Data and migration impact
Two tenant/generation scoped derived tables. Order flags and mail cohorts have composite paging indexes; order transition timestamps schedule clock changes. Generic projection summary payload holds active/building generation, source scan cursors, counters and current event fan-out cursor. A rebuild scans orders then mail in bounded pages with a retained starting sequence. On publication checkpoint advances only to that starting sequence; events committed during the build are replayed afterwards. Reads retain the old published generation until atomic pointer/counter publication. Obsolete generations are removed in bounded chunks.

Newly enqueued Business refreshes receive the earliest shared FIFO timestamp; older work remains ahead, preserving tenant/queue fairness without a private queue. Finite allowlisted cohort SQL literals keep partial indexes eligible even with generic prepared query plans. Source reply indexes hash long identities and verify the full retained value, avoiding B-tree key-size failures without truncation.

### Failure, security and tenant behavior
Shared `projections.refresh` serializes tenant cache builders and fences claims. Bounded chunk rows, totals and progress commit with run success. Failed transactions publish nothing. Replay computes current contributions and subtracts retained old contributions, never increments booking effects. API keeps owner authorization; cursors encode tenant, generation, filter and sort key, reject mismatches. Reads are side-effect free. Clock expiry and backlog remain visibly delayed until processed.

## Test Strategy and Traceability
| Requirements | Tests before implementation | Proof |
|---|---|---|
| FR-001/002/008, DR-001/003 | `tests/test_business_projection.py` | all counters/cohorts oracle, amendments/correction/cancellation, replay |
| FR-003 | same file | clock risk/overdue/hourly expiration |
| FR-004 | same file | acknowledgement ≠ reply ≠ completed work; exact lineage |
| FR-005/006, DR-002 | same file; Web contracts/browser | pagination, isolation, stale/read-only, owner authorization |
| FR-007 | same file | rollback/restart, concurrent rebuild/publication, shared dispatch |
| FR-009 | `scripts/benchmark_business_projection.py`; `benchmark.md` | synthetic 100-viewer timings and million-order test plan |
Required gates: `make spec-check lint business-annotations-check test web-build docs-catalog-check`, migration upgrade/downgrade and focused browser proof. Record failed/unavailable checks without completion claims.

## Rollout and Rollback
Apply additive migration before new worker/API code; no startup migration or production deployment. Bootstrap automatically via existing internal projection discovery. Old API code can read Reality while caches remain unused. Drain business projection refresh runs before schema removal. Cache deletion never removes Reality or event records. Large rebuild completion and legacy unrelated projection costs may limit fleet lag; measure rather than claim capacity.

## Review Risks
Fan-out coverage, duration precision, timestamp boundary equality, event backlog and concurrent build publication, old-generation cleanup, shared worker fairness, ancillary inventory/financial readers, baseline tests expecting synchronous reads.

## Complexity Tracking
No constitutional exception. The user explicitly requests and authorizes this implementation and its disposable schema; PR review retains merge authority.
