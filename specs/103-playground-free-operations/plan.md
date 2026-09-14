# Implementation Plan: Free Playground Operations

FR-014/T021: Adapter-only native details/summary disclosure in OperationChooser,
with localized label and theme-token styling. Keep four guided and two order
actions outside it. No persistence, schema, service or authorization changes.
Constitution check PASS. Scope reviewed against the user request; no unresolved
questions or critical analysis findings. Verify six visible actions initially,
twenty expanded, keyboard toggle without POST, and unchanged existing browser
journeys. Run web contracts, build, localization audit and spec policy. Rollback
only the disclosure markup and styles to restore the expanded chooser.

FR-013/T018–T020: strict single-record inputs for six existing master-data tools;
reuse shared master_data_update_snapshot and proposal normalization/revisions.
Bind exact bulk-service input/action to the decision and only permit that family's
create/update helpers and corresponding event. No ordinary endpoint or seed-scope
reuse. Use shared reference GETs and common Playground prepare/confirm/reject UI.
Receipt follows existing tool record IDs and action events. Add basic-field editor
and readable nested-record review. Tests first: six paths, rejection/idempotency,
foreign/stale input, policy tampering; contracts/build/i18n and browser checks.
Constitution PASS: no schema, external I/O or new business rules. Approved scope
reviewed; FR-013 maps to T018–T020; no unresolved clarification/critical finding.
Rollback removes these entries and narrow permissions; existing records remain.
FR-012/T017: Add bounded release input, exact decision binding and narrow mutation
allowlist for shared release_reservation plus reservation.released event. Snapshot
active reservation state at prepare and confirmation; observe through existing event
and reservation reads. UI uses existing reservations GET, shows active choices and
routes review through the common Playground step. No schema/new business rules.
Tests first: lifecycle, no stock/commitment change, wrong target, stale state,
idempotent confirmation, rejection; browser chooser/review/Back and all prior flows.
Constitution PASS, approved scope, no unresolved clarification or critical findings.
Rollback removes entry and narrow policy additions; recorded events remain.
FR-011: Add typed evidence_lines to existing document Inspector from document_detail;
no new endpoint or permission. FinanceOperation selects bounded existing order/open
item pages, then edits exact line/invoice targets through playgroundPrepareStep.
Keep normal free-mode pending review and reload recovery. Tests: Inspector identity,
intent payloads, browser selection/Back/partial amount; existing finance/API tests,
web contracts/build/i18n/spec. Constitution PASS; approved scope unambiguous, no
critical consistency findings. T015/T016 implement this increment; T017 remains.

FR-010 refinement: reuse OpenWork and FreeOperations; parent passes action-scoped
selection and a view request to the workspace. No backend/schema change. Add
browser entry/Back regression before verification. Constitution PASS, approved
direction, no unresolved clarification for fulfillment scope or critical findings.
Rollback removes UI entry wiring. Contracts/build/browser/localization required.

**Branch**: feature/playground-free-operations | **Date**: 2026-09-07
**Spec**: [spec.md](spec.md)

## Summary
Add a free-action editor alongside guided lessons in the same cockpit. Select open
work from the existing paginated commitment-control API, not the latest lesson.
Use existing order_create, reserve and movement_create confirmed Playground steps.

## Technical Context
React/TypeScript, existing CSS primitives; Python 3.12, FastAPI, SQLAlchemy 2,
PostgreSQL; pytest and existing Node/browser contracts. No dependencies or schema.

## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Existing order executor and shortest links | PASS |
| Reality authority | Shared commitment_page/open/fulfilled quantities | PASS |
| Proven schema | No persistence change | PASS |
| Tenant/services | Existing scoped reads and exact proposal decision scope | PASS |
| Tests first | FR/DR mapped below | PASS |
| Explainable UI | Quantities and record inspection, no document status | PASS |
| Received amounts | Existing manual-order contract, no new financial calculation | PASS |
| Smallest change | Presentation editor, no workflow engine | PASS |

## Design and Files
- services/playground.py: shipment review includes current open quantity/status;
  reservation review uses actual remaining quantity instead of original promise.
