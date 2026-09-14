# Research: Chat Master Data Proposals

## Tool granularity

**Decision**: Expose one explicit proposal tool per master-data family.

**Rationale**: Party, Item, and Location have different required fields, defaults, and
relationships. Explicit schemas help the model request missing business data and keep
the mutation allowlist review understandable.

**Alternatives considered**: A generic master-data CRUD tool weakens schema guidance and
expands authority. One tool per record prevents a natural request for three items from
being confirmed atomically.

## Batch boundary

**Decision**: Each family tool accepts a non-empty `records` list and confirmation is
atomic for that list. Mixed-family batches are excluded.

**Rationale**: Natural-language requests commonly create several sample records. One
proposal provides one review/confirmation moment and prevents partial same-family setup.

**Alternatives considered**: Multiple independent proposals make partial user outcomes
normal. Mixed-family batches add orchestration and rollback complexity without a proven
request.

## Required values and defaults

**Decision**: Mirror the established services: Party requires name and at least one role;
Item requires SKU and name with unit `pcs`; Location requires name with type `warehouse`.

**Rationale**: Chat must not create a second business contract. Existing accepted enum
values and relationship validation remain service-owned.

**Alternatives considered**: Requiring every optional field makes Chat cumbersome;
inventing Chat-only defaults creates adapter drift.

## Optional provenance

**Decision**: Omit SourceRecord creation when provenance is absent. When used,
`source_system` and `external_id` are supplied together and `source_payload` remains
lossless.

**Rationale**: This is the established master-reference model and the direct correction
to the import-only hallucination.

**Alternatives considered**: Synthetic `manual` SourceRecords misrepresent provenance;
requiring upload Evidence contradicts the existing domain.

## Transaction ownership

**Decision**: Add thin service-level batch entry points backed by shared no-commit record
builders and one final commit.

**Rationale**: Application tools may orchestrate but must not own persistence or allow
partial committed batches. Reusing builders keeps single and batch validation aligned.

**Alternatives considered**: Looping over current committing services is not atomic.
Adding a public `commit=False` flag leaks transaction control into callers.

## New hierarchy references

**Decision**: Location batches use local `ref` and `parent_ref` tokens resolved in input
order; `parent_location_id` remains an existing opaque identity only.

**Rationale**: Generated IDs do not exist when the model prepares one atomic hierarchy.
Local references express shortest links without treating human names as identity.

**Alternatives considered**: Resolving names is ambiguous and violates the identity
rule. Creating one proposal per hierarchy level loses atomic confirmation.
