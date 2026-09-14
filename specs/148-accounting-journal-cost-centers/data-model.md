# Physical Data Design: Operational Finance

**Status**: Proposed schema for technical review, not deployed. [data-structure.md](data-structure.md) explains the business concepts; this file chooses their storage boundaries. Fields listed below are the proposed typed business fields; existing repository conventions supply opaque IDs, tenant ID and audit metadata.

## Common constraints

Every table has tenant scope, including join/history tables. Relationships use `(tenant_id, id)` composite foreign keys and parent unique constraints where required. Codes are unique only in their declared tenant/namespace; IDs never derive from codes. Financial numeric fields use the existing `Numeric(18,4)` precision and Decimal: reject unrepresentable values rather than round them silently; preserve original representation in source payload. Dates are explicit business dates or UTC instants, never substituted for each other.

Evidence and revision rows are append-only. Mutable reference state is audited by BusinessEvent. Active revision pointers use optimistic version checks under the finance lock. No cascaded deletion of used evidence, accounts, entries, allocations or packages. Check constraints enforce owner XOR, valid direction/kind, positive explicit amounts and appropriate nullable fields. Lists of foreign IDs belong in child rows, not unvalidated JSON. Original payloads and immutable output/result envelopes may remain JSON/text because their members are not alternative relational authorities.

## Existing records retained

- SourceRecord/SourceArtifact: lossless external input and versions, unchanged.
- Document/DocumentLine: source or internal evidence. Add supported document-kind vocabulary for settlement adjustment, opening item, finance transfer and provider event; not operational status columns.
- LedgerEntry: replace the legacy `account` string with required `account_id`. Role/code/name come from the linked account. Recreate disposable fixtures; no compatibility snapshot or backfill.
- SettlementAllocation/LedgerReversal: retain identities and relationships. Generalize control-entry availability beyond invoice-backed targets; no parallel allocation table.
- ChangeProposal, BusinessEvent, job/schedule records: reuse for confirmation, audit and execution. Finance effects participate in their bound transaction.

## Accounts and coordination — FR-001, FR-021–FR-029, FR-049

| Table | Typed fields and constraints | Why stored |
|---|---|---|
| `subledger_account` | code, name, required supported role, state active/blocked, revision; unique tenant/code | Allowed destinations and role-wide reads |
| `finance_role_destination` | role, account_id, revision; unique tenant/role; compatible established role | Deterministic defaults |
| `money_account_detail` | account_id unique, purpose bank/cash/provider_available/provider_restricted/provider_disputed/in_transit, source_system_id optional, external_account_reference optional | Validate money purpose and source-account matching; currency remains on each event/entry |
| `finance_state` | tenant_id unique, revision | Serialize finance mutations and detect stale reads/actions; no rollout state or money |
| `finance_operation` | request_key unique per tenant, command_kind, canonical_request_hash, action_id optional, immutable result, recorded_at | Return exact result after lost response; conflicting reuse fails |
| `finance_posting_effect` | evidence_document_id, effect_kind, economic_namespace, economic_key, leg_key, posting_group_id, original_effect_id optional, contract_revision | Unique tenant/namespace/key/leg; link an economic effect to its one local group |
| `finance_effect_evidence` | effect_id, document_id OR document_line_id, asserted_relationship, decision_action_id optional | Additional evidence/matches without another posting; XOR evidence owner |

Bounded roles: receivable, payable, cash, gross_sales_counterpart, gross_purchase_counterpart, customer_reduction_counterpart, supplier_reduction_counterpart, opening_counterpart, provider_fee_counterpart, provider_clearing, provider_restricted, provider_disputed, transfer_in_transit. Provider-specific roles cannot be substituted for cash just because they represent money. No programmable role/sign rules.

Once established and used, role is immutable. Exact inverse entries can retain a blocked original account; new replacements cannot. Invoice-linked control legs select the original account before consulting any default.

Money accounts do not impose a single currency. Currency is authoritative on each received event and LedgerEntry; eligibility and amounts always partition by `(tenant, account, currency)`. One account may hold EUR and USD entries; reads and settlement keep currencies separate. Bank/cash accounts may operate without money-account detail; provider-specific operations require explicit compatible purpose/source-account configuration. Test setup must not invent a bank/provider identity when none was supplied. Different external money accounts require distinct local account identities; no matching across currencies is permitted.

## Received detail and references — FR-006–FR-010, FR-027, FR-030–FR-034

