# Feature Specification: Consolidate Receipt Manifest Membership

**Feature Branch**: Existing shared workspace; no branch switch.
**Created**: 2026-10-02
**Status**: Implemented, verified and reviewed; repository acceptance complete
**Language**: English
**Input**: The owner selected the bounded five-to-one receipt-manifest membership proposal by replying "ok weiter" after the costing audit and the proposed specification step.

## Context and Intent

### Problem

Receipt-cost reviews retain the exact inputs considered at confirmation. Five separate member stores represent the same relationship: an identified input belongs to one retained manifest. The owner wants less physical storage fragmentation while preserving every historical selection, received value and established interface.

### Scope

Consolidate exactly `cost_manifest_receipt`, `cost_manifest_component`, `cost_manifest_attribution`, `cost_manifest_correction` and `cost_manifest_replacement` into one physical typed membership store. Retain all five original logical resources, their column contracts and existing read/write behavior. The manifest header and selected evidence/decision identities remain unchanged. Net reduction is four physical tables.

### Non-Goals

No census, captured-review, company-input, basis, decision or projection consolidation; generic Settings or business-object registry; new financial authority; new lifecycle restrictions; rewritten historical digests; UI or command changes; live migration, deployment, commits or unrelated concurrent changes.

### Existing Contracts

