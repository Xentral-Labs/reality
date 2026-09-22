# Implementation Plan: Operational Integrity

**Branch**: `250-operational-integrity` | **Date**: 2026-09-22 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Close four demonstrated integrity gaps without adding business tables. Return dispositions inherit tracking identity from the arrived Movement. Commitment revisions use a reviewed atomic service that preserves an unambiguous retained allocation or refuses before effect. Existing commitment cancellation becomes a reviewed shared action with reason, event correlation, stable receipt, and all adapters. Proposal execution distinguishes synchronously proven no-effect failures from genuinely uncertain outcomes and settles recorded effects only through exact evidence reconciliation.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React for unified Web actions
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite
**Storage**: Existing PostgreSQL tables only; no migration planned
**Testing**: pytest unit/service/story/PostgreSQL/adapter tests; focused browser test; frontend build, i18n audit, generated catalog check
**Project Type**: shared domain/services/tools with CLI, API, MCP, Chat, and Web adapters
**Constraints**: Decimal; UTC; opaque IDs; append-only evidence; strict tenant scope; at-most-once confirmation; no document-owned operational state
**Scale/Scope**: Multiple dispositions/reservations/revisions per subject and concurrent confirmations; no warehouse task orchestration

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Arrived Movement remains physical evidence; resolving Movement uses `resolves_movement_id`; revisions/cancellation retain source/action correlation. | PASS |
| Reality owns operational state | Commitment, Reservation, Movement, hold, revision, and event remain authoritative; no Document lifecycle fields. | PASS |
| Proven schema only | Existing records express every scenario; no migration. | PASS |
| Tenant + shared service boundaries | Tenant-scoped services serve Web, MCP, Chat, CLI, and API. | PASS |
| Spec/test traceability | Every FR/DR maps to a planned failing proof below. | PASS |
| Explainable web behavior | Reviews/receipts expose identity, reservation effects, cancelled remainder, and links. | PASS |
| Received values not recomputed | Revisions/reasons are recorded; open, fulfilled, reserved, and unresolved remain derived observations. | PASS |
| Smallest coherent design | Reuse entities, cancellation, review, proposal CAS, events, and unified action UI. | PASS |

