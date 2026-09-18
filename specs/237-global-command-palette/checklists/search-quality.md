# Search Requirements Quality Checklist: Global Command Palette

**Purpose**: Reviewer-owned requirements-quality review before implementation.
**Created**: 2026-09-18
**Feature**: [spec.md](../spec.md)
**Focus**: Search completeness, safe launch/navigation, authorization and measurable responsiveness.
**Depth/audience**: Standard cross-feature review for the implementer and PR reviewer.

Ownership: Every item is intentionally unchecked. A reviewer marks `[x]` only when the written requirements satisfy the criterion, never to claim implementation completion. This generated checklist does not add a new product-approval requirement. The implementation skill reads these markers but must not mark them on the reviewer's behalf.

## Completeness

- [ ] CHK001 Are required record families, held search fields and unsupported payload search explicitly bounded? [Completeness, Spec §Coverage Matrix; FR-004; DR-005]
- [ ] CHK002 Are exact record destinations specified independently of current pagination and status defaults? [Completeness, FR-005; US2.1/4; UI contract §Exact target routes and readers]
- [ ] CHK003 Are capability, form, report, details and chat outcomes distinguished without promising unsupported execution? [Clarity, FR-003/017/018/020]
- [ ] CHK004 Are all five stories independently testable with explicit acceptance scenarios? [Completeness, Spec §User Scenarios & Testing]
- [ ] CHK005 Are query limits, empty/short inputs, result bounds and continuation semantics documented? [Completeness, FR-008/009; Search contract §Bounds and failure isolation]

## Domain Consistency

- [ ] CHK006 Are duplicate human references, source versions and multiple partner roles distinguished by actual identities? [Consistency, DR-004; US2.2/3]
- [ ] CHK007 Are Source → Evidence → Reality links preserved without new document operational states or stored derived authority? [Consistency, DR-001/002/005]
- [ ] CHK008 Are payment and shipment identities consistent with their underlying recorded objects? [Clarity, FR-005; Search contract §Family-to-authority mapping]
- [ ] CHK009 Are worklist meanings tied to existing canonical observations, including aging dates and blocker scope? [Consistency, FR-016; Search contract §Worklist integration]
- [ ] CHK010 Are shared service boundaries and the absence of business writes on selection unambiguous? [Consistency, FR-003/018; DR-003]

## Search and Interaction Clarity

- [ ] CHK011 Are exact/normalized/prefix/approximate ranking tiers consistent across local vocabulary and record providers? [Clarity, FR-007/008; Search contract §Matching and ranking]
- [ ] CHK012 Are visible result groups and category pagination described consistently with the twelve/four/fifty bounds? [Clarity, FR-006/009; UI contract §One palette, one launcher]
- [ ] CHK013 Are keyboard, focus, composition, repeated activation, touch and zoom requirements explicit? [Coverage, FR-010; US3.2/3/7]
- [ ] CHK014 Are selection identity, out-of-order responses, disappearance and company-switch behavior defined? [Coverage, FR-011; US3.4/6]
- [ ] CHK015 Are partial failure, retry, stale observations and no-match states distinguishable in the requirements? [Coverage, FR-012; US3.5]
- [ ] CHK016 Are report/template inputs, navigation history and existing drafts preserved by explicit requirements? [Consistency, FR-002/017/018; US1.4; US5.2]

## Security and Preferences

- [ ] CHK017 Are membership, report ownership, lesson restrictions and reauthorization required for discovery and resolution? [Coverage, DR-003; Plan §Failure, security, and tenant behavior]
- [ ] CHK018 Are browser preference contents, user/company boundaries, limits, logout and failed-resolution behavior specified? [Completeness, FR-013/014; Data model §Browser-local navigation preferences]
- [ ] CHK019 Is contextual prefill restricted to explicit existing targets without granting execution authority? [Clarity, FR-015; UI contract §Contextual actions]
- [ ] CHK020 Is company switching explicit and separated from business-record search scope? [Consistency, FR-019; US5.3]

## Evidence and Dependencies

- [ ] CHK021 Are performance workload, timing boundaries, concurrency, latency, percentile and cold/warm reporting specified measurably? [Measurability, SC-003; Quickstart §Performance gate]
- [ ] CHK022 Are each FR/DR and buildable success criterion mapped to tests and implementation work? [Traceability, SC-001–006; Tasks §Requirement Coverage]
- [ ] CHK023 Are migration/index ownership, existing-data compatibility and rollback requirements bounded without business-schema expansion? [Coverage, DR-005; Data model §Database search support migration]
- [ ] CHK024 Are scope acceptance, unresolved issues and the distinction between design validation and runtime acceptance recorded? [Clarity, Spec §Assumptions and Dependencies; Plan §Planning Validation]

## Review

- **Specification reviewer**: Product scope accepted in conversation on 2026-09-18; this detailed checklist has not been reviewed.
- **Domain/architecture reviewer**: To be recorded in implementation review evidence.
- **Decision**: Generated for review; no checkbox implies product/runtime completion.
