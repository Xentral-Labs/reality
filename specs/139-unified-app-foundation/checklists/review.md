# Requirements Review: Unified App Foundation

**Purpose**: Standard-depth reviewer checklist focused on action authority/recovery and coherent context/UX.
**Created**: 2026-09-07
**Feature**: [spec.md](../spec.md)
**Ownership**: Reviewer-owned requirements-quality artifact. New items remain unchecked. A checked item means its requirements were reviewed; it never means implementation or runtime verification passed.

## Scope and continuity

- [ ] CHK001 Is the first-increment ordinary-company scope clearly separated from later Analytics, master-data and practice migration? [Completeness, Spec Scope/Non-Goals]
- [ ] CHK002 Are new/legacy route continuity and unchanged practice admission specified without implying full legacy feature parity? [Consistency, FR-001 FR-003 FR-023; Plan Shell]
- [ ] CHK003 Is company selection distinguished from authorization, including delayed responses and saved-context boundaries? [Clarity, FR-002 DR-003]

## Action authority and recovery

- [ ] CHK004 Are exact intent, changed-review invalidation and separate dependent-action approval requirements unambiguous across all three entries? [Clarity, FR-009 FR-011 FR-012]
- [ ] CHK005 Are current review checks consistent with the existing capped reservation semantics? [Consistency, FR-014; Research R4-R5]
- [ ] CHK006 Are same-proposal duplication and different-proposal stock competition separately covered? [Coverage, FR-014 DR-006; Plan Concurrency]
- [ ] CHK007 Are shared-writer lock coverage, acquisition order and connection-loss behavior specified? [Completeness, DR-003 DR-006; Research R5]
- [ ] CHK008 Are executed history, mutable current observations and unresolved/no-evidence states distinguished? [Clarity, FR-015 FR-020; Data model Lifecycle]
- [ ] CHK009 Are old pending proposal review, all-adapter token enforcement and rollback constraints mutually consistent? [Consistency, FR-023; Contracts Proposal; Plan Rollback]

## Read and presentation quality

- [ ] CHK010 Are revision/correction-aware quantities and scoped pagination defined before the new UI consumes them? [Coverage, FR-006 DR-002; Research R3]
- [ ] CHK011 Do quantity/evidence/history requirements expose completeness and shortest true links without inventing source facts? [Consistency, FR-005 FR-008 DR-001 DR-004 DR-005]
- [ ] CHK012 Are global/case Chat contexts, legacy messages and failed-provider behavior clearly specified? [Completeness, FR-017 FR-018; Contracts Chat]
- [ ] CHK013 Are keyboard, viewport, language/theme and visual-reference acceptance criteria measurable? [Measurability, FR-021 FR-022 SC-006]
- [ ] CHK014 Does every FR/DR have both failing-proof and implementation coverage, and do final gates cover every SC? [Traceability, Tasks Requirement Coverage]

## Review status

Specification scope was approved by the owner on 2026-09-07. This newly generated checklist is provided for architecture/requirements review; no reviewer answers are fabricated. The implement workflow reads checklist state and must not silently mark these items complete.
