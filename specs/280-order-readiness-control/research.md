# Research: Order Readiness Control

## Decision 1 — Use the existing fulfillment queue projection

**Decision**: Render `fulfillment_queue` through the existing specialized projection endpoint.

**Rationale**: It already combines canonical commitment, stock, reservation, hold and payment
readiness and returns snapshot/pending metadata. Recalculation or a new endpoint would duplicate it.

## Decision 2 — Keep order evidence and readiness as separate views

**Decision**: Add `Readiness` beside `Customer orders`; do not add operational status to evidence rows.

**Rationale**: The two views answer different questions and preserve Documents as evidence.

## Decision 3 — Treat missing metadata as unavailable

**Decision**: A snapshot without completed observation metadata is not authoritative readiness.

**Rationale**: Zero rows could mean no work or no completed calculation; safe operations must
distinguish them.
