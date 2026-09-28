# Product Advisor Requirements Checklist: Reality Product Advisor

**Purpose**: Validate factuality, source governance, safety, language and evaluation requirements before implementation
**Created**: 2026-09-28
**Feature**: [spec.md](../spec.md)

**Ownership**: This is a reviewer-owned requirements-quality checklist. `[x]` means the reviewer accepts the requirement quality; it does not mean implementation is complete.

## Requirement Completeness

- [ ] CHK001 Are all evidence classes that may establish a public product claim explicitly included or excluded? [Completeness, Spec §FR-005–FR-007]
- [ ] CHK002 Are the requirements complete for narrow checks, broad process advice, technical questions, tenant follow-ups and out-of-scope requests? [Completeness, Spec §FR-002–FR-004]
- [ ] CHK003 Are requirements defined for native, agent-proposed, confirmation-required, manual, workaround and gap classifications? [Completeness, Spec §FR-014]
- [ ] CHK004 Are the public, authenticated-public, internal and tenant evidence boundaries fully distinguished? [Completeness, Spec §FR-016–FR-018, §DR-003]
- [ ] CHK005 Are knowledge freshness, removed sources, duplicate identity and broken-reference behavior all specified? [Completeness, Spec §FR-021–FR-023]

## Requirement Clarity

- [ ] CHK006 Is “material capability statement” clear enough to decide which answer statements require evidence? [Clarity, Spec §FR-008–FR-008a]
- [ ] CHK007 Are `proven`, `limited`, `unavailable` and `not established` defined sufficiently to prevent inconsistent classification? [Clarity, Spec §FR-009]
- [ ] CHK008 Is the boundary between an adjacent primitive and proof of an end-to-end capability unambiguous? [Clarity, Spec §FR-003, §FR-011]
- [ ] CHK009 Is the precedence rule for conflicting sources explicit and consistent with the more-restrictive conclusion? [Clarity, US1 scenario 4]
- [ ] CHK010 Is the condition for asking a clarification instead of answering broad questions objectively stated? [Clarity, Spec §FR-013]
- [ ] CHK011 Is “latest substantive user question” sufficiently defined for language detection and short follow-ups? [Clarity, Spec §FR-019–FR-019a]

## Requirement Consistency

- [ ] CHK012 Are the shared-service requirement and the allowance for additive authorized evidence consistent across Website, Docs and authenticated Chat? [Consistency, Spec §FR-001, §FR-017–FR-018]
- [ ] CHK013 Are code/test constraints consistent with the rule that only public-safe reviewed sources may establish public claims? [Consistency, Spec §FR-006–FR-007]
- [ ] CHK014 Are detected-language responses consistent with canonical English evidence and invariant identifiers/tool names? [Consistency, Spec §FR-019–FR-019a, Assumptions]
- [ ] CHK015 Are deterministic fallback requirements consistent with provider-assisted classification, semantic checking and prose generation? [Consistency, Spec §FR-010, §FR-020]
- [ ] CHK016 Are the new Advisor requirements consistent with spec 290 browsing, proposals, votes and Journey identities? [Consistency, Spec §FR-027, Existing Contracts]

## Acceptance Criteria Quality

- [ ] CHK017 Can the 100% source-coverage and zero-overclaim criteria be measured from structured claims rather than subjective prose review? [Measurability, Spec §SC-001–SC-002]
- [ ] CHK018 Is the 90% useful-answer threshold paired with a defined reviewed question set and acceptable clarification outcome? [Measurability, Spec §SC-003]
- [ ] CHK019 Is “materially consistent” defined sufficiently for cross-surface parity evaluation? [Measurability, Spec §SC-004]
- [ ] CHK020 Is the 180-word default clearly bounded by the user's request for more detail? [Measurability, Spec §SC-007]
- [ ] CHK021 Is the named nine-language evaluation matrix broad enough to cover existing locales, non-Latin scripts and distinct language families without implying a production-language limit? [Measurability, Spec §FR-024, §SC-008]

## Scenario and Edge-Case Coverage

- [ ] CHK022 Are compound questions with mixed support levels and sales/purchasing ambiguity covered by acceptance requirements? [Coverage, Edge Cases]
- [ ] CHK023 Are stale, contradictory, overly broad and duplicated evidence outcomes specified? [Coverage, Edge Cases]
- [ ] CHK024 Are provider timeout, malformed planning, invalid citations, failed validation and unavailable public links all covered by safe recovery requirements? [Coverage, Spec §FR-020, Edge Cases]
- [ ] CHK025 Are prompt injection attempts from users, history and every evidence source class addressed? [Coverage, Edge Cases]
- [ ] CHK026 Are requirements defined for an existing code path that is experimental, disabled, unreachable or not publicly contracted? [Coverage, Edge Cases]
- [ ] CHK027 Is the distinction between an agent preparing an action and a person confirming it covered for both prose and tool presentation? [Coverage, Spec §FR-011, §FR-014–FR-015]

## Security, Privacy and Operations

- [ ] CHK028 Are prohibited public disclosures enumerated broadly enough to cover source excerpts, paths, identifiers, provider details and inferred tenant information? [Security, Spec §FR-016, §SC-005]
- [ ] CHK029 Are tenant-specific follow-up requirements aligned with not-found isolation and existing confirmation semantics? [Security, Spec §FR-017, §DR-003, §DR-006]
- [ ] CHK030 Are public conversation retention and internal diagnostic retention boundaries explicitly separated? [Privacy, Assumptions]
- [ ] CHK031 Are rollout, compatibility and rollback requirements sufficient to prevent two competing capability truths during migration? [Operations, Plan §Rollout and Rollback]
- [ ] CHK032 Is source-allowlist review ownership defined for content that is public but not suitable as a product commitment? [Governance, Gap, Plan §Review Risks]

## Traceability and Governance

- [ ] CHK033 Does every FR/DR group map to an acceptance scenario and planned executable evidence? [Traceability, Spec §Requirement Traceability]
- [ ] CHK034 Are the buyer evaluation cases required to identify eligible sources, required limitations and forbidden claims? [Traceability, Spec §FR-024–FR-025]
- [ ] CHK035 Does the specification preserve Source → Evidence → Reality and avoid creating new business authority from advice? [Domain Consistency, Spec §DR-001–DR-002, §DR-007]
- [ ] CHK036 Are product-scope, architecture and final-review owners required before the corresponding workflow gates? [Governance, Repository workflow]

## Review

- **Specification reviewer**: Product owner, 2026-09-28
- **Domain/architecture reviewer**: Product owner, 2026-09-28
- **Decision**: Approved to proceed through analysis; checklist items remain reviewer-owned

## Notes

- `$speckit-implement` reads this checklist state but must not mark reviewer-owned items.
- Unchecked items require reviewer disposition before implementation begins.
