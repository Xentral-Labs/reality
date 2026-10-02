# Implementation Plan: Shared Inventory Observations

**Branch**: `codex/journey-consistency` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

Unify inventory calculations in one application service, retain bounded SQL pagination on Web, and correct existing projection metadata. Implement domain reuse → service query → existing tool reads → Web delegation, test-first.

## Technical Context

- Python 3.12+, SQLAlchemy 2, PostgreSQL, Decimal; existing FastAPI and TypeScript adapters.
- pytest service/story/adapter coverage using isolated PostgreSQL; Ruff and existing documentation/Web gates.
- Preserve set-based queries and PostgreSQL filtering/pagination. No per-item query loop.
- Base: `origin/main` commit `590c4d72`; no migration or dependencies.

## Constitution Check

| Principle | Before design | After design | Evidence |
|---|---|---|---|
| Source → Evidence → Reality | PASS | PASS | Existing records and movement links retained |
| Reality owns operational state | PASS | PASS | No document status introduced |
| Proven schema | PASS | PASS | No schema change |
| Tenant/service boundaries | PASS | PASS | Every aggregate scoped; Web delegates |
| Specification/test evidence | PASS | PASS | Owner-approved scope; failing regression first |
| Explainable Web | PASS | PASS | Same observations and provenance |
| Simplicity/storage | PASS | PASS | SQL service, existing lifecycle expressions |
| Received values | PASS | PASS | Read-time observations only |

## Project Structure

- `services/inventory_reads.py`: shared SQL position query and paginated read.
- `db/pagination.py`: storage-level pagination value object; preserve the existing Web import contract through re-export.
- `services/core.py`: existing inventory service delegates quantity derivation, retaining movement explanation lists.
- `web/read_models.py`: compatible forwarding adapter for inventory pagination.
- `config/projection_catalog.yaml`: accurate inputs, outputs and descriptions.
- `tests/test_shared_inventory_observations.py`: comparisons, revised/partially fulfilled promises, scope, filtering and projections.
- `docs/features/inventory.md`, generated Tool Usage references: durable contract and executable vocabulary.

## Verification and Review

Run regression first and observe failure. Run focused stock, projection, query and adapter coverage, then full backend suite and required Web gates. Regenerate documentation and verify a second generation produces identical artifacts. Review SQL tenant predicates, correction-aware incoming, transfer conservation, pagination and absence of adapter business arithmetic.

## Rollback

Revert code and generated references together. No data migration or write changes. Evaluate a projection-version increase only if previously materialized inventory quantities change.

## Complexity Tracking

No Constitution exceptions.

## Verification-blocker remediation (2026-10-02)

Spec impact: none for the additional performance refactor. Existing spec 146 FR-033 and spec 234 retained-inventory contracts remain unchanged. Profiling the existing setup timeout found 26,000 SQL round-trips, including repeated immutable inventory input identity reads. Batch those bounded tenant-scoped identities in `services/inventory_costing.py:_inputs`, preserving every integrity check, missing/foreign refusal and received value. No cache survives a service call, no confirmation is skipped, and the production 120-second setup limit is unchanged. Add query-count and scope regressions to `tests/test_inventory_costing_services.py` first; compare retained outputs, then rerun setup and full CI gates. All Constitution rows remain PASS; no new schema, dependency or business behavior.
