# Feature Specification: Explore the Reality data model

**Feature Branch**: `175-docs-data-model`
**Created**: 2026-09-12
**Language**: English
**Status**: Approved scope
**Input**: The owner accepted a Data Model entry in Tool Usage showing core objects, fields, examples, relationships, actions and derived values for ERP professionals.

## Context and Intent

### Problem
ERP professionals need to discover what a small operational model actually stores, where additional information belongs, and how to change it without assuming a document owns operational state.

### Scope
Add a bilingual Data Model explorer within Tool Usage, linked from the ERP handbook. Cover SourceRecord, Document, DocumentLine, Commitment, CommitmentRevision, Reservation, Movement, LedgerEntry and Fact. Explain each object through the existing Huber lamp example and authoritative field definitions.

### Non-Goals
No business schema, new predicates, mutation interface, live tenant records, API changes or migration. This is a reference, not an ERP table editor or a claim that every table is append-only.

## User Scenarios & Testing

### User Story 1 - Find the right place (Priority: P1)
An ERP professional opens Data Model, selects Commitment and understands the difference between an original promise, a revision, reserved stock and a shipment.
**Why this priority**: A trustworthy field reference needs the authority model first.
**Independent Test**: Open the Commitment address and inspect its purpose, example, related records and derived quantities.
**Acceptance Scenarios**:
1. **Given** Tool Usage, **When** selecting Data Model, **Then** all covered objects are discoverable with distinct business descriptions.
2. **Given** Commitment, **When** inspecting delivery dates, **Then** original due date and revisions are distinguished and revision tools can be reached.
3. **Given** an unused external field, **When** reading the overview, **Then** the reader learns it remains in SourceRecord unless supported operational or Fact semantics apply.

### User Story 2 - Inspect real fields (Priority: P1)
The reader finds all stored fields with types, storage nullability, defaults and meanings without mistaking storage requirements for tool input requirements.
**Why this priority**: Prevent invented fields and misleading input requirements.
**Independent Test**: Compare every displayed field and relationship with the current model and follow actions to their input contract.
**Acceptance Scenarios**:
1. **Given** any covered object, **When** inspecting fields, **Then** every stored column appears with its real type, nullability and default provenance.
2. **Given** a generated ID or timestamp, **When** inspecting its definition, **Then** generation is distinguished from user-supplied input.
3. **Given** a derived stock or open quantity, **When** inspecting the object, **Then** it is explicitly separate from stored fields.

### User Story 3 - Read and navigate (Priority: P2)
Readers search by object or field, follow relationships and action manuals, and share a direct link in English or German.
**Why this priority**: The reference must be usable on small screens and in the handbook.
**Independent Test**: Search due_at, navigate to revisions, open an action and return using browser Back; inspect narrow layout.
**Acceptance Scenarios**:
1. **Given** a field query, **When** searching, **Then** matching objects remain discoverable and the entire field name remains readable.
2. **Given** an object URL, **When** reloading or using Back, **Then** the selected object is restored.
3. **Given** either language and a narrow screen, **When** reading fields, **Then** text wraps without ellipsis and field details remain reachable.

### Edge Cases
Unknown hashes leave a usable explorer. Empty searches explain that no object matches. Optional values distinguish no default from null. Composite tenant keys retain their actual targets. Examples are labeled illustrative excerpts, never complete write payloads. Existing tool links retain their behavior.

## Requirements

### Functional Requirements
- **FR-001**: Expose covered core and ERP objects in a Data Model entry with business purpose and labeled example excerpts.
- **FR-002**: List every current stored field, type, storage nullability, default provenance and meaning, without presenting storage requirements as tool input requirements.
- **FR-003**: Expose actual relationships and links to existing action contracts; explain revision and correction semantics without offering mutations.
- **FR-004**: Distinguish stored operational fields, supported Facts, original source payload and derived observations.
- **FR-005**: Support object/field search, direct links and browser history in both languages with wrapping narrow layouts.
- **FR-006**: Link from the ERP handbook and keep generated metadata synchronized with authoritative definitions through automated checks.

### Key Entities
Documentation object, stored field, relationship, action reference and illustrative example. No new persistent business entities.

## Success Criteria

### Measurable Outcomes
- **SC-001**: All covered objects expose all stored fields without duplicate or invented columns.
- **SC-002**: Every published action reference resolves to an existing manual; every covered related object can be opened.
- **SC-003**: Delivery date, reservation, stock and unused upstream field examples identify their proper authority in both languages.
- **SC-004**: At a 375px viewport labels and field descriptions remain readable without text truncation; object links survive reload and Back.

