# Feature Specification: Intake decision coverage, demo and safe rollout

**Created**: 2026-10-03
**Status**: Specified; implementation pending
**Language**: English
**Input**: Owner requested decision-gated interpretation across imports, master data,
payments and changes, explicitly included bulk processing, and authorized autonomous
specification/planning and careful verification in this conversation.

## Context and Intent

### Problem

A common gate is ineffective if direct services, legacy adapters, live demo or setup keep writing accepted data outside it. Historical records cannot honestly be presented as having approvals that never occurred.

### Scope

Complete and test the writer coverage matrix, migrate live synthetic intake, retain narrow reviewed bootstrap/lesson behavior, define pending-job transition and preserve honest historical provenance with operational recovery.

### Non-Goals

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
- [Dependency 351-decision-gated-intake](../351-decision-gated-intake/spec.md)
- [Dependency 352-shopify-reviewed-intake](../352-shopify-reviewed-intake/spec.md)
- [Dependency 353-reviewed-file-master-imports](../353-reviewed-file-master-imports/spec.md)
- [Dependency 354-reviewed-financial-intake](../354-reviewed-financial-intake/spec.md)
- [Dependency 355-bulk-intake-agent-review](../355-bulk-intake-agent-review/spec.md)

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

- **FR-001**: The coverage matrix MUST enumerate catalogued mutation tools, canonical writers, interpreter branches and adapter entrypoints with owning spec, enforcement point, executable proof and any explicit exception.
- **FR-002**: UI, CLI, MCP, Chat, workers and direct canonical service/interpreter entrypoints MUST enforce the same approved-effect boundary for governed writes; auth-disabled/admin context MUST NOT bypass business approval.
- **FR-003**: Exceptions MUST be narrow and tested: immutable raw intake, queue/audit writes, read-derived observations and fixed confirmed setup/lesson initialization only; they MUST NOT grant subsequent operational mutation authority.
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
review and offers the owner the exact delegated-review setup from spec 355.
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

### Canonical master-data confirmation (FR-001–FR-003)

Party, Item and Location creation and updates cross the approved-effect boundary
at their canonical single-record writers, including callers that supply an
arbitrary action tag or run with authentication disabled. A private execution
scope binds the retained proposal, exact input, company, Session and root
transaction to the actual explicit confirmation; it must not authorize changed
callback arguments, a repeated canonical invocation or an intermediate commit.
Bulk master operations retain all records and their execution receipt in the
same root transaction. CLI create/update commands display the proposal and require
confirmation; `--yes` states the operator's explicit confirmation for scripted use.

Existing application identity policy remains in force. Named approvers are
rechecked against their current membership. A trusted local CLI confirmation
retains its real decision time and leaves unavailable person identity unnamed;
no synthetic person is invented. Authentication-disabled context alone grants
no canonical write authority.

Confirmed ordinary company creation may record exactly its own company partner
with the exact confirmed request and durable creation receipt in the same root
transaction. Its private authority does not permit a second partner, changed
intent, an intermediate commit or subsequent operational writes.

Canonical master effects recheck the retained confirming MCP token at the effect boundary, including current revocation and confirmation permissions. Historical token attribution remains separate from current execution authority.

Finance configuration applies only within the actual confirmed retained command
and its atomic locked transaction. Confirmation must not be inferred from an
action ID, caller-supplied actor, an earlier source/queue permission or a fabricated
executing claim. Fixed account defaults are initialization, and never authorize
arbitrary later account creation, update or default changes.

The confirmed account catalog preserves all existing registered account roles, including received down payments and realised exchange differences. Canonical configuration rechecks current Owner role even when an older ORM membership object remains cached.

An account confirmation grants only its canonical account maintenance and audit operations. It must not admit unrelated Documents, Movements or other business writes through callbacks; those require their own approved unit and transaction.

### Normalized document admission qualification (FR-001–FR-003)

Direct creation of normalized Document/DocumentLine evidence requires the current
retained confirmation for its exact document-producing application command, or
the existing exact intake/fixed preset authority. An arbitrary action identity
never supplies this authority. Manual document creation records supplied lines
and amounts only; it does not fabricate a line for header-only evidence. Header
writers and document corrections remain separately tracked until qualified.

## Atomic manual order qualification (FR-001–FR-003)

The existing order_create confirmation covers the exact retained manual payload,
its immutable source, normalized evidence, line-linked promises and applicable
credit holds. Its handler cannot change the payload, repeat the invocation, add
unrelated effects or commit before the executed receipt is ready. A callback
failure rolls back all new source/evidence/promises. No source value is derived.

