# Feature Specification: Reviewed file, master-data and stock imports

**Created**: 2026-10-03
**Status**: Specified; implementation pending
**Language**: English
**Input**: Owner requested decision-gated interpretation across imports, master data,
payments and changes, explicitly included bulk processing, and authorized autonomous
specification/planning and careful verification in this conversation.

## Context and Intent

### Problem

The general artifact interpreter can create items, parties, locations, orders and stock adjustments directly. The reviewed item CSV slice has stronger admission but currently rejects files beyond 500 rows and is not a common contract for other import targets.

### Scope

Move all existing business-target file profiles and their master-data effects to prepared admission. Reuse the reviewed item CSV experience, add stable large-file packaging, and distinguish externally stated stock from authorized book-stock correction.

### Non-Goals

No unrestricted mapping workbench, automatic master-data merge, SKU-as-identity, new provider formats, physical stock inference or silently changed update semantics.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Spec workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Owner's roadmap](../../docs/ideas/decision-gated-intake-plan.md)
- [111-unified-data-sources](../111-unified-data-sources/spec.md)
- [129-unified-item-csv-import](../129-unified-item-csv-import/spec.md)
- [132-unified-opening-stock](../132-unified-opening-stock/spec.md)
- [344-external-stock](../344-external-stock/spec.md)
- [308-customer-item-numbers](../308-customer-item-numbers/spec.md)
- [Dependency 351-decision-gated-intake](../351-decision-gated-intake/spec.md)

## User Scenarios & Testing

### User Story 1 - Review file meaning and master records (Priority: P1)

Upload a file, see its exact mappings/defaults and proposed records, and accept them once.

**Why this priority**: Uploading data must not itself consent to business changes.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** an uploaded item, party or location file, **When** mapping and preparation run, **Then** original bytes and source references are retained while business records remain unchanged.
2. **Given** duplicate SKU, invalid later row or conflicting current master state, **When** a package is confirmed, **Then** the package refuses without partial creation and gives row-specific reasons.
3. **Given** an exact valid package, **When** it is approved twice, **Then** one atomic set of records exists with the same opaque receipt identities.

### User Story 2 - Import a large file with explicit packages (Priority: P1)

Process 5,000 item rows without one manual decision per row and without concealing rejected rows.

**Why this priority**: The existing 500-row limit must be deliberately handled rather than assumed away.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** 5,000 valid new-item rows, **When** bounded preparation completes, **Then** fixed packages bounded by both row count and serialized byte size are available for one exact batch-review operation; the controlled small-row fixture yields ten packages.
2. **Given** invalid rows at the beginning, middle or end, **When** preparation groups rows, **Then** issues are visible and excluded rows are named before review; no approved package is silently changed.
3. **Given** a duplicate SKU crossing package boundaries, **When** the file is validated, **Then** the duplicate is detected across the full intake and reported before approval.

### User Story 3 - Review orders and stock effects from files (Priority: P1)

Distinguish a received statement from the accepted promises or stock corrections it would produce.

**Why this priority**: A file snapshot must not silently move book stock.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a sales-order file with several lines per order, **When** it is prepared and later approved, **Then** each order stays atomic across its evidence and commitments.
2. **Given** an inventory snapshot or external-stock file, **When** it is interpreted, **Then** received quantities and proposed corrections are visible separately with zero preapproval movements.
3. **Given** stock changes after review, **When** a correction is approved, **Then** the outdated correction refuses and requires renewed review.

### Edge Cases

- Foreign tenant identities at source, proposal, manifest, target and receipt reads.
- Duplicate source delivery, concurrent review/approval, stale state and token revocation.
- Invalid later content, interruption before/after commit and uncertain execution.
- Changed source versions, mappings, defaults or referenced records after review.
- Rejected/blocked work remains inspectable; read-only recovery never executes it.

## Requirements

### Functional Requirements

