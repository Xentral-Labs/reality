# Feature Specification: Intake decision coverage, demo and safe rollout

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

A common gate is ineffective if direct services, legacy adapters, live demo or setup keep writing accepted data outside it. Historical records cannot honestly be presented as having approvals that never occurred.

### Scope

Complete and test the writer coverage matrix, migrate live synthetic intake, retain narrow reviewed bootstrap/lesson behavior, define pending-job transition and preserve honest historical provenance with operational recovery.

### Non-Goals

Universal canonical-writer enforcement and another proposal/confirmation cycle for
direct authenticated human actions are outside this rollout.

No retroactive approval fabrication, tenant-purpose conversion, demo reseeding, new projection authority, source loss or deployment that silently enables a bypass.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Spec workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Owner's roadmap](../../docs/ideas/decision-gated-intake-plan.md)
- [146-company-setup-demo](../146-company-setup-demo/spec.md)
- [168-demo-order-to-cash](../168-demo-order-to-cash/spec.md)
- [249-web-mcp-review-parity](../249-web-mcp-review-parity/spec.md)
- [263-decision-trail](../263-decision-trail/spec.md)
- [323-proposal-decision-policy](../323-proposal-decision-policy/spec.md)
- [Dependency 356-decision-gated-intake](../356-decision-gated-intake/spec.md)
- [Dependency 357-shopify-reviewed-intake](../357-shopify-reviewed-intake/spec.md)
- [Dependency 358-reviewed-file-master-imports](../358-reviewed-file-master-imports/spec.md)
- [Dependency 359-reviewed-financial-intake](../359-reviewed-financial-intake/spec.md)
- [Dependency 360-bulk-intake-agent-review](../360-bulk-intake-agent-review/spec.md)

## User Scenarios & Testing

### User Story 1 - Prove all governed paths cross the boundary (Priority: P1)

Know that the same decision rule applies to UI, CLI, MCP, Chat, workers and direct application services.

**Why this priority**: A working Shopify path cannot stand in for complete admission coverage.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** an enumerated business writer and every caller family, **When** a bypass is attempted, **Then** accepted effects are refused without a valid matching decision context.
2. **Given** source/queue/audit persistence or derived read-time calculation, **When** it runs without business approval, **Then** it remains available without gaining authority to write accepted business records.

### User Story 2 - Run demo through the same admission (Priority: P1)

Observe live synthetic orders, invoices and payments receiving real decisions rather than special write privileges.

**Why this priority**: Demo must prove the production boundary, not a parallel shortcut.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a confirmed demo source with explicit scoped reviewer authority, **When** live intake occurs, **Then** it prepares and approves exact interpretations through shared services.
2. **Given** paused/revoked source or failed preparation, **When** work is retried, **Then** existing controls and markers are respected and no bypass or reseed occurs.
3. **Given** fixed profile initialization or read-only lesson Chat, **When** the new boundary is introduced, **Then** existing narrowly authorized initialization and read-only behavior remain intact.

### User Story 3 - Introduce the change without inventing history (Priority: P1)

Recover pending intake and understand old records honestly during deployment or rollback.

**Why this priority**: Changing admission must not lose sources or fabricate responsibility.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** historical records lacking an approval, **When** they are inspected after rollout, **Then** existing provenance remains and no human or agent approval is invented.
2. **Given** legacy queued jobs or in-flight work, **When** the new version starts, **Then** raw is retained and unapproved work becomes pending review rather than executing directly.
3. **Given** review unavailable or rollout reversed, **When** new raw data arrives, **Then** source capture continues while accepted effects wait and enforcement remains fail-closed.

### Edge Cases

- Foreign tenant identities at source, proposal, manifest, target and receipt reads.
- Duplicate source delivery, concurrent review/approval, stale state and token revocation.
- Invalid later content, interruption before/after commit and uncertain execution.
- Changed source versions, mappings, defaults or referenced records after review.
- Rejected/blocked work remains inspectable; read-only recovery never executes it.

## Requirements

### Functional Requirements

- **FR-001**: The coverage matrix MUST enumerate external intake sources, interpreter branches and adapter entrypoints with owning spec, enforcement point and executable proof. Manual human actions are classified separately and retain existing authorization and audit.
- **FR-002**: External intake through UI, CLI, MCP, Chat, workers and interpreter entrypoints MUST enforce the same approved-effect boundary. A direct authenticated human action is itself a decision; its canonical service call does not require an additional intake proposal.
- **FR-003**: Immutable raw intake, queue/audit writes and read-derived observations require no intake approval. Fixed confirmed setup/lesson initialization retains its existing exact authority. Direct authenticated human actions retain existing permissions and truthful audit attribution; none of these paths grants an agent or import unreviewed acceptance authority.
- **FR-004**: Continuous demo order/invoice/payment intake MUST use prepared proposals and exact authorized decisions; the current broader interpretation scope MUST NOT bypass admission.
- **FR-005**: Fixed confirmed profile/lesson initialization MAY use its existing narrow transaction-bound authority; its exact setup scope and effect attribution MUST be visible and must not authorize later arbitrary intake.
- **FR-006**: Source start/pause/stop, rate controls, deterministic upstream identities, completed-setup markers and worker transaction rules MUST remain preserved; retries MUST NOT override later source controls.
- **FR-007**: Historical documents/effects and immutable outcomes MUST remain unchanged; missing decision attribution MUST remain unknown/legacy rather than fabricated.
- **FR-008**: Cutover MUST drain or fence old workers, reclassify pending legacy jobs safely, and never let a new preparation-only result appear as an applied interpretation.
- **FR-009**: Rollback MUST preserve raw sources, proposals, approvals and receipts and keep governed admission fail-closed; disabling automatic review MUST NOT restore direct interpreter writes.
- **FR-010**: Operational reads MUST distinguish raw received, prepared, awaiting decision, review-required, applied, failed and unresolved; documentation/catalogs and required regression/migration checks MUST match actual behavior.

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

