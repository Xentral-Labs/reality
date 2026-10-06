# Requirements Review: Essential intake completeness

**Created**: 2026-10-06
**Purpose**: PR reviewer assessment of requirement quality.
**Ownership**: Unchecked items belong to the reviewer; they do not claim unfinished implementation or red checks.

- [ ] CHK001 Are required monetary fields and no-effect refusal outcomes explicit? [Clarity, Spec FR-001/002/008]
- [ ] CHK002 Are unknown price and explicit zero distinguished? [Consistency, Spec FR-003]
- [ ] CHK003 Are legitimate missing dates/totals allowed and visibly explained? [Coverage, Spec FR-004/005]
- [ ] CHK004 Are date precedence, local midnight and conflicting header rules specified? [Edge cases, Spec US2]
- [ ] CHK005 Are physical units and supported purchase conversion boundaries explicit? [Consistency, Spec FR-007]
- [ ] CHK006 Are immutable historical evidence, replay and tenant guards preserved? [Coverage, Spec DR-001/003]
- [ ] CHK007 Does every rule have positive and negative planned proof? [Traceability, Spec Requirement Traceability]