| Table | Typed fields and constraints | Why stored |
|---|---|---|
| `financial_component` | document_id XOR document_line_id; source_component_key/path; role line/detail/document_summary; nullable stated_net/tax/gross/base; currency; stated_case/account/center codes and namespaces | Exact received values, absent versus zero, repeated joins/export |
| `finance_reference` | kind cost_center/case_code/coding_group; code, name, state, revision; unique tenant/kind/code | Same-shaped managed references, not an arbitrary attribute store |
| `source_classification_mapping_revision` | source_system_id, declared_namespace, source_field_kind case_code/coding_group/cost_center, source_code, local_reference_id with matching kind, revision, replaces_id optional, activation_action_id, state draft/active/retired | Target-independent exact source-code translation; unique active tenant/source/namespace/field-kind/code |
| `component_assignment_revision` | component_id, revision, basis net/gross/base, case_reference_id optional, group_reference_id optional, actor/action, reason; unique component/revision | Internal classification and attribution distinct from source |
| `component_assignment_part` | assignment_revision_id, cost_center_reference_id, amount; unique assignment/center | Explicit shares; service enforces total ≤ the received basis |
| `accounting_target` | name, namespace, enabled, active_profile_revision_id | Target isolation and activation |
| `accounting_profile_revision` | target_id, revision, format `reality-neutral-finance-v1`, requirement flags for received fields/codes, immutable definition | Exact required-field validation, not arbitrary executable rules |
| `finance_mapping_revision` | target_id, revision, mapping_kind, transaction_kind/case/group_mode/group_id where applicable; local_account/reference_id OR declared_source_namespace/code; external account/tax/center reference outputs; replaces_id optional, activation metadata | Exact target mapping and historical package reproduction |

Reference kinds are checked through composite kind-aware keys or equivalent database constraints; a case ID cannot be used as a center. Assignment head selection is an explicit revision, not a latest-timestamp guess. Empty shares permit classification without cost attribution. Missing basis refuses amount assignment. Summaries are never added to their own child totals.

Source classification is separate from external target routing. Resolve an explicit source namespace/code through exactly one active source classification revision to an existing same-tenant, same-kind local reference. Missing, retired or conflicting mappings produce an explanation, never tax inference. Owner-confirmed activation replaces only the exact source scope under the finance lock. Original received codes remain unchanged; resolved source classification and a deliberate internal override retain separate provenance. Preview returns the selected source revision ID; preparation revalidates it and freezes it in the item revision links. A change cannot reinterpret an already prepared package. This lookup does not require an AccountingTarget.

Target mapping kinds are bounded: local-account, source-reference, local-center, case-routing. Each kind has a constrained shape. Case-routing scope `(target, transaction kind, case)` has exactly one active discrimination mode: no-discrimination or exact-group as defined in posting-matrix.md. Activation locks finance state, rejects overlapping/competing active mappings and retires the previous revision. A unique active scope key plus service overlap validation prevents ambiguous resolution. Package items retain exact selected revision IDs through manifest links; reference edits cannot mutate prepared bytes.

## Settlement and opening evidence — FR-035–FR-048, FR-053

| Table | Typed fields and constraints | Why stored |
|---|---|---|
| `settlement_adjustment_detail` | document_id unique, side customer/supplier, target_control_entry_id, reason_kind, reason_text, agreement_document_id optional, confirming_action_id | Accepted noncash reduction tied to one claim/liability; amount/currency come from evidence/entries |
| `opening_scope` | source_system_id, external_snapshot_key, cutover_date, coverage_kind individual/summary, side, party_id, currency, source_record_id | Detect repeated/replaced/overlapping opening coverage |
| `opening_item_detail` | document_id unique, scope_id, external_item_key, direction customer_debt/customer_credit/supplier_debt/supplier_credit, original_due_date nullable | Four explicit residual directions; unique scope/item; amount held on evidence/entries |
| `control_transfer_detail` | document_id unique, original_credit_entry_id, target_control_entry_id, confirming_action_id | Explain paired reclassification allocations and inverse correction |

Customer and supplier adjustment counterpart roles are distinct. Supplier reductions require explicit supported agreement/entitlement evidence or an internal declaration with authority/reason; a unilateral deduction note does not settle a payable. Zero/negative adjustments fail. Posting and allocation are atomic; cash can be recorded independently when no adjustment is accepted.

Opening scope is never a stored balance. New snapshot/detail overlap is reviewed, not added to old totals. Cutover does not fabricate original invoices, cash, net/tax or aging. Later historical evidence matches coverage/effect or requires review before posting. Corrections preserve the original and reverse only after dependent consumption is handled explicitly.

