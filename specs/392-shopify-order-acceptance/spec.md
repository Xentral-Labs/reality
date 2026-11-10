# Feature Specification: Exact external Shopify order acceptance

**Feature Branch**: `392-shopify-order-acceptance`
**Created**: 2026-11-09
**Language**: English
**Status**: Specification, plan and analysis approved; implementation under isolated verification

## User Scenarios & Testing

### Story1 - One exact complete order review (P1)
An Operator selects the existing buyer/company/location/item/unit references for
one immutable source-v2 order. One successor proposal freezes all selections,
source-stated money and explicit interpretation terms. A fully supported order
is eligible for exact human or finite standing-policy acceptance. Unknown or
unsupported evidence is held; no caller amount overrides or default units exist.

### Story2 - Exact external authorization, truthful attribution (P1)
A current explicitly configured external issuer signs the exact review/digests,
source/tenant and purpose. Reality validates the current submitting MCP token,
issuer/subject/mandate, limits, expiry, source and references in the effect
transaction, then applies only canonical order evidence/commitments with atomic
receipt. The issuer human/standing decision is retained as external, never a
fabricated local Principal. Original source and ImportJob.input stay unchanged.

### Story3 - Retries do not duplicate accepted business meaning (P1)
An exact duplicate proof/request returns the same receipt. A lost response is
reconciled through read-only status; changed proof/source/mapping/customer/limits
cannot claim the same intent. Revocation or unresolved previous391 holds produce
zero effects. No payment, fulfillment, stock movement, master-data creation or
other financial operation is authorized by order acceptance.

## Requirements

- **FR-001** Preserve391 contracts, stored digests and always-held legacy behavior.
  New successor preparations are immutable distinct Actions; no promotion/mutation.
- **FR-002** Support only `shopify_simple_undiscounted_order/1`: all <=100 selected
  source lines complete, original/current quantities equal, no edit/cancellation,
  same-currency complete MoneyBags, explicit zero discounts/tax/shipping/refunds/
  tips/duties/fees, exact stated unit*quantity==stated line total and sum of stated
  line totals==stated subtotal/current subtotal/order/current order total.
  Comparisons never persist recomputed money; missing is unknown. Documented fee
  null may be retained as not_applicable with selected empty additionalFees; it is
  never persisted as numeric0. Nullable duty pairs may be not_applicable_no_line_duties only with complete
  selected empty line duties on ALL unchanged original lines, editedfalse and
  explicit zeroRefunds. Missing/ambiguous evidence remains held. All persisted
  money must be exactly representable as canonical Numeric(18,4); no DB rounding.
- **FR-003** Copy final unit/line/order values only from stated source fields after
  FR-002. Unresolved unsupported pricing remains held, never an accepted default.
- **FR-004** Require an explicit current CompanyTimeZone record and freeze its
  evidence/digest. `processed_at_in_explicit_company_timezone` determines the
  interpreted document date with provenance. Explicit `not_promised` delivery
  terms are included in review/authorization; no due date is fabricated.
- **FR-005** Assess canonical current credit under delivery/finance locks: explicit
  positive configured customer limit, same currency, complete/priced exposure,
  sufficient capacity. Missing/default/unknown/incomplete evidence is held.
- **FR-006** Prepare/read one bounded exact proposal with source/job/hash/version/
  query digest, verified buyer mapping and current explicit reference fingerprints.
  Reject stale basis; preserve originals and job.input. Wire bound24000bytes.
- **FR-007** Dedicated accept requires purpose `shopify_source_order_acceptance/1`,
  configured Ed25519 issuer/key/company/subject, current MCP token and exact proof
  claims/digests, human or explicit standing mandate revision, expiry, amount/unit/
  order/effect caps, UUID jti and original compact proof digest. Standing scope
  also requires exclusive original source_created_after. No generic approval.
- **FR-008** Revalidate and lock current authority/source/customer/references/calendar/
  credit in deterministic order. Apply only closed canonical document+commitment
  effects through existing transaction-bound effect dispatch/case guards. Receipt,
  approval evidence and business records commit atomically; failure rolls back all.
- **FR-009** Status is authenticated read-only historical acceptance evidence, not a
  renewed approval. Exact replay is stable; different proof cannot alias accepted
  intent. Duplicate external order across proposals is refused without disclosure.
- **FR-010** Register narrow tools and complete catalogue/tenant/resource/guidance
  metadata, tests and generated docs. Old99 remains proposal-only, no adapter or
  migrations/deployment/worker startup in this packet.

## Data Requirements

- **DR-001** Reuse existing SourceRecord, ChangeProposal and canonical business tables;
  no original payload/input rewriting and no new table without proven necessity.
- **DR-002** Received unit/line/order money is recorded unchanged. Arithmetic is only
  admission comparison, not an alternative authoritative amount.
- **DR-003** Retain exact external attribution/proof identity and canonical effect IDs,
  source/review/bundle/plan fingerprints, never secrets/private signing keys.

## Non-Goals

Discounted/taxed/shipping-fee allocation, returns/order edits, payment/capture/refund,
stock reservation/movement, fulfillment, settlement, arbitrary customer/master data
creation, old99 acceptance, deployment, live company/provider operations.

## Success Criteria

- SC-001 One fully source-backed eligible synthetic human proof and standing proof
  reach canonical effects+atomic receipts; all required replay/refusal tests pass.
- SC-002 Unknown391/financial/calendar/credit evidence, revoked/mismatched authority,
  tenant/source/ref changes and generic confirmation create no business effects.
- SC-003 Full required local/hosted checks, independent review and honest limits are
  recorded; no autonomous full-O2C or real-provider delivery claim follows.

## Context and Intent

391 holds meaning rather than authorizing effects. This successor supports one
source-backed positive subset with truthful external authorization and current
canonical authority; it cannot silently promote391 or reuse generic confirmation.

## Assumptions and Dependencies

Current Reality schema and canonical finance/calendar/credit services are required.
Exact source-v2 selection and external issuer configuration are separately reviewed;
no existing company runtime is altered. Official2026-07 Order/LineItem contracts
are primary evidence for monetary semantics and documented not-applicable fields.

## Requirement Traceability

| Requirements | Tasks | Proof |
|---|---|---|
| FR-001..006,DR-001..002 | T002,T003 | Pure source/calendar/credit and immutable preparation tests |
| FR-007..009,DR-003 | T004 | Real isolated DB human/standing, replay/revoke/rollback tests |
| FR-010 | T005,T006 | Metadata/spec/tenant/generation/CI and independent review |
