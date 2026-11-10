# Shopify source reference lookup

**Language**: English

## Context and Intent

### Problem
Existing discovery does not expose exact company roles or canonical selection
digests. The unchanged four-field intake preflight cannot qualify newly selected
company, location or item references. Operators need bounded read candidates to
present explicit choices without inventing mappings.

### Scope
One read-only source-bound lookup for existing company, location and item records.

### Non-Goals
No mapping write, preparation, acceptance, master-data creation, upstream read,
price/unit default, permission expansion, old99 overlay, migration or deployment.

## User Scenarios & Testing

### US1 - Select existing references (P1)
Given an exact current held Shopify source, search each family or inspect an exact
opaque record ID. See at most 20 active qualified candidates with canonical current
digests. Multiple matching items remain multiple choices.

### US2 - Refuse stale context (P1)
Changed source/version, foreign tenant, modified role/location/item during lookup
refuses the read rather than returning a mixed-current report.

## Requirements
- **FR-001**: Require exact source_record_id/import_job_id/source_hash/positive integer
  source_version using the existing canonical held-source basis.
- **FR-002**: Strict input adds family company/location/item, query<=120 characters
  (empty allowed for bounded listing), optional exact record_id<=200. Limit is
  fixed 20, never caller-controlled. record_id overrides textual filtering.
- **FR-003**: Tenant-scope every query. Company requires active Party and explicit
  lowercase company role; use canonical _reference_check digest. Location requires
  active current _reference_check and stock compatibility when source ships.
- **FR-004**: Items are active and of a supported canonical item type. Return exact
  _item_digest, observed nonempty stock unit or null, and source line IDs whose
  received SKU exactly matches the item SKU. Never infer quantity semantics.
- **FR-005**: Return purpose, exact source_binding, observed_at, records with id,
  label,digest,active,roles,stockUnit,sourceLineIds and hasMore. Company roles are
  known observed roles; location/item role knowledge is explicitly unknown.
- **FR-006**: Read at most21 matching records for a 20-record page. Never autochoose a
  SKU or hide duplicate matching items. Bound response to 24000 UTF-8 bytes.
- **FR-007**: Re-read exact source and selected query fingerprints before return.
  Refuse if source or candidate evidence changes. No partial stale output.
- **FR-008**: Normal service/tool/MCP read route, readOnlyHint true and destructiveHint
  false, normal token grant checks. No write or generic confirmation capability.

## Data Requirements
- DR-001: Existing records only; no schema. Original source and job.input immutable.
- DR-002: Hashes use existing canonical literal-Unicode UTF-8 JSON digest semantics.

## Assumptions and Dependencies
Root approved these bounded requirements on10 November2026. Native390/391 source
basis and reference digest helpers exist. The current native runtime is required;
old99 deployment support is outside this packet. Caller approval is separate from
lookup. A returned stock unit states master data only, not a reviewed count mapping.

## Success Criteria
Tests cover all families, exact selection, duplicate SKU ambiguity, shipping and
role filters, tenant and source guards, in-flight reference change and unchanged
business/source/job counts. Authenticated MCP advertisement and wire response
schemas must match frozen JSON contracts. Required repository gates stay explicit.

## Requirement Traceability
| Requirement | Task | Test |
|---|---|---|
| FR-001/FR-007 | T003/T004 | test_bounds_tenant_and_source_guards; test_two_session_reference_change_refuses |
| FR-002/FR-006 | T002/T004 | test_bounds_tenant_and_source_guards |
| FR-003/FR-004 | T002/T004 | test_company_location_item_are_canonical_current_and_no_writes; test_roles_shipping_and_active_filters_never_choose_foreign_meaning |
| FR-005 | T002/T006 | test_duplicate_skus_are_candidates_and_exact_id_overrides_query; JSON schemas |
| FR-008 | T005/T006 | test_authenticated_mcp_read_contract_and_no_generic_permission |
| DR-001/DR-002 | T003/T006 | no-write snapshots; frozen schema/example validation |
