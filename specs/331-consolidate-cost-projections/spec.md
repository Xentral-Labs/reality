# Feature Specification: Consolidate cost projections

**Created**: 2026-10-02
**Status**: Approved scope
**Language**: English
**Input**: Reduce schema growth by reusing the original Reality model, starting with repeated cost generation, result and publication structures.

## Context and Intent

### Problem

Cost reporting has acquired separate persistence structures for inventory, contribution,
captured selections and company-wide observations. These structures repeat the lifecycle
of building a result, checking completeness and publishing a coherent generation. The
business needs those guarantees, but does not need a separate storage lifecycle for each
report. Reducing tables must preserve evidence and confirmed financial decisions.

### Scope

Consolidate the four existing cost-output families into a shared projection lifecycle.
Preserve all existing business outcomes, exact historical selection, explainability,
unknown-value semantics and interfaces. Migrate existing persisted outputs and references
without changing their meaning. Retire the superseded output tables after verified parity.
The technical plan must compare reuse of existing projections with a narrow extension;
it must not introduce a general business-object registry merely to reduce table count.

### Non-Goals

No configuration/settings redesign, return-announcement migration, dunning redesign,
generic allocation model, changes to Facts, new valuation algorithms, new financial
admission, new public reports, source rewriting or deletion of confirmed input history.
No expansion of existing company-scale or captured-report eligibility and size limits.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Receipt costing](../../docs/features/receipt-costing.md), including fixed captured caches

## User Scenarios & Testing

### User Story 1 - Keep exact financial answers (Priority: P1)

An operator opens a previously selected inventory or contribution result and obtains
the same values, missing-evidence assessment and trace to its confirmed inputs.

**Independent Test**: Compare old and consolidated readers for fixed historical selections,
including acquisition value, carrying value, DB1, DB2 and unknown portions.

**Acceptance Scenarios**:

1. **Given** a selected historical generation, **When** later evidence arrives,
   **Then** its historical result and input references remain unchanged, while its
   current freshness assessment follows the existing contract.
2. **Given** incomplete cost evidence, **When** a result is read,
   **Then** unknown amounts remain unknown and supported subtotals do not become final totals.
3. **Given** a result with confirmed ownership and valuation inputs, **When** it is inspected,
   **Then** the same opaque evidence and decision identities remain reachable.

### User Story 2 - Publish complete results reliably (Priority: P1)

An operator sees a coherent result even when builders retry, fail or run concurrently.

**Independent Test**: Exercise competing builders, interrupted builds and publication retries
for each of the four existing output families.

**Acceptance Scenarios**:

1. **Given** an interrupted build, **When** a report is read,
   **Then** no partial generation is exposed as complete or current.
2. **Given** concurrent or repeated builds for the same input and algorithm,
   **When** they complete, **Then** retry behavior and generation uniqueness retain existing semantics.
3. **Given** incompatible, obsolete or different equal-cursor candidates,
   **When** publication is attempted, **Then** existing publication refusal semantics are preserved.
4. **Given** a confirmed joint inventory or contribution review,
   **When** its result is exposed, **Then** membership is complete and cannot mix unrelated generations.

### User Story 3 - Simplify storage without losing access (Priority: P2)

A maintainer uses one shared output lifecycle while operators and saved analyses keep
access to existing exact results.

**Independent Test**: Migrate populated representative data, compare results and identities,
and verify the final schema inventory and existing reporting entrypoints.

**Acceptance Scenarios**:

1. **Given** populated legacy output tables, **When** migration completes,
   **Then** existing selection identities and published references still resolve without evidence loss.
2. **Given** a saved analysis selecting a historical generation, **When** it is reopened,
   **Then** it resolves the same basis and produces the same supported values.
3. **Given** the consolidated implementation, **When** inventory is inspected,
   **Then** the superseded output tables are absent and no runtime path depends on them.
4. **Given** a generation from another tenant, **When** it is requested or linked,
   **Then** it remains inaccessible and cannot be associated with local records.

### Edge Cases

- Empty populations, zero quantities, unknown costs and mixed currencies or units retain their current meaning.
- Inventory and contribution generations have different grains; consolidation must preserve both.
- A captured diagnostic is not a company financial report; consolidation cannot promote its authority.
- Hash mismatch, corrupted cached membership or an unsealed generation cannot be presented as valid.
- A company result may refer to inventory and contribution generations; those links must survive migration.
- Discarding an eligible unpublished cache must not remove retained inputs or protected published results.
- Existing saved identifiers, pagination bindings and algorithm versions must remain resolvable.

