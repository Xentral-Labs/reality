# Research: Live Demo Cost Readiness

## Decision 1: Extend the canonical evidence profile, not the calculator

**Decision**: Author explicit acquisition evidence for every positively stocked item
in `international_demo` and review it through the existing batch inventory service.

**Rationale**: The observed zero/unavailable results are truthful consequences of
missing reviewed evidence. The costing formulas and explanation paths already work for
P03/P05. Completing the profile fixes the cause while preserving authority.

**Alternatives considered**: Infer cost from selling price (rejected: invented
authority); render a non-zero placeholder (rejected: false); special-case demo reads
(rejected: Web/MCP divergence).

## Decision 2: Readiness is an orchestration gate at an exact cutoff

**Decision**: The existing setup worker must create/publish and verify the canonical
cost observations before the receipt reports ready. Live simulation starts only after
that verified cutoff is durable.

**Rationale**: `ready` is the user promise and the setup worker already owns profile,
live-source and projection preparation. The exact cutoff makes the result explainable
and prevents the first intake occurrence from invalidating it invisibly.

**Alternatives considered**: Let the UI wait for eventual jobs (rejected: browser as
orchestrator); start live intake first (rejected: deterministic race); block the API on
unbounded work (rejected: current queued setup contract).

## Decision 3: Invalidate only retained, affected scopes

**Decision**: Compare each retained review only with relevant opaque item movement and
reviewed-cost events. Normal Demo Data orders and settlement records remain unrelated;
changed physical or selling-cost authority makes the current read stale until an owner
explicitly confirms a replacement review.

**Rationale**: Live synthetic orders intentionally do not acquire new stock evidence.
Invalidating every company scope after every event is false, while automatically
replacing a review after changed evidence would invent financial authority. Relevant
event comparison preserves both current values and honest staleness.

**Alternatives considered**: Full-company invalidation (rejected: false); automatic
review creation (rejected: invented authority); new periodic demo schedule (rejected:
second orchestration path); direct generation inside source interpreters (rejected:
couples intake and cache publication).

## Decision 4: Reuse existing persistence

**Decision**: Store only a compact readiness summary in existing setup progress and use
existing SourceRecord, review, generation, event and job records.

**Rationale**: All required identities, cutoff, failure and replay semantics already
exist. No repeated core query requires a new typed business field or table.

**Alternatives considered**: A demo coverage table or new freshness table (rejected:
duplicate authority); a migration/backfill (rejected: historical companies are out of
scope).

## Decision 5: Preserve shared read parity

**Decision**: Do not add new value endpoints. Web, MCP, Chat, CLI and API continue to
read the shared costing services; only setup progress gains the existing calculation
stage's truthful outcome.

**Rationale**: Parity is strongest when there is one read result rather than several
contracts that must be synchronized.

**Alternatives considered**: Demo dashboard aggregates (rejected: parallel business
rule); client-side refresh button automation (rejected: not available to agents).
