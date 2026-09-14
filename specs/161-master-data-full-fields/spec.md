# Complete master data fields

**Language**: English

## Context and Intent
The unified Master data forms prepare canonical `party_update`, `item_update`, `location_update` and the matching create proposals, but the preparation service admits only a name (plus SKU and, on creation, unit for items). Every other operational field the same commands already accept — party roles, commercial defaults, item inventory behaviour, location hierarchy and external identity — is unreachable from the web form, although the page promises "details and commercial defaults". The owner asked for the complete field set in all four families.
### Problem
Operators cannot maintain payment terms, credit limits, currencies, accounting codes, tax identifiers, item types, tracking, default locations, purchase units, conversion factors, lead times, location types, parents, stock flags or external identity from Master data. The form is narrower than the command and the detail panel does not name the codes the operator would have to enter.
### Scope
Extend the preparation whitelist, its validation and its canonical proposal record to every field the shared create/update services accept for parties, items and locations, except lossless `source_payload`. Expose the editable codes (payment term code, source system, external ID) in the record detail. Give the web form per-family field groups with tenant-scoped choices, and show every reviewed field with a readable label in the proposal review. Keep preparation, review, confirmation, replay and stale-revision behaviour unchanged.
### Non-Goals
No new columns, services or tools. No editing of `source_payload` through the form; external evidence stays lossless. No party deletion, role removal of the register's own role, or clearing of an item's default location (the shared service does not support it). No change to legacy pages, Chat or MCP tool contracts beyond what they already accept.
## User Scenarios & Testing
### US1 — Full customer or supplier maintenance
Given a customer, opening Edit details shows name, party type, roles, accounting code, payment term, default currency, credit limit, tax identifier, source system and external ID prefilled from the record. Changing several fields, preparing and confirming records exactly those values, keeps untouched values, and the audit diff lists each changed field. Removing the customer role from the Customers register is refused.
### US2 — Item inventory behaviour
Given an item, the form offers SKU, name, unit, item type, tracking, default location (tenant-scoped choice), purchase unit, conversion factor, lead time, source system and external ID. Invalid values (unknown type, zero conversion factor, negative lead time) are refused before any proposal exists.
### US3 — Location hierarchy
Given a location, the form offers name, type, parent location, stock flag, source system and external ID. Creating a location can choose its type and parent. A location cannot become its own parent.
### US4 — Provenance stays truthful
Editing without touching source system or external ID keeps the same source record. Changing either creates a new immutable source version and the record's provenance follows it.
## Requirements
- **FR-001**: Preparation accepts, validates and canonicalises every operational field the shared create/update services accept for parties (name, type, roles, accounting code, payment term code, default currency, credit limit, tax identifier, source system, external ID), items (SKU, name, unit, item type, tracking type, default location, purchase unit, conversion factor, lead time days, source system, external ID) and locations (name, type, parent location, allows stock, source system, external ID). Unknown fields are still refused.
- **FR-002**: An update proposal carries the current value of every editable field the request omits, so canonical execution never resets an untouched field; roles must keep the register's own role; the reviewed revision check is unchanged.
- **FR-003**: Record detail exposes the editable codes — payment term code, source system and external ID — without changing the reviewed revision.
- **FR-004**: The web form shows per-family field groups with tenant-scoped choices for payment terms, currencies, units, locations and source systems, prefilled from the record; the review lists every field with a readable label in en/de/nl/es.
- **FR-005**: Validation failures name the field and no proposal is stored; replay with the same request identity keeps returning the same proposal.
## Success Criteria
Every field listed in FR-001 can be changed from the web form for each family and lands in the record with an exact before/after audit diff. Existing reference workspace, unified API and browser tests pass alongside the new field, validation and provenance tests.
## Assumptions and Dependencies
Extends spec 140 FR-006 from "basic" to the complete service field set; spec 041 audit diffs and spec 059 proposal confirmation remain the execution path. No schema change; the `Party`, `Item`, `Location` and `SourceRecord` columns already exist.

## Requirement Traceability

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001, FR-005 | T002, T003 | `test_reference_workspace.py` full-field create/update and rejection tests |
| FR-002 | T002, T003 | omitted-field preservation and role guard tests |
| FR-003 | T002, T003 | detail code exposure test, `test_unified_workspace_api.py` |
| FR-004 | T004, T005 | `unified-app-contract.test.mjs`, `unified-workspaces-browser.mjs`, i18n audit |
