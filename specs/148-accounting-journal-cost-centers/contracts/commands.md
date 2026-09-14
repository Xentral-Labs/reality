# Shared Finance Command Contracts

These are planned public tool names and Pydantic schemas. Register the same names in command discovery and route API/CLI/MCP/Chat through the existing application-tool mechanism. They are not currently executable. Existing eight ERP posting commands retain their names and strict contracts; extend their service internals, not their signs or meaning.

## Common envelope

Reads take tenant from trusted execution context, never an unrestricted input override. Mutations take `request_id`, `expected_finance_revision`, operation-specific opaque IDs and explicit Decimal strings. Preview returns the canonical normalized request, revision, proposed effect, evidence/missing-information references and a proposal ID using existing confirmation facilities. Execution takes that confirmed proposal ID and rechecks authority/revision/availability. Automation has its own named authority, not a fake interactive approver.

Money accounts may hold multiple currencies; event/entry currency controls matching and availability, and every amount remains partitioned by currency. Clean fixtures may use the same account ID for multiple currencies; balances remain separate. Provider events require explicitly configured compatible money-account purpose and identity.

Amounts are positive strings with a currency; direction comes from a bounded command kind, never a caller-supplied debit/credit sign. Unknown fields fail validation except the existing lossless external payload boundary. Preview performs no posting. Failure codes: `not_found`, `forbidden`, `stale_revision`, `invalid_input`, `account_unavailable`, `insufficient_available`, `held`, `ambiguous_mapping`, `missing_evidence`, `economic_effect_conflict`, `idempotency_conflict`, `review_required`, `limit_exceeded`. Domain refusal rolls back the entire financial mutation.

Success returns `operation_id`, `finance_revision`, `affected` typed IDs, `posted_effect_ids`, `allocation_ids`, exact before/after observations with currency/basis, and follow-up read references. These observations are a command receipt, not stored balance authority. A response lost after commit is recovered by request ID. Request-ID reuse with different canonical input conflicts.

## Catalog and evidence commands

| Tool | Required business input | Result and guards |
|---|---|---|
| `finance.account.create` | code, name, bounded role | Owner; no entries created |
| `finance.account.update` | account_id, name/code/state, account_revision | Used role immutable; supported role required at creation |
| `finance.account.set_default` | role, account_id | Owner; active compatible role |
| `finance.account.import_preview` / `finance.account.import_confirm` | source_record_id, selected references, explicit role assignments / preview ID | ≤200; collisions and unknown roles reviewed; no number inference |
| `finance.reference.create` / `finance.reference.update` | kind, code/name/state or ID+revision | Owner; center/case/group only; retired history preserved |
| `finance.source_mapping.draft` / `finance.source_mapping.activate` / `finance.source_mapping.retire` | source system, namespace, field kind, exact source code, local reference ID / revision ID | Owner; target-independent, same-tenant/kind, one active exact scope, audited replacement |
| `finance.source_mapping.resolve` | source system, namespace, field kind, exact source code | Read-only; local reference plus selected revision or missing/conflicting reason; no target required |
| `finance.component.assign` | component_id, basis, case/group IDs optional, center/amount parts, reason | One immutable revision; received amount must support basis; partial allowed |
| `finance.target.configure` | target identity and neutral profile requirement flags | Owner; versioned profile, no executable tax rules |
| `finance.mapping.draft` / `finance.mapping.activate` / `finance.mapping.retire` | target, kind, exact scope/destinations; revision ID | Owner; test exact match and overlap before activation |
| `finance.mapping.resolve` | target, transaction kind, component/assignment revision | Read-only; selected revision or structured zero/multiple-match reason |

Received components are created only by registered interpretation contracts or explicit internal evidence services. UI assignment never edits received values. Source-code and internal classification conflicts require an explicit choice/reason visible in the output.

## Settlement commands

