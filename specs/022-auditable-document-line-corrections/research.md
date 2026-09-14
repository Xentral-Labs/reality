# Research: Auditable Manual Document-Line Corrections

## In-place Evidence with event audit

**Decision**: Retain opaque IDs for unchanged lines, update corrected Evidence, assign
IDs to additions, remove permitted omissions, and record exact before/after values in
one `document.corrected` BusinessEvent.

**Rationale**: Manual Evidence is not immutable Source, and existing header correction
already uses mutation plus audit. Stable retained IDs preserve shortest links.

**Alternatives considered**: Replacement Documents require lineage and disrupt Reality
provenance; a correction table duplicates BusinessEvent without a proven calculation.

## Derived optimistic-concurrency revision

**Decision**: SHA-256 canonical JSON of all stored editable line fields, ordered by
opaque ID, is the revision token.

**Rationale**: It detects every stale line edit without stored revision state.

**Alternatives considered**: A version column lacks a repeated schema use case; latest
event sequence creates false conflicts; last-write-wins violates FR-009.

## Idempotent retry

**Decision**: Normalize and compare intended/current state before checking revision. An
identical snapshot containing the current opaque IDs succeeds as a no-op and emits no
event. A retry that repeats an ID-less addition after the first request succeeded is a
stale divergent request: it fails safely and creates neither another line nor event.

**Rationale**: This prevents every duplicate effective correction without an idempotency
table. A lost response involving only retained IDs can be recognized as a no-op; a lost
response involving a server-identified addition requires reload before further editing.

**Alternatives considered**: Persisted request keys add infrastructure; duplicate events
make the audit ambiguous.

## Economic classification

**Decision**: Item, quantity, unit, prices, amount, requested/promised time, line type,
addition, and removal are economic. Source-line reference, SKU, and description are
presentation/reference Evidence.

**Rationale**: The former can change operational or financial interpretation; the latter
can be corrected without changing derived Reality.

**Alternatives considered**: Locking every field is unnecessarily strict; allowing every
field contradicts approved decision 1A.

## Protected Reality paths

**Decision**: Check Commitments by `document_id` or `document_line_id` and LedgerEntries
by `document_id`, always tenant-scoped. Reservations and Movements remain transitively
protected through Commitment.

**Rationale**: These are the existing shortest proven Evidence-to-Reality links.

**Alternatives considered**: Direct queries to every Reality table duplicate links;
Document-only checks miss line-only Commitments.

## Adapter scope

**Decision**: Extend existing Web/API correction only; do not add CLI, MCP, chat, or agent.

**Rationale**: Those correction surfaces do not exist today, and chat would require a
separate proposal/confirmation flow. Future adapters reuse the same service.

**Alternatives considered**: All adapters expands feature count; API-only fails the
approved operator journey.
