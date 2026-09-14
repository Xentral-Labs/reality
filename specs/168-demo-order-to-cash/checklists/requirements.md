# Requirements Checklist: Demo Data pays its orders

**Purpose**: Validate requirement quality before implementation
**Created**: 2026-09-10
**Feature**: [spec.md](../spec.md)

## Completeness

- [x] CHK000 Specification and review evidence are written in English.
- [x] CHK001 Every user story is independently testable (US1–US5 each name an independent test).
- [x] CHK002 Every FR/DR is specific, observable, and unambiguous (FR-001–FR-025, DR-001–DR-007).
- [x] CHK003 Edge cases cover tenant isolation, currency, blocked account, unposted invoice, payment before invoice, replay, reversed invoice, empty references, changed references, lost eligibility, missing term.
- [x] CHK004 Scope, non-goals, assumptions, and dependencies are explicit; the seven owner decisions are listed as assumptions.
- [x] CHK005 The single schema change (`settlement_schedule_id`) has a repeated core-logic use case (every control action, FR-019).

## Domain Consistency

- [x] CHK006 Source → Evidence → Reality remains traceable (DR-001; invoice and payment are SourceRecords first).
- [x] CHK007 Operational state is derived from Reality, not stored on Documents (DR-003; no status, counter or candidate table).
- [x] CHK008 Relationships use opaque IDs and shortest true links (DR-002; numbers look up, allocations link ledger entries).
- [x] CHK009 CLI/API/Web/MCP/Chat share application services (FR-015 reuses the settlement flow and MCP tool).
- [x] CHK010 Important UI results have an Inspect/explanation path (FR-024 links; candidates carry reasons).

## Evidence

- [x] CHK011 Every requirement maps to scenarios and planned executable proof (spec traceability table; tasks Requirement Coverage).
- [x] CHK012 No unresolved `[NEEDS CLARIFICATION]` marker remains.
- [ ] CHK013 Reviewers and approval state are recorded (pending owner sign-off of the spec text).

## Review

- **Specification reviewer**: owner decisions recorded 2026-09-10; spec text review pending
- **Domain/architecture reviewer**: N/A until plan review
- **Decision**: Draft
