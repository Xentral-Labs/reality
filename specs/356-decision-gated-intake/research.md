# Research: Decision-gated interpretation and admission

Read-only repository investigation on 2026-10-03. Findings describe the current
checkout; proposed behavior is not claimed as implemented.

## R01: Reuse existing prepared proposal JSON

- Decision: Reuse existing prepared proposal JSON.
- Rationale: The item CSV path already retains exact reviewed rows and a digest; a separate provisional-document schema would add business authority before approval.
- Alternatives rejected: Provisional Document statuses and rollback-only interpreter previews.

## R02: Split preparation and transaction-bound apply

- Decision: Split preparation and transaction-bound apply.
- Rationale: core.process_import_job and file_interpreters commit internally; wrapping those calls cannot atomically retain approval and effects.
- Alternatives rejected: A confirmation wrapper around the existing mutating interpreter.

## R03: Guard writes, not every event indiscriminately

- Decision: Guard writes, not every event indiscriminately.
- Rationale: tenant_policy currently protects practice contexts but permits ordinary-company writers; event attribution is not authority.
- Alternatives rejected: An event-only global gate would reject source/queue telemetry and still obscure writer coverage.

## Compatibility review

Legacy tests that expect immediate accepted interpretation need deliberate updates
to prepare → review → approve assertions, preserving their existing domain refusal
checks. The roadmap is not evidence of current autonomous agent permission or
5,000-row support. No unresolved product clarification remains; engineering defaults
and limits are explicitly documented in spec/plan/contracts.
