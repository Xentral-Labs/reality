# Feature Specification: Reviewed existing buyer mapping for a retained Shopify source

**Feature Branch**: `389-shopify-source-buyer-mapping`
**Created**: 2026-11-09
**Language**: English
**Status**: Reviewed bounded scope under Tobias's explicit authorization

## User Scenarios & Testing

### User Story 1 - Select an existing customer without changing business Reality (Priority: P1)
An operator asks Tuesday Main to resolve the retained order's missing Reality buyer mapping. The assistant searches existing same-company active customers and prepares an exact mapping-only human review. It cannot create a customer or approve its own proposal.

**Acceptance Scenarios**:
1. A bounded search returns only existing active customer-role identities and useful labels, with fresh record digests and exact retained source/job binding; no email/address is needed.
2. Selection of an observed opaque candidate yields a frozen review containing the original source/hash/integer version and chosen customer's identity/label/digest.
3. Foreign, inactive, non-customer, changed or fabricated candidates and stale source/job bindings are refused without new records or disclosure.

### User Story 2 - Record only the exact human-confirmed mapping (Priority: P1)
A person explicitly confirms the existing-customer choice in Main. Tuesday's trusted host attests that exact human decision; Reality verifies it and retains an immutable mapping-only receipt.

**Acceptance Scenarios**:
1. A valid exact short-lived human-review proof records one mapping receipt and original approval Source. Original Shopify Source and frozen job input remain unchanged.
2. A manual submission token, model message, approved=true, invalid/wrong/replayed signature, other tenant/subject/review/digest, expired review or changed source/customer cannot approve a mapping.
3. Exact retry returns the same receipt. Concurrent approval or a second customer for the original source cannot remap it silently.
4. Source job remains review-required with explicit buyer_mapping_recorded_intake_pending outcome. No sales order, customer, stock, payment or fulfillment is created or accepted.

## Context and Intent

### Problem
The retained Shopify selection does not establish the upstream buyer; the actual missing input is an explicit existing Reality customer mapping. Replaying source capture cannot rewrite frozen mapping, and old99 has no full reviewed intake subsystem.

### Scope
Existing-customer selection, exact mapping review, trusted Main human confirmation, immutable mapping/approval evidence and readback for one host-pinned retained source/job. Use current and old99 common records and services.

### Non-Goals
New customers, original-source rewriting, ImportJob.input changes, upstream buyer inference, generic approval authority, accepted sales orders, full intake interpretation, remapping, payment, fulfillment, inventory effects, broader Shopify scopes, schema migration, global workers or deployment.

## Requirements

- **FR-001** Search only existing active same-company customer-role identities; return bounded labels/digests without unnecessary personal fields.
- **FR-002** Prepare a frozen mapping-only review bound to exact current source/job/hash/positive integer version and fresh customer digest; stable nonce replay cannot silently refresh or change it.
- **FR-003** Commit only a strict Ed25519 exact-review proof from a pinned issuer/key/allowed external subject, minted by Main only after explicit authenticated human approval. Models and manual submission tokens are never approvers.
- **FR-004** Recheck current source selection, job association, customer eligibility/digest, policy/proof/review expiry and submitter authority after waits; changed basis fails closed.
- **FR-005** Retain raw approval proof and frozen review as immutable original Source; record mapping-only Action output with truthful external attribution, never an invented Reality user.
- **FR-006** Exact retries are idempotent; concurrent approvals and attempted remapping cannot produce a second choice for the original source.
- **FR-007** Preserve original Shopify payload/hash/version/pointer and ImportJob.input. Keep review_required and append a named needs_review outcome distinguishing chosen buyer from full intake.
- **FR-008** Candidate/prepare/status are narrow source-bound capabilities; privileged commit is not model-admitted. Generic approve/execute cannot execute this proposal type.
- **DR-001** Reuse existing SourceRecord/SourceStream, ChangeProposal and InterpretationOutcome records with normal tenant services; no new tables/columns or direct adapter ORM business writes.

## Assumptions and Dependencies
Tobias explicitly authorizes mapping-only review/approval of the existing retained test source. A trusted private host policy pins exact tenant/source/job/shop/order and public Main issuer authority. The private signing key remains Tuesday-host-only. Customer absence in an unselected Shopify field is unknown, not customerless evidence. Full future intake must consume separately reviewed mapping evidence through a new explicit preparation contract, not mutation of old job input.

## Success Criteria
- **SC-001** Eligible customer selection and exact signed approval produce one auditable mapping receipt while all original-source/job-input values and business-record counts stay unchanged.
- **SC-002** All authority/basis/signature/concurrency negatives refuse without accepted effects or foreign disclosure.
- **SC-003** Current-code isolated tests and version-pinned old99 overlay proof pass before live readiness is claimed; CI/reviewer gates remain explicit.

## Requirement Traceability

| Requirements | Scenarios | Tests/tasks |
| --- | --- | --- |
| FR-001/002/004 | Story1 selection and stale basis | T002/T004 candidate/preparation/tenant tests |
| FR-003/005/008 | Story2 exact human proof and truthful attribution | T003/T005 signature/MCP/generic-approval tests |
| FR-006/007/DR-001 | Story2 replay/concurrency/no business effects | T003/T004 idempotency/immutable-source/old99 proof |