Transfer entries remain ordinary LedgerEntry rows. Paired SettlementAllocation rows consume the original credit and target invoice through the transfer legs atomically. Transfer-generated control legs are not standalone spendable credit origins.

## Money and trade controls — FR-049–FR-055

| Table | Typed fields and constraints | Why stored |
|---|---|---|
| `money_event_detail` | document_id unique, source_account_id, event_kind, external_event_key, external_payout_key optional, payout_mode direct/two_leg optional, related_event_document_id optional | Capture/fee/reserve/dispute/refund/payout/bank leg semantics and replay constraints |
| `advance_assignment` | payment_control_entry_id, order_document_id XOR commitment_id, amount, confirming_action_id | Explicit earmark to one intended operation, not another cash posting |
| `advance_assignment_change` | assignment_id, kind release/consume, amount, settlement_allocation_id for consume, action_id | Append-only partial release/conversion; remaining amount derived |
| `payable_hold` | payable_control_entry_id, placement_action_id, reason, responsible_actor_id | V1 whole-item payment execution hold |
| `payable_hold_release` | hold_id unique, action_id, reason | Auditable release, active state derived |
| `finance_relationship_assertion` | document_id XOR document_line_id as subject, relationship_kind, state linked/not_applicable/unknown, related_document_id OR related_line_id for linked only, evidence/action reference, supersedes_id optional | Explicit source-backed or internal linkage and its authority |
| `finance_coverage_assertion` | source_system_id, party_id optional, coverage_kind, period_start/end, evidence_version_id, assertion, supersedes_id optional | Scoped completeness, invalidated by contradictory/version-changed evidence |

Money event identity binds external account namespace + event key + leg kind, never amount/date alone. Payout mode is exclusive for one source payout identity; direct and two-leg representations cannot both post. Partial batch matches use explicit component/line evidence links, preserving uncovered lines. Fees use stated fee evidence; later invoices match the same effect. Unsupported loss/FX remains review. Pending authorization is evidence without money entries.

Advance availability is payment-origin availability less active earmarks. Consume creates an ordinary allocation and its assignment-change in the same transaction; an explicit own-earmark conversion does not subtract it twice. Invoice linkage and stated allocation amount are required. Cancellation causes review/release/refund choices, never automatic refund.

Holds block new internal payment execution across individual and run paths. Observed executed cash is still recorded with a during-hold exception; it is not retroactively rejected. Multiple active holds require all relevant holds to be released. No hold flag is added to a Document.

## Handoff and automatic recording — FR-002–FR-004, FR-011–FR-016

| Table | Typed fields and constraints | Why stored |
|---|---|---|
| `handoff_package` | target_id, profile_revision_id, operation_id, prepared_at, canonical_payload, payload_hash | Immutable bounded artifact and repeat download |
| `handoff_item` | package_id, evidence_document_id, target_effect_key, evidence_version_key, correction_of_item_id optional | Exact item/version matching; stable effect key across explicit retries |
| `handoff_item_revision_link` | item_id, assignment_revision_id OR mapping_revision_id OR source_classification_mapping_revision_id | Relational frozen revision manifest, exactly one typed revision link |
| `handoff_receipt_detail` | document_id unique, target_id, external_receipt_key, supplied_item/effect/version references, matched_item_id nullable, outcome delivered/accepted/rejected/posted, external_posting_reference optional, asserted_at nullable | Source-backed independent remote outcome; unmatched/conflicting receipts retained |
| `recording_authority` | source_system_id, document_kind, interpretation_contract_revision, owner_action_id, state enabled/paused/revoked, revision | Narrow permission independent of intake |
| `financial_recording_outbox` | evidence_document_id, interpretation_contract_revision, economic_key, state pending/recorded/review, effect_id optional, reason_code optional, attempt_count | Eligibility committed with evidence; recoverable bounded processing |

Outbox unique key covers evidence version and interpretation contract. A new source version does not override economic-effect uniqueness. Review is not automatically retried indefinitely; explicit correction/reactivation is required. Transient worker failures retain pending work and shared queue retry semantics. Source evidence remains durable when recording fails. Receipt matches are resolved by source/target/version identities, never by choosing the most advanced outcome. Conflicts are a derived read result, not erased receipt history.

## Derived reads and state transitions

No tables for outstanding balance, available credit, profit, external posting status, operational readiness or aggregate cost total. Read them from effective entries/allocations, received components, assignments, controls and receipt evidence. Eligibility origin whitelist: customer/supplier payment excess, credit-note control entries and opening-credit entries. Invoice reductions, neutral counterparts, inverses and transfer intermediates are excluded.