| Tool | Required business input | Result and guards |
|---|---|---|
| `finance.customer_payment.record` / `finance.supplier_payment.record` | party, currency, actual amount, money account, evidence, optional selected allocations | Actual cash independent of invoice amount; invoice-specific legacy strict commands remain strict |
| `finance.customer_adjustment.record` / `finance.supplier_adjustment.record` | target control entry, explicit reduction amount, reason, agreement/declaration evidence | Separate noncash group; supplier entitlement required; never infer skonto |
| `finance.customer_settlement.record` / `finance.supplier_settlement.record` | actual payment plus selected allocations and optional explicit adjustment | Atomic combined operation; cash-only command remains available if adjustment cannot be accepted |
| `finance.credit.allocate` | side, selected origin entry IDs/amounts, target entry IDs/amounts | Same tenant/party/currency/concrete account; origin whitelist; no automatic netting |
| `finance.credit.refund` | side, origin IDs/amounts, actual refund evidence and money account | Reuses existing credit; no duplicate payment; all origins locked/revalidated |
| `finance.control.transfer` | side, original credit entry, target control entry, explicit amount, reason | Atomic reclassification and two allocations; preserves role balance |
| Existing reversal tool, extended supported origins | original group/effect, reason and dependent allocation handling | Exact inverse; independent cash/adjustment/refund histories; blocked original permitted |

Example: customer invoice 1,000, actual receipt 980 and accepted reduction 20 yield cash 980, separate noncash 20, outstanding zero. Without accepted reduction, outstanding is 20. Receipt 1,020 allocated 1,000 yields available credit 20. Supplier directions mirror this with explicit agreement validation. No tax adjustment amount is derived from the gross reduction.

## Opening and trade controls

| Tool | Input | Contract |
|---|---|---|
| `finance.opening.preview` / `finance.opening.import` | source/snapshot/cutover, bounded selected item declarations / preview ID | Four directions, original due date nullable, explicit summary coverage; atomic batch; duplicate/overlap refusal |
| `finance.money_event.record` | supported source event evidence, account identities, explicit related event/leg | Capture, stated fee, restriction, dispute, payout and bank receipt only when evidenced; pending is non-posting |
| `finance.money_event.match` | existing effect and additional evidence IDs, relationship, reason | Does not post again; ambiguous matches remain review |
| `finance.advance.assign` | payment control entry, order OR commitment, amount | Earmarks available credit without moving cash |
| `finance.advance.release` | assignment ID, amount, reason | Releases purpose only |
| `finance.advance.apply` | assignment ID, invoice target, amount and billing link | Allocation and earmark consumption atomic |
| `finance.payable_hold.place` / `finance.payable_hold.release` | payable entry, reason/responsible actor / hold ID+reason | Whole-item V1; check all existing individual/run execution paths |
| `finance.relationship.assert` / `finance.coverage.assert` | bounded relation/scope, explicit state, evidence or internal declaration and reason | No guessed link or completeness; immutable superseding assertions |

Payment services distinguish a request to execute a new payment from recording already-executed source-backed cash. A hold refuses the first; the second preserves evidence and emits an inspectable exception. This is not an unguarded bypass flag for agents.

## Handoff and automation

| Tool | Input | Contract |
|---|---|---|
| `finance.handoff.preview` | target, selected evidence IDs, explicit retry/correction intent if applicable | Ready items, exclusions and exact revision token; no preparation side effect |
| `finance.handoff.prepare` | confirmed exact selection and preview revision | ≤200 items/4 MiB; atomic immutable package; changed selection requires new preview |
| `finance.handoff.download` | package ID | Read-only exact stored bytes/hash; no remote-success inference |
| `finance.receipt.import` | source record in neutral receipt contract | Preserve unmatched/conflicting evidence; no guessed posting status |
| `finance.recording_authority.configure` | source/type/contract revision, enabled/paused/revoked | Owner confirmation; register shared drain schedule on activation |
| `finance.recording.retry` | reviewed outbox item and corrected evidence/authority context | Explicit supported retry; same economic identity |

