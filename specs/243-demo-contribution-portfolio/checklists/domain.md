# Domain Requirements Checklist: Demo Contribution Portfolio

**Purpose**: Validate financial-authority, traceability, and demo-boundary requirement quality before implementation
**Created**: 2026-09-20
**Feature**: [spec.md](../spec.md)

**Ownership**: These items review the written requirements. `[x]` means a reviewer approves the requirement quality; it does not mean the implementation is complete.

## Requirement Completeness

- [x] CHK001 Are the minimum portfolio size and required outcome classes explicitly specified? [Completeness, Spec §FR-001-FR-002]
- [x] CHK002 Are required selling-cost composition differences and direct/allocated coverage explicitly specified? [Completeness, Spec §FR-003]
- [x] CHK003 Are the boundaries for empty companies, existing demo companies, execution fixtures, and continuous Demo Data documented? [Coverage, Spec §Non-Goals, §FR-011]

## Financial Authority and Traceability

- [x] CHK004 Do the requirements distinguish received revenue, acquisition cost, and selling costs from derived DB1/DB2 observations? [Consistency, Spec §FR-004, §DR-002-DR-003]
- [x] CHK005 Is the complete SourceRecord → evidence → movement/ledger/review path specified for every portfolio outcome? [Traceability, Spec §DR-001]
- [x] CHK006 Are explicit reviewed-zero requirements defined so missing selling costs cannot be interpreted as zero? [Clarity, Spec §FR-004, Edge Cases]
- [x] CHK007 Are opaque identity, stable discovery labels, and shortest-link requirements mutually consistent? [Consistency, Spec §FR-008, §DR-004]

## Scenario and Recovery Coverage

- [x] CHK008 Are positive, low-positive, negative, zero-selling-cost, and incomplete contribution scenarios objectively distinguishable? [Measurability, Spec §US1-US3]
- [x] CHK009 Are retry, replay, and partial-initialization requirements sufficient to prevent duplicate authority records? [Recovery, Spec §FR-009, Edge Cases]
- [x] CHK010 Are signed return and late-knowledge requirements separated from ordinary complete outcomes? [Clarity, Spec §FR-007]
- [x] CHK011 Are multi-currency non-aggregation and tenant-isolation boundaries explicitly addressed? [Edge Cases, Spec §Edge Cases, §FR-010]

## Acceptance and Evidence

- [x] CHK012 Can every complete outcome be reconciled exactly from source-backed inputs to DB1 and DB2? [Acceptance Criteria, Spec §SC-003]
- [x] CHK013 Does every FR and DR map to a scenario and planned executable proof? [Traceability, Spec §Requirement Traceability]
- [x] CHK014 Are the business documentation expectations specific enough to explain purpose, arithmetic, gaps, and continuous-data boundaries? [Clarity, Spec §FR-012]

## Notes

- Reviewer records approval by checking each item before implementation begins.
- `$speckit-implement` reads this checklist state but does not modify it.
- Product/domain review approved by the owner on 2026-09-20.