Reference active → blocked/retired is audited; original evidence remains immutable. Proposal preview → confirmed execution follows existing authority rules. Outbox pending → recorded/review commits with effect/outcome. Package prepared is immutable; remote assertions are independent events, not transitions of the package. Reversal creates inverse history rather than deleting rows.

## Clean local schema and fixture proof

The owner-approved local cutover replaces compatibility migration. Keep the Alembic chain valid, create required account FKs directly and update all fixture producers/callers to account IDs. No old-string backfill, unresolved account role, dual-column write or old-binary rollback support. FinanceState retains only coordination revision; no per-tenant rollout stage.

Test empty-database migration and deterministic minimal-account setup, then generate synthetic evidence/entries through shared services. A reset/reseed is explicitly invoked only for a positively identified disposable local/test database, never by API/scheduler/worker startup. Existing real external opening-item/coverage contracts remain unchanged. New-model sources, entries and correction history stay immutable during ordinary operation.

## First implemented slice — 2026-09-09

The owner explicitly approved account setup, required account IDs in existing posting paths, settlement safeguards, settings UI and clean test fixtures. This is a bounded implementation of the larger design, not completion of the 58 functional requirements.

- Persist `SubledgerAccount`, `FinanceRoleDestination` and `FinanceState` beside `LedgerEntry` in `db/core.py`; do not create the future evidence/operation/target tables before their use cases are implemented. Migration `0047_finance_accounts` follows the actual root head `0046_company_setup_demo`.
- Keep the five existing technical role keys: `accounts_receivable`, `accounts_payable`, `cash`, `sales_revenue`, `inventory`. Their display meanings are customer receivables, supplier payables, cash/bank, gross sales counterpart and gross purchase counterpart. The future conceptual `receivable`/`payable`/`gross_*` names do not require renaming these stable keys. Introduce additional roles only with their consuming slice.
- `LedgerEntry.account_id` is the only stored account authority. The Python/SQL `account` accessor derives the operational role through the tenant-scoped account relationship; it is neither a stored account code nor a legacy identity. Journal API and projection values also expose the concrete account ID and current display code. Existing role-filtered reports remain aggregate operational views.
- Confirmed creation of an ordinary or practice company initializes five reference accounts/defaults through a common private bootstrap. It creates no monetary entries. Explicit initialization remains available for an empty catalog. No country chart or tax treatment is guessed.
- Account maintenance uses shared services, typed proposal tools, owner confirmation, expected finance revision and a single transaction for the mutation and terminal proposal result. Finance mutations serialize through a tenant row. This does not claim the future economic-effect identity/outbox contract.
- Invoice-bound payment/refund commands retain the original control account even if its role default changes. Normal new use of a blocked account fails; exact reversing entries retain the original account ID. Allocation requires identical control account, party and currency; effective allocations at either endpoint consume availability.
- The migration refuses a populated ledger, performs no automatic deletion/backfill and permits an empty-only test downgrade. Temporary test databases exercise upgrade/downgrade. The active port-8080 worktree and its database are outside this cutover.
- The company settings panel reuses root web forms, tables, buttons, localization and theme styles. A separate synthetic browser harness verifies the component without touching a tenant. Integrating it into the newer active unified shell remains a separate checkout integration step.

Constitution review for this slice: PASS. No document operational status, derived monetary Fact, duplicated source/line foreign key, alternate adapter posting rule, cross-tenant relationship or automatic external effect is introduced. No critical cross-artifact finding remains for this bounded slice after recording the actual table placement, role keys, bootstrap behavior and deployment boundary here. Broader story acceptance remains open.

## Implemented adjustment refinement (2026-09-10)

The separate acceptance slice does not add `settlement_adjustment_detail`. Existing
immutable SourceRecord payloads retain the entered category, reason, supplier
agreement, external source/effect reference, accepted amount/currency, confirming
action/user and timestamp. The dedicated `customer_settlement_adjustment` or
`supplier_settlement_adjustment` Document owns the evidence, and its allocated
control entry is the shortest authoritative invoice relationship. A later typed
extension still requires a repeated filter/join use case; no balance is stored.

Implemented role keys are `customer_reduction` and `supplier_reduction`, representing
the conceptual customer/supplier reduction counterparts above. Migration 0049
permits them without rewriting accounts or entries. Automatic company bootstrap
keeps its five base roles. Explicit owner-confirmed account initialization can add
missing reduction defaults; existing defaults remain unchanged. Exact historical
reversal can use blocked originals. Available-credit reads exclude these
invoice-bound reductions.

