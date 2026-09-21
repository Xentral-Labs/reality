# Implementation Plan: Complete Demo Business Journeys

## Technical Context

Extend the existing Python 3.12/SQLAlchemy 2 canonical profile and its PostgreSQL
scenario tests. Reuse `core` services for documents, commitments, movements, postings,
allocations and cancellations. Add durable Markdown documentation. No schema, API or
browser business-rule change is required.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Each journey starts with immutable synthetic source evidence and uses normal services. |
| Reality is operational authority | PASS | Returns and cancellations are movements/commitment events; settlement is ledger-derived. |
| Proven schema only | PASS | No schema changes. |
| Tenant/service boundaries | PASS | Existing tenant-scoped services only. |
| Specification/tests first | PASS | Scenario assertions precede fixture changes. |
| Explainable product | PASS | The catalog provides stable references and inspection guidance. |
| Simplicity/storage discipline | PASS | One profile extension, no new infrastructure. |
| Received values not recomputed | PASS | Authored quantities and amounts remain source-stated. |

## Design

1. Increment the canonical profile version.
2. Add stable journey constants and build them through the existing profile helpers.
3. Use exact order-line links for return/credit exception derivation and settlement
   allocations for financial closure.
4. Extend the international demo scenario test with quantities, document dates,
   references, balances and exception assertions.
5. Publish `docs/features/demo-data-catalog.md` and link it from the company setup
   contract.
6. Seed deterministic settlement cases through the existing payment, allocation and
   accepted-adjustment services. Record overpayments first, allocate only the open
   invoice amount, and retain the unallocated control-account balance as credit.

## Risk and rollback

The extra records increase setup work and change fixture counts. Accepted adjustments
also need the ordinary finance account and confirmation boundary during the already
confirmed profile initialization; keep that authority fixed to authored profile data
and never expose a general unconfirmed mutation path. Keep the additions
bounded and verify setup timeout coverage. Rollback is removal of the new versioned
profile journeys and catalog section; no stored schema needs reversal.
