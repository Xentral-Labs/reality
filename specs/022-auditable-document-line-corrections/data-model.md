# Data Model: Auditable Manual Document-Line Corrections

## Persistence decision

No schema change. Existing tenant-scoped Document, DocumentLine, Commitment,
LedgerEntry, and BusinessEvent records are sufficient.

## Persistent entities

- **Document**: Opaque tenant-owned Evidence header. `source_record_id` must be null.
  Header values, including gross amount, are unchanged by line correction.
- **DocumentLine**: Opaque tenant-owned line Evidence. Existing IDs retain rows, omitted
  IDs remove rows, and absent IDs create server-identified rows. Editable fields are
  source-line reference, item, SKU, description, quantity, unit price, gross amount,
  promised/requested time, unit, and line type. Input order is not stored.
- **Commitment**: Existing `document_id` and `document_line_id` are protected shortest
  links. No relationship changes.
- **LedgerEntry**: Existing `document_id` is protected financial provenance.
- **BusinessEvent**: Existing `document.corrected` subject/event stores the exact grouped
  line delta in the same transaction.

## Derived application values

`ManualDocumentLineSnapshot` contains Document ID, canonical revision, deterministic
lines, linked-Reality/correctability flags, and safe guidance. It is not persisted.

`ManualDocumentLineInput` contains an existing opaque ID or null for addition plus all
editable Evidence values. The collection is the complete intended snapshot.

`ManualDocumentLineCorrectionResult` contains the new revision, complete resulting
lines, changed/no-op flag, and added/updated/removed counts.

## Validation

- Document, existing line IDs, and referenced Items belong to the tenant.
- Existing IDs are unique and belong to the target Document; human references do not target rows.
- Source-line references satisfy the existing per-Document uniqueness constraint.
- At least one line remains; quantity is positive; all values reuse manual-entry normalization.
- Divergent requests require the current revision; external Evidence is rejected.
- Add/remove or economic deltas fail when protected Reality exists; reference-only edits may proceed.

## State transitions

```text
identical intended state → no-op, no event, current revision
current revision + permitted delta → corrected Evidence + one event + new revision
stale revision + divergent delta → conflict, no change
linked Reality + economic delta → owning-workflow guidance, no change
```

There is no migration, backfill, or destructive rollback.
