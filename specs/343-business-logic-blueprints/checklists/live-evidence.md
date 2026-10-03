# Live Evidence Checklist: Explainable Business Logic and Test Blueprints

**Purpose**: Review requirements quality for live-source freshness and business/test evidence before implementation.
**Created**: 2026-10-03
**Feature**: [spec.md](../spec.md)
**Audience**: Product/domain and implementation reviewers; standard depth, pre-implementation.

Checkboxes belong to the reviewer. A checked item means the requirements-quality criterion was accepted, not that implementation passed. This checklist is generated unchecked.

## Completeness

- [ ] CHK001 Are public entry kinds and incremental explanation boundaries explicitly defined? [Completeness, Spec §Scope, FR-001, FR-015]
- [ ] CHK002 Are prerequisites, inputs, decisions, calculations, effects and refusal conditions required for every completed blueprint? [Completeness, Spec FR-002]
- [ ] CHK003 Are actual test setup, fixture assumptions, assertions and parameter cases required independently of test names? [Completeness, Spec FR-007–FR-008]
- [ ] CHK004 Is the distinction between test discovery, assertion evidence, measured coverage and executed results unambiguous? [Clarity, Spec FR-008–FR-009]

## Freshness and Consistency

- [ ] CHK005 Is running code explicitly distinguished from disk changes, repository HEAD and documentation release? [Consistency, Spec FR-017–FR-019, Plan §Service and adapter flow]
- [ ] CHK006 Are missing source, mismatched versions and changed-source-during-analysis outcomes specified? [Coverage, Spec US1.3, Plan §Failure, security, and tenant behavior]
- [ ] CHK007 Do freshness requirements exclude pre-generated final explanations without excluding exact raw-source provenance? [Consistency, Spec FR-017–FR-019, Plan §Data and migration impact]
- [ ] CHK008 Are shared-rule identity and source-version identity distinguished consistently across all four channels? [Clarity, Spec FR-004–FR-005, FR-010–FR-011]

## Domain Consistency

- [ ] CHK009 Are source-stated values distinguished from derived observations in rule explanations and case comparison? [Consistency, Spec DR-001–DR-002]
- [ ] CHK010 Are current-state evaluation and recorded historical decisions distinguished when information has changed? [Coverage, Spec FR-013, US4.3]
- [ ] CHK011 Are public generic evidence and authenticated tenant case reads bounded without alternate business calculations? [Completeness, Spec FR-014, DR-003]
- [ ] CHK012 Are incomplete fixture facts and similar-but-different cases prevented from being described as proven matches? [Clarity, Spec FR-012, US4.1–US4.2]

## Acceptance Criteria Quality

- [ ] CHK013 Is full inventory coverage measurable independently of deep reference-journey completeness? [Measurability, Spec SC-001–SC-002]
- [ ] CHK014 Is the reference journey's decision-boundary denominator defined before claiming complete coverage? [Clarity, Spec FR-015, Plan §Reference journey boundary]
- [ ] CHK015 Does the professional-review criterion measure business understanding without requiring source-code reading? [Measurability, Spec SC-003]
- [ ] CHK016 Are missing, failed, skipped and older-version evidence cases covered without a false verification claim? [Coverage, Spec SC-005, US2.4]

## Review

- **Specification scope**: User accepted continuation after the live-source clarification.
- **Requirements-quality reviewer**: Pending reviewer assessment.
- **Decision**: Draft review checklist; no implementation result implied.

## Notes

The implementation skill reads checklist state but does not change reviewer-owned markers. All repository artifacts are English. No extension hooks are configured.
