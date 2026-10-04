# Research: Bulk intake settlement and delegated agent review

Read-only repository investigation on 2026-10-03. Findings describe the current
checkout; proposed behavior is not claimed as implemented.

## R01: Keep current Chat restrictions

- Decision: Keep current Chat restrictions.
- Rationale: Current domain/proposal_decisions reports built_in_chat_can_confirm=false and autonomous_agent_delegation=false; spec 274 predates conflicting restrictions in 278/323.
- Alternatives rejected: Treating older Chat capability text or a token permission as unattended delegation.

## R02: Keep provider I/O outside scheduled handlers

- Decision: Keep provider I/O outside scheduled handlers.
- Rationale: Scheduled jobs are transaction-bound with a 30s default and 120s maximum; existing confirmation commits internally.
- Alternatives rejected: Calling a provider or the generic commit-owning executor from a scheduled handler.

## R03: Bound manifest and execution independently

- Decision: Bound manifest and execution independently.
- Rationale: 500 package rows, 500 selected proposals and 25 units per run are different limits.
- Alternatives rejected: An all-or-nothing 5,000-row transaction combined with promises of independent failure isolation.

## Compatibility review

Legacy tests that expect immediate accepted interpretation need deliberate updates
to prepare → review → approve assertions, preserving their existing domain refusal
checks. The roadmap is not evidence of current autonomous agent permission or
5,000-row support. No unresolved product clarification remains; engineering defaults
and limits are explicitly documented in spec/plan/contracts.
