# Feature Specification: Operational read performance

**Status**: Approved scope — user requested implementation after the local benchmark on 2026-09-09.

## Context and Intent

### Problem
Exceptions takes about three seconds and Finance about 4.6 seconds to appear in the active local live-demo company. Repeated derivations and unrelated refresh work delay ordinary navigation.

### Scope
Reduce repeated read work in Exceptions and the Finance open-items view while preserving existing results and freshness.

### Non-Goals
No new business rules, schema, background jobs, stale-result window, UI redesign, new infrastructure, or large-tenant capacity claim. Orders is a comparison measurement, not a separate redesign.

## User Scenarios & Testing

### User Story 1 — Read Exceptions promptly (Priority: P1)
An operator sees the same currently derived exceptions with less waiting.
**Independent test**: Compare all classes, causal values, ordering and trace links against the existing individual derivators at a fixed observation instant.
**Acceptance scenarios**:
1. Given open, revised and corrected commitments, when Exceptions opens, then it preserves every existing finding and trace while sharing repeated input reads.
2. Given a later business change or a different company in the same session, when read again, then no prior evaluation input is reused.

### User Story 2 — Open Finance without rebuilding unrelated views (Priority: P1)
An operator sees current open items and complete filtered totals after new business events.
**Independent test**: Read a stale finance projection and prove that unrelated projections are not rebuilt; compare rows and totals to the canonical financial service.
**Acceptance scenarios**:
1. Given new business events, when Finance opens, then its own results refresh without rebuilding delivery, inventory or exceptions.
2. Given payments, reversals, empty results and another tenant, when Finance opens, then existing filtering, totals, trace links and tenant isolation remain valid.

### Edge Cases
Quantity-only and date-only revisions, equal revision timestamps, movement corrections, direct and invoice-linked credits, missing optional evidence, no records, derivation failure, repeated reads after mutation, concurrent intake and cold projections.

## Requirements

- **FR-001**: Exceptions MUST preserve classes, values, order and Source → Evidence → Reality links at a fixed observation instant while eliminating repeated per-record input reads.
- **FR-002**: Shared exception inputs MUST be limited to one evaluation and one tenant/session, including cleanup on failure; later evaluations MUST read current records.
- **FR-003**: Finance open-items refresh MUST avoid deriving unrelated operational projections while preserving event-based invalidation and explicit full-refresh compatibility.
- **FR-004**: Both views MUST preserve existing filters, counts, complete-result totals and tenant boundaries without changing authoritative records or schema.
- **FR-005**: Validation MUST include automated result-parity, query-budget, freshness and tenant-isolation regression tests, plus repeat local browser measurements with method and limitations recorded.

## Success Criteria

- **SC-001**: Two repeat local navigations to each affected view show at least a 50% reduction in median data-response time against the recorded baseline (Exceptions 2.80 seconds; Finance 4.26 seconds). This is an acceptance observation on this local stack, not a hardware-independent SLA.
- **SC-002**: Existing business regression checks and added parity/freshness/isolation checks pass with no intentional output differences.

## Assumptions and Dependencies

The user's “ok mach” approves the proposed optimization of Finance and Exceptions. The active port-8080 worktree and live demo remain running; unrelated uncommitted integration work is preserved. PostgreSQL, canonical shared services and existing projection checkpoints remain authoritative implementation contracts. Local timing comparisons use the same company with live intake continuing, so counts may grow. No unresolved product clarification remains.

**Language**: English

## Repository Language
All repository code, tests, specifications, plans, tasks and documentation are English.

## Requirement Traceability

| Requirement | Scenario | Tests / task |
|---|---|---|
| FR-001 | US1.1 | test_operational_read_performance.py parity/query budget; T003–005 |
| FR-002 | US1.2, failure edge | test_operational_read_performance.py freshness/isolation/cleanup; T003/T005 |
| FR-003 | US2.1 | test_operational_read_performance.py targeted refresh; T006–007 |
| FR-004 | US1.1/2, US2.2 | Added parity/isolation/page/totals plus existing business suites; T003/T006–007 |
| FR-005, SC-001–002 | Both stories | Full gates and local click evidence in quickstart.md; T008–009 |
