# Implementation Plan: Unified Movement Corrections

**Language**: English
**Date**: 2026-09-08
**Spec**: [spec.md](spec.md)

## Technical Context
Existing Python 3.12/SQLAlchemy/PostgreSQL services and FastAPI/application tools; React/TypeScript shared action UI. No dependency/schema. Worktree `/private/tmp/reality-107`; shared local preview data must not receive test business mutations.

## Constitution Check
| Principle | Design evidence | Result |
| --- | --- | --- |
| Source/Evidence/Reality | Movement correction links originals and evidence; no rewritten source | PASS |
| Reality authority | Stock/fulfillment derived; reservations not invented | PASS |
| Proven schema | Existing correction, proposal and event action fields | PASS |
| Shared services/tenancy | Projected validation remains core; locked state-bound execution | PASS |
| Tests/spec | FR mapping and failing backend/browser proofs precede code | PASS |
| Explainability | Explicit inverse/replacement and per-pool signed effect | PASS |
| Received values | No external totals recomputed or stored | PASS |
| Simplicity | Dedicated correction semantics plug into existing proposal lifecycle | PASS |

## Design and paths
- `packages/reality-core/src/reality/services/core.py`: fix selected-replacement preview; pure projected inventory/identity/fulfillment reads in `_append_movement` for validation after excluding the selected original. No temporary ORM writes in preview. Validate supported replacement fields and tracked inverse availability. Add optional action_id to existing correction execution/event with tenant check; preserve direct API semantics and fingerprint replay.
- `services/movement_correction_actions.py`: exact review using shared core preview, bounded affected pool/current reference/commitment snapshots, separate observation, attributable correction proof/receipt reconstruction, overlapping unresolved action guard.
- `services/delivery_actions.py`: early correction dispatch for review/detail/reconcile and unresolved-action checks. Do not pass standalone correction through delivery_case or single-commitment assumptions. Reuse request identity, preparation, review token and confirmation plumbing.
- `tools/application.py`: map correction action_id, avoid a second legacy preview overwriting unified intent, retain canonical tools and existing confirmation lifecycle. Canonical confirmation requires an explicit current review token and confirmed flag.
- `web/api.py`: add correction to existing prepare allowlist; existing scoped movement snapshot is the selected-record read. No direct UI write endpoint.
- `apps/web/src/unified/CorrectionCard.tsx`: specialized form and review content with the same proposal API/recovery/Inspector conventions. ActionCard dispatches correction proposals by their loaded tool; no identity-prefix guessing. Shared launcher and Warehouse row entry, Chat and Decisions select the same stored proposal. Form supports reverse or quantity replacement; canonical richer replacement data remains preserved when edited. Explicitly prevent silently copying unsupported newer return relationships.
- `apps/web/src/api.ts`, `UnifiedApp.tsx`, `ActionLauncher.tsx`, `WarehousePage.tsx`, `ChatPage.tsx`, `DecisionsPage.tsx`, `localization.tsx`: typed envelope, movement target, menu eligibility from catalog, four languages and refresh.

## State and recovery
Snapshot the selected movement/revision, each original/replacement item/location stock pool (physical/reserved/identity), relevant current commitments/holds and human reference labels. Recompute under tenant mutation lock. Correction and delivery reviews block unresolved intersecting pools in both directions; unrelated tenants remain independent. Exactly one action-linked correction event plus immutable relation/record values proves receipt. Later correction of a replacement does not invalidate original receipt evidence. Missing or ambiguous evidence remains unresolved. No repeated mutation during reconciliation.

## Verification and rollback
Tests first: isolated PostgreSQL stories for inverse/replacement and chained preview, serial/tracked/dependent stock validation, malformed/foreign references, state change, unknown outcome, attribution, actor/practice and HTTP/tool parity. Browser fixture proof for all entry points, no-preparation effect, review/edit/reload/reject/confirm and four-language responsive light/dark states. Then full backend, frontend contracts/build/i18n/format, existing action browsers, spec/Ruff/diff and visual review. Restart shared preview only after checks, with read-only live login/read validation. Old routes remain; no migration/deployment/retirement.