WriterCoverageRow: canonical writer, caller families, owning spec, enforcement, test and explicit exception. LegacyIntakeState: retained source/job history without fabricated approval. DemoAdmissionContext: production proposal/apply with the same source controls; fixed setup context remains narrowly distinct.

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
| FR-001 | US1 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_writer_inventory_has_no_unowned_path` | T003, T005, T004 |
| FR-002 | US1 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_all_transports_and_direct_calls_are_guarded` | T003, T005, T004 |
| FR-003 | US1 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_exceptions_cannot_be_reused_for_business_effects` | T003, T005, T004 |
| FR-004 | US2 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_live_demo_uses_real_decisions` | T006, T008, T009 |
| FR-005 | US2 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_bootstrap_scope_is_fixed` | T006, T008, T009 |
| FR-006 | US2 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_demo_controls_and_retry_markers_survive` | T006, T008, T009 |
| FR-007 | US3 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_historical_provenance_is_honest` | T010, T011, T012, T013 |
| FR-008 | US3 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_pending_job_cutover_is_safe` | T010, T011, T012, T013 |
| FR-009 | US3 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_rollback_preserves_decision_boundary` | T010, T011, T012, T013 |
| FR-010 | US3 | `packages/reality-core/tests/test_intake_rollout_coverage.py::test_status_and_documentation_are_truthful` | T010, T011, T012, T013 |
| DR-001, DR-002, DR-003, SC-001 | US1–US3, edge cases | `packages/reality-core/tests/test_intake_rollout_coverage.py` source/attribution, derived-state and tenant refusal matrix | T001, T002, T014, T015 |
| SC-002 | All | Required gates and final evidence review | T016 |

## Demo reviewer enrollment and fallback

Source connect/start and confirmed company creation do not implicitly create a
general agent mandate. New and existing live demos continue generating raw sources
and prepared proposals; without a configured authorized reviewer their accepted
business effects wait. The UI states **awaiting reviewer**, links to human decision
review and offers the owner the exact delegated-review setup from spec 360.
Connecting an external agent and confirming a scoped mandate are explicit actions.
After expiry/revocation, new units return to that waiting state; already committed
decisions remain valid. Pending source production is subject to existing saturation
controls, so missing review cannot create an unbounded backlog. Fixed historical
profile setup and its completion marker remain unchanged.

This fallback is part of FR-004/FR-006/FR-010. A running raw-data source must not be
displayed as successful order-to-cash acceptance when the reviewer is absent.

## Preparation-only legacy entrypoint result

FR-008/FR-010 change `process_import_job`, `process_shopify_import_job` and
`ingest_shopify_order` to return the retained prepared proposal for pending intake,
without accepted effects. The bound synthetic entrypoint has the same meaning and
preserves its caller transaction. Historical completed jobs lacking a retained
proposal return no new interpretation; their evidence and unknown attribution stay
unchanged. Import work reports prepared counts separately from completed acceptance.
Demo uses the `demo.order` pure profile plus the existing invoice/payment profiles.
Raw source connection scopes admit no document, commitment or financial effects.

FR-003/FR-005 fixed setup also covers legacy compact/month examples: their real
confirmed proposal freezes the authored profile version and date; private scope
binds its session/root transaction and cannot be reused by continuous intake.
Examples use source-stated values and shared pure plan/scoped effects. Anonymous
configuration-only first-workspace bootstrap never seeds business effects.


### Unstated commercial values during cutover

DR-001 also applies to delivery readiness. An accepted file order without a
source-stated gross total keeps that amount unknown. Standard delivery readiness
continues to derive operational stock/reservation conditions; a prepayment policy
blocks with `prepayment_amount_unstated` until reviewed stated evidence exists.
Required and remaining amounts remain null, never reconstructed from line prices.
The regression proof is `test_unstated_order_total_stays_unknown_in_delivery_readiness`.

## Independent defect retained from closed PR #352

FR-006 and spec 146 require Demo Data controls and shared worker transactions to
remain correct. Production/settlement workers and Pause currently acquire the two
schedules in opposite orders. Retain only the stable schedule/run/connection lock
ordering correction, with the genuine two-connection regression in
`tests/test_demo_schedule_lock_order.py`. It adds no decision layer, schema or
canonical-writer gate. Existing cancellation/revision/replay rules remain intact.

Plan Constitution Check: PASS; this restores existing source-control behavior.
Proof order: observe the real lock inversion before the fix; apply the two service
changes; verify the regression and existing scheduler/demo/import families.
