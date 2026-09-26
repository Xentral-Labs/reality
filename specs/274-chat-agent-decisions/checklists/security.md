# Security Requirements Checklist: Chat Agent Decisions

**Purpose**: Validate authorization, attribution and lifecycle requirement quality before implementation
**Created**: 2026-09-25
**Feature**: [spec.md](../spec.md)

New markers are reviewer-owned. `[x]` means requirements quality was reviewed, not that implementation is complete.

## Authority Completeness

- [ ] CHK001 Are generic confirmation authority and operation-specific person/owner authority explicitly separated? [Completeness, Spec §FR-003, §FR-008]
- [ ] CHK002 Is the server-owned boundary against authority from conversation, history, attachments, source values and tool output complete? [Coverage, Spec §FR-005]
- [ ] CHK003 Are read-only Playground restrictions stated for both proposal and confirmation access? [Completeness, Spec §FR-009]

## Attribution Clarity

- [ ] CHK004 Is Chat-agent attribution distinguished unambiguously from person, MCP token and unknown attribution? [Clarity, Spec §FR-006, §DR-003]
- [ ] CHK005 Does the specification forbid inferring personal approval from the authenticated browser session? [Consistency, Spec §Non-Goals, §DR-003]
- [ ] CHK006 Is durable attribution justified independently of expiring interaction telemetry? [Schema proof, Spec §DR-005]

## Lifecycle and Recovery

- [ ] CHK007 Are proposal-first, exact opaque identity and separate confirmation-call requirements mutually consistent? [Consistency, Spec §FR-002-FR-003]
- [ ] CHK008 Are replay, rejection, cross-tenant, stale-review and executing/unknown outcomes covered without implying safe blind retry? [Coverage, Spec §FR-007, Edge Cases]
- [ ] CHK009 Is prepare-only behavior explicit when the user does not request confirmation? [Alternate flow, US1 scenario 4]
- [ ] CHK010 Is the single-turn propose-and-confirm case specified as two observable ordered lifecycle steps? [Clarity, Edge Cases]

## Measurability and Traceability

- [ ] CHK011 Can the no-direct-mutation rule be objectively proven before and after the confirmation boundary? [Measurability, Spec §SC-001]
- [ ] CHK012 Do provider parity requirements cover both tool authority and outcome semantics? [Completeness, Spec §FR-012, §SC-005]
- [ ] CHK013 Does every security-sensitive requirement map to an acceptance scenario and planned executable proof? [Traceability, Spec §Requirement Traceability]

## Notes

- Review before implementation; `$speckit-implement` must not change these markers.