## Atomic invoice qualification (FR-001–FR-003)

Existing sales_invoice_record, supplier_invoice_record and
supplier_invoice_free_record confirmations cover the exact retained payload and
its source, evidence, postings and offsets. These database-only commands settle
with their executed receipts; callbacks cannot change/repeat a parent invocation
or commit accepted evidence before receipt completion. Callback failure leaves
no new accepted evidence, postings or manual source. Credit families remain a
separate qualification slice.
## Current interactive MCP confirmation authority (FR-003)

A synchronous confirmation received through interactive MCP retains its actual
verified request principal within the application transaction. Before canonical
effects, its credential and consent grant must still be current, unrevoked,
unexpired, belong to the same real user/company/client and permit the actual
confirmation tool/scope. Dispatch-time authentication alone is insufficient.
HTTP/CLI and existing manual-token decision behavior remains unchanged. No
credential, grant, principal or consent is manufactured.
## Live source control lock-order regression (FR-005)

Production and settlement workers and source controls must acquire both actual
Demo Data schedule locks in the same stable order before unfinished run and
connection locks. A settlement worker must not retain its own schedule before
waiting for the production schedule. Pause keeps the existing unfinished-run
409/retry behavior and never returns a deadlock-induced 500 or cancels dispatched
work. Keep actual current revisions and request-key replay intact.
## Atomic customer credit qualification (FR-001–FR-003)

The existing sales_credit_record confirmation must own the invoice-linked and
legacy return-credit parent, normalized evidence, exact credit posting and optional
explicit settlement allocation in one root transaction. Freeze each canonical
invocation before callbacks. Changed or repeated calls, early root commits,
post-write failures and unrelated header/stock effects refuse without partial
business records. Preserve stated totals, position values, reason and netting;
confirmation grants neither refund nor inventory authority. Existing historical
records receive no manufactured approval. Supplier credit posting remains a
separate writer qualification, not coverage claimed by this family.
## Fixed new-company reference exception (FR-003)

The fixed base-account initializer may write only the authored reference accounts
and initial FinanceState for the exact newly inserted company in the same root
transaction. It must refuse existing companies, changed company identity,
repeated initialization, early root commit and post-write failure. Ordinary and
Playground/storyline creation use the same initializer. This structural exception
creates no financial posting, person approval or authority for later account
configuration. Historical migration specimens remain historical.
## Confirmed commercial master data (FR-001–FR-003)

Payment term and price-list creation/update, price tiers, pricing groups and
their membership/list assignments must use the existing retained application
decision. Direct canonical writes, absent confirmation, changed/repeated calls,
early root commits, post-write failures and unrelated business effects refuse.
REST and CLI must prepare the actual stated input and confirm using the actual
request principal or explicit CLI action. Keep existing identifiers, stated
discount/maturity/price/quantity/priority values, tenant scope and receipt replay.
Fixed confirmed demo/lesson reference definitions use their existing narrow scope
and frozen authored invocation; they never fabricate a person approval. Raw
source references, lifecycle activation and other writer families remain separate
qualifications, not claimed complete by this group.
Commercial proposals also retain the exact current tenant-scoped referenced
records as non-authoritative review basis. Changed references require renewed
review before any effect; callers may not supply or overwrite that private basis.

### Current authority for fixed confirmed application profiles (FR-003)

The existing demo_seed and normal_month confirmed application profiles must
recheck their actual current confirming person, manual token and interactive
MCP consent before canonical writes. Fixed authored input does not exempt a
revoked or expired confirmation credential or a removed confirming membership.
Use existing transaction/root/fixed-definition checks; retain successful profile
values and receipt replay. Separately bound company/lesson initialization remains
its existing authority and does not acquire a synthetic interactive principal.
## Confirmed master-data lifecycle (FR-001–FR-003)

The existing master_data_lifecycle command must retain explicit confirmation for the actual party, item, location or payment-term active flag and current referenced record. Direct canonical writes, absent confirmation, changed/repeated invocation, early root commit, post-write failure and unrelated effects refuse atomically. Preserve unchanged-flag idempotency, lifecycle before/after event values and actual receipt attribution/replay. REST PATCH and CLI activate/deactivate use the same retained decision with explicit confirmation. The finite public model strings resolve to existing model types; existing internal type-valued calls retain their meaning. No deletion, schema or invented historical approval is introduced.

