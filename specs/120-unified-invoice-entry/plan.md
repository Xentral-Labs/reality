# Implementation Plan: Unified Invoice Entry

## Technical Context
Python 3.12, SQLAlchemy 2/PostgreSQL, canonical application tools, FastAPI, React/TypeScript.
No schema, dependencies or public command expansion.

## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Manual source, linked invoice line and balanced ledger entries | PASS |
| Reality authority | No document operational status | PASS |
| Proven schema | Existing proposal and immutable event storage | PASS |
| Tenant/shared services | Pure core preview, tenant-scoped evidence selection and current access | PASS |
| Tests first | Isolated financial-effect, stale/recovery and browser proofs before implementation | PASS |
| Explainability | Stated amounts and exact evidence links; observation separate from proof | PASS |
| Received values | Amount supplied, never derived | PASS |
| Simplicity | Existing single-line tools and common proposal lifecycle | PASS |

## Design
Extract private invoice validation in `packages/reality-core/src/reality/services/core.py`.
Preserve credit semantics. Add immutable invoice creation evidence in the same transaction.
`services/invoice_actions.py` provides review, unresolved-line guard and exact historical proof.
`services/delivery_actions.py` dispatches both tools and common reconcile; `web/api.py` expands
prepare allowlist. Reuse evidence-document search and inspector lines for selection.
`apps/web/src/unified/InvoiceCard.tsx` uses common lifecycle and reference reads. Integrate in
ActionCard, ActionLauncher, FinancePage, UnifiedApp, ChatPage, DecisionsPage and api.ts.

## Validation and rollback
Tests cover both directions, inert preview, stated unequal totals, billing limits, foreign/stale
references, no physical/payment effects, token enforcement, replay and exact recovery proof.
Browser fixtures exercise entry, review, edit/reject, lost response and localized responsive views.
Run complete core tests, web contracts/build/format/i18n, action browser regressions, lint/spec/diff.
Restart local preview only after verification; live smoke is read-only. No migration or retirement.
Rollback presentation dispatch plus eligibility together; retain immutable recorded evidence.
