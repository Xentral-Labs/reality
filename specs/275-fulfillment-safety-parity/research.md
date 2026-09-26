# Research: Fulfillment Safety Parity

## Decision 1 — Store an explicit prepayment policy on PaymentTerm

**Decision**: Add a non-null `requires_prepayment` boolean to the tenant-scoped payment term,
defaulting false for existing and newly omitted values.

**Rationale**: Fulfillment repeatedly filters, constrains and acts on this agreement. The policy is
not derivable from `due_days`, code or label without inventing semantics. PaymentTerm already owns
the other typed commercial timing policy and orders already retain its opaque ID.

**Alternatives considered**:

- Infer from code `VORKASSE` or zero due days: rejected because human labels/numbers are not identity
  or authority and zero-day payment is not necessarily prepayment.
- Store a payment status or prepayment flag on Document/Commitment: rejected because documents do
  not own fulfillment/payment state and the agreement already has a shorter link.
- Add a generalized policy table immediately: rejected because one proven binary policy does not
  justify a new abstraction.

## Decision 2 — Derive readiness from order evidence and allocations

**Decision**: Required amount is the order's stated gross amount. Qualifying received amount is the
sum of active customer-payment allocations to posted sales-invoice receivables whose billed lines
map unambiguously to that order's lines and match customer/currency/tenant.

**Rationale**: This follows existing shortest links, counts recorded money rather than recomputing
it, works for partial payments, and excludes unrelated/unallocated/reversed money.

**Alternatives considered**:

- Treat invoice open amount as payment received: rejected because credits/reductions can reduce open
  amount without money arriving.
- Count all customer credit: rejected because unallocated credit has not been stated or confirmed as
  payment for this order.
- Require one invoice per order: rejected because partial billing is normal; only ambiguous
  attribution blocks.

## Decision 3 — One service returns both decision and fingerprint evidence

**Decision**: A batch-capable fulfillment-readiness service returns normalized blockers, values,
links and a canonical relevant-state structure used by both reads and review-token hashing.

**Rationale**: A separate fingerprint query would recreate the same rule and can drift. Returning
the state basis makes decisions explainable and lets review freshness cover exactly what affected
the answer.

**Alternatives considered**:

- Extend only the materialized projection: rejected because execution must not depend on a stale
  cache and review needs authoritative current state.
- Implement payment checking inside MCP/Chat: rejected by the shared-service boundary and the
  reproduced parity defect.

## Decision 4 — Terminalize only known effect-free failures

**Decision**: Proposal execution catches domain refusals or known rolled-back transactions at the
shared boundary, stores a structured failed receipt, and re-raises the refusal. Unexpected failures
retain executing/unknown until evidence-based reconciliation.

**Rationale**: The system can truthfully classify deterministic synchronous validation refusal and
complete rollback, while timeout/process-loss cases remain genuinely uncertain.

**Alternatives considered**:

- Reset to proposed: rejected because the attempted confirmation and refusal are audit evidence and
  retrying unchanged invalid intent is misleading.
- Mark every exception failed: rejected because an effect may have committed before communication
  failed.

## Decision 5 — Test the serialized MCP contract

**Decision**: Preserve the purpose-discriminated shipment schema builder, make executable input
validation consume the same vocabulary, and test the actual MCP `tools/list` serialization plus
generated documentation.

**Rationale**: The registry source already contains branches, yet the live Claude client reported an
empty schema. A registry-only assertion cannot prove what a client receives.

**Alternatives considered**:

- Add prose examples only: rejected because an agent needs machine-readable required/nested/enum
  fields.
- Duplicate schemas in documentation: rejected because generated docs must follow the executable
  catalog.
