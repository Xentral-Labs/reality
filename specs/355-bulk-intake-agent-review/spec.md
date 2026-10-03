# Feature Specification: Bulk intake settlement and delegated agent review

**Created**: 2026-10-03
**Status**: Specified; implementation pending
**Language**: English
**Input**: Owner requested decision-gated interpretation across imports, master data,
payments and changes, explicitly included bulk processing, and authorized autonomous
specification/planning and careful verification in this conversation.

## Context and Intent

### Problem

One item CSV proposal can already cover a small package, but no general multi-proposal bulk approval exists. Current policy does not grant autonomous agent delegation, and scheduled handlers cannot perform provider calls or commit business transactions themselves.

### Scope

Exact batch review and settlement, bounded durable processing, revocable unattended external-agent intake review, truthful attribution, operator recovery and measurable volume verification. Reuse existing scheduler/worker only for database-bound preparation and already-authorized apply.

### Non-Goals

No blanket approve-all filter, unrestricted background authority, new timer/queue engine, network calls inside transaction-bound scheduled handlers, removal of built-in Chat confirmation restrictions or weakening of finance permissions.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Spec workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Owner's roadmap](../../docs/ideas/decision-gated-intake-plan.md)
- [129-unified-item-csv-import](../129-unified-item-csv-import/spec.md)
- [249-web-mcp-review-parity](../249-web-mcp-review-parity/spec.md)
- [263-decision-trail](../263-decision-trail/spec.md)
- [273-stale-review-refresh](../273-stale-review-refresh/spec.md)
- [274-chat-agent-decisions](../274-chat-agent-decisions/spec.md)
- [278-human-chat-confirmation](../278-human-chat-confirmation/spec.md)
- [323-proposal-decision-policy](../323-proposal-decision-policy/spec.md)
- [325-readable-proposal-reviews](../325-readable-proposal-reviews/spec.md)
- [Dependency 351-decision-gated-intake](../351-decision-gated-intake/spec.md)

## User Scenarios & Testing

### User Story 1 - Review and approve a fixed batch (Priority: P1)

Select exact packages or independent decisions, inspect every unit and settle them without per-row clicks.

**Why this priority**: Scale must not weaken exact consent or coherent-unit atomicity.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a fixed set of 500 pending order proposals, **When** batch review is prepared, **Then** complete paginated membership, exact digests and all exception summaries are available.
2. **Given** a reviewed manifest with mixed valid/stale/invalid units, **When** approval proceeds, **Then** eligible independent units complete and every other unit has an honest result.
3. **Given** a newly arriving proposal or renewed child review, **When** the old manifest is approved, **Then** the arrival is excluded and the changed child review is not silently accepted.

### User Story 2 - Delegate review with a narrow mandate (Priority: P1)

An owner permits a named external agent to inspect and decide specific intake types within explicit limits.

**Why this priority**: A technical confirmation permission is not autonomous business authority.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** an owner-issued active mandate and named agent token, **When** the agent reviews the full source and exact proposal, **Then** it can settle only covered effects and attribution identifies the token and mandate.
2. **Given** uncertainty, prompt injection, expired/revoked mandate or uncovered effect, **When** the agent tries to decide, **Then** it receives a coded refusal or human-review handoff without business effects.
3. **Given** an ordinary built-in Chat request, **When** confirmation is attempted, **Then** current human-review restrictions remain; background delegation is not inherited from chat text.

### User Story 3 - Recover and measure large intakes (Priority: P1)

See partial progress, recover after interruption and verify that thousands of records can pass without manual per-record work.

**Why this priority**: Correctness and measured throughput must be proved together.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** 5,000 items in ten packages or 500 five-line orders, **When** controlled automated review and settlement runs, **Then** exact result counts are produced without per-record interaction and no preapproval effects.
2. **Given** interruption or concurrency at chunk boundaries, **When** processing resumes, **Then** there are zero duplicate or partially accepted units and every exception remains inspectable.

### Edge Cases

- Foreign tenant identities at source, proposal, manifest, target and receipt reads.
- Duplicate source delivery, concurrent review/approval, stale state and token revocation.
- Invalid later content, interruption before/after commit and uncertain execution.
- Changed source versions, mappings, defaults or referenced records after review.
- Rejected/blocked work remains inspectable; read-only recovery never executes it.

## Requirements

### Functional Requirements

