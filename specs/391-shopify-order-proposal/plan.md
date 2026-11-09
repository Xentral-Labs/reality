# Approved Bounded Proposal Plan

## Audit evidence
- services/shopify_intake.py prepare_order reads job.input, uses first exact SKU,
  supplies item.unit or pcs, and constructs prospective effects/credit observations.
- services/intake.py prepare_intake/_prepare_intake writes intake_proposal_id into
  job.input; review_intake/_validate_current_plan depend on pointer plus mapping
  equality. Unmodified reuse would violate our source-input retention contract.
- apply_prepared_intake requires a real local delivery Principal and, for protected
  finance scope, local owner. intake_review mandates require a local owner-issued
  token/grant, current owner membership and registered source/capability scope.
  An external Main JWS subject is not that user, and a manual token is not approval.

## Proposed smallest packet
1. Agree exact mapping-bundle/plan envelope and closed proposal-only purpose.
2. Extract one pure canonical Shopify plan builder accepting resolved immutable
   mapping/evidence inputs. No fabricated ImportJob, source mutation or accepting
   API. Both native/portable preparation use it; existing legacy paths retain their
   behavior until explicit reviewed-origin adoption is designed and tested.
3. Resolve exact current same-tenant references through existing shared reads,
   spec389 buyer lineage and spec390 unique-item/unit diagnostics. Explicit caller
   selections remain proposed until independent policy/human admission.
4. Retain a dedicated non-generic-executable proposed Action with stable request
   identity, full digest and source/buyer/reference binding. Review checks current
   basis without changing immutable job.input or promoting operational state.
5. Return bounded digest/summary/holds for Now; expose retained full interpretation
   through exact authenticated review, not oversized chat checkpoints.
6. Prove isolated current and exact-old99 proposal/read behavior; do not copy a new
   intake model/finance subsystem or migrate the pilot. No acceptance in this slice.

## Successor acceptance boundary (separate review)
Extend canonical current-preparation origin resolution so an approved bundle can
be current without a rewritten job.input pointer. Add exact external issuer or
standing-mandate admission with truthful external attribution, current owner/
policy/revision/expiry, closed effects/amounts/units and immutable original proof.
Then invoke the canonical transaction/effect executor, not a parallel apply loop.
Old99 lacks that subsystem; choose and prove an explicit supported deployment/
application route before claiming autonomous O2C readiness. No fake Principal,
generic confirm token, arbitrary projection overrides or silent schema upgrade.

## Source evidence gaps
Current selected/projection contract has original unit-price evidence but no
interpreted final discounted line amount, agreed source sales unit or promised
local delivery date. Preserve unknowns; future richer acquisition must be a
separately reviewed immutable evidence source/version, not replacement of original
payload with a different query selection under an unchanged hash/version.
Company business timezone/credit context also needs a proven current/old99 route.
Do not default UTC or claim unavailable credit tables were read.

## Constitution Check
Candidate PASS only if no original/input rewrite, no invented source values or
human, no new core schema, shared rules, tenant scope, no-effect tests and exact
unknowns remain. Contract and preimplementation analysis approval required before
code. No exceptions assumed.

Product kind comes from mapped Item.item_type, never requiresShipping. Nonshipping stocked products remain item lines; shipping/type contradictions stay held.
