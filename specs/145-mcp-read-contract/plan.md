# Implementation Plan: Seven MCP Read Improvements

**Branch**: `145-mcp-read-contract` | **Date**: 2026-09-08 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary
Keep existing business calculations and list consumers; add shared read contracts, metadata and tenant/filter-bound continuation. Public MCP defaults to pages; internal existing calls remain lists. Finance changes deliberately to balances by currency. Retained order explanation reuses delivery_case and document_detail instead of the open queue.

## Technical Context
Python 3.12+, SQLAlchemy 2, PostgreSQL, Decimal and UTC. No dependency/schema changes. pytest on temporary PostgreSQL databases. Current main 2183b88, isolated worktree. Existing environment Python can run with project pytest pythonpath; no global editable-install changes.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Read retained document/line/source/effect links | PASS |
| Reality owns state | Stock/reservations and delivery_case determine observations | PASS |
| Proven schema only | No business table or field change | PASS |
| Tenant and service boundaries | Shared services validate every tenant/reference/cursor | PASS |
| Spec/test traceability | All nine FR and three DR mapped to test tasks | PASS |
| Explainable web | No UI changes; internal list consumers preserved | PASS |
| Received values | Only balances/stock derived; source values untouched | PASS |
| Simplicity | Existing derivation builder reused; live keyset, no stored snapshots | PASS |

Post-design review: all checks remain PASS. No exceptions.

## Repository Structure and Layer Changes
- `packages/reality-core/src/reality/services/read_contracts.py`: pagination, metadata, currency and location reads; read-only orchestration.
- `services/core.py`: discovery statement/serialization reuse and mapped direction correction.
- `services/projections.py`: unit/revision fields, public non-persisting derivation and retained explanation reusing shared services.
- `tools/application.py`: dispatch page vs legacy through shared handlers.
- `mcp/catalog.py`: existing names/permissions, page defaults and filter schemas.
- `config/command_catalog.yaml`: accurate guidance for changed reads.
- `config/tenant_isolation_catalog.yaml`: register new scoped diagnostic boundaries with executable evidence.
- `docs/SPEC_COVERAGE_MATRIX.md`: map the durable contract and new test family.
- `tests/test_mcp_read_contract.py`, affected existing tests: service/story/transport proofs.
- `docs/features/mcp_reads.md`, `docs/features/chat.md`, generated `apps/docs/content/{,de/}catalogs/mcp-tools.md`: output migration and persistence contract.

## Design
Shared SQL discovery statement uses tenant scope, optional query/record ID, ascending ID and `id > cursor`; fetch limit+1. Cursor is bounded base64 JSON containing version, scope digest and last key; it grants no authority. Every query applies tenant scope independently. Live keyset semantics are explicit; no false event-sequence snapshot guarantee.

Existing operational builder produces deterministic rows without writes for page-mode reads; paginate sorted row keys. Existing projection_rows remains cached for legacy callers. Add unit and original/effective promise fields to the shared builder, bump derivation version so old caches refresh. Location rows reuse stock_at/active_reserved and open supplier quantity; explicitly requested zero-stock locations are included. Aggregate view remains default; location mode is explicit or selected by location filter.

Order resolver prioritizes opaque document/commitment identities; ambiguous display references fail. Reuse document_detail and delivery_case to include closed records; top-level source/reservations/movements and fulfillment remain available, with additive evidence and metadata. Closed commitments cannot imply executable demand/readiness.

Finance groups only receivable/payable accounts by recorded currency, normalizing signs by account; zero/negative balances remain valid and no artificial EUR row is introduced.

Metadata includes tenant, filters, observed_at, read contract version, derivation version where applicable, observed local event sequence, unknown upstream freshness, live consistency and persistence flags. Direct reads use no_autoflush and do not commit; authentication last_used_at remains outside this boundary.

## Test Strategy and Traceability
All new tests live in `tests/test_mcp_read_contract.py`; update existing discovery assertions for the public default envelope while retaining explicit legacy tests.

| Requirement | Test | Expected initial failure |
|---|---|---|
| FR-001 FR-002 | currencies, empty/foreign balances, ledger direction | false EUR / missing attribute |
| FR-003 FR-004 | units, mismatches, revisions, two locations/filter/zero | missing unit/location fields |
| FR-005 | fulfilled/cancelled/mixed orders, ambiguity/provenance | open-queue-only lookup |
| FR-006 FR-007 | >100 pages, malformed/foreign/filter cursor, metadata | raw truncated list |
| FR-008 FR-009 | SQL read-only guard, MCP defaults, internal/legacy lists | cache writes / missing new schema |
| DR-001 DR-002 DR-003 | evidence/tenant/Decimal checks across stories | missing explicit contract |

## Rollout and Rollback
No migrations. Public list responses default to `{records,next_cursor,has_more,metadata}`; clients using raw lists must read records or explicitly request legacy. Application list defaults and web projection endpoints stay compatible. Finance uses `{balances,metadata}` without the old mixed-currency response. Deploying is outside this task. Rollback code together with catalog/docs; no authoritative data cleanup.

## Review Risks
Wrong unit basis; location null interpreted as aggregate; duplicate human references; live paging mistaken for a snapshot; accidental cached read in direct diagnostics; response-format compatibility. Full derivation cost is retained for operational pages: responses are bounded, not a new scalable analytics backend.

## Complexity Tracking
No constitutional exceptions or schema expansion.
