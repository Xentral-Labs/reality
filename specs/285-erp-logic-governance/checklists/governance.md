# ERP Governance Requirements Checklist: Governed ERP Logic Ownership

**Purpose**: Validate that the ownership, boundary and semantic-parity requirements are complete and unambiguous before implementation
**Created**: 2026-09-27
**Feature**: [spec.md](../spec.md)

**Ownership**: This is a reviewer-owned requirements-quality checklist. `[x]` means a reviewer has
accepted the requirement quality; it does not mean implementation is complete. Implementation does
not change these markers.

## Ownership and Trace Completeness

- [ ] CHK001 Is the governed population defined without ambiguity for commands, public reads, aliases, helpers and exclusions? [Completeness, Spec §FR-001–FR-003, §FR-016]
- [ ] CHK002 Does each required trace relationship distinguish primary ownership from supporting-service reuse and multi-group discovery membership? [Clarity, Spec §Edge Cases, Plan §Governance trace]
- [ ] CHK003 Are the minimum executable-evidence requirements explicit for both mutations and reads that have no business command? [Completeness, Spec §FR-002, §FR-014]
- [ ] CHK004 Are missing, duplicate, stale and conflicting ownership outcomes all specified as fail-closed conditions with actionable diagnostics? [Coverage, Spec §FR-003, §FR-008, §FR-015]
- [ ] CHK005 Is the boundary between generated governance metadata and business authority stated consistently across spec, plan, data model and contract? [Consistency, Spec §DR-001, Plan §Data and migration impact]

## Adapter and Layer Boundaries

- [ ] CHK006 Are all governed adapter and automated-runtime categories explicitly covered, including Web, API, CLI, Chat, MCP, workers, scheduler, integrations and demo paths? [Coverage, Spec §FR-004–FR-005, §DR-007]
- [ ] CHK007 Are permitted transport validation, authorization, tenant selection, formatting and presentation behavior clearly distinguished from prohibited business decisions and writes? [Clarity, Spec §FR-006]
- [ ] CHK008 Are requirements for boundary exceptions narrow enough to exclude whole-module exemptions and complete enough to detect stale exceptions? [Clarity, Spec §FR-007, Contract §Architecture exception contract]
- [ ] CHK009 Is the dependency direction consistent with the existing services that currently call tool-layer code, with those cases requiring explicit resolution or bounded classification? [Consistency, Plan §Repository Structure and Layer Changes]
- [ ] CHK010 Are tenant isolation, authorization, confirmation and idempotency preservation requirements stated for every affected entrypoint class? [Completeness, Spec §FR-017, §DR-004]

## Critical Calculation Semantics

- [ ] CHK011 Is each inventory semantic grain defined precisely enough to prevent dimensional positions and operational item/location stock from being treated as interchangeable? [Clarity, Spec §FR-011–FR-013, Plan §Four critical calculation owners and parity]
- [ ] CHK012 Are fulfilment rules complete for revisions, qualifying movements, corrections, cancellation, over-fulfilment clamping, holds, reservations and returns? [Coverage, Spec §US3, Plan §Review Risks]
- [ ] CHK013 Are invoice open amount, unused credit, party/currency net balance and account balance explicitly separated, including cutoff and multi-currency behavior? [Clarity, Spec §US3, Research §R7]
- [ ] CHK014 Are contribution candidate, reviewed, stale and unknown states defined consistently without allowing shared arithmetic to create shared authority? [Consistency, Spec §DR-003, Research §R8]
- [ ] CHK015 Is the required response to a discovered semantic disagreement unambiguous, including who must approve any later resolution? [Exception Flow, Spec §FR-013, §Assumptions and Dependencies]

## Compatibility and Completion

- [ ] CHK016 Is public compatibility defined across names, ordering, schemas, descriptions, access classes, confirmation, events, outputs and facade imports? [Completeness, Spec §FR-009, Contract §Compatibility contract]
- [ ] CHK017 Are success criteria measurable for complete capability coverage, registered-consumer parity, exception decay and reviewer lookup time? [Measurability, Spec §SC-001–SC-006]
- [ ] CHK018 Are rollback and partial-delivery requirements explicit for trace validation, semantic consolidation and registry modularization? [Recovery, Plan §Rollout and Rollback]
- [ ] CHK019 Does requirement traceability cover every FR, DR and buildable success criterion with a named initial failing proof? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy and Traceability]
- [ ] CHK020 Are the initial four semantic audit families and the structural-only treatment of other ERP capabilities consistently bounded in every artifact? [Scope, Spec §Clarifications, Plan §Technical Context]

## Review

- **Specification reviewer**: Owner scope approval recorded 2026-09-27
- **Domain/architecture reviewer**: Pending
- **Decision**: Draft — all items intentionally remain unchecked for reviewer assessment

## Notes

- Review requirement quality only; implementation verification belongs to `tasks.md` and the final
  `review.md` evidence record.
- `$speckit-implement` reads checklist state but does not modify reviewer-owned markers.
