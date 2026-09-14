# Implementation plan: Unified Receipt and Reservation Release

**Language**: English
**Spec**: [spec.md](spec.md)
**Date**: 2026-09-07

## Technical Context
Existing Python/SQLAlchemy/PostgreSQL services and React/TypeScript/Tailwind UI. No dependency or schema changes. Two additional company action presentations, one existing review lifecycle. Research is bounded to repository code, not new technology selection.

## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Receipt follows commitment; release follows reservation to commitment | PASS |
| Reality owns state | Stock derives from movements/reservations, no document status | PASS |
| Proven schema only | Existing entities only | PASS |
| Tenant/shared services | Scoped resolver; canonical movement_create/reservation_release tools | PASS |
| Spec/test traceability | FR mapping below; tests before behavior | PASS |
| Explainability | Event, reservation/movement and evidence Inspector links | PASS |
| Received values | Enter quantity, preserve existing service constraints | PASS |
| Simplicity | Extend ActionCard and delivery review instead of another action engine | PASS |

## Design and affected paths
1. Preserve domain semantics in `services/core.py`: release is whole-reservation only; receipt validates through `_append_movement(validate_only=True)`. No new release arithmetic.
2. Extend `services/delivery_reads.py` exact case reads to customer/supplier direction based on a scoped commitment lookup.
3. Extend `services/delivery_actions.py` with reservation-to-commitment resolution, release snapshot and token, receipt effects and location identity, dedicated event/receipt verification and reconciliation. Include receipt/release in unresolved same-stock-pool protection. Exact release intent remains reservation_id only; derived commitment context must not be passed as a new tool argument.
4. Update `tools/application.py` execution lock/resolver and `web/api.py` prepare allowlist. Company Chat automatically gets the same review via canonical eligibility; practice excludes this review as before.
5. Extend `apps/web/src/unified/ActionCard.tsx`, `ActionLauncher.tsx`, `UnifiedApp.tsx`, `OrdersPage.tsx`, `WarehousePage.tsx`, `ChatPage.tsx`, `DecisionsPage.tsx` and `apps/web/src/api.ts`. Receipt uses incoming commitments; release uses bounded active reservations. Preserve modal recovery and edit/reject behavior. Use existing record reads and pagination, with explicit empty/retry states. Pass selected record context via local action state; persisted proposal URL is recovery authority.
6. Update localization, durable WEB_SPEC and migration status after verification.

## Failure and recovery
A preparation request key binds the exact submitted intent. Release review records reservation ID/status/quantity/tracking plus relevant case/inventory. Confirmation rechecks it under the existing tenant mutation lock. Inactive release is rejected before handler invocation. Missing/foreign identities are not found. Receipt verifies destination (not shipment origin). Recovery matches action event and exact record; release recovery uses reservation.released and reservation receipt, never calls release again. Existing recorded release events contain commitment_id only; verify reviewed quantity against the immutable released reservation and exact action/event identity without rewriting historical payloads. Unknown execution blocks conflicting work until reconciliation proves the outcome.

## Test Strategy and Traceability
| Requirements | Tests and initial failure |
| --- | --- |
| FR-001, FR-003 | New `tests/test_unified_receipt_release.py`: partial receipt, invalid direction/overreceipt, stale state, foreign identity; currently eligibility/customer-only case fails |
| FR-002, FR-003 | Same test file: full release, inactive/stale reservation, foreign identity, unchanged physical/open quantities; currently release ineligible |
| FR-004 | Same tests plus API proof: prepare/confirm replay, event reconciliation, unresolved pool, company Chat proposal parity, retained practice behavior |
| FR-005, FR-006 | `apps/web/scripts/unified-receipt-release-browser.mjs`, existing browser journeys, frontend contracts/i18n/build: register and launcher entry, review/edit/reload, empty/error, layout/keyboard |

## Verification and rollback
Run targeted regression first, full backend suite, frontend contracts/i18n/format/build, spec policy/Ruff and relevant browser journeys. Existing local sample preview is isolated; no external production mutations. No migration required. Frontend flag rollback retains compatible token-aware backend. Rollout/retirement stay pending.
