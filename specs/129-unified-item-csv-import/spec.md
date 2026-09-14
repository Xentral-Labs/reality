# Reviewed new-item CSV import
**Language**: English
## Context and Intent
### Problem
The source/import assessment found no current web upload path and unsafe legacy item-file replay/partial failure behavior. The owner approved the proposed narrow CSV slice with “ok” after reviewing the assessment.
### Scope
Import new items through one reviewed, synchronous application operation in unified Data & sources. Preserve original bytes and source links. Repair item-file atomicity/replay/retry defects identified in the assessment.
### Non-Goals
Vendor connections, other CSV profiles, updates/merge, schema expansion, broad mapping workbench, arbitrary background automation, provider-dependent parsing and old-app retirement.
## User Scenarios & Testing
### US1 — Import new items (P1)
An authorized member selects a UTF-8 CSV, source label and SKU/name/unit columns; previews every row, confirms once, sees exact created items and original source/file links. Stage/review creates no items. No AI provider is required.
### US2 — Prevent accidental changes (P1)
Invalid later rows, existing (including inactive) SKUs, duplicates and concurrent changes reject the whole item batch. Repeated confirmation, duplicated upload and a lost response cannot silently create duplicate items. Names and SKU remain source values rather than opaque identity.
### US3 — Recover and inspect (P1)
Reload restores the reviewed/recorded proposal, exact result and original-file access. Foreign artifact/proposal/source/item IDs disclose nothing. Existing item-file worker processing is atomic, replay-safe and retry recognizes file profiles.
## Requirements
- **FR-001**: Stage original UTF-8/BOM CSV bytes, maximum 2 MiB, 500 data rows, 50 unique nonempty header columns and 500 characters per mapped value; comma/semicolon/tab delimiter detection. Reject empty/malformed input, duplicate headers, ragged rows and invalid encoding. Source code is explicit, bounded and does not claim a live connection.
- **FR-002**: Map required SKU/name and optional unit; explicit fallback unit defaults to pcs and is shown in review. Only these mapped fields enter the new-item profile. Preserve original bytes including unused fields. Full-file validation returns row-specific errors before item writes.
- **FR-003**: Use existing item_create application tool, ChangeProposal and state-bound confirmation. Bind exact artifact hash, mapping, source, defaults and normalized rows to the review. Confirmation revalidates artifact and SKU conflicts under the shared tenant lock. Create source, all items and attributable events atomically; no new schema or financial records.
- **FR-004**: Reject duplicate SKUs within the CSV and any existing tenant SKU, including inactive items. This is import policy, not a global identity or uniqueness rule. Concurrent master creation/update and imports serialize validation. Same proposal/recovery never reruns item creation; changed file/mapping cannot silently reuse a different review.
- **FR-005**: UI supports stage → mapping → review → explicit confirm → verified results, cancel before confirmation, busy locks, read-based recovery and bookmarked proposal. Show exact item/source/original-file links; failed or unknown outcomes never claim success or auto-submit.
- **FR-006**: Apply existing active-user/tenant authorization to upload, preview, confirm, status and download; ordinary business members allowed, Playground excluded. Original download is attachment-only, scoped, and exposes no storage details. Four languages, keyboard and mobile/dark layout.
- **FR-007**: Repair existing item-target file worker processing: validate all rows first, commit the item batch together, completed-job replay returns existing items without writes and retry identifies supported artifact profiles. Other import profiles remain outside this repair scope.
## Assumptions and Dependencies
Existing SourceArtifact, SourceRecord, Item, BusinessEvent, ChangeProposal and import-job/outcome records suffice. The new UI uses synchronous item creation because a queue receipt is not proof of imported items. SKU conflicts are rejected, not matched to authoritative identities. Staging retains an original but is not consent to create items. Uploaded files and originals are tenant-protected. Existing direct master-data semantics remain unchanged except sharing the serialization lock.
## Success Criteria
All FRs have passing service/API and real isolated browser proof. A malformed later row leaves zero newly imported items; replay produces the same IDs; download bytes equal upload. Full required backend/frontend checks green.
## Requirement Traceability
| Requirement | Tests | Implementation |
|---|---|---|
| FR-001/002 | T001 service/API + T006 browser | T002 parser/staging + T005 UI |
| FR-003/004 | T001 service/concurrency/recovery | T002/T003 services/tool lifecycle |
| FR-005/006 | T001 API + T006 real browser | T004 API + T005 UI/localization |
| FR-007 | T001 legacy regressions | T002 worker repairs |
