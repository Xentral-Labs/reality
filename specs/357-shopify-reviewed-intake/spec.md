# Feature Specification: Reviewed Shopify orders, changes and refunds

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

**Created**: 2026-10-03
**Status**: Specified; implementation pending
**Language**: English
**Input**: Owner approved reviewed external intake, including imported master data,
payments, changes and bulk processing. Direct authenticated human actions are decisions
and retain existing audit attribution without another approval cycle.

## Context and Intent

### Problem

Shopify first-order interpretation directly creates sales orders, lines and delivery commitments. Some later reductions and cancellations are applied automatically, and refund interpretation creates evidence and downstream changes without an exact prior decision.

### Scope

Prepare and review first orders, later source versions, cancellation and refund interpretations through the shared admission boundary while retaining source ordering, update safety, unknown-item behavior and lossless payloads.

### Non-Goals

Universal canonical-writer enforcement and another proposal/confirmation cycle for
direct authenticated human actions are outside this rollout.

No direct Shopify API integration, new shipment authority, refund payout execution, automatic acceptance of currently unsupported edits or inference of unprovided prices/totals.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Spec workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Owner's roadmap](../../docs/ideas/decision-gated-intake-plan.md)
- [081-shopify-update-guard](../081-shopify-update-guard/spec.md)
- [296-shop-order-changes](../296-shop-order-changes/spec.md)
- [263-decision-trail](../263-decision-trail/spec.md)
- [Dependency 356-decision-gated-intake](../356-decision-gated-intake/spec.md)

## User Scenarios & Testing

### User Story 1 - Review a newly received shop order (Priority: P1)

See the shop's exact order, references and promised lines before accepting it.

**Why this priority**: First imports are the clearest proof of the admission boundary.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a new shop order with known item lines, **When** it is processed, **Then** a pending order interpretation exists and no order or delivery promise exists yet.
2. **Given** an approved exact interpretation, **When** it is applied, **Then** one order with its lines and authorized promises is accepted, linked to source and decision.
3. **Given** unknown SKU, a non-shipping line or unstated price, **When** review is prepared, **Then** the exact uncertainty or absence is visible without invented items, promises or zero prices.

### User Story 2 - Review an upstream change (Priority: P1)

Inspect before/after meaning and effects of a later shop source version.

**Why this priority**: A lower quantity can affect reservations and completed work.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** an open order and a lower upstream quantity, **When** the version is processed, **Then** a pending change proposal shows the reductions and reservation consequences without applying them.
2. **Given** a stale or timestamp-conflicting delivery, **When** it is processed, **Then** the source is retained and no newer accepted order is overwritten.
3. **Given** a change the existing guard does not support, **When** a reviewer attempts approval, **Then** it remains review-required or refuses rather than becoming newly supported implicitly.

### User Story 3 - Review refunds and return announcements (Priority: P1)

Understand which refund evidence and operational changes the shop statement would introduce.

**Why this priority**: Evidence of a refund must not imply authorization to pay money.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a refund in an order payload, **When** its own source is prepared, **Then** refund evidence, reductions and possible return announcements are pending and visible.
2. **Given** an approved refund interpretation, **When** it is applied, **Then** only its authorized evidence and supported operational effects appear; no refund payment or ledger posting is invented.

### Edge Cases

- Foreign tenant identities at source, proposal, manifest, target and receipt reads.
- Duplicate source delivery, concurrent review/approval, stale state and token revocation.
- Invalid later content, interruption before/after commit and uncertain execution.
- Changed source versions, mappings, defaults or referenced records after review.
- Rejected/blocked work remains inspectable; read-only recovery never executes it.

## Requirements

### Functional Requirements

