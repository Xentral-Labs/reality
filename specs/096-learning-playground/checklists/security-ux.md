# Security and Learning UX Requirements Checklist

Purpose: reviewer-owned quality review before implementation. Created: 2026-09-06.
Feature: ../spec.md. All items intentionally unchecked; checked means reviewer approval of
requirements quality, not software completion. Implementation must not silently mark these done.

## Completeness and boundaries

- [ ] CHK001 Is pending-account Playground admission narrowly distinguished from production access? [Clarity, Spec FR-001]
- [ ] CHK002 Are every-user/private-run and archived-read boundaries defined across all transports? [Coverage, Spec FR-003, DR-003]
- [ ] CHK003 Are business egress and intentional managed-provider/account-mail exceptions explicit? [Clarity, Spec Assumptions]
- [ ] CHK004 Are no-key entry, initial reference dataset and zero initial stock unambiguous? [Completeness, Spec US1, FR-002]
- [ ] CHK005 Are unsupported scenarios separated from the first complete lesson and free-text action set? [Consistency, Spec Non-Goals, FR-008]

## Failure and provenance

- [ ] CHK006 Are duplicate confirmation, stale preview and unknown execution requirements distinct? [Clarity, Spec FR-009]
- [ ] CHK007 Are automatic effects and derived read observations kept separate from authoritative records? [Consistency, Spec FR-005, DR-004]
- [ ] CHK008 Is restart defined without deletion, including failed replacement initialization? [Coverage, Spec US4, FR-010]
- [ ] CHK009 Are quotas quantified with meaningful fallback and account-wide enforcement? [Measurability, Spec FR-011, Assumptions]
- [ ] CHK010 Are reference ambiguity and article-versus-stock creation covered without invented identity? [Coverage, Spec FR-007]

## Learning and acceptance

- [ ] CHK011 Are the three workspace regions, responsive sizes and locale expectations concrete? [Clarity, Spec FR-013]
- [ ] CHK012 Are guided success and provider failure independently usable and measurable? [Measurability, Spec SC-001, US3.5]
- [ ] CHK013 Are performance/visual/security release evidence and human review ownership specified? [Completeness, Spec SC-002–004]
- [ ] CHK014 Are public preview claims consistent with authenticated runtime capability? [Consistency, Spec FR-012]

Review decision: pending owner/domain/security review. No requested product choice remains
unanswered; this checklist is the normal approval gate for the detailed design.
