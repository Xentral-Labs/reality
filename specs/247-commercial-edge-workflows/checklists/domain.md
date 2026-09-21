# Requirements Quality Checklist: Commercial Edge Workflows

**Purpose**: Reviewer gate for financial meaning, traceability and safe boundaries
**Created**: 2026-09-21
**Ownership**: `[x]` records reviewer approval of requirement quality, not implementation completion.

## Requirement Completeness

- [ ] CHK001 Are creation, reversal and replay requirements defined for notices and every financial effect? [Completeness, Spec §FR-001..FR-009]
- [ ] CHK002 Are customer and supplier deposit directions both covered without implying statutory tax accounting? [Coverage, Spec §FR-007..FR-009]
- [ ] CHK003 Are normal and boundary demo examples required for all four workflows? [Completeness, Spec §FR-013]

## Requirement Clarity

- [ ] CHK004 Is the distinction between a dunning notice and its optional charge unambiguous? [Clarity, Spec §FR-001..FR-004]
- [ ] CHK005 Is bad debt distinguished from tolerance, discount and reusable customer credit? [Clarity, Spec §FR-005..FR-006]
- [ ] CHK006 Is deposit availability defined as a derived value rather than stored authority? [Clarity, Spec §DR-002]
- [ ] CHK007 Is a permitted overdelivery explicitly conditional on a prior quantity restatement? [Clarity, Spec §FR-010..FR-011]

## Consistency and Safety

- [ ] CHK008 Are all source values preserved consistently with the no-recomputation rule? [Consistency, Spec §DR-001]
- [ ] CHK009 Are tenant, party, side and currency mismatch outcomes defined atomically? [Coverage, Spec §FR-003, §FR-008]
- [ ] CHK010 Are confirmation, evidence and idempotency requirements consistent across all mutations? [Consistency, Spec §FR-012]

## Acceptance Quality

- [ ] CHK011 Can each success criterion be objectively verified through named scenarios? [Measurability, Spec §SC-001..SC-006]
- [ ] CHK012 Are the no-automation, no-tax and no-silent-adjustment boundaries explicit enough to prevent scope drift? [Boundary, Spec §Non-Goals]

## Notes

- `$speckit-implement` reads this checklist but does not change reviewer-owned markers.