V1 neutral package envelope: `schema_version`, `package_id`, `target_id`, `profile_revision_id`, `prepared_at`, `items`. Each item contains `item_id`, `effect_key`, `evidence_version`, source/document references, transaction kind, currency, received nullable components and their roles/bases, separate source/internal/target annotations, exact source-classification/target-mapping/assignment revision IDs, gross operational entry references, correction relation and explicit omissions. Canonical bytes use a fixed serializer revision recorded in the profile. Do not hash a payload field containing its own hash.

V1 neutral receipt envelope: `schema_version`, `external_receipt_id`, target namespace, explicit item/effect/version references, outcome (`delivered`, `accepted`, `rejected`, `posted`), optional asserted timestamp/external posting reference/reason. Item outcome must be explicit; batch acceptance cannot be expanded into item posting. Original unknown fields remain in SourceRecord. Receipt identity is unique within tenant/target/source namespace; changed content under the same identity is conflicting evidence, not an overwrite.

The recurring drain handles at most 20 rows/25 seconds. It rechecks authority under the finance lock, uses transaction-bound posting and finishes effect/outbox/job success atomically according to the shared scheduling contract. Evidence intake is never rolled back because downstream queue capacity is unavailable. No HTTP call to external accounting is part of this command set.

## Implemented separate reduction command

`finance.adjustment.context` reads a selected invoice's outstanding amount,
currency, control account, configured counterpart and finance revision.
`finance.adjustment.accept` is proposal-only; arguments are `invoice_id`, a stated
decimal-string `amount`, `expected_revision`, `reason_category`, `reason`, optional
`agreement`, and optional paired `source_record_id`/`source_effect_id`. Supplier
acceptance requires nonempty agreement/entitlement text. No percent calculation,
new cash or external accounting write occurs.

The confirming company owner supplies actor identity through the authenticated
execution boundary. Account role/state, current invoice capacity and source/effect
identity are rechecked under shared locks. Source, document, both postings,
allocation and executed receipt commit together. Replay uses the original proposal
ID; the receipt exposes source/document/posting/entry/allocation IDs and the accepted
amount, currency and zero cash change. Existing `ledger_reverse` reverses the
adjustment group independently from actual payment.

Adapters: CLI `finance-adjustment-context` / `finance-adjustment-propose`; MCP
`finance_adjustment_context` / `finance_adjustment_propose`; web context GET
`/finance/adjustments/context/{invoice_id}` and proposal POST
`/finance/adjustments/proposals`. The existing proposal approval route confirms.

## Guided settlement contract

`finance.settlement.context` reads a tenant-scoped invoice or available-credit
Document by `document_id`, including current revision and matching invoice choices.
`finance.settlement.apply` proposes one mode: `payment`, `allocate_credit`, or
`refund_credit`. Common fields: expected_revision, document_id. Payment requires
amount, allocation_amount, reference, effective_at, optional reduction object.
Credit allocation requires invoice_id and amount. Refund requires amount, reference
and effective_at. Payment/refund optionally accept source_record_id/source_effect_id
as a pair. Amounts are exact decimal strings (maximum four decimal places).
Reduction is the existing stated amount/category/reason/agreement/evidence contract.
Unexpected or mode-inapplicable fields are rejected. Owner confirmation executes
through the existing atomic finance branch. All modes return evidence references
and reviewed cash/allocation/reduction/remaining observations.


Guided settlement adapter paths: GET `/finance/settlements/context/{document_id}`
with optional `query`, POST `/finance/settlements/proposals`, and existing proposal
approval/rejection. CLI: `finance-settlement-context` / `finance-settlement-propose`.
MCP: `finance_settlement_context` / `finance_settlement_propose`. The tool schema is
an object envelope listing mode-specific fields; the discriminated typed validator
rejects fields from other modes and enforces their required inputs. Payment/refund
timestamps must include a timezone. Amounts fit the existing Numeric(18,4) storage
without rounding. Invoice choices are same-party/currency/account, at most 50 with a
search and explicit more-results indicator. No choice implies authorization to allocate.

