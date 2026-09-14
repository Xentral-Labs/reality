# Research: Controlled Fact Observation

## Decision: Facts are observations, not mutation mirrors

**Rationale**: The existing model and Constitution place Fact beside typed Reality primitives, while BusinessEvent already records state changes. Mirroring typed state would create competing truth.

**Alternatives considered**: Create a Fact after every mutation; derive Facts from events. Both were rejected because they duplicate authoritative typed records and confuse evidence with audit history.

## Decision: Require SourceRecord in the new-write contract

**Rationale**: A Fact claims an observed statement. Requiring the immutable source makes that claim independently inspectable. Human statements can first be captured losslessly as a manual/chat SourceRecord.

**Alternatives considered**: Allow optional provenance; accept model reasoning as provenance. Both weaken the Source → Evidence → Reality invariant.

## Decision: Use a bounded catalog and canonical scalar values

**Rationale**: A predicate is useful only when producers and consumers agree on its subject and value semantics. The existing fact catalog is the smallest machine-readable enforcement point.

**Alternatives considered**: Free-form predicates; a generic ontology service; a new JSON column. Free form invites drift, an ontology is premature, and deterministic JSON scalar text fits the existing storage.

## Decision: Store tenant-scoped request fingerprints

**Rationale**: Agents, networks, and confirmation retries can repeat requests. A database uniqueness constraint provides exactly-once persistence under concurrency while preserving caller idempotency keys outside stored clear input.

**Alternatives considered**: Query by all Fact content; rely only on ChangeProposal status. Content can intentionally repeat at a later time, and non-agent callers also need retry safety.

## Decision: Keep proposal and interpretation above the core

**Rationale**: Reality should validate the storage contract, while source-specific parsing, confidence, and semantic selection remain replaceable. Chat/MCP use the existing ChangeProposal boundary.

**Alternatives considered**: Embed LLM interpretation in `record_fact`; let agents write directly. Both violate the service boundary and make model behavior authoritative.
