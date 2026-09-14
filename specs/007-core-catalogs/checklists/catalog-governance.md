# Catalog Governance Checklist: Canonical Core Catalogs

**Purpose**: Validate catalog-authority and drift requirements before implementation  
**Created**: 2026-08-31  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete.

## Requirement Completeness

- [x] CHK001 Are required fields defined for all four catalog categories, including an explicitly empty Fact-predicate vocabulary? [Completeness, Spec §FR-001–FR-006]
- [x] CHK002 Is the definition of a public Command distinguished from internal mutating helpers? [Clarity, Spec §FR-010]
- [x] CHK003 Are both missing and stale implementation/catalog relationships required for Events and Projections? [Completeness, Spec §FR-008–FR-009]
- [x] CHK004 Are migration-preservation requirements defined for parameter descriptions and all existing entries? [Completeness, Spec §FR-014]

## Consistency and Authority

- [x] CHK005 Are the composed view and separate authorities consistent without allowing consumers to merge files independently? [Consistency, Spec §FR-001–FR-002]
- [x] CHK006 Is it unambiguous that catalogs document but never own Source, Evidence, Reality, or Command decisions? [Clarity, Spec §DR-001–DR-004]
- [x] CHK007 Are Projection invalidation descriptions consistent with the explicit non-goal of implementing selective asynchronous workers? [Consistency, Spec §Non-Goals]
- [x] CHK008 Are the Web reference requirements consistent with existing tenant membership and shared-service rules? [Consistency, Spec §FR-012, DR-003]

## Scenario and Edge-Case Coverage

- [x] CHK009 Are duplicate, missing, stale, unknown-reference, alias, and empty-vocabulary cases all addressed? [Coverage, Spec §US2, Edge Cases]
- [x] CHK010 Are dynamic Event or Fact names required to use an explicit registry rather than escaping completeness checks? [Coverage, Spec §Assumptions]
- [x] CHK011 Is offline validation explicitly required for both application and data-model catalogs? [Coverage, Spec §FR-011]
- [x] CHK012 Are authenticated, unauthenticated, and rename-without-frontend-duplication scenarios specified? [Coverage, Spec §US3]

## Acceptance and Traceability

- [x] CHK013 Can catalog completeness and uniqueness be measured objectively across all categories? [Measurability, Spec §SC-001–SC-003]
- [x] CHK014 Does every FR and DR map to an acceptance scenario and planned executable proof? [Traceability, Spec §Requirement Traceability]
- [x] CHK015 Are rollback and no-schema/no-infrastructure boundaries explicit enough for review? [Clarity, Spec §Non-Goals, DR-005]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product owner approved the requirements and architecture review on 2026-08-31.

