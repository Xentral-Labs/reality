# Research: Complete Operational Exception Coverage

## Decision 1: One Shared Typed Derivation Service

**Decision**: Add one tenant-explicit exception service owning derivation and explanation;
Core compatibility, projections, Web, tools, fallback Chat, and MCP consume it.

**Rationale**: Core currently derives only commitment risk while the Web read model
independently adds a narrow import rule. A single service removes contradictory business
rules and provides one explainable contract.

**Alternatives considered**: Extending both SQL paths would preserve drift. Deriving only
from projection rows would make a disposable cache authoritative. Adapter-specific
classification violates the shared-service boundary.

## Decision 2: Source-Controlled Closed Taxonomy

**Decision**: Record five visible classes and one nested cause in a YAML taxonomy and
cross-check it against an explicit derivation registry and named test evidence.

**Rationale**: Documentation alone cannot detect a missing implementation or test. A
closed inventory makes `013/FR-005` durable without persisting exception state.

**Alternatives considered**: Function names alone omit product labels, cause structure,
authority, and evidence. A database table would create unjustified mutable state.

## Decision 3: Stable Derived Identity

**Decision**: Use `exc__{class_id}__{authoritative_record_id}` and re-derive the current
tenant queue before explanation.

**Rationale**: The class plus opaque authoritative ID is stable and collision-safe across
record types. Re-derivation makes resolved, stale, unknown, and foreign identities
non-disclosing without stored lifecycle.

**Alternatives considered**: Human numbers are not identity. Record ID alone collides
when more than one class can use a record. Persisted exception IDs imply lifecycle state.

## Decision 4: Controlled UTC for Overdue Supply

**Decision**: Accept an optional evaluation instant in the shared service, defaulting to
current UTC, and define overdue as `due_at < as_of` with positive remaining quantity.

**Rationale**: This is deterministic, excludes equality and missing dates, and continues
to derive open quantity from receipts rather than Document state.

**Alternatives considered**: Database current time makes focused tests brittle. A stored
overdue flag duplicates derived state. Date-only comparison loses operational precision.

## Decision 5: Conservative Movement Context Rule

**Decision**: Classify shipment, receipt, and return as unexplained only when both
Commitment and SourceRecord links are absent. Exclude opening stock, transfer, and
adjustment; adjustment already requires an audited reason in the owning service.

**Rationale**: These execution types normally need business context, while the excluded
types have intrinsic location context or an enforced reason. The rule uses current fields
and does not create a weak retroactive link.

**Alternatives considered**: Flagging every unlinked Movement creates false positives.
Parsing ChangeProposal JSON as a general relationship is not a shortest true link. A new
reason/FK field lacks an approved schema use case.

## Decision 6: Payment Control Entry Is Finance Authority

**Decision**: Derive an unmatched financial event from the positive unallocated remainder
of the payment-side AR/AP control LedgerEntry, using tenant-scoped SettlementAllocations.

**Rationale**: Existing payment calculations already use this relationship. It handles
partial allocation exactly and works for customer and supplier directions.

**Alternatives considered**: Cash amount ignores allocation direction. Document status is
not financial truth. Human payment numbers cannot identify a posting.

## Decision 7: No New Remediation for Append-Only Movement

**Decision**: Prove clearing only for classes with existing owning actions. An unexplained
Movement remains explainable and visible; no retroactive mutation is added in this spec.

**Rationale**: Movement is historical Reality. Inventing a repair link, ticket, or reason
field solely to make the exception disappear would violate schema and authority rules.

**Alternatives considered**: Mutating Movement damages history. A compensating Movement
does not explain the original. A persisted exception acknowledgement is explicitly out
of scope.

## Decision 8: Preserve the Existing Presentation Contract

**Decision**: Keep `severity`, `title`, `id`, and `impact`; add stable class, cause,
record, causal-value, and trace fields. Use the shared explain result for Inspector.

**Rationale**: The frontend can display new classes without business-rule changes while
operators and agents gain complete explanation.

**Alternatives considered**: A breaking response shape adds unrelated frontend work.
Keeping only the four legacy fields cannot prove class identity or lineage.
