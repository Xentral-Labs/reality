# Feature Specification: Decision-gated interpretation and admission

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

Registered interpreters currently create accepted evidence and operational records while interpreting a source. A later audit entry is not prior approval. The common boundary must protect the meaning accepted from a source before that meaning becomes business authority.

### Scope

A prepared interpretation, exact-review confirmation, transaction-bound application and a shared bulk contract. Inventoried intake writers are classified before enforcement; source storage, audit records and read-time observations remain outside business-effect admission.

### Non-Goals

Universal canonical-writer enforcement and another proposal/confirmation cycle for
direct authenticated human actions are outside this rollout.

No provisional business documents, inferred source amounts, provider integration, printed document production, retrospective approvals or new general workflow engine.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Spec workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Owner's roadmap](../../docs/ideas/decision-gated-intake-plan.md)
- [005-source-ingestion](../005-source-ingestion/spec.md)
- [059-safe-proposal-confirmation](../059-safe-proposal-confirmation/spec.md)
- [129-unified-item-csv-import](../129-unified-item-csv-import/spec.md)
- [263-decision-trail](../263-decision-trail/spec.md)
- [273-stale-review-refresh](../273-stale-review-refresh/spec.md)
- [323-proposal-decision-policy](../323-proposal-decision-policy/spec.md)

## User Scenarios & Testing

### User Story 1 - Prepare meaning without accepting it (Priority: P1)

Receive and inspect a source and proposed interpretation without changing the company's accepted evidence or operational state.

**Why this priority**: Preserving source truth is useful even when interpretation is wrong.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** an immutable received source, **When** interpretation is prepared, **Then** a reviewable proposal exists and no accepted Document, DocumentLine, master record or Reality effect has been created.
2. **Given** missing or ambiguous required meaning, **When** preparation is attempted, **Then** the raw source remains available with a coded review issue and zero business effects.

### User Story 2 - Accept exactly the reviewed interpretation (Priority: P1)

Approve or reject one exact proposal and obtain an honest execution receipt.

**Why this priority**: The decision must authorize the effect before it happens.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** an exact pending proposal and current authorized reviewer, **When** its offered review is approved, **Then** the evidence, effects, decision attribution and receipt become durable together exactly once.
2. **Given** a changed source, reference, proposal or reviewer authority, **When** confirmation is attempted, **Then** it refuses without business effects and explains whether renewed review is required.
3. **Given** a crash or concurrent confirmation, **When** the operator retries, **Then** the retained receipt is returned or no effects exist; no duplicate or partial unit is accepted.

### User Story 3 - Review many fixed units (Priority: P1)

Review an exact import package or fixed set of independent proposals without per-row clicks.

**Why this priority**: Bulk must preserve the same authorization and atomicity as a single decision.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a reviewed package with fixed membership, **When** one decision approves it, **Then** the complete package succeeds or no part becomes accepted.
2. **Given** a manifest of independent proposals including an invalid unit, **When** bulk settlement runs, **Then** unrelated valid units can complete and every unit has an explicit result.
3. **Given** new arrivals or interruption, **When** the same batch resumes, **Then** membership does not expand and already committed units are not applied again.

### Edge Cases

- Foreign tenant identities at source, proposal, manifest, target and receipt reads.
- Duplicate source delivery, concurrent review/approval, stale state and token revocation.
- Invalid later content, interruption before/after commit and uncertain execution.
- Changed source versions, mappings, defaults or referenced records after review.
- Rejected/blocked work remains inspectable; read-only recovery never executes it.

## Requirements

### Functional Requirements