- **FR-001**: Batch preparation MUST freeze at most 500 exact proposal IDs and their review digests; duplicate IDs, foreign IDs and open-ended filters MUST NOT form executable membership.
- **FR-002**: Review MUST provide complete paginated membership and proposed effects, all exclusion/issue counts and exact source links. A sample or aggregate alone MUST NOT substitute for the review basis.
- **FR-003**: One bulk confirmation MUST retain a distinct decision/receipt per independent child, preserve each child's stronger authority and keep atomicity per semantic unit. An atomic package MUST NOT become row-by-row partial writes.
- **FR-004**: Execution MUST be bounded to at most 25 independent units per run, reconcile uncertain outcomes, and resume from retained receipts without changing membership or repeating completed effects. Durable continuation configuration MUST contain only the parent ID, manifest revision and opaque continuation ID, never member payloads. A stale completed continuation MUST produce a zero-effect replay and MUST NOT enqueue new work.
- **FR-005**: Stopping a batch MUST prevent future chunk claims while retaining committed results; an already claimed bounded chunk may finish. Original reviewer authority and source/review freshness MUST be checked for each unexecuted unit, and subsequent chunks MUST honor committed revocation.
- **FR-006**: Unattended review MUST require an explicit owner-issued, revocable, expiring mandate bound to tenant, named agent identity, exact source/profile scope, permitted effects, finite rows per unit and units per UTC day, and finite per-unit/daily source-stated amount limits in one currency for financial effects. Concurrent batches MUST NOT evade those limits.
- **FR-007**: The reviewer MUST compare the complete source with the exact prepared meaning and effects, retain a structured verdict/reasons and deterministic validation results, and escalate uncertain or contradicted meaning.
- **FR-007a**: Named agents MUST be able to read the complete original source payload and artifact through bounded 64 KiB byte pages outside database-only workers. Structured coverage MUST name every original byte range and relevant original row/line identity, with exact source and plan hashes; summaries MUST NOT substitute for complete source assessment. Coverage claims establish binding, not proof of cognitive understanding. Oversized review sources MUST escalate rather than silently truncate.
- **FR-008**: Agent decisions MUST name actual token identity and mandate version without inventing human approval. Source content and model output MUST NOT grant permissions or alter the reviewed manifest.
- **FR-009**: Mandate and token/issuer authority MUST be checked at decision and execution; finance effects MUST retain applicable owner requirements. Ordinary built-in Chat and read-only Sandbox restrictions MUST remain unchanged.
- **FR-010**: External assessment MUST occur outside the existing database-only scheduled handler contract. Scheduled processing may prepare work or apply a retained exact authorized verdict, but MUST NOT call a provider or commit internally.
- **FR-011**: Web, MCP and CLI MUST use the same exact-review and bulk services; status/reload MUST be read-only and report pending, executed, rejected, stale, failed and unresolved units distinctly.
- **FR-012**: Volume verification MUST include 5,000 items and 500 five-line orders, mixed failures and restart/concurrency; it MUST measure preparation, review and apply separately with declared environment, bounded memory and per-run deadlines.
- **FR-013**: Controlled bulk apply per-record median time and query count MUST be at most 1.5 times the same-environment repeated single-unit baseline; measurements MUST use three runs and show all counts. Provider latency/cost MUST be reported separately, not hidden in local throughput claims.

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

IntakeBatch: fixed child identities/digests, confirmation and durable progress/results. IntakeReviewMandate: current scoped authority linked to the granting decision and named token. AgentReviewEvidence: exact source/plan digest, deterministic results, reviewer verdict and mandate revision. ChildDecision: own effects, attribution and receipt.

## Success Criteria

- **SC-001**: Every preparation/refusal scenario produces zero unapproved accepted
  business records; every approved coherent unit has exactly one truthful retained
  result and no duplicates after replay or concurrent settlement.
- **SC-002**: Every FR/DR has acceptance evidence, implementation tasks and executable
  verification; completion requires all required repository checks to pass.
- **SC-003**: The 5,000-item and 500-order workloads complete with exact counts,
  no per-record manual interaction, recoverable bounded processing and the measured
  performance/resource budgets in the plan. Live provider cost/latency is reported
  separately from controlled automated-verdict throughput.

## Assumptions and Dependencies

