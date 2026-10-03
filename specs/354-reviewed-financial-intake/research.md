# Research: Reviewed invoice, payment and allocation intake

Read-only repository investigation on 2026-10-03. Findings describe the current
checkout; proposed behavior is not claimed as implemented.

## R01: Reuse finance atomic execution

- Decision: Reuse finance atomic execution.
- Rationale: The FINANCE_COMMANDS approval branch already keeps effects and receipt in one transaction; the generic approval branch does not.
- Alternatives rejected: A wrapper invoking commit-owning payment intake during confirmation.

## R02: Keep allocation visible and exact

- Decision: Keep allocation visible and exact.
- Rationale: interpret_customer_payment currently chooses a uniquely stated reference and allocates up to the open amount.
- Alternatives rejected: Recompute a different allocation while executing the approved plan.

## R03: Accept unmatched money only through explicit meaning

- Decision: Accept unmatched money only through explicit meaning.
- Rationale: Missing invoice identity need not prevent an otherwise valid payment from being deliberately recorded.
- Alternatives rejected: Invent an invoice or authorize a write-off to force reconciliation.

## Compatibility review

Legacy tests that expect immediate accepted interpretation need deliberate updates
to prepare → review → approve assertions, preserving their existing domain refusal
checks. The roadmap is not evidence of current autonomous agent permission or
5,000-row support. No unresolved product clarification remains; engineering defaults
and limits are explicitly documented in spec/plan/contracts.
