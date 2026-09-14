# UX and Mutation Safety Checklist: Workspace Views and Actions

**Purpose**: Validate UX, catalog, safety, and traceability requirement quality before implementation
**Created**: 2026-09-03
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer approves the requirement quality; it does not mean implementation is complete.

## Requirement Completeness

- [ ] CHK001 Are all five workspace identities and the complete distinction between persistent navigation, Views, and Actions specified? [Completeness, Spec §FR-001-FR-004]
- [ ] CHK002 Are the required metadata and validation rules defined for both authoritative-register and materialized-Projection Views? [Completeness, Spec §FR-002, FR-018]
- [ ] CHK003 Are the core Warehouse Action families and their shared-service boundary exhaustively bounded? [Completeness, Spec §Scope, FR-012]
- [ ] CHK004 Are action availability, empty-company guidance, and missing-prerequisite requirements documented without making workspaces disappear? [Coverage, Spec §FR-007, Edge Cases]

## Requirement Clarity and Consistency

- [ ] CHK005 Is `View` unambiguously defined as the user-facing term for both authoritative registers and rebuildable read models? [Clarity, Spec §Scope, FR-005]
- [ ] CHK006 Are canonical labels and technical Projection/Command names kept consistently separate across requirements? [Consistency, Spec §FR-005]
- [ ] CHK007 Is the difference between workspace discovery and contextual record-page actions clear enough to prevent duplicate business behavior? [Clarity, Spec §Scope]
- [ ] CHK008 Are multi-workspace membership and deterministic ordering requirements compatible and duplicate-free? [Consistency, Spec §FR-006, FR-018]

## Mutation and Security Requirements

- [ ] CHK009 Does the specification require explicit confirmation for every workspace mutation and exact server preview/revision confirmation for snapshot-sensitive actions? [Coverage, Spec §FR-010]
- [ ] CHK010 Are authoritative revalidation, stale refusal, atomic failure, and no-partial-write requirements specified for confirmation races? [Coverage, Spec §US2, FR-014, DR-004]
- [ ] CHK011 Are tenant isolation and non-disclosure requirements defined for selectors, previews, mutations, results, and classification metadata? [Security, Spec §FR-011, FR-015, DR-003]
- [ ] CHK012 Is generic command execution explicitly excluded while every displayed Action is required to resolve to an explicit Web-capable shared command? [Boundary, Spec §Non-Goals, FR-009]

## Traceability and Domain Requirements

- [ ] CHK013 Are Source → Evidence → Reality expectations stated for each applicable Warehouse mutation without manufacturing Evidence? [Domain, Spec §DR-001]
- [ ] CHK014 Are shortest links, opaque identity, append-only Movement correction, and absence of Document operational state consistently protected? [Domain, Spec §DR-002, DR-006]
- [ ] CHK015 Are success-result, affected-View refresh, and Inspector/explanation requirements complete for actions with and without Source evidence? [Traceability, Spec §FR-013]
- [ ] CHK016 Are browser responsibilities restricted to presentation and orchestration while eligibility and business invariants remain server-owned? [Consistency, Spec §DR-005]

## Scenario and Non-Functional Coverage

- [ ] CHK017 Are primary, empty, alternate-workspace, error, stale, cross-tenant, and recovery scenarios represented by acceptance criteria or edge cases? [Coverage, Spec §User Scenarios, Edge Cases]
- [ ] CHK018 Are bounded-selector and large-tenant requirements sufficient to prevent an unbounded business-register preload? [Scalability, Spec §FR-011]
- [ ] CHK019 Are desktop, mobile, keyboard, expanded, disabled, dialog, and localization requirements defined for every new interaction class? [Accessibility, Spec §FR-016-FR-017]
- [ ] CHK020 Are success criteria measurable for discovery time, catalog drift, mutation safety, traceability, and required repository gates? [Measurability, Spec §SC-001-SC-008]

## Notes

- `$speckit-implement` reads this review state but does not modify these markers.

## Review

- **Specification reviewer**: Pending
- **Domain/architecture reviewer**: Pending
- **Decision**: Draft