- The owner authorized this direction and autonomous preparation. These artifacts do not claim implementation, human review of an unseen design, release approval or verified runtime behavior.
- Existing business validation and stronger authorization remain in force; admitting a source does not authorize unsupported new business semantics.
- A coherent order is one unit; an item package is at most 500 rows; a manifest contains at most 500 independent units. These are different bounds, not interchangeable promises.
- Implement after the listed dependency contracts are available; adapter tests may use the shared typed plan contract before all other adapters are delivered.

## Requirement Traceability

| Requirement | Scenario(s) | Planned executable proof | Tasks |
| --- | --- | --- | --- |
| FR-001 | US1 | `packages/reality-core/tests/test_bulk_intake_review.py::test_manifest_is_fixed_and_tenant_scoped` | T003, T005, T006, T007 |
| FR-002 | US1 | `packages/reality-core/tests/test_bulk_intake_review.py::test_review_covers_every_member` | T003, T005, T006, T007 |
| FR-003 | US1 | `packages/reality-core/tests/test_bulk_intake_review.py::test_bulk_settlement_preserves_child_authority` | T003, T005, T006, T007 |
| FR-004 | US1 | `packages/reality-core/tests/test_bulk_intake_review.py::test_bounded_runs_resume_exactly` | T003, T005, T006, T007 |
| FR-005 | US1 | `packages/reality-core/tests/test_bulk_intake_review.py::test_stop_and_revocation_affect_remaining_units` | T003, T005, T006, T007 |
| FR-006 | US2 | `packages/reality-core/tests/test_bulk_intake_review.py::test_mandate_scope_is_enforced` | T008, T009, T011, T013 |
| FR-007 | US2 | `packages/reality-core/tests/test_bulk_intake_review.py::test_reviewer_checks_source_not_only_summary` | T008, T009, T011, T013 |
| FR-008 | US2 | `packages/reality-core/tests/test_bulk_intake_review.py::test_agent_attribution_and_injection_boundaries` | T008, T009, T011, T013 |
| FR-009 | US2 | `packages/reality-core/tests/test_bulk_intake_review.py::test_authority_revocation_and_chat_limits` | T008, T009, T011, T013 |
| FR-010 | US2 | `packages/reality-core/tests/test_bulk_intake_review.py::test_scheduled_handler_remains_database_only` | T008, T009, T011, T013 |
| FR-011 | US3 | `packages/reality-core/tests/test_bulk_intake_review.py::test_surfaces_share_bulk_semantics` | T014, T015, T016 |
| FR-012 | US3 | `packages/reality-core/tests/test_bulk_intake_review.py::test_volume_workloads_and_resource_bounds` | T014, T015, T016 |
| FR-013 | US3 | `packages/reality-core/tests/test_bulk_intake_review.py::test_bulk_has_measured_nonregression` | T014, T015, T016 |
| DR-001, DR-002, DR-003, SC-001 | US1–US3, edge cases | `packages/reality-core/tests/test_bulk_intake_review.py` source/attribution, derived-state and tenant refusal matrix | T001, T002, T017, T018 |
| SC-002 | All | Required gates and final evidence review | T019 |
| SC-003 | US3 | `reality.benchmarks.intake` and volume/restart tests | T014, T016, T019 |

## Delegated batch execution-time permission

FR-005/FR-006 require each queued delegated child to re-read the actual token's
current permission for `intake_agent_batch_review_and_queue`. The original parent
review and cached transport principal cannot substitute for that permission.
Removing it after submission makes remaining children review-required without
accepted effects. Each retained child verdict binds the fixed ordered manifest,
current mandate revision, original source coverage and exact prepared digest.
### Bulk transport details

FR-011 includes explicit pending-source selection in Decisions, capped at 500
retained proposal identities/digests and cleared on company change. Preparing a
batch never approves it or selects future arrivals. Review and results are paged
at at most 100 units; each child exposes its exact meaning and complete original
source download/artifact link. Current progress, no-effect refusals and receipts
remain visible, and stop affects further units only. Trusted local CLI exposes the
same prepare/review/confirm/status/stop services; confirmation and stop require an
explicit current member identity, and confirmation includes the exact digest.

## Original mandate decision integrity

FR-005/FR-006 require every material read and settlement to compare the current
mandate's normalized scope, named token, expiry and active revision with the exact
executed owner grant. Editing the retained mandate cannot enlarge or replace that
grant. Revocation remains a separate confirmed decision, not scope renewal. Tests
must issue genuine narrower owner grants when testing commercial limits, rather
than mutating a mandate after approval.
