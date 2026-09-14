# Data Model: Business-readable Inspectors

## Persistence

No persistent entity, field, relationship, index, or migration is added.

## Read model

The existing Inspector explanation remains a transient tenant-scoped read model and
adds:

- **meaning**: concise statement of what the record means in business terms;
- **business reference**: best available authoritative display reference plus its kind;
- **guidance**: next review step when authoritative guidance exists;
- **technical rows**: exact identifiers and machine fields retained for disclosure.

The existing status, metrics, Source → Evidence → Reality trail, related sections,
events, and source payload remain. Human references are presentation only. Every link
continues to use opaque `kind` and `id` values.
