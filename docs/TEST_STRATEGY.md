# Test Strategy

Business stories outrank ORM tests. All persistence tests use isolated temporary
PostgreSQL databases and fixed timestamps where business dates affect behavior.

## Layers

1. **Unit** — Decimal validation, state transitions, stock math, risk and balances.
2. **Service integration** — real SQLAlchemy session, tenant scope, provenance,
   immutability, idempotency and rollback behavior.
3. **Business stories** — O2C, P2P, shortage, partial flows, cancellation, return,
   correction, payment and credit across the public service layer.
4. **Adapters** — CLI and Web prove they call services and expose equivalent state.
5. **Golden scenario** — deterministic September 2026 month, safe to reset and rerun.
   It deliberately ends with conditions still in the operational exception queue, because
   showing what a month leaves behind is the point of the demo rather than a defect in it.
   `test_the_month_ends_with_exactly_these_exceptions` pins every entry together with the
   act that produces it; changing that set is a change to the story and must be argued as
   one, never quietly resolved.

## Required assertions

- Every business query is isolated by tenant, including aggregate queries.
- Money and quantities are compared as Decimal values, never binary floats.
- Source payloads round-trip losslessly and existing SourceRecords are not updated.
- Fulfillment equals linked movements; availability equals movements minus active
  reservations; financial balances equal balanced ledger postings.
- Documents never acquire operational delivery, reservation, or payment status.
- Mutating chat actions cannot execute without confirmation.
- IDs/FKs drive all traces; human numbers are display-only.

## Test map

| Feature | Unit | Service | Story | Adapter |
|---|---:|---:|---:|---:|
| Tenancy/master data | validation | isolation/CRUD | duplicate external values | CLI/Web |
| Shopify/evidence | mapping | immutable/idempotent | order ingestion | CLI |
| Commitment/reservation | lifecycle/math | scoped writes | shortage/cancel | CLI/Web |
| Movement/inventory | stock math | receive/ship/transfer | partial/return | CLI/Web |
| Ledger | balance math | append-only posting | invoice/payment/credit | CLI/Web |
| Explain/timeline | risk | provenance traversal | full trace | CLI/Web |
| Chat/tools | confirmation | shared services | proposed mutation | Web |

The suite must pass with `pytest`; `ruff check .` is the static quality gate. A feature
is checked off in `V0_CHECKLIST.md` only when its acceptance tests are green.
## Company access security

Membership-invitation coverage combines service stories, HTTP auth/API contracts,
real PostgreSQL migration and concurrency tests, tenant-isolation catalog proof,
notification retry/lease/retention tests, and frontend source/localization/build gates.
Tests assert that account existence is not disclosed, no membership exists before
explicit acceptance, token material is never persisted or logged in clear text, and a
removed membership denies the next protected tenant request without ending the global
session or other memberships.