- **FR-001**: A first Shopify order MUST prepare evidence and delivery effects without creating accepted records; the old post-hoc shopify_order_interpreted action MUST NOT count as approval.
- **FR-002**: Review MUST show the resolved company/customer/location, source order and line identities, received currency/totals/prices/quantities, defaults and proposed commitments.
- **FR-003**: Unknown items, non-shipping lines and unstated prices MUST retain their current safe semantics; a reviewer MUST NOT gain a bypass for domain validation. An unstated source line amount MUST remain null in evidence and commitments and display as unknown. Source-provided zero or inconsistent amounts MUST remain exactly stated; manual authoring still requires its explicit amount. Reviewed credit checks MUST treat unknown amounts as unpriced exposure.
- **FR-004**: Approved first-order application MUST be atomic for the order and its lines/authorized commitments, tenant-scoped and idempotent. The transaction-bound executor MUST bind canonical operations and their exact invocation arguments, including omitted optional defaults, callbacks and nested effects; attribution alone MUST NOT authorize an additional write.
- **FR-005**: Previously automatic reductions and unshipped cancellations MUST require exact decision approval and show the current quantities, shipment/reservation state and planned effects.
- **FR-006**: Source ordering, equal-timestamp conflicts and stale versions MUST remain enforced at preparation and application. A newer arrival MUST invalidate an outdated offered review rather than silently substitute its payload.
- **FR-007**: Unsupported increases, new lines, commercial/address changes and reservation choices MUST retain the existing needs-review safeguards; admission approval alone MUST NOT implement unsupported change semantics.
- **FR-008**: Approved supported changes MUST use canonical revision/cancellation services, with current-state checks, one decision trail and all-or-nothing order-version application.
- **FR-009**: Refund payloads MUST remain separate immutable sources; their evidence and supported cancellation/return effects MUST be proposed before becoming accepted.
- **FR-010**: A Shopify refund interpretation MUST NOT create a financial posting or payout; supported return announcements and reductions MUST apply atomically with that refund unit and replay safely.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality wherever applicable, immutable
  lossless source payloads and received values. Review comparisons are observations,
  not replacement source authority. Use opaque IDs and shortest true links.
- **DR-002**: Documents MUST NOT own operational fulfilment, inventory or payment
  status; accepted operational state remains derived from Reality records.
- **DR-003**: All reads/writes MUST be tenant-scoped and all transports MUST use
  shared application services. Cross-tenant identities behave as not found and never
  become authority through caller-supplied actor or scope claims.

### Key Entities

ShopOrderPlan: one source version, resolved parties/location, evidence lines and proposed commitments. ShopChangePlan: current order review basis plus supported revisions/cancellations. ShopRefundPlan: independent refund source, evidence lines and supported operational announcements.

## Success Criteria

- **SC-001**: Every preparation/refusal scenario produces zero unapproved accepted
  business records; every approved coherent unit has exactly one truthful retained
  result and no duplicates after replay or concurrent settlement.
- **SC-002**: Every FR/DR has acceptance evidence, implementation tasks and executable
  verification; completion requires all required repository checks to pass.

## Assumptions and Dependencies

- The owner authorized this direction and autonomous preparation. These artifacts do not claim implementation, human review of an unseen design, release approval or verified runtime behavior.
- Existing business validation and stronger authorization remain in force; admitting a source does not authorize unsupported new business semantics.
- A coherent order is one unit; an item package is at most 500 rows; a manifest contains at most 500 independent units. These are different bounds, not interchangeable promises.
- Implement after the listed dependency contracts are available; adapter tests may use the shared typed plan contract before all other adapters are delivered.

## Requirement Traceability

| Requirement | Scenario(s) | Planned executable proof | Tasks |
| --- | --- | --- | --- |
| FR-001 | US1 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_first_order_waits_for_decision` | T003, T004, T005 |
| FR-002 | US1 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_review_preserves_received_values` | T003, T004, T005 |
| FR-003 | US1 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_unknown_and_unstated_lines_are_visible` | T003, T004, T005 |
| FR-004 | US1 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_approved_order_is_atomic_and_replay_safe` | T003, T004, T005 |
| FR-005 | US2 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_reductions_are_proposed_not_applied` | T006, T007, T008 |
| FR-006 | US2 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_older_version_cannot_replace_newer` | T006, T007, T008 |
| FR-007 | US2 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_unsupported_edits_still_refuse` | T006, T007, T008 |
| FR-008 | US2 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_changed_order_uses_canonical_services` | T006, T007, T008 |
| FR-009 | US3 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_refund_interpretation_waits_for_decision` | T009, T010, T011 |
| FR-010 | US3 | `packages/reality-core/tests/test_shopify_intake_admission.py::test_refund_is_not_payment_authority` | T009, T010, T011 |
| DR-001, DR-002, DR-003, SC-001 | US1–US3, edge cases | `packages/reality-core/tests/test_shopify_intake_admission.py` source/attribution, derived-state and tenant refusal matrix | T001, T002, T012, T013 |
| SC-002 | All | Required gates and final evidence review | T014 |

### User audit review clarification (2026-10-04)

FR-002 review proof presents each prepared business effect once, preserving all
arguments and collapsed technical inspection. Single-source review and selected
batch children expose original source/file downloads. Known line-level missing
amounts/prices and unknown items use readable notices and one-based line positions;
unknown issue codes remain visible. Exact digest confirmation is unchanged.
