# Implementation Plan: Commercial Edge Workflows

**Branch**: `245-demo-setup-finance-readiness` | **Date**: 2026-09-21 | **Spec**: [spec.md](./spec.md)

## Summary

Add four bounded confirmed workflows by extending existing truthful primitives. Dunning gets a notice and invoice-membership record; its optional fee is a separate posted charge. Bad debt extends confirmed settlement adjustments with a dedicated account role. Deposits use explicit document types but reuse control-account entries and settlement allocations. Overdelivery needs no schema: immutable commitment revisions already support a higher quantity and fulfilment already reads the quantity in force. Shared services feed tools, web and canonical profile v9.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React for web
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, React/Vite
**Storage**: PostgreSQL
**Testing**: pytest service/story/adapter tests; Vitest frontend tests; browser smoke test
**Project Type**: backend services/API/tools plus independent frontend
**Constraints**: Decimal, UTC, opaque links, lossless source, tenant scope, preview/confirm mutations
**Scale/Scope**: Manual single-notice and clearing actions; no scheduler, delivery provider or tax engine

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
| --- | --- | --- |
| Source → Evidence → Reality | SourceRecord and evidence documents precede notice, ledger allocation or revision records | PASS |
| Reality owns operational state | Balances derive from ledger/allocation/reversal; fulfilment derives from movements and quantity in force | PASS |
| Proven schema only | Only dunning identity/membership and dedicated financial roles are new | PASS |
| Tenant + shared service boundaries | Services enforce tenant scope; tools and adapters call them; mutations are confirmed | PASS |
| Spec/test traceability | FR/DR rows map to test-first tasks and quickstart cases | PASS |
| Explainable web behavior | Results link to documents, ledger/revision, source and events | PASS |
| Received values not recomputed | Fee, deposit, write-off, level and quantity are stated; balances are derived | PASS |
| Smallest coherent design | No scheduler, delivery integration, tax engine, deposit balance table or second fulfilment rule | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0089_commercial_edge_workflows.py
packages/reality-core/src/reality/db/core.py
packages/reality-core/src/reality/domain/finance.py
packages/reality-core/src/reality/services/dunning.py
packages/reality-core/src/reality/services/finance/deposits.py
packages/reality-core/src/reality/services/finance/settlement.py
packages/reality-core/src/reality/services/demo_profile.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/tests/
apps/web/src/
apps/docs/content/demo-data/
docs/features/
```

## Design

### Reality flow

- Dunning: SourceRecord → dunning-notice Document → DunningNotice → opaque invoice memberships → optional fee Document → balanced receivable/revenue posting.
- Bad debt: SourceRecord → settlement-adjustment Document → balanced receivable/bad-debt-expense posting → SettlementAllocation.
- Deposit: SourceRecord → customer/supplier-deposit Document → cash/control posting → SettlementAllocation to a later invoice.
- Overdelivery: source evidence → existing CommitmentRevision with higher quantity → ordinary Movement bounded by `commitment_quantity`.

### Service and adapter flow

Each feature provides context/preview and confirmed execution services. Application tools register shared actions; tenant policy grants explicit operations. API adapters only parse and serialize. React consumes the endpoints and reuses inspector links. Demo seeding invokes the same services under profile authority.

### Data and migration impact

- Add `dunning_notice` with tenant/id, document/source, party, currency, notice date, level, stated fee and timestamps.
- Add `dunning_notice_invoice` with tenant/notice/invoice composite foreign keys and uniqueness.
- Add `bad_debt_expense` and `dunning_fee_revenue` account roles and defaults.
- Add no deposit table and no overdelivery field. Document types express deposit meaning; allocations express consumption.
- Existing data needs no backfill. Application rollback precedes schema downgrade.

### Failure, security, and tenant behavior

Services lock finance or delivery state before revalidation. Cross-tenant records resolve as unavailable. Same-party/currency/side checks precede writes. Action/source identities make replay idempotent. Failures roll back atomically. UI owns no business rules.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
| --- | --- | --- | --- |
| FR-001..FR-004 | service/story/adapter | `tests/finance/test_dunning.py`, API/web tests | no notice or fee service |
| FR-005..FR-006 | service/story | extend `tests/finance/test_adjustments.py` | unsupported reason/account |
| FR-007..FR-009 | service/story/adapter | `tests/finance/test_deposits.py` | no explicit deposit workflow |
| FR-010..FR-011 | domain/story | commitment/shipment tests | missing surface/demo proof |
| FR-012 | tool/policy | confirmation and isolation tests | tools unregistered |
| FR-013..FR-015 | scenario/docs/web | demo/docs contract tests | profile cases absent |

## Rollout and Rollback

Apply migration before application. New document types are ignored by older readers. Reverse financial actions through normal services before downgrade. Profile versioning prevents replay from rewriting older demo companies.

## Review Risks

- Dunning fee must not mutate the invoice or invent tax.
- Bad debt must never become reusable credit.
- Deposit must stay distinguishable while reusing allocation math.
- Overdelivery remains impossible without a prior revision.
- Reversal must restore balances exactly once.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| --- | --- | --- | --- |
| None | — | — | — |