Planning gate: all rows PASS. No exception requires approval.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py
packages/reality-core/src/reality/services/return_dispositions.py
packages/reality-core/src/reality/services/return_disposition_actions.py
packages/reality-core/src/reality/services/commitment_actions.py
packages/reality-core/src/reality/services/delivery_actions.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/src/reality/cli/app.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/config/resource_catalog.yaml
packages/reality-core/tests/test_returns.py
packages/reality-core/tests/test_commitment_revisions.py
packages/reality-core/tests/test_commitment_actions.py
packages/reality-core/tests/test_application_tools.py
packages/reality-core/tests/test_return_announcement_adapters.py
packages/reality-core/tests/test_postgresql_integration.py
packages/reality-core/tests/scenarios/test_b2b_operational_integrity.py
apps/web/src/unified/ActionCard.tsx
apps/web/src/api.ts
apps/web/src/localization.tsx
apps/web/scripts/operational-integrity-browser.mjs
apps/docs/content/tool-usage/
apps/docs/.vitepress/data/tool-usage.json
docs/features/commitments.md
docs/features/reservations.md
docs/features/movements.md
docs/WEB_SPEC.md
```

Dependency direction remains core/domain → services → tools → adapters. `commitment_actions.py` owns state-bound reviews and receipts but calls existing core primitives; adapters contain no business decisions.

## Design

### Reality flow

**Return**: source/evidence → arrived return Movement → reviewed disposition → resolving Movement with the same applicable handling unit, lot, and serial. The direct resolving link remains authority; source/event records explain it.

**Revision**: optional source → append-only CommitmentRevision → derived effective/open quantity. Review derives allocation consequences. A homogeneous allocation can be released and replaced at the exact retained quantity in one transaction. For heterogeneous allocations, review returns eligible opaque reservation choices and a replacement proposal carries the operator's retained quantities; missing or stale choice is refused. Movements remain unchanged.

**Cancellation**: confirmed reason/source → existing Commitment cancellation → released Reservations and CommitmentHolds → correlated cancellation event. Fulfilled quantity stays derived from Movements; only the open remainder closes. Document remains evidence. Existing internal call sites are migrated to supply their already-known business reason; no generic reason is invented.

**Proposal lifecycle**: CAS claim → shared handler transaction → exact event/Reality correlation. Pre-handler validation remains proposed. A post-claim domain failure may be restored only after complete rollback is known and the action contract proves no separately committed effect. Otherwise it remains executing/unresolved. Reconciliation uses exact evidence; absence alone never proves rollback.

### Service and adapter flow

1. Propose canonical return, revise, or cancel intent.
2. `review_delivery` routes to a specialist review containing normalized intent, before/effect/after, and a tenant/state-bound token.
3. Explicit confirmation validates current state under the delivery-state lock.
4. One tenant-scoped transaction writes correlated effects/events.
5. Detail/reconciliation returns lifecycle, verification, effect, current observation, remaining work, and links.
6. MCP/Chat expose propose/read/reconcile; confirmation remains outside model schemas. Web presents the same review/result. CLI/API stay thin.

The direct Web revision endpoint must delegate to the reviewed boundary or become a compatibility adapter that cannot bypass confirmation. No adapter may call revision/cancellation primitives as an alternative rule path.

### Data and migration impact

No schema change. Existing Movement identity/resolution, Reservation history, CommitmentRevision, Commitment status, BusinessEvent action correlation, SourceRecord, and ChangeProposal receipt express all accepted behavior. No automatic repair: historical bad movements require explicit movement correction; historical excess reservations require reviewed release/revision handling.

### Failure, security, and tenant behavior

- Lock tenant delivery state and affected return/commitment before rechecking review.
- Concurrent disposition, shipment, reservation, revision, or cancellation makes stale review fail before effect.
- Cross-tenant IDs are not found and never leak through review/reconciliation.
- Repeated confirmation replays stored receipt; executing never triggers mutation replay.
- Reset only caught, proven rolled-back no-effect domain refusals; unexpected/process failures remain unresolved.
- Reconciliation matches proposal, action-correlated evidence, normalized intent, and exact values.
- Existing principal and confirmation rules remain unchanged.

## Test Strategy and Traceability

Tests are added first and observed failing where practical.

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-004, DR-001–DR-002 | service + concurrency | `test_returns.py` plus PostgreSQL identity/split/stale/race cases | Disposition omits tracking identity |
| FR-005–FR-008, DR-003–DR-004 | service + story | `test_commitment_revisions.py` for homogeneous/ambiguous allocations, partial retention, fulfilment/race | Revision leaves over-reservation |
| FR-009–FR-012 | service + story | `test_commitment_actions.py` and B2B story for pre/post-fulfilment cancellation | No reviewed cancel action |
| FR-013–FR-016, DR-005 | application + concurrency | Application/PostgreSQL tests for refusal, rollback, lost response, evidence mismatch, true unknown | Known failures strand executing |
| FR-017–FR-018 | adapter + browser | MCP registry, API/CLI, action card, browser parity | Cancel absent; direct revision bypasses review |
| FR-019, DR-006–DR-008 | regression + review | Historical read, tenant isolation, schema/diff review | Silent repair/correlation risk |
| SC-001–SC-007 | business story | `test_b2b_operational_integrity.py` reconciles item/location/identity/outcomes | Aggregate checks miss wrong location |
| SC-008 | full gates | Backend, PostgreSQL, lint, Web, i18n, spec, docs generation/check | Regression/stale catalogs |

## Rollout and Rollback

Public tools are additive; service behavior is corrective. Old proposals and records remain readable. Direct unreviewed revision clients receive confirmation-required behavior. Catalog/docs regeneration publishes cancellation and revised receipts.

Rollback removes new adapters/orchestration while append-only records remain valid. No data rollback is required. Inspect executing proposals from new tools before rollback; never replay automatically.

## Review Risks

- Partial retention must not choose a lot/location implicitly.
- Resetting executing without rollback proof can duplicate effects.
- Cancellation reason must live in event/source evidence, not proposal-only authority.
- Legacy direct revision must not remain a bypass.
- Identity inheritance must cover handling unit, lot, and serial.
- Long-lived docs currently state revisions leave reservations unchanged and must change with behavior.
- Existing cancellation call sites and fixtures must provide explicit reasons without changing their prior business outcome.

## Post-Design Constitution Check

No table, duplicate relationship, Document state, adapter rule, or automatic replay is added. All eight Constitution rows remain PASS.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
