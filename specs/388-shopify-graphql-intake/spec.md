# Feature Specification: Reviewed Shopify GraphQL intake

**Feature Branch**: `388-shopify-graphql-intake`
**Language**: English
**Created**: 2026-11-09
**Status**: Scope reviewed by coordinating agent under Tobias's explicit bounded authorization
**Input**: Tobias authorizes retaining Shopify test order #1004 in Reality and preparing an exact review proposal; no payment, fulfillment or automatic acceptance.

## User Scenarios & Testing

### User Story 1 - Retain and review a newly acquired order (Priority: P1)
A company operator can inspect the original acquired order and an exact proposed interpretation before any operational effect.

**Independent Test**: Enqueue an original retrieved GraphQL order entity, prepare it through the existing intake services, and verify the retained proposal and original selected entity payload while business records remain unchanged.

**Acceptance Scenarios**:
1. Given complete supported source data and explicit existing company/customer/location references, acquisition and preparation retain the original selected entity payload and one reviewable proposal; no order, commitment, movement or payment is applied.
2. Given replay of the same payload, the same source/job/proposal is returned without duplicated business records.
3. Given unknown optional source fields, they round-trip unchanged in the source and do not become invented business facts.

### User Story 2 - Refuse unsupported meaning safely (Priority: P1)
A reviewer sees a retained preparation refusal when data, identity or mapping is insufficient.

**Acceptance Scenarios**:
1. Missing mapping, identity mismatch, partial lines, wrong currency, provider errors, cancellation or prior accepted interpretation retain the source/job and refuse preparation without business effects.
2. Foreign-tenant references fail without foreign record disclosure.
3. A source-stated unit price is retained; an unstated line total remains unknown and is never calculated from quantity and price.

## Context and Intent

### Problem
Existing Shopify intake consumes a legacy fixture-shaped payload. A current GraphQL response cannot truthfully be relabeled as that original source.

### Scope
One newly acquired, unfulfilled Shopify order; immutable original selected order entity retention, bounded interpretation, existing exact proposal preparation and failure retention.

The source payload is the unmodified `data.order` JSON object, not the transport envelope, not a reconstructed REST document and not the complete upstream resource. Volatile GraphQL cost metadata stays outside source identity.

### Non-Goals
Vendor authentication or transport, recurring jobs, new master data, arbitrary GraphQL interpretation, updates to accepted orders, refund interpretation, apply/accept, financial or fulfillment effects, and production completeness claims.

## Requirements

- **FR-001** Preserve the exact retrieved original selected order entity, unknown fields and original source identity/hash without rewriting it into a legacy payload.
- **FR-002** Recognize a distinct supported source shape and prepare using existing reviewed intake, tenant and authority boundaries; never call acceptance.
- **FR-003** Validate exact opaque order/line identity, complete bounded lines, received currency/money, and supported first-order state. Never recompute source amounts.
- **FR-004** Require existing explicit company/customer/location mappings. Missing/foreign mappings create no master data or operational effects.
- **FR-005** Replays are idempotent; prior accepted interpretation of the same external Shopify identity refuses a second first-order interpretation, including legacy source shapes.
- **FR-006** Refusal retains source/job and existing explainable failure outcome. Unsupported later changes remain reviewable without automatic application.
- **DR-001** Existing SourceRecord -> ImportJob -> ChangeProposal -> explicit decision chain remains authoritative, with no schema migration or direct adapter ORM writes.

## Key Entities
Existing SourceRecord, ImportJob and ChangeProposal only. Original Shopify GIDs and received source versions identify upstream records; human order numbers are labels.

## Assumptions and Dependencies
Tobias has authorized this bounded test source/proposal write. The caller must independently own valid Shopify read consent and Reality enqueue/prepare authority. Existing company/customer/location references are supplied explicitly. Acquisition must request the supported complete field selection and supply source update time. Unknown line totals remain unknown. No live-provider execution is performed by this implementation lane. Customerless order #1004 retains an existing named needs-review refusal until a real buyer mapping is explicitly supplied; no zero-effect fake proposal is generated.

## Success Criteria
- **SC-001** Original payload round-trips unchanged, replay yields one source/job/proposal, and preparation creates zero operational effects.
- **SC-002** Every negative acceptance case retains a refusal without foreign disclosure or invented values.
- **SC-003** Existing legacy Shopify intake and required repository checks remain green before completion is claimed.

## Requirement Traceability

| Requirement | Acceptance | Test |
| --- | --- | --- |
| FR-001/003 | Story1 original/value preservation and Story2 bounds | test_shopify_graphql_intake.py pure and original-roundtrip tests |
| FR-002/004/DR-001 | Story1 real proposal/no effects and Story2 missing/foreign mapping | test_shopify_graphql_intake.py service/MCP tests |
| FR-005/006 | Story1 replay and Story2 accepted identity refusal | test_shopify_graphql_intake.py replay/cross-type tests |