The existing confirmed party_merge parent includes the exact duplicate deactivation in its own atomic root receipt. Its parent and nested lifecycle invocation must be frozen; direct or changed/repeated/partial merge effects refuse. Preserve current merge eligibility and review, source reason/identities, survivor history and unchanged validation refusals. Merge confirmation grants no unrelated header or financial effect.

The two fixed confirmed application profiles admit only their currently authored direct party/item/location canonical creation families. They do not inherit newly registered lifecycle/merge or other arbitrary canonical family authority. Separately retained source-intake and company/lesson profile scopes keep their own exact existing definition checks.

## Confirmed manual document corrections (FR-001–FR-003)

The existing document_correct and document_lines_correct commands must retain explicit confirmation of the actual current manual document and stated header or complete line changes. Canonical direct writes, absent confirmation, changed/repeated invocation, early root commits, post-write failure and unrelated effects refuse atomically. Preserve current revision/downstream-Reality restrictions, statement amounts and identities, before/after evidence, actual request attribution and receipt replay. REST correction endpoints prepare and explicitly confirm the same retained command and preserve response shapes. Appending a corrected external source version remains lossless raw intake/queue preparation; it cannot accept changed document or Reality meaning without a separate reviewed apply. Header-only creation and other canonical writers remain separate qualification.

Correction preparation retains every actual public canonical default, including omitted optional fields, before execution. Decimal/date statements use the existing lossless canonical serialization; they are never recalculated. Changed referenced payment terms or items require renewed review even when document/line revisions remain unchanged.

## Retained commercial defaults and partner roles (FR-001–FR-003)

Existing commercial commands must retain actual public canonical defaults and serialize stated Decimal/date values before confirmation. Default changes after preparation cannot redefine approved meaning. Commercial and manual-correction references to a business partner include its current separately held roles; a separately confirmed role change requires renewed review even if the main partner/document row is unchanged. Preserve source values, current person/token consent, tenant scope and exact frozen effect ownership. This closes retained-input/reference integrity only; remaining canonical writer qualification stays separate.

## Atomic selected-invoice payments and customer refunds (FR-001–FR-003)

The existing customer_payment_post, supplier_payment_post and customer_refund_post commands bind their canonical parent, exact payment/refund evidence, balanced posting and selected settlement allocation to the actual retained confirmation. Direct canonical parents, changed or repeated callbacks, early root commits, post-write failure and unrelated header/stock effects refuse atomically. Current retained payment context and actual current person/token consent are rechecked at the canonical parent. Source-stated amounts, effective date, currency/account/selected control identities, reference, replay and foreign-currency rules stay unchanged. A bookkeeping confirmation never initiates a transfer. Standalone supplier refund/credit/posting and header-only creation remain separately qualified.

The selected-payment review retains public defaults and current exact cash/control/FX-account and partner references. Changed defaults or invoice context after dispatch require renewed review. The existing explicitly listed payment_run is also a governed atomic parent: retain each selected obligation/current eligibility, stated amount/reference and confirmed total, freeze the whole run and every exact supplier-payment child, and settle one receipt with the complete run. Its REST endpoint and the existing customer/supplier payment and refund endpoints require actual explicit confirmation; existing customer/supplier payment CLI commands show the actual review and require yes or --yes. Preserve authored fixed/demo payment calls under their actual narrow confirmed definitions: add only their two existing payment parent families to the literal fixed list, freeze actual calls and keep lifecycle/merge/refund/general future writers excluded.


Ordinary payments in practice/Storyline companies retain and recheck the same current payment review as business-company payments. Company purpose does not bypass the reviewed canonical parent. The existing real transaction-bound guided-lesson proposal scope retains its exact step-preview/schema contract and actual step confirmation; never manufacture such a scope or allow an unmatched session/company/tool to suppress ordinary review.

## Standalone financial evidence follow-up

Existing sales/supplier invoice posting, customer/supplier credit posting, customer/supplier credit netting and selected supplier refund commands must retain current selected evidence/account/partner/settlement references and actual explicit consent. Freeze each existing canonical parent and its exact posting/allocation/refund children; do not let callbacks change, repeat, commit early or add unrelated effects. Business effects and the executed receipt settle in the application-owned root. Direct/private-commit calls require the actual supported scope. Preserve stated money, exchange rates, currency, current domain eligibility and response shapes. Existing HTTP endpoints require actual explicit confirmation; fixed/profile callers freeze only their actual authored families and retain their existing authority. Source reception and header-only creation remain separately tracked; no external transfer, schema change or invented historical decision.
