# Research: Large-Tenant Register Benchmark

## Decision 1: Treat 10,000 orders/day as read cardinality

**Decision**: Populate at least 10,000 orders on one UTC business date and prove the
existing Web large-tenant read contract. Do not translate the daily count into an
orders-per-second target.

**Rationale**: Spec 016 and `docs/WEB_SPEC.md` define the missing evidence as bounded
core-register behavior, not ingestion concurrency, hardware, or latency thresholds.

**Alternatives considered**: A compressed-day write load overlaps the separate
100,000-order capacity idea and requires intentionally deferred decisions.

## Decision 2: Use PostgreSQL and production read models

**Decision**: Execute cases through existing `reality.web.read_models` functions against
PostgreSQL. Do not benchmark browser rendering or HTTP transport.

**Rationale**: These functions are the narrowest shared Product Web boundary containing
tenant filtering, counting, aggregation and pagination without transport noise.

**Alternatives considered**: Direct ORM queries test a benchmark-specific path; HTTP-only
cases add variance and obscure SQL inspection.

## Decision 3: Separate deterministic setup from measured cases

**Decision**: Provide reduced and full profiles from one fixed-seed definition. Setup
uses existing domain/service and projection behavior, is measured separately, and must
pass cardinality and sample-trace validation before read evidence is accepted.

**Rationale**: Construction establishes context but is not part of the read claim. One
definition prevents CI and full-acceptance behavior from drifting.

**Alternatives considered**: A database dump is brittle across schema revisions; random
factory data prevents repeatable counts and page identities.

## Decision 4: Add no benchmark dependency

**Decision**: Use monotonic timing, SQLAlchemy statement observation, PostgreSQL plans
where required, Pydantic v2 as the canonical result validator/schema authority, and the
existing test stack.

**Rationale**: Acceptance is boundedness and correctness. Statistical latency tooling
adds little without an approved SLO.

**Alternatives considered**: `pytest-benchmark` and external load generators suit a
future concurrent capacity test, not this proof.

## Decision 5: Combine behavioral and structural evidence

**Decision**: Retain result assertions plus evidence that tenant scope,
filter/count/order/limit occur in database statements before materialization.

**Rationale**: Fast results alone cannot detect incorrect totals or Python scans; SQL
shape alone cannot prove business outcomes.

**Alternatives considered**: Timing thresholds are environment-dependent; returned
length alone misses unbounded intermediate work.

## Decision 6: Retain evidence beside the feature

**Decision**: Write Pydantic-validated JSON and derived Markdown beneath this feature's
`evidence/` directory using neutral `benchmark-result` names until final review.

**Rationale**: Versioned evidence binds the claim to revision, schema, environment and
dataset. CI logs are ephemeral and prose alone is hard to validate.

## Decision 7: Remediate red cases only

**Decision**: Plan no index or production change upfront. A failing case must justify
the smallest read/projection correction.

**Rationale**: The Constitution rejects schema expansion without proven need; the
benchmark exists to produce evidence before optimization.

## Decision 8: Reuse narrowly in the later capacity idea

**Decision**: Reuse the dataset definition, register cases, tenant sentinels and report
format where compatible. Leave arrival curves, ingestion, concurrent workers, resources,
recovery, soak, bottleneck analysis and AWS validation unresolved.

**Rationale**: This prevents duplicated groundwork without overstating a read-cardinality
proof as production capacity.
