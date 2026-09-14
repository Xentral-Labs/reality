# Reliability and Deployment Requirements Checklist: Shared Scheduled Jobs

**Purpose**: Reviewer-owned requirements-quality review before implementation.
**Created**: 2026-09-09
**Feature**: [spec.md](../spec.md)

Unchecked items await reviewer evaluation. A checked item means the written requirement is satisfactory, not that runtime behavior is implemented. Implementation must not change these markers automatically.

## Completeness and Clarity

- [ ] CHK001 Are scheduler materialization and worker consumption independently defined, including the requirement for both roles? [Clarity, Spec FR-009/012]
- [ ] CHK002 Are accepted cron grammar, UTC, interval bounds and missed-time semantics explicit? [Completeness, Spec FR-002/005; developer contract Timing]
- [ ] CHK003 Are create/control/manual request identity and stale-revision behavior unambiguous? [Clarity, Spec FR-004/009; data model]
- [ ] CHK004 Are pause, resume, edits, terminal failure and unresolved-run interactions consistent? [Consistency, Spec US1-4, US2-3/4]
- [ ] CHK005 Are queue-cap deferral, per-schedule serialization and bounded global discovery stated without claiming unlimited fairness? [Coverage, Spec FR-004/008; developer contract Limits]

## Effect and Tenant Boundaries

- [ ] CHK006 Does the contract distinguish a lease from effect idempotency and define stale-writer fencing? [Clarity, Spec FR-006; data model Transactions]
- [ ] CHK007 Are the no-commit/no-direct-network handler boundary and future external-effect review explicit? [Consistency, Spec Non-Goals; developer contract Transaction]
- [ ] CHK008 Are tenant catalog discovery and tenant-scoped business queries distinguished? [Completeness, Spec DR-002]
- [ ] CHK009 Are current actor/source authorization, archive, revocation and in-flight limitations defined? [Coverage, Spec FR-003/008, US2-4]
- [ ] CHK010 Are source provenance, commercial-value authority and no-auto-confirmation preserved? [Consistency, Spec DR-001/003/004]
- [ ] CHK011 Is invitation cleanup bounded without changing its retention meaning or email delivery? [Coverage, Spec FR-011]

## Operations and Evidence

- [ ] CHK012 Are subprocess timeout, retries, process shutdown and uncertain completion measurable? [Measurability, Spec FR-006/007/008; research defaults]
- [ ] CHK013 Is host cron cadence distinguished from application job cadence and worker execution? [Clarity, Spec FR-009/012; deployment runbook]
- [ ] CHK014 Is migration ownership explicit for both new entrypoints and rollback non-destructive? [Completeness, Spec FR-012; plan Rollout]
- [ ] CHK015 Do planned paths, CLI examples, status labels and spec 146 dependency agree? [Consistency, Spec FR-013]
- [ ] CHK016 Does every FR/DR have acceptance and test/implementation task mappings? [Traceability, Spec Requirement Traceability; tasks Requirement Coverage]
- [ ] CHK017 Are schema proof, retained run identity and review ownership recorded without claiming implementation approval? [Coverage, Spec Assumptions; data model; plan gate]

## Review

- Specification approval: Benedikt Sauter explicitly approved spec 147 on 2026-09-09, including separate scheduler/worker deployments. See the specification Approval Record.
- Detailed checklist evaluation: pending; overall specification approval does not assert an item-by-item technical review.
- Architecture/schema reviewer: pending before migration implementation.
- Decision: specification approved; detailed technical review and runtime implementation remain pending.
