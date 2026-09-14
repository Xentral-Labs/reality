# Implementation Plan: Shopify Update Guard

**Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

## Summary

Reuse the existing needs-review outcome. In the Shopify interpreter, after returning
an existing interpretation but before context resolution or writes, decline source
versions greater than one. Remove the destructive replacement block. A dedicated
InterpretationNeedsReview subtype supplies a fixed safe explanation; generic exceptions
retain their sanitized explanation. Completed review jobs return None; explicit retry
may record another review. The synchronous helper distinguishes review from stale.

## Technical Context

Python 3.12, SQLAlchemy 2, PostgreSQL, existing pytest fixtures and FastAPI TestClient.
No dependencies, schema, migration, frontend behavior or new public endpoints.
Scope is one interpreter and shared processing outcome handling. No vendor research or
new technology choice is needed. The existing guard needs no additional lookup for
version detection; completed-review checks use a bounded tenant-scoped outcome query.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Sources retained; updates produce no invented Reality |
| Reality owns operations | PASS | Existing commitments and execution untouched |
| Proven schema | PASS | No schema change |
| Tenant/shared services | PASS | Scoped outcome lookup; existing service path |
| Specification/test evidence | PASS | User-approved scope; regression tests before code |
| Explainable product | PASS | Existing coverage and job explanation |
| Simplicity/storage | PASS | Existing PostgreSQL models and review mechanism |

Rechecked after design: all PASS, no exceptions.

## Project Structure

- `packages/reality-core/src/reality/services/core.py`: guard and review handling.
- `packages/reality-core/tests/test_shopify_and_explain.py`: replace unsafe baseline
  expectations, prove first-version failure recovery remains available.
- `packages/reality-core/tests/test_shopify_update_guard.py`: business-state,
  lifecycle, duplicate/retry, batch, synchronous helper and HTTP coverage.
- `docs/features/shopify_ingestion.md`, `docs/ERP_MONTH.md`,
  `specs/005-source-ingestion/spec.md`: align authoritative contracts.
- Relevant integration/lifecycle public docs: clarify update quarantine using English
  replacement text as required by the repository language contract, including legacy
  localized pages that otherwise retained contradictory behavior descriptions.

## Implementation Order and Verification

Write tests first and observe failure. Add the service guard and completed-review
handling, then update contracts. Run focused tests, full backend suite (including
migration tests), lint, spec policy, and web/site/docs verification targets.
No deployment, production data writes or historical repair.

## Migration and Rollback

No migration. Existing successful interpretations remain readable. Pending changed
versions become review outcomes when processed. Rollback to old code can re-enable
destructive interpretation on retry, so keep changed-source processing paused if
rolling back. A code rollback does not undo historical business effects.

## Review Risks

Completed review must not call the interpreter outside its exception boundary.
Consecutive reviewed versions must not bypass the guard. Raw exception text must not
be exposed. The newest source pointer does not imply newest interpreted Reality.
Previously successful source versions must still return their historical records.
