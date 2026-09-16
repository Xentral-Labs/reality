# Feature Specification: Visible record provenance and source addressing

**Created**: 2026-09-16
**Language**: English
**Status**: Implemented. Scope authorized by user request on 2026-09-16, including the explicit decision to place the external base address on `SourceSystem`, the approval of FR-007 after the connector-association defect was demonstrated, and the instruction to remove the unreachable master-data detail panel this work uncovered (FR-015).

## Context and Intent

### Problem
Almost every operational record already knows where it came from: `source_record_id` exists on Party, Item, Location, Document, Commitment, Shipment, Movement, LedgerEntry, Fact and BusinessEvent, and `SourceRecord` retains the identity `(source_system, source_type, external_id, version)` plus the immutable payload. The Facts register and the master-data detail expose this; the operational workspace does not. A user looking at a sales order cannot see that it arrived from Shopify, cannot inspect the payload that produced it without leaving the page, and has no way to reach the same order in the system that owns it.

### Scope
One shared origin contract, rendered consistently wherever a record is listed or opened; one in-place inspection of the originating source record, including its retained payload and its interpretation outcome; and an optional, configuration-only external address so a user can open the same record in the system it came from.

### Non-Goals
Field-level provenance ("this address came from HubSpot") is deliberately deferred: it is an assertion about a Fact, not about a record, and deserves its own specification. Also out of scope: storing a per-record external URL supplied by an interpreter, writing back to any external system, credentials, transport, scheduling or any vendor API call, origin badges on aggregate rows, and any change to ingestion, interpretation or the immutability of source payloads.

## User Scenarios & Testing

### User Story 1 - See where a record came from (Priority: P1)
An operator scanning the orders register sees which orders arrived from which system, and which were entered by hand.

**Why this priority**: Origin is the first question asked when a record looks wrong, and it is currently unanswerable without leaving the workspace.
**Independent Test**: Open an operational register containing imported and manually created records; confirm both state their origin.

**Acceptance Scenarios**:
1. Given a register row whose record carries a source, when the register is displayed, then the row states the source system name and the external reference.
2. Given a register row whose record carries no source, when the register is displayed, then the row states that the record was created in the application, naming the deciding user where one is recorded.
3. Given a record detail or card, when it is opened, then the same origin statement appears with the source version and the time the version was received.
4. Given a register whose records are derived rather than imported, when it is displayed, then the origin column is available but not shown by default.
5. Given a source system that was renamed or removed after ingestion, when an affected record is displayed, then the retained textual source identity is still shown and no link is offered.

### User Story 2 - Inspect the original payload in place (Priority: P1)
An operator opens the origin of one record and sees exactly what arrived and what it produced, without losing the register.

**Why this priority**: This is the product's explainability promise applied to the one link that was missing from the workspace.
**Independent Test**: Activate the origin of an imported record and confirm identity, payload, interpretation outcome and produced records are readable in place.

**Acceptance Scenarios**:
1. Given an origin statement for an imported record, when it is activated, then a bounded inspection opens in place showing source identity, version, received time and import state.
2. Given that inspection, when it is displayed, then the retained source payload is readable, bounded and read-only.
3. Given that inspection, when the source record has a terminal interpretation outcome, then its classification, interpreter and reason are stated; a source without a terminal outcome is labeled as not recorded rather than given a fabricated outcome.
4. Given that inspection, when it is displayed, then every record produced from the same source record is listed by its own name or number and remains reachable.
5. Given that inspection, when the full explanation is requested, then the existing Inspector opens on the same source record with its existing back navigation.

### User Story 3 - Reach the record in the system that owns it (Priority: P2)
An administrator configures a source system's address once; afterwards every record from that system offers a direct link to its counterpart.

**Why this priority**: It converts a read-only observation into the action people actually want, and it is configuration, not integration.
**Independent Test**: Configure a base address on an installed source system and follow the link from a record of a supported source type.

