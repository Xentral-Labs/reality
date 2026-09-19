# Desktop Security and Recovery Requirements Checklist

**Purpose**: Reviewer-owned requirement-quality checks before architecture approval.
**Created**: 2026-09-19
**Feature**: [spec.md](../spec.md)

- [ ] CHK001 Are local identity and hosted identity semantics explicitly distinguished without claiming email verification? [Clarity, FR-003, data-model.md]
- [ ] CHK002 Is the OS-account trust boundary and its limitation explicit? [Completeness, FR-008, Assumptions]
- [ ] CHK003 Are capability replay, cross-origin and cross-tenant failures defined? [Coverage, FR-008, DR-003]
- [ ] CHK004 Are credential custody, failed unlock and portable recovery covered together? [Consistency, FR-007, FR-013]
- [ ] CHK005 Are checkpoint rollback and later restore with intervening writes distinguished? [Clarity, FR-012, US4]
- [ ] CHK006 Are restored background-source effects and unresolved outcomes addressed? [Coverage, contracts/desktop.md]
- [ ] CHK007 Are first-run defaults, AI skip and live activity consent unambiguous? [Clarity, FR-002, FR-004, FR-006]
- [ ] CHK008 Are close, Quit, sleep and crash semantics consistent across artifacts? [Consistency, FR-009–011]
- [ ] CHK009 Are all new schema fields justified by repeated policy use? [Completeness, DR-003, data-model.md]
- [ ] CHK010 Are measurable performance and clean-machine release criteria separated from unverified assumptions? [Measurability, SC-001, SC-002, SC-005]
- [ ] CHK011 Does every requirement have test and implementation coverage? [Traceability, tasks.md]
- [ ] CHK012 Are architecture approval, credentials and release evidence clearly distinguished from product-scope acceptance? [Clarity, Review Record, plan.md]

Reviewer and decision: pending. Unchecked means review pending, not an implementation failure.