## Assumptions and Dependencies
The owner's “ja mach” approves the proposed product scope. Existing intentional bilingual documentation remains bilingual. Current application models and catalog contracts are authoritative; metadata is generated without querying tenant data. Existing documentation build and deployment continue to work. Tests are required for schema completeness, semantic boundaries and navigation rendering.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001, FR-004 | T002–T003; data-model.test.mjs; reviewed bilingual authority examples |
| FR-002, FR-003 | T004–T005; test_data_model_reference.py; data-model.test.mjs |
| FR-005 | T006; browser navigation and responsive rendering checks |
| FR-006 | T007–T009; handbook links, deterministic catalog and Docker build |

## Approved ERP expansion

The owner accepted adding master data, pricing, warehouse/shipping and finance records after reviewing the first nine-record version. This extends the same explorer, with no business mutation or schema changes.

- **FR-007**: Cover Party, PartyRole, PartyHold, Item, Location, PaymentTerm; PriceList, PriceListEntry, PartyPriceList, PartyGroup, PartyGroupMember, PartyGroupPriceList; HandlingUnit, Lot, SerialUnit, Shipment, ShipmentPackage, ShipmentEvent, ShipmentEventSupersession, ReturnAnnouncement, MovementCorrection; SubledgerAccount, FinanceRoleDestination, LedgerReversal, SettlementAllocation; and CommitmentHold, with all real fields, examples, relationships and existing catalog actions.
- **FR-008**: Group the reference into core/evidence, master data, pricing, warehouse/shipping and finance. Search must find matching records across groups; following a relationship or direct URL must reveal its group automatically. Empty catalog action lists must be explained without inventing a standalone tool.

Acceptance: open Shipment, Party and Item directly in either language; inspect all fields and related records. Search tracking_number from another group, select ShipmentPackage, follow Shipment and return with browser Back. No narrow-screen ellipsis or overflow. Every covered record has one named group. Account balances, stock and transport progress remain derived, never new fields or mirror Facts.

Traceability: FR-007 → T010/T011, schema parity and ERP catalog contracts; FR-008 → T010/T012/T013, browser group/search/history checks. Public scope is these business records, not every administrative, integration or infrastructure table.

## Approved field table presentation

- **FR-009**: Replace field cards with a semantic table containing field name, meaning, storage requiredness, type, storage default and relationships. All values are visible without expanding individual fields. Long text wraps. On narrow screens only the labeled, keyboard-scrollable table region scrolls horizontally; the page must not overflow. Existing field search and relationship navigation remain intact. The owner explicitly requested the table presentation.

Acceptance: open Commitment in DE/EN at desktop/mobile widths; inspect all 17 rows and six column headers, filter due_at and follow a field relationship. Traceability: T014–T016, table contract and browser acceptance.

## Approved unified explorer presentation

- **FR-010**: Resources, Processes, Data model and Technical use one visual system for heading/description hierarchy, search spacing, filter controls, object cards, list surfaces and detail surfaces, including selected/hover/focus states. Compact optional model guidance replaces the large always-visible introduction cards. Preserve the field table, all metadata, query/filter functions, navigation and responsive reading.

Acceptance: compare all four tabs in DE/EN at 375/1280px, in light/dark themes. Shared card/filter/panel treatments match; labels wrap; model guidance remains available by keyboard; tables scroll locally; resource/process/tool/model navigation still works. The owner requested a consistent graphic treatment across the section. Traceability: T017–T019; visual contract tests and browser screenshots/computed-style checks.

## Compact documentation header and search

- **FR-011**: In both locales, use a short Search/Suchen header button with its descriptive accessible name preserved. At tablet widths (768–1279px), show the first three navigation destinations alongside the existing full-menu button; at 1280px and above show the complete navigation. Mobile retains the existing menu. The search input has one visible focus treatment around the containing search bar, while other controls retain keyboard focus indicators.

Acceptance: inspect English and German home and article headers at 375, 768, 1024, 1194, 1280 and 1600px without overlapping controls or page overflow. Open search, type a query, navigate by keyboard and close it. Inspect the single input focus treatment in both themes. The owner requested a narrower header search, usable tablet navigation and correction of the duplicate search border.
