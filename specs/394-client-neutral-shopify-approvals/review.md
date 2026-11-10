# Maintainer review proposal

This is a documentation-only proposal. No runtime change is included, no existing
protocol has been renamed, and no implementation or deployment is approved.

## Recommended direction

1. Keep the existing Shopify operations and application services. Generalize only
   their external approval boundary and new approval-source attribution.
2. Use operation-specific neutral proof types. Candidate names are
   `reality-shopify-buyer-mapping+jwt` and
   `reality-shopify-order-acceptance+jwt`, with explicitly reviewed versions.
   These are suggestions, not a published protocol commitment.
3. Resolve signing trust by the complete configured issuer/key/purpose/tenant
   binding. Never trust an arbitrary issuer label or a key ID in isolation.
   Reuse existing external-approval patterns where appropriate without merging
   the authority of unrelated purposes or introducing a second generic executor.
4. Store new approval sources under a neutral external-application convention,
   with issuer attribution in verified evidence. The convention must distinguish
   operation, issuer and exact reviewed identity so two clients cannot collide.
5. Preserve historical proofs, source identities and receipts exactly. Resolve
   retained formats through an explicit compatibility reader, not source edits,
   proof rewriting, automatic re-signing or a permissive format alias.

## Compatibility recommendation

- Prefer neutral contracts for all new submissions after an explicit rollout.
- Keep existing history/status and original-result reconciliation available under
  current read permission. Reconciliation cannot dispatch a second effect.
- Inventory retained approvals, outstanding proposals, unknown outcomes and actual
  consumers before deciding whether a submission transition is needed.
- Do not enable legacy submissions automatically. If a transition is needed,
  review its exact issuer, purpose, expiry and removal conditions separately.
- Preserve the global external-order duplicate guard, original receipt identity
  and cumulative standing exposure across formats. A changed namespace or proof
  version must never reset prior consumption or create a second first-order intake.
- Do not remove a compatibility reader while retained evidence still needs it.
  A removal needs its own reviewed retention/verification approach.
- Rollback must not rewrite newly retained neutral evidence or re-enable an old
  writer silently. Pin the chosen compatible reader/writer versions before rollout.

## Boundaries to preserve

- Source payloads and source-stated money remain unchanged.
- Mapping recognition, order preparation and actual order acceptance remain distinct.
- The model and submitting token never receive issuer signing credentials or
  become the human approver. Standing authority remains separately scoped and finite.
- Source/reference/policy/finance/calendar checks and transaction locks still run
  at the effect boundary; format validity alone is not execution authority.
- No payment, stock movement, reservation, fulfillment or public deployment is added.

## Decisions requested from the maintainer

- Does the neutral external-approval boundary belong in the existing Shopify
  services, using shared proof-verification primitives only where justified?
- Are the proposed neutral proof names and new source-attribution convention
  suitable, or should established repository naming be used instead?
- Is retained read/reconciliation compatibility sufficient, or is a bounded
  submission transition required after inspecting actual retained state?

These are review decisions, not blockers concealed by claimed implementation.
After acceptance: prepare the technical plan and Constitution Check, derive test-first
tasks, run cross-artifact analysis, and implement in a separate reviewed PR.

## Verification of this proposal

Documentation checks establish only specification structure and patch hygiene.
The requirement matrix in spec.md is future acceptance work. No model, provider,
database, workflow or deployment operation is needed to review this proposal.
