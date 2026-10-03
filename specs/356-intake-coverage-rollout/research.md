# Research: Intake decision coverage, demo and safe rollout

Read-only repository investigation on 2026-10-03. Findings describe the current
checkout; proposed behavior is not claimed as implemented.

## R01: Live demo and bootstrap have different authority

- Decision: Live demo and bootstrap have different authority.
- Rationale: Continuous demo interprets sources through bounded scope while fixed setup has an exact confirmed profile; keep only the latter narrow exception.
- Alternatives rejected: An unrestricted demo/source-start approval covering every future business effect.

## R02: Preserve old provenance truth

- Decision: Preserve old provenance truth.
- Rationale: decision_attribution intentionally returns unknown for decisions without a decider and no event decision where none exists.
- Alternatives rejected: Backfill approvals or attribute historical imports to the deployment operator.

## R03: Fail closed on rollout

- Decision: Fail closed on rollout.
- Rationale: An older commit-owning interpreter process can still produce unapproved records after new preparation code is deployed.
- Alternatives rejected: Deploy new clients without draining/fencing old writing workers.

## Compatibility review

Legacy tests that expect immediate accepted interpretation need deliberate updates
to prepare → review → approve assertions, preserving their existing domain refusal
checks. The roadmap is not evidence of current autonomous agent permission or
5,000-row support. No unresolved product clarification remains; engineering defaults
and limits are explicitly documented in spec/plan/contracts.
