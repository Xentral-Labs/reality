# Implementation Plan: Unified Payment Entry

## Technical Context
Python 3.12, SQLAlchemy/PostgreSQL, existing canonical payment tools, FastAPI and React/TypeScript.
No schema, new command/event vocabulary or dependencies.

## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Preserve optional supplied payment source; payment document → postings → allocation | PASS |
| Reality authority | Derive remaining amount; no document payment state | PASS |
| Proven schema | Reuse proposal, events and financial records | PASS |
| Tenant/shared services | Shared pure validation, current access and common mutation lock | PASS |
| Tests first | Isolated financial/recovery tests and browser fixture before adapters | PASS |
| Explainability | Historical proof plus current balance and explicit original-source availability | PASS |
| Received values | Stated payment amount recorded unchanged | PASS |
| Simplicity | Existing selected-invoice payment and existing immutable event chain | PASS |

## Design
`packages/reality-core/src/reality/services/core.py`: private pure payment preview shared by
customer/supplier execution; type/source/active-entry/capacity validation. Use common tenant
mutation lock for selected-invoice payment and allocation; preserve atomic outer transactions.
`services/payment_actions.py`: relevant invoice/control/source/allocation review state, token,
unresolved-invoice guard, exact proof from document.recorded/ledger.posted/settlement.allocated,
canonical two-ledger receipt recovery and separate current invoice observation.
`services/delivery_actions.py` and `web/api.py`: common dispatch/prepare/reconcile eligibility.
`apps/web/src/unified/PaymentCard.tsx`: invoice search, amount/reference/time, before/after
review and common recovery. Integrate ActionCard, ActionLauncher, FinancePage, UnifiedApp,
ChatPage, DecisionsPage, api.ts and localization.tsx.

## Validation and rollback
Tests cover both directions, partial-to-remaining, wrong type/source/tenant, nonfinite/excess
amount, stale/reversed invoice, overlap guard, exact receipt, replay, historical reversal,
authorization, HTTP, rollback and existing practice flows. Preserve canonical ledger-only output.
Run full core suite, web contracts/build/format/i18n, payment browser and prior invoice/action
journeys, spec/Ruff/diff. No live financial test mutation, migration or deployment.
Rollback UI entry and proposal eligibility together; never remove recorded payment evidence.

Payment review uses the shared currency formatter with explicit four-place precision and native
decimal-text formatting. Other callers retain their default currency formatting. Preview rejects
amounts that PostgreSQL Numeric(18,4) cannot hold unchanged before any financial write.
