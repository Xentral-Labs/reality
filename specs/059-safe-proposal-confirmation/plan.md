# Implementation Plan: Safe Proposal Confirmation

## Technical Context

Python 3.12, SQLAlchemy 2, PostgreSQL, FastAPI, MCP, Pydantic v2, pytest. The existing
`ChangeProposal` table stores string lifecycle state and a JSON result. `BusinessEvent` already
has opaque `action_id`, `causation_id`, and `correlation_id` fields. No schema expansion is needed.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Proposal governs; Reservation owns allocation; BusinessEvent proves the committed effect. |
| Reality operational authority | PASS | Verification re-reads Reality rather than trusting transport success. |
| Proven schema only | PASS | Existing proposal, reservation, commitment, and event fields suffice. |
| Tenant/service boundaries | PASS | Conditional claim and verification live in shared services used by adapters. |
| Human confirmation | PASS | Confirm remains explicit and excluded from model-selected tools. |
| Evidence before completion | PASS | PostgreSQL concurrency and planted-defect tests precede implementation. |
| Simplicity | PASS | One lifecycle claim, one bounded receipt, one reconciliation read; no workflow framework. |

## Design

1. Claim execution with one tenant-scoped conditional PostgreSQL update from `proposed` to
   `executing`, commit the claim, and only the winner may enter the handler.
2. Return the stored result for `executed` proposals. Refuse `executing`, `rejected`, failed,
   foreign, or invalid proposals without entering the handler. An `executing` record is an
   explicit unknown until reconciled; it is never blindly retried.
3. Pass the opaque proposal ID into reservation execution. The reservation-created event records
   it as `action_id`; the handler returns proposal, capability, reservation, commitment,
   requested/applied/shortage quantities, and event ID. Store this receipt as proposal output.
4. Add a tenant-scoped `proposal_execution_status` read which returns the lifecycle and validates
   a reservation receipt against proposal input, Reservation, Commitment, and BusinessEvent.
   It separately reports execution evidence, operational-state evidence, and that downstream
   business outcome is not proven.
5. Add guidance for both confirmation and reconciliation. Keep confirm excluded from default
   model schemas while contract discovery remains a read.

## Test Strategy

- Real PostgreSQL two-session race: one conditional claim, one handler execution, one reservation,
  one correlated event; replay returns the same receipt.
- Service tests for executing/rejected/foreign/invalid refusals and lost-response reconciliation.
- Planted defects for wrong commitment, quantity, reservation, missing event, and unrelated event.
- MCP tests for confirm discovery, reconciliation read, read-only behavior, bounded unknown names,
  and continued confirm exclusion from model schemas.
- Full backend, tenant, API/MCP, migration, lint, and spec-policy gates.

## Migration and Rollback

No migration. Existing `proposed`, `executed`, and `rejected` values remain valid; `executing` is
an additive lifecycle value. Rollback must first inspect any `executing` proposals because they
may represent an indeterminate committed effect.

## Risks

- A process can stop after claim and before final receipt: preserve `executing`, expose explicit
  reconciliation, and never retry automatically.
- Legacy mutation handlers commit internally: the pre-handler claim is deliberately committed
  first so concurrent callers cannot enter them.
- Receipt drift: validate against authoritative records and pin the public shape in tests/catalog.
