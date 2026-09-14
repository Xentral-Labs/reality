# Domain and Security Requirements Checklist: Reality Gap Workflow

**Purpose**: Reviewer gate for self-service interpretation requirements
**Created**: 2026-09-04
**Feature**: [spec.md](../spec.md)

**Ownership**: `[x]` means a reviewer approves the requirements quality; it does not mean implementation is complete.

## Completeness

- [x] CHK001 Are capture, investigation, classification, preparation, simulation, activation, replay, disablement, and developer-handoff requirements all defined? [Completeness, Spec §User Stories]
- [x] CHK002 Are role requirements complete for members, owners, Chat, MCP, and Web? [Completeness, Spec §FR-001, §FR-005, §FR-010, §FR-021]
- [x] CHK003 Are the allowed declarative rule fields and prohibited executable capabilities bounded without relying on implementation judgment? [Clarity, Spec §FR-021–FR-022]
- [x] CHK004 Are historical replay scope, retry, partial failure, and outcome requirements defined? [Coverage, Spec §FR-023–FR-026]

## Domain Consistency

- [x] CHK005 Is RealityGap consistently separate from Source, Evidence, Reality, Fact, ChangeProposal, BusinessEvent, and OperationalException? [Consistency, Spec §DR-001]
- [x] CHK006 Are Fact implementation requirements consistent with the existing source, subject, predicate, immutability, and idempotency contract? [Consistency, Spec §DR-005]
- [x] CHK007 Is the boundary between self-service Fact mappings and developer-governed model changes explicit in every implementation path? [Clarity, Spec §FR-027, §DR-006]
- [x] CHK008 Are shortest-link and no-Document-operational-state requirements explicit for every successful outcome? [Coverage, Spec §DR-007]

## Security and Failure Coverage

- [x] CHK009 Are tenant isolation requirements specified for gaps, entries, evidence, rules, simulations, outcomes, and Facts? [Coverage, Spec §FR-003–FR-005, §DR-003]
- [x] CHK010 Are stale decisions, ambiguous subjects, invalid values, superseded sources, and concurrent execution addressed? [Edge Cases, Spec §Edge Cases]
- [x] CHK011 Are source privacy, bounded examples, and provider-access limitations defined across all surfaces? [Security, Spec §FR-004, §FR-019]
- [x] CHK012 Are activation and replay confirmation requirements consistent with the existing mutation boundary? [Consistency, Spec §FR-012, §DR-010]
- [x] CHK013 Are disable and rollback semantics explicit without implying deletion or rewriting of immutable Facts? [Recovery, Spec §FR-024]

## Acceptance Quality

- [x] CHK014 Can parity across Chat, MCP, and Web be objectively verified from the requirements? [Measurability, Spec §FR-005, §SC-002]
- [x] CHK015 Are simulation counts and representative failures sufficiently defined to judge approval readiness? [Clarity, Spec §FR-023]
- [x] CHK016 Are performance and bounded-result expectations measurable for both normal queues and large tenants? [Measurability, Spec §FR-015, §SC-007]
- [x] CHK017 Are condition operators, operand types, conjunction mode, output modes, and evaluation bounds closed and objectively testable? [Clarity, Spec §FR-040–FR-042, §FR-052]
- [x] CHK018 Are Commitment and DocumentLine resolution, line iteration, and per-element provenance consistent with shortest true links and opaque identity? [Consistency, Spec §FR-043–FR-044, §DR-012]
- [x] CHK019 Are explicit negative Facts, normal non-applicability, invalid input, ambiguity, and conflicts semantically distinct? [Consistency, Spec §FR-042, §FR-046, §DR-013]
- [x] CHK020 Are observation time, correction/version behavior, replay continuation, retry, and cumulative progress completely specified? [Recovery, Spec §FR-045, §FR-047, §SC-010]
- [x] CHK021 Do rule summaries expose enough bounded operational evidence to support an activated ERP rule without raw database inspection? [Observability, Spec §FR-048]
- [x] CHK022 Are conditional configuration and lifecycle controls required to remain equivalent across service, Chat, MCP, HTTP, and Web? [Parity, Spec §FR-050–FR-051]

## Notes

- Reviewers record requirement-quality approval before implementation begins.
- The owner approved the expanded ERP-ready rule boundary on 2026-09-04 before implementation.
