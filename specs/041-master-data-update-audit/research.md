# Research: Auditable Master Data Updates

## Existing BusinessEvent payload

**Decision**: Add authoritative `changes` entries with normalized `before` and `after` values to the existing immutable event payload.

**Rationale**: BusinessEvent is already tenant-scoped, sequenced, subject-linked, and JSON-capable; another history table is unnecessary.

**Alternatives considered**: Snapshot tables duplicate master data; summaries remain insufficient; database triggers bypass business and actor context.

## Proposal shape and staleness

**Decision**: Use opaque target IDs, complete intended update representations, and server-generated revisions of reviewed normalized snapshots.

**Rationale**: This matches existing update contracts, gives exact previews, avoids patch/null ambiguity, and rejects stale confirmation.

**Alternatives considered**: Merge-patch input obscures clearing semantics; names/SKUs as identity violate the Constitution.

## Diff normalization

**Decision**: Compare public normalized snapshots, including roles and nullable relationships, after canonical validation.

**Rationale**: Events describe effective business changes rather than whitespace, case, Decimal format, or duplicate-role artifacts.

**Alternatives considered**: Raw-input diffs create false positives; ORM dirty tracking does not clearly cover collections and normalization.

## Proposal provenance

**Decision**: Reuse `BusinessEvent.action_id` for the executing ChangeProposal.

**Rationale**: It is the shortest existing link to reviewed input and actor type.

**Alternatives considered**: Copying proposal metadata into payloads duplicates immutable data; a new FK is unnecessary.

## Compatibility and no-ops

**Decision**: Preserve existing event summary keys additively and emit no update/lifecycle event for an equal normalized state.

**Rationale**: Existing consumers remain compatible, while the event stream never claims a change that did not occur.

**Alternatives considered**: Replacing payloads risks consumers; recording attempts belongs in ChangeProposal/action audit.
