# Fulfillment Safety Requirements Checklist: Fulfillment Safety Parity

**Purpose**: Validate safety, parity and recovery requirement quality before implementation
**Created**: 2026-09-26
**Feature**: [spec.md](../spec.md)

`[x]` means the reviewer approved the requirement-quality criterion; it does not mean the
implementation is complete. `$speckit-implement` reads this state and does not change it.

## Requirement Completeness

- [ ] CHK001 Are the required, received and remaining prepayment amounts defined for unpaid, partial, full, reversed and unrelated allocations? [Completeness, Spec §US1/FR-003–FR-005]
- [ ] CHK002 Are every readiness input and every supported blocker family named without assigning operational state to Documents? [Completeness, Spec §US2/FR-007–FR-010]
- [ ] CHK003 Are terminal failure and genuinely unknown execution outcomes both specified with distinct recovery behavior? [Completeness, Spec §US3/FR-013–FR-015]
- [ ] CHK004 Are complete public-contract requirements defined for both shipment directions and all four supported purposes? [Completeness, Spec §US4/FR-016–FR-019]

## Requirement Clarity

- [ ] CHK005 Is the prepayment policy explicitly distinguished from term code, label and zero due days? [Clarity, Spec §FR-001]
- [ ] CHK006 Is a qualifying allocation bounded by tenant, customer, currency, active state and unambiguous order-backed evidence? [Clarity, Spec §FR-004]
- [ ] CHK007 Is the boundary between proposal-time refusal, stale-review refusal, terminal failed execution and unknown executing outcome unambiguous? [Clarity, Spec §US2–US3]
- [ ] CHK008 Are "relevant" versus "unrelated" state changes defined sufficiently to make review-token freshness objectively testable? [Clarity, Spec §FR-011–FR-012]

## Requirement Consistency

- [ ] CHK009 Are Browser/Chat, application and MCP requirements stated as one shared decision rather than transport-specific behavior? [Consistency, Spec §FR-007–FR-010]
- [ ] CHK010 Are payment evidence requirements consistent with Source → Evidence → Reality and the no-recomputation rule? [Consistency, Spec §Context/FR-003–FR-004]
- [ ] CHK011 Are the new requirements explicitly bounded against overlapping draft spec 267 and existing stale-review spec 273? [Consistency, Spec §Non-Goals/Assumptions]

## Acceptance Criteria Quality

- [ ] CHK012 Can parity be measured by comparing exact blocker codes, amounts and opaque evidence IDs? [Measurability, Spec §SC-001–SC-004]
- [ ] CHK013 Can proposal lifecycle correctness be measured without inferring success from absence of an event? [Measurability, Spec §SC-005]
- [ ] CHK014 Does final reconciliation state exact inventory, reservation, invoice-open and premature-effect outcomes? [Measurability, Spec §SC-007]

## Scenario and Edge-Case Coverage

- [ ] CHK015 Are primary, alternate, exception and recovery scenarios covered for prepayment dispatch? [Coverage, Spec §US1/Edge Cases]
- [ ] CHK016 Are ambiguous partial/consolidated invoice attribution and multi-movement atomic refusal addressed? [Coverage, Spec §Edge Cases]
- [ ] CHK017 Are tenant isolation and cross-party/currency evidence explicitly covered as safety boundaries? [Coverage, Spec §US1/FR-004]
- [ ] CHK018 Is rollback behavior documented for the schema field and for proposals whose effect cannot be proven? [Coverage, Plan §Rollout and Rollback]

## Dependencies and Assumptions

- [ ] CHK019 Is the use of existing billed-line and settlement-allocation links documented as the shortest true dependency path? [Assumption, Spec §Assumptions]
- [ ] CHK020 Is the false default for existing terms explicit and free of name-based migration assumptions? [Assumption, Spec §Assumptions/FR-001]

## Review

- **Audience/timing**: Product/domain and PR reviewers before implementation
- **Depth**: Formal release gate for the P0/P1 safety slice
- **Focus**: Prepayment enforcement, cross-surface parity, proposal recovery and executable MCP contracts
- **Owner-approved scope**: 2026-09-26
- **Review decision**: Approved by the owner on 2026-09-26; implementation may proceed.

## Notes

- Items remain reviewer-owned. The owner approved proceeding on 2026-09-26; checkbox
  state is preserved because implementation automation must not alter reviewer markers.