## Opening delivery command

`finance.opening.context` reads current account revision, permitted destinations and
party choices. `finance.opening.import` accepts expected_revision, source_namespace,
snapshot_key, cutover_date, coverage_kind (individual/summary), reason and 1–100 rows.
Each row carries party_id, direction (customer_debt/customer_credit/supplier_debt/
supplier_credit), currency, amount (stated residual), external_item_key, reference,
optional original_document_date/due_date/original_total/source_record_id. Preview
shows account matches, exact independent totals and unknown dates. Confirmation is
owner-bound and atomic. Original-total metadata is never posted or recomputed.
Same proposal replay returns its receipt; source/snapshot/item conflicts cannot be
bypassed by another proposal ID. Manual entry only; optional existing-source links
preserve externally retained evidence.

### Managed reference catalog slice

Reads: `finance.references.list` (optional kind, state, query, limit, offset),
`finance.references.history` (reference_id, limit, offset).
Writes: `finance.reference.create` (kind, code, name, reason, expected_revision),
`finance.reference.update` (reference_id, name, state, reason, expected_revision).
Preview returns `reference: {before, after, reason}`; confirmation returns the
persisted reference. Update name/state are required to make the full intent
reviewable. Shared active resolver takes tenant, reference ID and expected kind.
HTTP uses `/finance/references`, `/{reference_id}/history`, `/proposals`; existing
proposal approval/rejection endpoints apply. UI review shows server snapshots.

### Component attribution slice

Read `finance.components.context`: document_id, optional limit/offset/reference_query;
returns summary, paged eligible component owners, evidence hashes, current assignment,
finance revision and active reference options. Read `finance.component.history`: component_id,
limit/offset. Write `finance.component.assign`: document_id, optional document_line_id,
basis net/gross/base, expected_evidence_hash, expected_revision, optional case/group IDs,
parts [{cost_center_reference_id, amount}], reason. Null IDs/empty parts explicitly clear
the previous internal assignment. No amount, currency or code edits to source evidence.
Preview returns before/after, basis amount, assigned/unassigned, source/evidence links.
API `/finance/components/context/{document_id}`, `/{component_id}/history`, `/proposals`
uses shared services and the existing owner approval endpoint. CLI/MCP expose the same
contracts. First acceptance creates a normalized component and one revision atomically.

`finance.matrix.read` takes no business arguments. CLI `finance-matrix`, MCP
`finance_matrix` and GET `/finance/matrix` return the same shared matrix. Members
may read; account changes retain the existing owner-confirmed proposal boundary.


Source classification slice: shared `finance.source_mapping.set` confirmed proposal; `finance.source_mappings.list` and `.history` read tools. GET `/finance/source-mappings`, GET `/finance/source-mappings/{mapping_id}/history`, POST `/finance/source-mappings/proposals`. Component context adds a separate `source_resolution` observation per actual component; existing source codes and evidence hash stay unchanged. Scope/revision/actor/reason and reference snapshots are returned; reads do not materialize components.

## Finance-specific external target commands

Owner-confirmed `finance.target.create/update`, `finance.target_reference.create/update`
and `finance.target_mapping.set` use the existing ChangeProposal/approval boundary.
Their typed shapes live in `domain/target_mappings.py`; extra fields are rejected.
Each command requires expected finance revision and reason. Simple account references
cannot carry case/group/tax output fields. Case-routing requires exact transaction,
case and declared group mode. Reference and target identities cannot be changed by
an update. Catalog edits invalidate pending mapping approvals through finance revision.
Shared reads are `finance.targets.list`, `finance.target_references.list`,
`finance.target_mappings.list/history/preview`. Preview takes target/document identity
and bounded pagination and returns separately labelled received components and gross
operational account references. It is read-only and makes no export-readiness claim.
CLI `finance-target-read` and `finance-target-propose` expose these same named tools;
MCP and the web adapter invoke the same shared services and confirmation boundary.
