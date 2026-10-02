# Implementation Plan: Consistent Proposal Decision Policy

**Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Scope approval**: Owner accepted the concrete draft and instructed continuation.
**Language**: English.

## Summary

Introduce a small immutable decision-policy value and a shared resolver/enforcer.
Use it for proposal next-step metadata and the existing approval checks. Separate
approval from rejection: rejection currently has no action-specific owner rule.
Keep specialized report ownership and transaction-sensitive checks in their services.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL, pytest; existing React/TypeScript frontend.
No new dependency, persistence or migrations. Scope is proposal decision guidance,
existing authority checks and their presentation, not a new authorization system.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Business handlers and their effects unchanged | PASS |
| Reality owns operational state | No document or business-state additions | PASS |
| Proven schema only | In-memory decision value; no tables or migration | PASS |
| Tenant + shared service boundaries | Existing tenant-scoped proposal lookup, shared checks | PASS |
| Spec/test traceability | Requirement matrix below and test-first tasks | PASS |
| Explainable web behavior | Display role requirement from shared metadata | PASS |
| Received values not recomputed | No money, quantities or source values changed | PASS |
| Smallest coherent design | Resolver and existing checks; no delegation engine | PASS |

The check passes before and after design. No exception or schema review required.

## Repository Structure and Layer Changes

- `packages/reality-core/src/reality/domain/proposal_decisions.py`: immutable policy,
  approval authority and distinct rejection requirement; compatibility serialization.
- `packages/reality-core/src/reality/services/proposal_decisions.py`: resolve exact
  action requirements and execute existing identity/owner/member checks at their
  existing lifecycle phases.
- `packages/reality-core/src/reality/services/proposal_reviews.py`: replace parallel
  role inference with resolver; retain verification reads from catalog.
- `packages/reality-core/src/reality/tools/application.py`: use shared policy at
  existing preflight, execution and locked member recheck points.
- `apps/web/src/api.ts`, `apps/web/src/unified/ProposalReviewCard.tsx` and localization:
  additive policy type; owner approval message without inventing owner-only rejection.
- `services/delivery_actions.py`: add identical next-step metadata to specialized
  delivery detail without changing its existing observation/verification logic.
- Shared `DecisionReview.tsx` requirement presentation and specialized delivery cards:
  pass held next-step metadata into the shared decision bar. CreditHoldRelease accepts
  an existing proposal ID so the decision queue opens its existing appropriate dialog;
  terminal proposals do not expose confirmation again.
- Focused backend tests, existing handoff expectations and proposal browser proof.

## Design

### Reality flow

No new evidence or business records. Existing ChangeProposal identity and decision
attribution remain authoritative; policy is derived at read and execution time.

### Service and adapter flow

Resolver receives application action, held arguments and registration availability.
It returns approval authority separately from explicit authorized decision, access
channels, autonomous delegation (false) and human involvement verification (false).
Keep required_principal as a deprecated compatibility summary; it does not assert
that a human was verified. Reviewed arguments require member checks in addition to
stronger owner requirements, not instead of them. Reference actions have a member
check in non-Playground execution, even without a delivery marker. Private reports
retain sealed author checks. Membership removal retains owner rules.
Unknown/retired actions are unavailable for approval but remain rejectable.

Enforcement preserves ordering: cost, credit, report and reviewed-member preflight;
identity and finance owner checks after lifecycle validation; reviewed member checks
again under lock; reference member checks under lock outside Playground. Existing
report reveal and handlers retain their own ownership/business validation.
Rejection stays access-context governed and does not acquire approval authority rules.
Adapter access continues to exclude built-in Chat settlement and to require external
confirmation scope/tool permission. Metadata describes paths, never authorizes them.

### Data and migration impact

No persistence changes. Add decision_policy within next_step. Existing summary fields
remain available. Existing malformed input handling and retired-action behavior remain.

### Failure, security, and tenant behavior

Reuse existing refusal codes and checks, including trusted local, disabled-auth,
platform-admin and transaction-bound profile exceptions. Do not infer human identity
from external token attribution. Preserve stale review, claims, no-effect failure,
replay and tenant isolation. Do not move checks across their effect transactions.

## Test Strategy and Traceability

| Requirement | Proof | Initial failure |
|---|---|---|
| FR-001, FR-002, FR-003 | New tests/test_proposal_decision_policy.py role/policy matrix; credit release owner/member story | Policy absent; credit mislabeled member |
| FR-004 | Ordinary proposal and member shipment/reference regressions | New metadata absent |
| FR-005, FR-006 | MCP access tests; Chat confirmation/security; policy and token attribution contract | New metadata absent |
| FR-007 | Changed membership, stale review, tenant/replay tests and existing approval suite | Policy unavailable |
| FR-008 | Exact handoff dictionaries, Web source contract and browser review with old/new payloads; docs generation | New policy absent |
| DR-001, DR-002 | Existing stock/finance stories, cross-tenant and decision-attribution suites; full pytest | Existing behavior must remain green |

## Rollout and Rollback

Additive metadata; clients accept absent policy during rolling deployment and use
legacy summary. No migrations. Roll back code and metadata together. Regenerate docs.

## Review Risks

- Owner role and active user status are not identical checks across services.
- Approval and rejection differ today; preserve that difference explicitly.
- Locked member rechecks and executed replay ordering must not move.
- Concurrent unrelated work exists in the checkout; do not revert or incorporate it.

## Complexity Tracking

No Constitution exceptions.