**Acceptance Scenarios**:
1. Given an installed source system without a base address, when a record from it is displayed, then origin is shown without a link and the detail offers the one-time configuration path.
2. Given a base address configured on the source system and a vendor address template for the record's source type, when the origin link is activated, then the external record opens in a separate context, with the target host visible before activation.
3. Given a base address whose scheme is not https, or which carries user information, when it is saved, then it is rejected with a stated reason.
4. Given a source type for which the vendor declares no address template, when a record of that type is displayed, then origin is shown without a link and nothing is guessed.
5. Given a source system created by hand rather than installed from the catalog, when a base address is configured, then origin is still shown, and a link is offered only where a vendor template can be resolved.
6. Given two connectors whose catalog names share a prefix, when instances of both are installed, then each instance resolves to exactly one connector shell, both for address templates and for the existing instance grouping.

### User Story 4 - Do not imply a single origin where there is none (Priority: P3)
A user opening a record that has been shaped by more than one system sees that, instead of a badge that names only the first.

**Why this priority**: The creating source is one honest answer but becomes a false one as soon as a second system contributes observations.
**Independent Test**: Record Facts from a second source system about an existing record and open its detail.

**Acceptance Scenarios**:
1. Given a record whose Facts reference more than one distinct source system, when its detail is opened, then all contributing source systems are disclosed and the creating source remains identified as such.
2. Given such a record, when it appears in a register, then the row continues to state the creating source only, without implying exclusivity.

### Edge Cases
A source record superseded by a newer version shows the version the record was produced from and states that a newer version exists. A source record whose payload exceeds the display bound is truncated with an explicit notice, never silently. An unmapped source record has no produced records; the inspection says so. Base addresses with and without a trailing separator resolve identically. An external reference containing path separators or whitespace is encoded before composition. A record from the `demo_data` connector states that origin plainly. Cross-tenant source systems, source records and base addresses behave as not found.

## Requirements

- **FR-001**: Operational registers, detail views and cards MUST state record origin through one shared read contract that carries source system code and name, source type, external reference, source version and received time. A second origin shape MUST NOT be introduced; the existing Facts origin shape is the basis.
- **FR-002**: A record without a source MUST state that it was created in the application, naming the deciding user where the change proposal records one. An empty origin MUST NOT be rendered.
- **FR-003**: Origin MUST be available as a register column governed by the existing table preferences, shown by default for registers whose records are predominantly imported and hidden by default for derived registers.
- **FR-004**: Activating an origin statement MUST open a bounded in-place inspection of the source record showing identity, version, received time, import state, the retained payload, the terminal interpretation outcome where one exists, and the records produced from that source record, each reachable by its own identity. The existing full Inspector MUST remain reachable and unchanged.
- **FR-005**: The retained payload MUST be presented read-only and bounded, with an explicit notice when truncated. Payload presentation MUST NOT alter, normalize or re-derive any received value.
- **FR-006**: `SourceSystem` MUST accept an optional external base address. It MUST be settable and clearable through the existing source configuration surface, MUST be validated as an absolute `https` address without user information, and MUST be bounded in length.
- **FR-007**: `SourceSystem` MUST record the connector shell it was installed from, and that record MUST become the only basis for associating an instance with a connector, replacing the description-prefix inference. Existing instances MUST be resolved once, by unambiguous rules only, and MUST remain unassociated where the existing rules are ambiguous. The value MUST be optional for hand-created systems, and installation behavior MUST be otherwise unchanged.
- **FR-008**: The connector catalog MUST be able to declare, per connector, a relative address template per source type. Template inputs MUST be restricted to the source record's own identity (`source_type`, `external_id`); payload fields MUST NOT be used, and unresolved templates MUST yield no link rather than a guessed one.
- **FR-009**: A resolved external link MUST open in a separate browsing context with no opener relationship, MUST expose its target host before activation, and MUST be composed with the external reference encoded.
- **FR-010**: Where a base address is absent, a template is missing, or a source system no longer exists under its retained textual code, origin MUST still be stated and the link MUST be omitted. The detail view MUST offer the path to configure the address.
- **FR-011**: A record whose Facts reference more than one distinct source system MUST disclose the contributing systems in its detail view while continuing to identify the creating source. Register rows MUST state the creating source only.
- **FR-012**: Origin for a register page MUST be resolved in bounded lookups for the displayed page, without a per-row query, and list reads MUST NOT join import jobs or interpretation outcomes. The resolution MUST join the retained textual source system code within the tenant.
- **FR-013**: All origin, payload, outcome and configuration reads and writes MUST be tenant-scoped, MUST go through shared application services, and MUST behave as not found across tenants.
- **FR-014**: All new labels MUST be localized in English, German, Dutch and Spanish. German MUST use the established vocabulary: Quellsystem, Originalquelle, Herkunft.
- **FR-015**: The master-data detail branch that cannot render MUST be removed rather than extended. Its section is hidden exactly when a record is selected, while its content renders only then, so every action it declares is unreachable; each of those actions is already offered by the row preview. Removal MUST keep the guidance branch and the section's conditional visibility, MUST NOT change any reachable behavior, and MUST be proven by an assertion that counts the affected controls in the document rather than in the accessibility tree, where a hidden duplicate is invisible.