- **FR-001**: File staging MUST preserve original bytes and tenant-scoped access; preparation MUST create a source describing the original artifact before business approval, without rewriting bytes or treating normalized rows as the original.
- **FR-002**: Existing item, party and location profiles MUST prepare exact fields, opaque reference resolutions, defaults, row identities and issues; no master record may be created or changed by preparation.
- **FR-003**: Current item-import duplicate/existing-SKU checks, update revision checks and tenant boundaries MUST be revalidated under the shared execution locks.
- **FR-004**: Accepted package records, events, source links and receipt MUST commit together; replay MUST return retained identities and never re-read a file to create records again.
- **FR-005**: Large-file intake MUST support 5,000 item rows and a 20 MiB raw CSV bound while retaining the existing 500-row/2 MiB single-package profile limits. Limits MUST be checked before business writes and shown in review.
- **FR-006**: Package membership and excluded-row reasons MUST be fixed before review; whole-input structural validation and cross-package duplicate detection MUST precede settlement. Partitioning MUST respect both row and exact serialized-byte limits, preserve complete coherent units, and explicitly report oversized units. Invalid content MUST NOT be silently dropped.
- **FR-007**: A changed file, mapping, defaults or partition MUST require a fresh prepared review; completed packages MUST remain unchanged on interruption, retry or response loss.
- **FR-008**: Sales-order file profiles MUST group complete orders as semantic units and preserve customer-item mapping and unstated-price rules.
- **FR-009**: Inventory snapshot correction MUST be a separately visible authorized effect bound to current book stock; no movement may be created before approval.
- **FR-010**: External-stock statements MUST be prepared before acceptance and MUST NOT themselves correct book stock. Bank-statement profiles MUST route to the financial intake package rather than bypass it.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality wherever applicable, immutable
  lossless source payloads and received values. Review comparisons are observations,
  not replacement source authority. Use opaque IDs and shortest true links.
- **DR-002**: Documents MUST NOT own operational fulfilment, inventory or payment
  status; accepted operational state remains derived from Reality records.
- **DR-003**: All reads/writes MUST be tenant-scoped and all transports MUST use
  shared application services. Cross-tenant identities behave as not found and never
  become authority through caller-supplied actor or scope claims.

### Key Entities

FileIntakeManifest: artifact/source identity, parser version, mapped profile, complete row membership and excluded issues. MasterPackage: at most 500 reviewed rows. FileOrderPlan: all rows belonging to one order. StockStatementPlan and StockCorrectionPlan: different accepted meanings and effects.

## Success Criteria

- **SC-001**: Every preparation/refusal scenario produces zero unapproved accepted
  business records; every approved coherent unit has exactly one truthful retained
  result and no duplicates after replay or concurrent settlement.
- **SC-002**: Every FR/DR has acceptance evidence, implementation tasks and executable
  verification; completion requires all required repository checks to pass.

## Assumptions and Dependencies

- The owner authorized this direction and autonomous preparation. These artifacts do not claim implementation, human review of an unseen design, release approval or verified runtime behavior.
- Existing business validation and stronger authorization remain in force; admitting a source does not authorize unsupported new business semantics.
- A coherent order is one unit; an item package is at most 500 rows; a manifest contains at most 500 independent units. These are different bounds, not interchangeable promises.
- Implement after the listed dependency contracts are available; adapter tests may use the shared typed plan contract before all other adapters are delivered.

## Requirement Traceability

| Requirement | Scenario(s) | Planned executable proof | Tasks |
| --- | --- | --- | --- |
| FR-001 | US1 | `packages/reality-core/tests/test_file_intake_admission.py::test_original_artifact_precedes_approval` | T003, T004, T005 |
| FR-002 | US1 | `packages/reality-core/tests/test_file_intake_admission.py::test_master_preparation_has_no_effects` | T003, T004, T005 |
| FR-003 | US1 | `packages/reality-core/tests/test_file_intake_admission.py::test_master_conflicts_refuse_atomically` | T003, T004, T005 |
| FR-004 | US1 | `packages/reality-core/tests/test_file_intake_admission.py::test_master_receipt_replays_exactly` | T003, T004, T005 |
| FR-005 | US2 | `packages/reality-core/tests/test_file_intake_admission.py::test_large_file_is_partitioned_before_legacy_limit` | T006, T008, T009 |
| FR-006 | US2 | `packages/reality-core/tests/test_file_intake_admission.py::test_full_file_validation_covers_package_boundaries` | T006, T008, T009 |
| FR-007 | US2 | `packages/reality-core/tests/test_file_intake_admission.py::test_mapping_change_and_resume_are_safe` | T006, T008, T009 |
| FR-008 | US3 | `packages/reality-core/tests/test_file_intake_admission.py::test_file_order_is_one_atomic_unit` | T010, T011, T012 |
| FR-009 | US3 | `packages/reality-core/tests/test_file_intake_admission.py::test_snapshot_does_not_adjust_before_approval` | T010, T011, T012 |
| FR-010 | US3 | `packages/reality-core/tests/test_file_intake_admission.py::test_external_statement_is_not_book_stock` | T010, T011, T012 |
| DR-001, DR-002, DR-003, SC-001 | US1–US3, edge cases | `packages/reality-core/tests/test_file_intake_admission.py` source/attribution, derived-state and tenant refusal matrix | T001, T002, T013, T014 |
| SC-002 | All | Required gates and final evidence review | T015 |
