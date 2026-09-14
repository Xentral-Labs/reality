# Plan: Unified Delivery Holds

**Language**: English
**Date**: 2026-09-08
**Spec**: [spec.md](spec.md)

## Technical Context
Python 3.12, SQLAlchemy/PostgreSQL, existing FastAPI/tool contracts, React/TypeScript/Tailwind. No new dependency/schema. Domain semantics remain existing hold/release; scope is company presentation and exact review/recovery.

## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Hold→Commitment→evidence; event links exact action | PASS |
| Reality owns state | No document fulfillment state; quantities unaffected | PASS |
| Proven schema only | Existing action_id/event fields and hold records | PASS |
| Tenant/shared services | Scoped reads; existing shared tools and tenant mutation lock | PASS |
| Specification/test evidence | FR test matrix in spec/tasks; failing proofs first | PASS |
| Explainable web | Reason, scope, original note and event/commitment links | PASS |
| Received values | Preserve note and recorded reason; no money calculations | PASS |
| Simplicity | Extend shared card; small hold-review helper, no new engine | PASS |

## Design and exact paths
- `packages/reality-core/src/reality/services/core.py`: add optional action_id to hold_commitment/release_commitment_hold, validate proposal tenant, attach to existing events. Extract shared read-only hold preparation validation for use by review and mutation, preserving direct caller no-op behavior.
- `services/hold_actions.py`: snapshot all active own holds sorted by ID; reject no-op review, validate through shared core; verify/recover exact action events and entity receipts. Release review does not store a duplicate commitment link on holds.
- `services/delivery_actions.py`: include canonical hold tools, delegate hold review/proof, include holds in unresolved pool detection; support plural hold receipt reconciliation.
- `services/delivery_reads.py`: add explicit blocker scope/note/creation metadata for all active own holds and the applicable customer-wide hold; expose sorted canonical hold reasons in case metadata. Keep existing blocker fields compatible.
- `tools/application.py`: map _action_id for hold handlers; use existing review enforcement and execution lock. MCP tool schemas stay unchanged.
- `web/api.py`: extend delivery-action preparation allowlist only.
- `apps/web/src/api.ts`, `unified/ActionCard.tsx`, `ActionLauncher.tsx`, `DeliveryCase.tsx`, `ChatPage.tsx`, `DecisionsPage.tsx`, `localization.tsx`: exact selected-case reason discovery, no quantity/tracking editor for holds, original note, read/review/errors, native case controls and shared proposal presentation. Launcher supports existing customer work selection; supplier commitments remain usable through canonical tool proposals.

## State, failures and rollback
Review snapshots all active own-hold IDs and immutable content. Creation refuses existing active own holds at review; release refuses none. Core direct no-op behavior remains compatible. Confirm re-reads under the existing lock before handler execution. Same-reason replacement changes IDs and invalidates review. Action-linked events enable proof even when response is lost; plural release matches the entire reviewed set. Creation proof remains valid after release. Party holds remain independent. Rollback keeps token-aware backend and existing legacy routes. No data migration, production deployment or retirement.

## Verification
`tests/test_unified_delivery_holds.py` proves FR-001–005: prepare/confirm/replay, invalid/stale/foreign/no-op, scope/unchanged quantities, canonical tool/API review, event and plural release recovery. Browser `apps/web/scripts/unified-holds-browser.mjs` proves FR-001–006: case/global/Decisions, correct scope, fields, edit/reload, outcomes, localized responsive states. Add tests before behavior changes. Run targeted then full backend, frontend contracts/build/i18n/format, existing action/delivery browsers and spec/Ruff/diff checks. Review source→evidence→reality and unchanged schema before completion.
