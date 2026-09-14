# Contract: Manual Document-Line Correction

## Read editable snapshot

`GET /api/tenants/{tenant_id}/documents/{document_id}/line-correction`

For manual Evidence, returns `document_id`, canonical `revision`, `correctable: true`,
`has_linked_reality`, `economic_changes_blocked`, safe `correction_guidance`, and the
complete normalized `lines`. Each line exposes its opaque ID and editable Evidence
values. For externally sourced Evidence, the same read returns `correctable: false`,
an empty editable line list, and guidance to use source-version correction; it never
exposes a writable snapshot. The ordinary Inspector remains readable for all Evidence.

## Replace complete snapshot

`PUT /api/tenants/{tenant_id}/documents/{document_id}/line-correction`

```json
{
  "expected_revision": "sha256-hex",
  "lines": [
    {
      "id": "lin_opaque",
      "item_id": "itm_opaque",
      "source_line_id": "1",
      "sku": "SKU-1",
      "description": "Corrected widget",
      "quantity": "2.0000",
      "unit": "pcs",
      "unit_price": "10.0000",
      "gross_amount": "20.0000",
      "promised_at": "2026-09-05",
      "line_type": "item"
    }
  ]
}
```

The array is the complete intended state. Omission removes an existing line; a missing
ID adds a line. Human references never select a row.

Success returns Document ID, new revision, complete resulting lines, `changed`, and
added/updated/removed counts. An identical current-state retry containing the current
opaque IDs returns `changed: false`, zero counts, current revision, and no extra event.
A retry that repeats an ID-less addition after the first request succeeded is stale and
is rejected; it never creates another line or event.

## Failures

- Unknown/foreign Document, line, or item: non-disclosing existing error policy.
- External Evidence: source-version correction guidance.
- Empty/invalid snapshot: validation error and no mutation.
- Stale divergent revision, including a repeated already-applied ID-less addition:
  conflict with reload guidance and no mutation.
- Linked Reality plus economic delta: owning correction guidance and no mutation.

Exact status mapping follows existing `NotFound`/`InvalidOperation` policy and is fixed
by API tests before UI implementation.

## Audit

One changed replacement emits `document.corrected` with `changed_fields: ["lines"]`
and `line_changes` groups for added, removed, and changed opaque IDs. Entries contain
all normalized before/after fields. Actor/action context is attached only when supplied.