- web/api.py: additive commitment-control location field from the scoped commitment.
  Existing quantity/open/reserved fields suffice; do not add unused unit/fulfilled fields.
  apps/web/src/api.ts: additive target type and optional paging.
- apps/web/src/playground/FreeOperations.tsx: reviewed single action editor.
- OpenWork.tsx: compact paged table with customer/supplier actions and inspect.
- PlaygroundPage.tsx: presentation mode/selected work and shared refresh.
- PlaygroundWorkspace.tsx: Open work tab and custom action heading.
- localization.tsx: all four languages. Reuse existing appearance tokens.

Mode preference is per-run session storage and never authority. Pending proposal
review resumes on reload and blocks changing mode/work. Rejection returns to free
selection; executing/uncertain outcomes require refresh, never automatic replay.
Server validation continues to own stale references, stock, holds and quantities.

## Test Strategy and Traceability
| Requirements | Tests | Initial failure |
|---|---|---|
| FR-003, DR-001–002 | Commitment-control response | Missing location |
| FR-004–005, DR-002 | Stale selected commitment test | Incomplete shipment revision |
| FR-001–006 | Node/browser mixed-operation journey | No free mode/open work |
| SC-001–002 | Backend suite, web gates, viewport/reload story | New journey absent |

## Rollout and Rollback
Existing feature gate and mutation permissions unchanged; code revert restores UI.
Additive read fields remain compatible. Stronger freshness checks may require
rejecting and re-preparing old proposals. No migration.

## Review Risks
Never derive targets from latest history or confuse a page with all open work.
Never automatically confirm a newly prepared action. Shopify and batch execution
require an independent transaction/action design and remain later increments.

## Complexity Tracking

FR-009 approved refinement: add ExecutionStatus.tsx, with serialized read-only GET
polling every three seconds, cancellation guards and read-error retry. Stop on proven
discard or settlement. No time-based inference of failure and no automatic writes.
Render mutually exclusive localized messages, retaining the explicit reject service
for proven non-execution. Tests first: source safety contract and browser fixtures for
read failure/retry, settlement, unknown state and proven discard. Constitution PASS;
review/analysis finds no ambiguity or critical gap. UI-only; rollback is a code revert.
No Constitution exception or new service authority.

## Approved shipment recovery correction

FR-008: share commitment movement quantity validation between core execution and
Playground preparation/confirmation. No generic conversion of unknown executions.
An owner-confirmed rejection can settle only the historical overdelivery with saved
state proving the invalid quantity, no action events and no movements for its target,
under the existing run advisory lock. Keep input/output and attribution; no stock
mutation. Rejected steps cease blocking capacity. UI offers explicit discard for
this proven case; otherwise only refresh. A rejected step returns to the local
operation list. Derive editor defaults from server order/receipt context on step
change. Tests cover invalid preparation, old preview confirmation, safe rejection,
unknown/effect/foreign refusal, correct quantity, reload and local navigation.
Review/analysis: approved scope unambiguous, Constitution PASS, T012 traces FR-008
and FR-005; no schema or permission broadening.

## Approved register separation

FR-007 moves normal obligations out of the attention pane. Rename the goods tab;
add OpenItems.tsx calling the existing tenant-scoped finance projection with flow,
status, search and paging. Add the optional outstanding filter (open and partial)
to shared projection page/totals filtering, keeping existing exact statuses intact.
Workspace receives a presentation slot and keeps record
inspection. No schema, domain, mutation or financial derivation changes. Tests first:
source contracts then browser filters, partial/settled data, inspection, paging,
themes and viewport. Constitution PASS; approved scope is unambiguous and each
requirement maps to T011. Analysis: no critical consistency findings.

## Approved UI refinement — grouped chooser

Replace mode tabs with two headings in OperationChooser; parent selection opens
the existing free editor directly. Preserve free/guided context only for resuming
pending reviews, not as visible navigation. Reset single-editor selection when
preparing or cancelling so settlement returns to the common list. Use compact rows
and local pane overflow. No backend changes; Constitution remains PASS. Regression
contracts and both browser journeys prove FR-001/FR-005/FR-006. Requirements reviewed
against owner approval; no ambiguity or critical consistency findings remain.
