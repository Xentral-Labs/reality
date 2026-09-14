# [CHECKLIST TYPE] Checklist: [FEATURE NAME]

**Purpose**: Validate requirement quality before implementation
**Created**: [DATE]
**Feature**: [Link to spec.md]

## Completeness

- [ ] CHK000 Specification and review evidence are written in English.
- [ ] CHK001 Every user story is independently testable.
- [ ] CHK002 Every FR/DR is specific, observable, and unambiguous.
- [ ] CHK003 Edge cases cover tenant isolation, failure, partial flows, and corrections where relevant.
- [ ] CHK004 Scope, non-goals, assumptions, and dependencies are explicit.
- [ ] CHK005 Schema changes have a repeated core-logic use case.

## Domain Consistency

- [ ] CHK006 Source → Evidence → Reality remains traceable.
- [ ] CHK007 Operational state is derived from Reality, not stored on Documents.
- [ ] CHK008 Relationships use opaque IDs and shortest true links.
- [ ] CHK009 CLI/API/Web/MCP/Chat share application services.
- [ ] CHK010 Important UI results have an Inspect/explanation path.

## Evidence

- [ ] CHK011 Every requirement maps to scenarios and planned executable proof.
- [ ] CHK012 No unresolved `[NEEDS CLARIFICATION]` marker remains.
- [ ] CHK013 Reviewers and approval state are recorded.

## Review

- **Specification reviewer**: [name/date]
- **Domain/architecture reviewer**: [name/date or N/A]
- **Decision**: Draft / Changes requested / Approved