## Requirements

### Functional Requirements

- **FR-001**: All four cost-output families MUST share one generation/completeness/publication lifecycle while retaining their distinct result grains and eligibility rules.
- **FR-002**: Historical selection MUST reproduce the same supported values, unknown states and input identities as before consolidation.
- **FR-003**: Current freshness and publication eligibility MUST preserve existing cursor, input and algorithm checks.
- **FR-004**: Failed, incomplete, competing and retried builds MUST preserve existing atomicity, uniqueness and refusal semantics.
- **FR-005**: All existing shared-service and reporting interfaces MUST preserve result shapes, errors, confirmation and selection behavior.
- **FR-006**: Migration MUST preserve existing opaque generation identities, references and published selections, including saved analyses; parity failure MUST prevent destructive retirement.
- **FR-007**: Eligible cache disposal MUST preserve retained evidence, decisions, selection membership and protected published results.
- **FR-008**: Final persistence MUST retire the thirteen identified output tables and reduce the total table count by at least eight; the plan MUST justify any shared replacement structures.

### Domain and Traceability Requirements

- **DR-001**: SourceRecords, Documents, Reality records and confirmed input/review history MUST remain authoritative and unchanged by consolidation.
- **DR-002**: Stored calculated outputs MUST remain disposable observations and MUST NOT become Facts or financial authority.
- **DR-003**: Every read, write, link, publication and migration mapping MUST preserve tenant isolation.
- **DR-004**: Important results MUST retain their shortest true links to exact confirmed inputs and original evidence.
- **DR-005**: Normal reads MUST remain read-only and MUST NOT rebuild, enqueue or alter results as a side effect.

### Key Entities

- **Generation**: An exact, versioned observation of an identified input basis, with completion and integrity proof.
- **Result member**: A value or unknown-state observation at its existing inventory, contribution or captured-member grain.
- **Publication**: Selection of an eligible complete generation for one existing scope.
- **Retained basis**: Existing immutable inputs and decisions from which outputs can be reproduced; separate from disposable results.

## Success Criteria

- **SC-001**: Every representative historical and current parity scenario returns identical supported values, unknown states and evidence identities.
- **SC-002**: All four output families pass retry, interruption, concurrent publication and cross-tenant acceptance checks.
- **SC-003**: All existing selection identifiers in the migration fixture remain resolvable, including saved analyses and published selections.
- **SC-004**: The final table inventory contains at least eight fewer tables and none of the thirteen superseded output tables.
- **SC-005**: Every existing required cost-reporting and migration check passes; no captured diagnostic gains financial authority.

## Assumptions and Dependencies

The user accepted starting the simplification work. The owner approved this concrete first slice on 2026-10-02 before technical planning. Later settings and domain redesigns
remain separate slices. The minimum reduction of eight is an approved scope target; it does not authorize weakening financial guarantees.
Existing requirements and regression tests are the behavioral baseline. Legacy stored
outputs must be supported even if a local development database is empty. Existing
unrelated working-tree changes belong to other work and must remain untouched.

## Requirement Traceability

| Requirement | Acceptance coverage | Planned verification |
|---|---|---|
| FR-001 | US2.1–4, US3.3 | Shared lifecycle contract for all four families |
| FR-002, DR-001, DR-002, DR-004 | US1.1–3 | Exact historical/value/evidence parity and authority checks |
| FR-003 | US1.1, US2.3 | Freshness, algorithm and publication refusal regression checks |
| FR-004 | US2.1–4 | Transaction failure, concurrent build and retry service checks |
| FR-005 | US1, US3.2 | Shared-service, analytics and adapter regression suites |
| FR-006 | US3.1–2 | Populated migration parity, legacy identity and saved-analysis checks |
| FR-007 | Cache disposal edge case | Disposal and protected-reference regression checks |
| FR-008 | US3.3 | Migration/model inventory and absence of legacy runtime dependencies |
| DR-003 | US3.4 | Cross-tenant read/write/link and migration isolation checks |
| DR-005 | US1, US3.2 | Read-only/no-enqueue regression checks |