## Success Criteria

- **SC-001**: Every operational register and detail family that can carry a source states an origin for each displayed record, with no blank origin in any of the four languages.
- **SC-002**: One activation from a register row reveals the source identity, payload, outcome and produced records without navigating away.
- **SC-003**: After configuring one base address, every record of a supported source type from that system offers a working external link, and no record from an unconfigured system offers one.
- **SC-004**: Adding origin to a register page issues a bounded, constant number of additional statements per page, independent of the number of rows.
- **SC-005**: No stored business value, source payload, interpretation outcome or received amount changes as a result of this feature.
- **SC-006**: Every configured source system is associated with at most one connector shell, and no instance is listed under a connector it was not installed from.
- **SC-007**: Each master-data action is present exactly once in the document when a record is open.

## Assumptions and Dependencies

`source_record_id` is already present on the operational tables and is not extended here. `SourceRecord.source_system` remains the immutable textual snapshot; the join to configured systems is by tenant-scoped code, and a missing match is a supported state, not an error. Placing the base address on `SourceSystem` is the user's explicit decision: one configured instance has exactly one external address, and per-capability addressing is rejected as unproven. Recording the connector shell on `SourceSystem` is new schema and is justified by FR-007: the existing `connector_shells` read reconstructs the vendor by testing whether an instance description starts with a connector's display name, which associates one instance with several connectors whenever two catalog names share a prefix. The catalog contains such a pair today, so this is a present defect the feature resolves rather than a risk it introduces. Base addresses are configuration and carry no credentials, which keeps the registry descriptive as `docs/features/source_ingestion.md` requires; the specification updates that document rather than forking its rules. Exposing the retained payload in the Inspector follows existing explain reads that already return `source_payload`.

## Requirement Traceability

| Requirement | Acceptance | Test | Implementation |
|---|---|---|---|
| FR-001 | US1 1, 3 | T004, T012 | T005, T013 |
| FR-002 | US1 2 | T004 | T005 |
| FR-003 | US1 4 | T012 | T013 |
| FR-004 | US2 1, 3, 4, 5 | T006 | T007 |
| FR-005 | US2 2 | T006 | T007 |
| FR-006 | US3 1, 3 | T008 | T009, T010 |
| FR-007 | US3 5, 6 | T008 | T009 |
| FR-008 | US3 2, 4 | T008 | T010 |
| FR-009 | US3 2 | T012 | T013 |
| FR-010 | US3 1, 4; US1 5 | T008, T012 | T010, T013 |
| FR-011 | US4 1, 2 | T014 | T015 |
| FR-012 | SC-004 | T004 | T005 |
| FR-013 | Edge cases | T004, T008 | T005, T010 |
| FR-014 | All user stories | T011 | T013 |
| FR-015 | US1 3 | T018 | T018 |