## Guided settlement composition

No new tables or fields. Payment and refund SourceRecords retain confirmed stated
input; their Documents and posting groups retain separate identities. Reduction
uses its existing dedicated evidence. An allocation links the original credit entry
to the invoice or refund control entry. Read-time available credit counts both ends.
The proposal receipt references every created source/document/group/allocation.

## Opening delivery refinement (2026-09-10)

Migration 0050 adds `opening_scope` and `opening_item_detail` as Evidence. A scope
holds tenant, original source namespace, snapshot reference, cutover date, coverage
kind, existing party, direction and currency. An item links its scope to its opening
Document, with stable external item identity and optional original due date. Composite
foreign keys enforce tenant agreement for party, scope and document. No amount or
mutable balance is repeated in these tables. Optional original total/date and supplied
source reference remain in the immutable confirmation SourceRecord.

Four dedicated opening Document types use receivable/payable control entries against
`opening_counterpart`; automatic company setup remains five base defaults. Explicit
account initialization may add the neutral role. The imported amount is the stated
residual, with no cash, turnover or tax entry. Due dates for opening debt come only
from the stated opening item, never current payment terms. Financial projection
version 3 rebuilds disposable rows with opening origin and receivable/payable flow.

Scope/item identity remains reserved after reversal. Reversal neutralizes the original
posting and makes dependent allocations ineffective through existing read-time rules;
replacement and any subsequent reallocation require separate explicit operations.
A changed snapshot or overlapping summary/detail requires reconciliation outside this
bounded editor, rather than silently replacing authority. File upload and guided
coverage reconciliation remain later work.

### Delivered reference catalog refinement

`finance_reference`: id, tenant_id, kind, code, name, state, revision. Required
kind enum: cost_center/case_code/coding_group; state active/blocked; revision > 0.
Unique tenant/kind/code and tenant/id/kind support kind-aware future references.
Codes (max 100) and names (max 200) are trimmed and nonempty. Code and kind are
immutable. `finance.reference_changed` BusinessEvent stores before/after snapshots,
reason and actor; action_id links the confirmed proposal. No amounts or derived
financial state are stored here.

### Component attribution schema refinement

financial_component: id,tenant_id, document_id XOR document_line_id (unique owner),
stated_net/tax/gross/base Numeric(18,4) nullable, currency. Source path/role are
unambiguously derived from the owner; no duplicate document/source FK on line owners.
DocumentLine gains unique tenant/id for its composite link.
component_assignment_revision: id,tenant_id,component_id,revision,basis,case_reference_id
and kind constant,group_reference_id and kind constant, reason,actor_id,action_id,
created_at,reference_snapshot (immutable display labels only). Unique component/revision.
component_assignment_part: id,tenant_id,assignment_revision_id,cost_center_reference_id,
kind constant,amount; unique revision/center. Composite links enforce kind/tenant.
No mutable head or total columns. Assignment event links the component and revision.

Operational matrix slice: no schema changes. Domain descriptions and tenant-scoped
account/default reads generate the view; no stored matrix or readiness projection.


## Source classification delivery schema

`source_classification_mapping_revision`: opaque id, tenant_id, source_system_id, namespace, field_kind (case_code/coding_group), source_code, reference_id, revision, replaces_id, state (active/blocked), is_current, reference_snapshot JSONB, reason, actor_id, action_id, created_at. Exact scope is tenant/source/namespace/kind/code. Composite tenant/source and tenant/reference/kind FKs; tenant/self predecessor FK; unique scope/revision; unique current scope. Drafts remain existing ChangeProposals. Replacements and blocks append revisions and clear only the predecessor current marker; prior decision content is retained. Cost-center translation remains outside this slice.

Source revision refinement: `state` records the immutable active/blocked decision; `is_current` selects the current revision. Replacing a revision clears only its current marker, preserving the prior decision state. A partial unique index on `is_current` enforces the exact current scope.

## Delivered external-target slice

[target-mappings.md](target-mappings.md#data-model) specifies accounting_target,
accounting_target_reference and finance_target_mapping_revision with composite
tenant/target/kind constraints, exact noncompeting scope shapes and immutable mapping
snapshots. These three tables are deployed locally at `0054_target_mappings`. This bounded
design supersedes the broad finance_mapping_revision sketch for the first target
routing delivery. Profile/package/receipt tables remain deferred. Drafts reuse
ChangeProposal; external codes are reference values, never local primary keys.
