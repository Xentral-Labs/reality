# Pre-implementation architecture review

Date: 2026-09-07. Reviewer: Codex, implementation review. Product owner authorized continuation after planning. This is design scrutiny, not runtime acceptance and not a replacement for final PR review. Reviewer-owned checklist markers are unchanged.

The planned service changes preserve existing Reality records and their shortest links. No schema expansion or constitutional exception is needed. The 29 FR/DR requirements and eight success criteria have implementation and verification coverage. Ordinary-company admission remains separate from practice admission. The prototype is a presentation reference only.

The following constraints are release gates, with executable proof in T016–T022 and T038:

- Claim the proposal, then acquire the tenant row guard before final validation and the domain handler. All direct stock/hold/revision writers use the same transaction guard. Refusal before handler invocation is distinct from uncertain handler execution. Audit outer correction, practice, manual-document and import lock ordering. Transaction-scoped locks release automatically on rollback/connection loss; no pooled session lock is introduced.
- Preserve capped reservation behavior. Immutable creation evidence proves the original allocation after subsequent consumption; current reservation quantity cannot serve as that proof.
- Require exact review authority through every adapter before exposing reviewed proposal creation. UI rollback retains compatible backend handlers. Unknown execution cannot authorize a retry.
- Effective quantities and dates determine SQL filters before pagination. Scope inventory by item/location/unit; missing observations and sampled totals are distinct.
- Treat persisted Chat context as explanation only; each tool call still enforces authenticated tenant scope.

No blocking design conflict was found. Implementation may proceed test-first behind the disabled rollout flag. Runtime lock coverage, recovery and actual browser evidence remain required before activation; no architecture claim certifies those tests in advance.

Implementation refinement: R5 now uses the existing tenant row lock and an atomic final-check/effect transaction, replacing cross-commit advisory locking. This reduces transaction ownership changes. The refinement preserves FR-014/DR-006 and requires the same concurrency, stale-review and recovery proofs before activation.


## Implementation review

The implementation keeps schema and canonical domain records unchanged. SQL reads
are tenant scoped and bounded before pagination. Shared fulfillment expressions
and core effective-value/correction helpers are reused; original payloads remain
lossless. Review quantity normalization treats PostgreSQL Decimal scale as a
representation detail and preserves exact values.

The transaction guard covers reservation/release, movements/corrections,
commitment creation/revision/cancellation, commitment/document/party holds,
manual-document corrections, stale-promise closure, relevant master-data updates
and lifecycle changes. Composite imports and practice operations reach this same
core boundary. No new session subclass, pinned connection or pooled advisory lock
was added. Membership removal already locks the same tenant, and approval rechecks
the confirming principal inside the final-effect transaction.

Old pending in-scope proposals obtain a review under their original ID. Legacy UI
and MCP consume the same authority. Direct CLI commands call guarded core services;
there is no CLI approval command to retrofit. Disabling only the frontend feature
flag is supported; reverting the token-aware backend independently is not a safe
rollback. Practice-only paths retain their existing policy.

Original review metadata remains immutable after execution. Verification uses
immutable action-correlated events rather than mutable current reservation quantity.
Reconciliation settles only matching recorded evidence and never calls a handler.
The card retains recorded receipts when subsequent observations fail. Successful
approvals do not append duplicate delivery Chat notifications.

Validation findings resolved: PostgreSQL quantity-scale drift, native-dialog focus
restoration, original reservation verification after consumption, stale state and
missing confirmation, untranslated strings, and mobile header width. Technical
review found no remaining blocking issue for the opt-in local foundation. The
feature stays disabled by default. Owner visual acceptance, deployment and later
module migration remain separate steps.
