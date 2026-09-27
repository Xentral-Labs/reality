# Trust and Product-Truth Checklist: Business Journey Guide

**Purpose**: Validate requirement quality for public capability claims, evidence boundaries and product feedback
**Created**: 2026-09-27
**Feature**: [spec.md](../spec.md)

`[x]` records reviewer approval of requirements quality, not implementation completion.

## Completeness

- [ ] CHK001 Are all five support states and their required public explanations specified? [Completeness, Spec §FR-002]
- [ ] CHK002 Are evidence requirements defined for every support state rather than only `supported`? [Completeness, Spec §FR-003]
- [ ] CHK003 Are the fields permitted in public, internal and generated outputs explicitly distinguishable? [Completeness, Spec §FR-004, §FR-012]
- [ ] CHK004 Are requirements present for browsing, asking, proposing, voting, moderation and catalog evolution? [Coverage, Spec §US1–US5]
- [ ] CHK005 Are proposal lifecycle transitions and terminal-state rationale requirements complete? [Completeness, Spec §FR-016]

## Clarity and Consistency

- [ ] CHK006 Is “material capability claim” sufficiently bounded by the citation and status-ceiling requirements? [Clarity, Spec §FR-006–FR-007]
- [ ] CHK007 Are public static fallback and provider-assisted answers described consistently without making Docs depend on the API? [Consistency, Spec §FR-010, Plan §Service and adapter flow]
- [ ] CHK008 Is the distinction between complete capability catalog and demo-profile examples unambiguous? [Clarity, Spec §FR-023]
- [ ] CHK009 Are account-global proposals consistent with tenant isolation requirements and explicitly excluded from business state? [Consistency, Spec §DR-003, Research §account-global feedback]
- [ ] CHK010 Is “Business Journey Guide” canonical and is the prohibited alternate name bounded across visible and accessible copy? [Consistency, Spec §FR-022]

## Security, Privacy and Abuse

- [ ] CHK011 Are authentication requirements specified for each protected evidence and mutation path? [Coverage, Spec §FR-011–FR-018]
- [ ] CHK012 Are public prompt injection, confidential text, provider failure and internal-evidence leakage scenarios addressed? [Coverage, Spec §Edge Cases]
- [ ] CHK013 Are rate/length bounds and moderation outcomes measurable enough for release acceptance? [Ambiguity, Spec §FR-010, §FR-018]
- [ ] CHK014 Are Chat mutation confirmation requirements consistent with direct Web proposal/vote actions? [Consistency, Spec §FR-017, §DR-006]

## Acceptance and Evolution

- [ ] CHK015 Can complete 228-ID coverage and no-duplicate publication be objectively measured? [Measurability, Spec §SC-001]
- [ ] CHK016 Does the curated answer matrix cover supported, partial, recognition-only, missing and out-of-scope conclusions in both languages? [Coverage, Spec §SC-002, §SC-008]
- [ ] CHK017 Are stale tool, demo and related-journey references all included in freshness requirements? [Completeness, Spec §FR-020–FR-021]
- [ ] CHK018 Are concurrent vote, retry and withdrawal outcomes objectively specified? [Measurability, Spec §SC-007]
- [ ] CHK019 Is rollback behavior documented for static assets, API availability and additive proposal storage? [Coverage, Plan §Rollout and Rollback]
- [ ] CHK020 Is the advisory nature of votes explicit enough to prevent a roadmap promise? [Clarity, Spec §FR-024]

## Notes

- Reviewer-owned; `$speckit-implement` must not mark these items.
