# Feature Specification: Explicit Shopify mapping bundle and order proposal

**Feature Branch**: `391-shopify-order-proposal`
**Created**: 2026-11-09
**Language**: English
**Status**: Combined proposal-only boundary approved; implementation under isolated verification

## User Scenarios & Testing

### Story1 - Operator prepares one complete human-review boundary (P1)
Given a current immutable source, a verified existing buyer and explicit existing
company/location/item/unit selections, an Operator prepares one source-linked
order interpretation for review in Now. Selections and prospective effects are
frozen together; proposal creation is not approval or business acceptance.

Acceptance: exact references and selected source lines are visible; source money
is preserved, unknown commercial/date evidence stays unknown; no default unit,
master-data creation, original/input rewrite or business effect occurs.

### Story2 - Important choices and changed evidence remain explicit (P1)
Missing or ambiguous existing references, absent reviewed quantity semantics and
commercial uncertainty produce typed decisions/holds. A changed source, buyer,
reference or selected item invalidates preparation/review currentness. Replay of
the same request and identical intent returns one retained proposal; a changed
intent cannot reuse the request ID.

### Story3 - A proposal cannot become an implicit mandate (P1)
Generic confirmation and model calls cannot execute the dedicated proposal type.
A later exact human or explicit standing-mandate acceptance channel must validate
this same bundle and plan before invoking canonical application. That later
channel is outside this proposal-only slice.

## Context and Intent

### Problem
Canonical native prepare_order still reads mappings only from job.input, selects
first SKU and derives its unit from the item/defaultpcs. prepare_intake writes a
proposal pointer into job.input, and native review/apply require that pointer.
The schema99 pilot lacks the reviewed-intake subsystem. Replaying source capture,
faking job.input or inventing a local Reality Principal is not an integration.

### Scope
Proposed TWO-method contract: source_order_prepare(propose) freezes explicit
mapping selections and a canonical PreparedIntake-shaped closed plan in one
non-executable Action; source_order_review(read) restores exact retained meaning,
digest and current/stale status. The verified spec389 buyer relationship is a
separate existing authority; proposed company/location/unit selections are not
misrepresented as already reviewed. A properly verified policy can eventually
admit them, but a caller boolean or manual token cannot.

### Non-Goals
Actual provider/company-database operations, business application today, generic
confirmation grants, fake human identities, schema99 full-intake migration,
source/job.input rewriting, auto-selected customer/master data, default/conversion
units, recomputed source amounts, payment/fulfillment, or claiming proposal-only
compatibility as autonomous application readiness.

## Requirements

- **FR-001** Bind exact tenant/source/job/hash/positive version/external order/shop/query and current verified buyer review/digest/approval Source.
- **FR-002** Require explicit existing active company/location and complete source-line membership with existing item identity/digest plus explicit same-stock-unit quantity interpretation. No silent aliases, SKU-first selection, defaults or conversions.
- **FR-003** Server resolves all received quantities/money from immutable selected source. Caller provides no amount/price overrides. Original-price evidence cannot silently become final agreed price; unknown final/line/date evidence is held.
- **FR-004** Freeze selection bundle and canonical closed prospective document/commitment/credit-hold meaning together. Return bounded summary/digest and source links; retain unknowns without claiming readiness.
- **FR-005** Preserve original source, current pointer and ImportJob.input. Preparation may retain a dedicated proposed Action and safe pending interpretation evidence, but no operational business records or approved mapping are invented.
- **FR-006** Exact stable request replay is idempotent; source/reference changes, duplicate accepted external identity and competing preparation refuse or become stale without accepted effects.
- **FR-007** Dedicated proposal is not registered for generic execution. Later acceptance needs a distinct purpose-bound human/standing-mandate proof and current authority/evidence validation; no borrowed buyer proof or fabricated Reality Principal.
- **FR-008** Current native and old99 storage/read compatibility is proved separately. A portable proposal snapshot does not imply old99 canonical application support.
- **DR-001** Reuse existing Action/Source records and pure PreparedIntake meaning; no new core table without a separately demonstrated need. Interpretation rules are shared, not duplicated by the compatibility layer.

## Assumptions and Dependencies
The coordinator must accept the combined two-method/single-review boundary and
proposal-origin retention design before implementation. Tobias's actual customer
selection is deferred; synthetic existing-reference fixtures permit all code and
negative proof without making that choice. Native external issuer acceptance and
standing-policy admission are a successor boundary, not permission inferred from
this proposal. Shopify order1004 is not test:true and is not a payment/fulfillment
validation order.

## Success Criteria
- **SC-001** Synthetic exact known mappings produce one inspectable non-executable proposal with unchanged original/input and no business effects.
- **SC-002** Missing/changed references, units, selected financial meaning, source versions and nonce conflicts remain explicit and fail closed.
- **SC-003** Generic confirmation cannot apply the proposal; old99 proof claims only the behavior actually supported.

## Requirement Traceability

| Requirement | Scenario | Planned proof |
| --- | --- | --- |
| FR-001/002/003 | Stories1/2 exact interpretation | Source/buyer/reference/unit/value and unknown-evidence tests |
| FR-004/005/DR-001 | Story1 retained proposal | Canonical builder parity, immutable snapshots and no-effect SQL checks |
| FR-006 | Story2 currentness/replay | Concurrent request, stale refs and accepted external identity tests |
| FR-007/008 | Story3 authority and deployment | Generic execute refusal, explicit acceptance-unavailable and old99 proof |
