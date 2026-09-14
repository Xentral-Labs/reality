# Agent Parity Requirements Checklist: Complete Chat and MCP Command Coverage

**Purpose**: Validate requirement quality for the formal PR review gate
**Created**: 2026-09-02
**Feature**: [spec.md](../spec.md)

Reviewer ownership: `[x]` means a reviewer approved the quality of the written
requirement, not that implementation has been completed.

## Requirement Completeness

- [ ] CHK001 Are all canonical tenant business command families either eligible or explicitly excluded/blocked? [Completeness, Spec §FR-001]
- [ ] CHK002 Are the discovery families and the mutation-relevant fields they must return fully enumerated? [Completeness, Spec §FR-004]
- [ ] CHK003 Are both sales and purchase order Evidence-to-Reality requirements defined? [Completeness, Spec §FR-010–FR-011]
- [ ] CHK004 Are create, update, lifecycle, hold/release, correction/reversal, and source-version cases covered where the underlying catalog supports them? [Coverage, Spec §FR-012–FR-014]

## Requirement Clarity and Consistency

- [ ] CHK005 Is “complete” unambiguously bounded to canonical tenant business commands plus required discovery? [Clarity, Spec §Assumptions]
- [ ] CHK006 Is the difference between direct reads, proposed mutations, and confirmed execution consistent throughout the requirements? [Consistency, Spec §FR-002–FR-003]
- [ ] CHK007 Are opaque identity rules consistent between discovery, proposal inputs, persistence, and order creation? [Consistency, Spec §FR-005, DR-006]
- [ ] CHK008 Is ordinary explicit Web/API form submission clearly distinguished from agent proposal approval? [Clarity, Spec §Non-Goals]
- [ ] CHK009 Are Documents consistently restricted to Evidence while fulfillment/payment remain Reality-derived? [Consistency, Spec §FR-010, DR-002]

## Acceptance and Scenario Quality

- [ ] CHK010 Can 100% command classification and mapping be measured without subjective review? [Measurability, Spec §SC-001]
- [ ] CHK011 Does each business family have an independently observable proposal-before-approval and execution-after-approval scenario? [Coverage, Spec §SC-002–SC-003]
- [ ] CHK012 Is atomic rollback measurable for multi-record and multi-line proposals? [Acceptance Criteria, Spec §FR-009, SC-003]
- [ ] CHK013 Are tenant isolation, authorization, stale state, rejection, validation failure, and replay scenarios all specified? [Coverage, Spec §FR-007, FR-022]
- [ ] CHK014 Is the order trace objectively required to expose SourceRecord, Document, DocumentLine, and Commitment identities? [Measurability, Spec §SC-004]

## Security and Operational Boundaries

- [ ] CHK015 Are excluded destructive/global/auth/maintenance operation classes specific enough for executable classification? [Clarity, Spec §FR-016]
- [ ] CHK016 Is the special current-human-owner requirement for membership execution explicit? [Security, Spec §FR-015]
- [ ] CHK017 Are existing-token behavior and newly introduced permission grants specified? [Security, Spec §Assumptions, Plan §Rollout]
- [ ] CHK018 Are safe error disclosure and foreign-tenant not-found behavior specified consistently? [Security, Spec §FR-022, DR-004]

## Dependencies and Assumptions

- [ ] CHK019 Is reliance on existing canonical services distinguished from the one missing order orchestration service? [Dependency, Spec §Assumptions]
- [ ] CHK020 Is the no-schema-change decision consistent with exact preview/result storage and audit requirements? [Consistency, Plan §Data and migration impact]
- [ ] CHK021 Are compatibility requirements for existing tool names and response shapes explicit? [Completeness, Spec §FR-017]
- [ ] CHK022 Are documentation and public metadata requirements sufficient for an agent to discover required/default/optional fields safely? [Completeness, Spec §FR-020]

## Notes

- This checklist is reviewer-owned and must not be modified by implementation automation.
- Record ambiguities as spec changes before approving the checklist.