- **FR-001**: Store sources losslessly before interpretation; source storage and queue/audit writes MUST NOT require a business-effect approval.
- **FR-002**: Preparation MUST create a pending proposal describing evidence, resolved references, proposed effects, defaults and uncertainties, without creating accepted business records.
- **FR-003**: A proposal MUST bind the exact source versions, artifact content, mapping, interpreter version and relevant current reference state; confirmation MUST NOT silently reinterpret its meaning.
- **FR-004**: Confirmation MUST recheck current permission and relevant state against the exact offered review; arbitrary action IDs, booleans and conversation claims MUST NOT grant execution authority.
- **FR-005**: Evidence, Reality effects, attribution, outcome references and execution receipt MUST commit atomically per approved unit; no-effect refusal MUST leave no partial business records.
- **FR-006**: Rejected, stale, failed, awaiting-decision and successfully applied interpretations MUST remain distinguishable. New phase outcomes MUST receive unique monotonic attempt numbers without overwriting immutable history; replay MUST return retained results without appending another phase or invoking a mutating interpreter.
- **FR-006a**: Known preparation failures MUST retain a prepare-phase outcome and safe reason without automatic business execution. Explicit renewed review MUST name the previous proposal and an idempotent request identity, preserve earlier immutable plans, and make earlier unaccepted reviews stale. Completed receipts MUST NOT be reinterpreted. Renewal creates proposed meaning only and requires its own exact decision. Unknown infrastructure failures MUST propagate with their transaction rolled back.
- **FR-007**: Accepted external intake MUST use a server-established effect scope bound to the tenant, transaction, proposal and approved operations; external adapters and interpreters MUST NOT bypass it. This does not require a second proposal for direct authenticated human actions.
- **FR-008**: One package decision and batch settlement of independent decisions MUST be distinct modes. Package membership MUST be fixed before review; regrouping MUST require a new review.
- **FR-009**: Batch approval MUST name exact proposal IDs and review digests, retain per-unit authorization and receipts, and isolate failures only across independent units.
- **FR-010**: Preparation and execution MUST be bounded, recoverable and idempotent; unresolved outcomes MUST be reconciled before any redispatch. Bulk progress MUST NOT authorize unreviewed effects.

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

PreparedIntake: versioned non-authoritative meaning, immutable source/artifact references, opaque resolved targets, current-state review basis and planned effects. ChangeProposal: exact unit with pending/executed/rejected lifecycle, review and receipt. ImportJob/InterpretationOutcome: retained source-processing history with prepared/review-required/applied classifications. ApprovedEffectScope: ephemeral internal transaction capability, never persisted as business authority.

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
- This is the shared foundation; transport/adapter rollout is completed by specs 357–361, and a first Shopify slice must not be claimed as universal coverage.

## Requirement Traceability

| Requirement | Scenario(s) | Planned executable proof | Tasks |
| --- | --- | --- | --- |
| FR-001 | US1 | `packages/reality-core/tests/test_intake_admission.py::test_raw_survives_prepare_failure` | T003, T004, T005 |
| FR-002 | US1 | `packages/reality-core/tests/test_intake_admission.py::test_preparation_has_no_business_effects` | T003, T004, T005 |
| FR-003 | US1 | `packages/reality-core/tests/test_intake_admission.py::test_mapping_and_source_are_frozen` | T003, T004, T005 |
| FR-004 | US2 | `packages/reality-core/tests/test_intake_admission.py::test_stale_or_forged_approval_refused` | T006, T010, T008, T009 |
| FR-005 | US2 | `packages/reality-core/tests/test_intake_admission.py::test_effects_and_receipt_are_atomic` | T006, T010, T008, T009 |
| FR-006 | US2 | `packages/reality-core/tests/test_intake_admission.py::test_outcomes_and_replay_are_truthful` | T006, T010, T008, T009 |
| FR-007 | US2 | `packages/reality-core/tests/test_intake_admission.py::test_direct_writer_and_scope_reuse_refused` | T006, T010, T008, T009 |
| FR-008 | US3 | `packages/reality-core/tests/test_intake_admission.py::test_package_and_batch_modes_are_distinct` | T011, T012, T013 |
| FR-009 | US3 | `packages/reality-core/tests/test_intake_admission.py::test_mixed_batch_has_exact_results` | T011, T012, T013 |
| FR-010 | US3 | `packages/reality-core/tests/test_intake_admission.py::test_batch_resume_does_not_duplicate` | T011, T012, T013 |
| DR-001, DR-002, DR-003, SC-001 | US1–US3, edge cases | `packages/reality-core/tests/test_intake_admission.py` source/attribution, derived-state and tenant refusal matrix | T001, T002, T014, T015 |
| SC-002 | All | Required gates and final evidence review | T016 |

## Integration acceptance: company calendar

FR-002/FR-005 and DR-001 reuse spec 349's company-calendar contract: source instants
are reviewed as the company's local business day. A changed calendar statement
invalidates that offered review; confirmation never silently derives a different
day. Regression proof: `test_intake_admission.py::test_prepared_shop_day_uses_and_freezes_the_company_calendar`.


The renewed-review service is also exposed through the Web intake-unit endpoint.
Preparing renewed meaning preserves the prior immutable plan and creates no
business effects; the resulting proposal requires separate exact confirmation.
The Web discards previous proposal content while a different proposal loads.
