# Inspector Read Contract

`GET /api/tenants/{tenant_id}/inspector/{kind}/{record_id}` remains read-only and
tenant-scoped.

In addition to the current record identity, status, metrics, trail, sections, events,
and optional source payload, a successful response provides:

- `meaning`: one business-language explanation of the record;
- `business_reference`: nullable `{label, value}` using the best authoritative human
  reference available through existing links;
- `guidance`: nullable next review step; null when no authoritative guidance exists;
- `technical_rows`: exact identifiers and machine fields for secondary display.

Fact responses describe the predicate/value as an observation and resolve source or
document context without changing subject identity. Exception responses use the current
derived explanation and catalog guidance. Missing optional context is null or explicitly
described as manual/internal; it is never fabricated.

Existing kinds, paths, authorization, 404 behavior, and opaque links remain compatible.