- [Remaining costing assessment](../../docs/ideas/cost-storage-consolidation.md) and [physical metadata inventory](../../docs/ideas/cost-storage-inventory.json).
- [Receipt costing](../../docs/features/receipt-costing.md), [data model](../../docs/DATA_MODEL.md) and [architecture](../../docs/ARCHITECTURE.md).
- [Constitution](../../.specify/memory/constitution.md) and [Spec Kit workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- [Spec 316 compatibility contract](../331-consolidate-cost-projections/contracts/compatibility.md): existing shared-storage boundaries and view infrastructure, without extending its output lifecycle to these memberships.

## User Scenarios & Testing

### User Story 1 - Preserve historical receipt reviews (Priority: P1)

A business owner reads an earlier receipt-cost review after new decisions or corrections have arrived and sees the original selected inputs and supported result.

**Why this priority**: Simplifying storage must not silently change a confirmed historical review.

**Independent Test**: Record all five member families, retain a review, introduce later knowledge and compare the original manifest membership, digest, trace and receipt result before and after consolidation.

**Acceptance Scenarios**:

1. **Given** a review with all five families, **When** reading it after consolidation, **Then** its manifest ID, member IDs, selected input IDs, digest and historical result are exact.
2. **Given** later attributions, corrections or replacements, **When** rereading the old review, **Then** the old selected input set and historical result remain unchanged.
3. **Given** an empty family or missing cost support, **When** reading the retained review, **Then** absence and unknown values retain their original meaning rather than becoming zero or fabricated evidence.
4. **Given** inconsistent manifest membership and digest, **When** reading the review, **Then** the existing corrupt-manifest refusal remains effective.

### User Story 2 - Keep familiar member interfaces and tenant isolation (Priority: P1)

Existing receipt-cost services and inspectors continue writing and reading the same five kinds of manifest members, without exposing another tenant's values or confusing different kinds of selected input.

**Why this priority**: Storage reuse is useful only if familiar operations and integrity remain exact.

**Independent Test**: Exercise existing service and record-inspection paths plus original direct persistence operations for every family, including duplicate and wrong-tenant refusal.

**Acceptance Scenarios**:

1. **Given** a valid member of each family, **When** using existing reads, writes and returned identities, **Then** each original logical resource retains its columns and behavior, including member detail, ordering and paging.
2. **Given** equal member IDs in different families or tenants, **When** inserting and reading them, **Then** each remains independently identifiable without renaming an ID.
3. **Given** a target or manifest in another tenant, or a missing target, **When** linking a member, **Then** the link is rejected without changing valid rows.
4. **Given** an existing tenant/manifest/selected-input tuple, **When** inserting a duplicate in that family, **Then** the original uniqueness refusal remains effective; the same input may still belong to another manifest.
5. **Given** a write using the wrong logical family or multiple family targets, **When** applying it, **Then** storage rejects the inconsistent shape and does not move the row into another family.
6. **Given** a company with members in all five families, **When** counting or deleting that company's records, **Then** each physical member is visited once and another company's records remain unchanged.

### User Story 3 - Safely change and restore populated storage (Priority: P1)

An operator can prepare a reversible storage change and verify that it preserves the complete business record, before deciding separately whether to apply it to a live system.

**Why this priority**: A table reduction is unacceptable if rollback loses values or old schema contracts.

**Independent Test**: Upgrade a populated isolated database, perform supported membership operations, downgrade and re-upgrade; compare all exact values and original schema contracts.

**Acceptance Scenarios**:

1. **Given** a populated predecessor schema with cross-family and cross-tenant ID collisions, **When** upgrading, **Then** all original member columns and all unrelated business records are unchanged and five member stores become one.
2. **Given** supported changes made after upgrading, **When** restoring the predecessor schema, **Then** those current values and the original column, key, constraint and index contracts are restored exactly.
3. **Given** the restored schema, **When** upgrading again, **Then** values and logical interfaces remain exact.
4. **Given** an unsupported predecessor state or a failed parity verification, **When** attempting the change, **Then** it aborts without partially retiring storage or silently repairing values.

### Edge Cases

- Equal IDs across any of the five families and across tenants; distinct rows must not collide.
- No manifests, empty member families, multiple manifests selecting the same target and duplicate selection within one family.
- Wrong-tenant parent or target, nonexistent target, unknown family and inconsistent target shape.
- Historical hashes omit physical storage-routing details and retain the exact old input selections.
- Original supported direct updates/deletes are preserved; this refactor does not introduce census-style immutability rules.
- Interrupted migration, repeated metadata creation, partial metadata selection, tenant purge and downgrade after supported post-upgrade writes.

## Requirements

### Functional Requirements

- **FR-001**: Replace only the five physical member stores with one typed store, reducing physical application table count by exactly four while retaining five distinct logical resources.
- **FR-002**: Preserve every original member ID, tenant, manifest and selected-input identity, including equal IDs across families and tenants; do not translate identities.
- **FR-003**: Preserve each family's tenant/manifest/selected-input uniqueness and true tenant-qualified parent/target relationships. Missing and cross-tenant links MUST be rejected.
- **FR-004**: Preserve the original five logical column contracts and supported reads, inserts, updates, deletes and returned values. Reject wrong-family access or inconsistent target shapes at the persistence boundary.
- **FR-005**: Preserve existing receipt-cost service/tool behavior, confirmation, permissions, error codes, record-detail links, ordering and paging; use the same application services.
- **FR-006**: Preserve exact manifest membership, family-specific digest inputs, corrupt-manifest detection and historical receipt results after later knowledge is introduced.
- **FR-007**: Preserve missing support and empty-family semantics, all received amounts and all existing lifecycle behavior. Do not introduce new member immutability or parent-state admission rules as part of this change.
- **FR-008**: Populated upgrade, downgrade and re-upgrade MUST preserve exact values, including supported post-upgrade changes, and restore original member column/key/constraint/index contracts. Verification failure MUST abort transactionally without silent repair.
- **FR-009**: Preserve schema creation/drop, migration inspection, FK index coverage and tenant deletion/counting semantics, visiting shared physical rows once.
- **FR-010**: Leave all source, evidence, ledger, decision, review, census, captured-selection, company-input and existing projection authorities unchanged; no live migration or deployment is included in implementation acceptance.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality and the exact received values behind selected receipt inputs. Membership represents a retained selection, not a new source or financial authority.
- **DR-002**: Each member MUST retain its shortest true relationship to its manifest and original typed input. Facts, untyped identity strings or current-selection reconstruction MUST NOT replace these relationships.
- **DR-003**: All member queries and links MUST retain tenant scope; CLI, tools and Chat MUST keep existing service and confirmation boundaries.

### Key Entities

- **Receipt input manifest**: An identified retained set of inputs supporting a historical receipt-cost review, with an exact digest and knowledge boundary.
- **Manifest member**: An opaque, tenant-owned membership connecting that manifest to one receipt basis, component basis, attribution revision, correction basis or component replacement.
- **Selected input authority**: The existing received/admitted basis or retained decision, preserving its own identity, values and history.

## Success Criteria

- **SC-001**: The bounded change removes exactly four independently stored application tables while retaining all five logical membership resources.
- **SC-002**: Every member value and every unrelated business value in populated roundtrip acceptance fixtures is preserved exactly, including cross-family/tenant ID collisions and supported changes made after upgrade.
- **SC-003**: Every historical review acceptance scenario retains the same input selection, digest, received amounts and result after consolidation and later knowledge changes.
- **SC-004**: Every FR and DR has a mapped executable acceptance proof and all required repository gates pass before implementation is called complete.

## Assumptions and Dependencies

- The owner's latest continuation selects the four-table reduction described in the audit; broader costing consolidation remains outside scope.
- Current inspected metadata has no incoming physical FKs to these five members. Planning must confirm actual predecessor DDL and dependency inventory rather than treating metadata as a deployed database audit.
- The predecessor includes accepted specs 316/319/324. Migration numbering and parent revision must be rechecked against concurrent work before implementation.
- Existing typed inputs and manifest parent remain available. Current lifecycle and direct-write behavior must be measured before compatibility design is finalized.
- Existing schema-view infrastructure may be reused if it proves equivalent behavior; implementation details belong in the plan.
- Shared workspace state and another feature's `.specify/feature.json` are preserved. Downstream commands use `SPECIFY_FEATURE_DIRECTORY=specs/330-consolidate-manifest-members` explicitly.
- Live execution, merge and deployment require separate authorization; none is needed to prepare and verify this bounded change in isolation.

## Open Questions

None. Remaining storage/view/default/index mechanics are planning decisions under the preservation requirements above, not unresolved product scope.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
| --- | --- | --- |
| FR-001 | US3.1 | Physical/logical schema inventory and populated migration proof |
| FR-002 | US1.1, US2.2, US3.1 | Cross-family/tenant collision and exact row parity proofs |
| FR-003 | US2.3–4 | Database FK/uniqueness and tenant refusal proofs |
| FR-004 | US2.1, US2.5 | Per-family original persistence-operation and view-shape proofs |
| FR-005 | US2.1, US2.3 | Existing costing service/tool and cost-record inspection regressions |
| FR-006 | US1.1–2, US1.4 | Historical manifest, later knowledge and corruption regressions |
| FR-007 | US1.3, US2.1 | Empty/unknown, exact received-value and lifecycle compatibility proofs |
| FR-008 | US3.1–4 | Populated upgrade/downgrade/re-upgrade, exact DDL and abort proofs |
| FR-009 | US2.6, US3.1–3 | Metadata lifecycle, FK index, autogeneration and count/purge proofs |
| FR-010 | US3.1–3 | Unrelated authority snapshots and reviewed scope diff |
| DR-001 | US1.1–3, US3.1 | Exact authority snapshots and received-value provenance regressions |
| DR-002 | US1.1, US2.3–5 | Typed family FK inventory and wrong-link refusal proofs |
| DR-003 | US2.1, US2.3, US2.6 | Tenant, permissions, confirmation and shared-service regressions |

The plan and tasks will supply concrete new test names and requirement-to-task mapping before implementation begins. This specification marks requirements readiness only; no acceptance test or migration is represented as completed.
