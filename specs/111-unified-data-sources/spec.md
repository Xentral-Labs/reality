# Feature Specification: Unified Data and Sources

**Feature Branch**: `139-unified-app-foundation` (isolated additive increment)
**Created**: 2026-09-07
**Language**: English
**Status**: Owner-authorized continuation of the new-design migration.
**Input**: Continue toward one coherent App using useful existing capabilities.

## Context and Intent

### Problem
Source investigation still leaves the new App. Operators and technical staff need to find where records came from and distinguish received originals from interpreted evidence.

### Scope
Move Data & sources into the unified shell with registered systems, received source records and evidence documents. Follow an exact source version into its evidence and native Inspector. Keep metadata registers paginated and payloads out of lists.

### Non-Goals
No connection setup, external import, retry/execution, credential management, new interpretation rules, source edits/deletion, schema, AI policy change, full Explorer redesign, deployment, merge or legacy/Playground retirement.

## User Scenarios & Testing

### US1 — Understand registered origins (P1)
An operator searches registered systems, sees configured active state and the number of held source versions, and opens that system's received records.

Independent proof: systems sharing names remain distinct by opaque IDs/codes; counts include every held version, even beyond the first page. Disabled means configuration state, never unavailable connectivity or loss of retained evidence.

### US2 — Follow a received version into evidence (P1)
An operator searches source metadata, filters by system, sees version, received timestamp and import-job status, then opens the original or the evidence for that exact source ID.

Independent proof: two versions of the same external identity remain distinct. Evidence for one version excludes another version and foreign-company documents. List payloads never contain original payload text, job input or errors; the exact original is available through the Inspector as escaped text.

Acceptance: missing job is shown as no job; completed job means execution status, not successful interpretation. Records without evidence show an honest empty list. Sources without a registered system remain discoverable.

### US3 — Inspect documents inside the App (P2)
An operator searches by number/reference or source metadata, filters document type/system or exact source, pages through evidence and opens a document's Inspector.

Independent proof: documents retain recorded amounts and currencies individually, with no invented fulfillment/financial state. Search and exact-source filters apply before totals/pagination. Company switching clears selected source/record and filters; reload preserves tab and selection.

### Edge Cases
Multiple versions, identical labels/codes across tenants, unregistered origins, no source on manual evidence, no job, completed review-required interpretation, no evidence, inactive systems, malformed/foreign IDs, empty/error/retry, long external IDs and untrusted payloads.

## Requirements

- **FR-001**: Data & sources is a unified destination with Systems, Received records and Evidence documents; retain supporting setup/import/Explorer paths.
- **FR-002**: Systems are tenant-scoped, searchable, server-paged and show configured active state plus complete source-version counts without loading payloads.
- **FR-003**: Source records are server-paged metadata only, with exact system filter and metadata search, opaque ID, version, received timestamp and exact job status; no payload/input/error in list reads.
- **FR-004**: Selecting a source opens its native Inspector or evidence filtered to that exact source version. Foreign records cannot leak through filters or Inspector.
- **FR-005**: Evidence uses shared document reads, server search/type/system/exact-source filters and paging; amounts remain recorded values in their own currencies, never an operational status authority.
- **FR-006**: URL state preserves tab, filters, page and initial Inspector; company switching clears scoped context. Read navigation creates no authoritative records or jobs.
- **FR-007**: All controls support en/de/nl/es, light/dark and 390/1440 px, keyboard focus, empty/loading/error/retry and safe rendering without horizontal page overflow.

## Key Entities
Existing SourceSystem, SourceRecord, ImportJob and Document evidence. No new entity, state machine or authority.

## Assumptions and Dependencies
The owner's continued instruction covers the next bounded workspace in the agreed migration direction. Existing tenant authorization and ordinary-company admission remain. Stored source versions, not unique external identities, are counted. Source system code is the existing SourceRecord origin field; exact source identity remains opaque. Job status is faithfully recorded, not equated with interpretation success. Advanced configuration/import operations stay reachable through supporting paths.

## Success Criteria
Every listed source can open its original and exact-version evidence. Counts/search/page boundaries are correct for multi-page, multi-version and multi-tenant fixtures. No source payload loads as part of systems/source lists. All seven requirements have executable coverage and all visual/keyboard gates pass before technical completion.

## Requirement Traceability
| Requirements | Stories | Planned evidence |
| --- | --- | --- |
| FR-001 FR-006 | US1 US3 | Route and browser traversal/reset tests |
| FR-002 FR-003 | US1 US2 | Metadata-only SQL/API paging/count/filter tests |
| FR-004 FR-005 | US2 US3 | Exact-version and foreign evidence tests, native Inspector browser |
| FR-007 | US1–US3 | Localization and responsive/keyboard/error browser matrix |
