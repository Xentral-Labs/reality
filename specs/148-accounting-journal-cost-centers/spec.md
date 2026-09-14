# Feature Specification: Operational Subledgers and External Accounting Handoff

**Feature Branch**: Not created; specification maintained on the existing working branch.  
**Created**: 2026-09-09  
**Updated**: 2026-09-09 — trade-finance gaps closed in requirements: money paths, advances, holds, trade evidence, cross-account settlement and agent explanations.  
**Status**: Account-catalog slice integrated, verified and running on local port 8080. Full finance roadmap remains open; see [verification-results.md](verification-results.md).
**Language**: English  
**Input**: Reality must not become accounting software. Customers retain external accounting software. Keep explainable operational subledgers, source-stated accounting information, a small managed subledger account catalog, optional cost-center references and a traceable handoff, with internal structures and screens matching the current application.

## Local development cutover decision — 2026-09-09

The owner is the only current local tester and has no real account population to migrate. Build a clean new schema and regenerate disposable test fixtures. No old-account-string backfill, unresolved legacy-account state, dual account columns, old-binary compatibility or per-tenant migration rollout is required. Keep the repository Alembic chain coherent; do not rewrite unrelated migration history. A reset/reseed must target an explicitly identified disposable local/test database and must not occur automatically on application startup or against an arbitrary configured database. This planning change does not execute a reset.

This removes local development compatibility work, not business integrity: newly recorded evidence/entries remain immutable and tenant-scoped, with explicit reversals. Customer/supplier opening imports, external historical-source matching and coverage remain product features for customers moving from other systems.

## Context and Intent

### Problem

Reality already has an operational financial journal, open items, payments, settlement allocations and reversals. The previous draft expanded that into a general ledger and financial statements. The owner rejected that responsibility: external accounting software remains the authority for financial accounting.

The real gap is reliable operational recording and explainable handoff. Users must distinguish a business event recorded in Reality from an export prepared for accounting, a delivery acknowledged by another system and an externally confirmed posting. Neither a balanced operational journal nor a successful file download proves that financial accounting is complete.

### Scope

- [Trade finance controls](trade-finance-controls.md): provider/bank money paths, earmarked advances, payable holds, explicit control reclassification and coverage-aware goods–invoice–payment explanations.
- [Agent finance contract](agent-finance-contract.md): shared structured answers, authority/Fact boundaries and verified action results.
- Preserve and strengthen existing receivable/payable, payment and settlement subledgers.
- [Opening subledger item import](opening-items.md) for customer receivables/credits and supplier payables/credits, with cutover provenance and replay protection.
- A minimal tenant-owned subledger account catalog defines which accounts may be used: stable identity, code/name, operational role, active/blocked state, deterministic posting destinations and optional target-specific external references.
- Explicit [customer and supplier payment differences](payment-differences.md): accepted skonto/deductions, open disputed residuals and reusable/refundable overpayments, with separate cash and claim/liability-reduction evidence and a shared Customers/Suppliers available-credit view.
- A fixed [transaction matrix and flexible declared case mapping](posting-matrix.md), with optional coding groups and exact versioned external destination resolution.
- Record supported financial evidence once through the existing shared posting services after translation, subject to explicit bounded automation authority.
- Retain source-stated net, tax and gross components without calculating missing amounts or changing the existing gross operational posting basis.
- Optional internal cost-center assignment and external account/cost-center/tax-code references for explanation and handoff.
- A versioned, inspectable, neutral export package and source-backed recording of external receipts. No specific accounting vendor is selected.
- Separate operational completeness, handoff readiness and externally evidenced processing outcomes.
- Journal and control views, open items, payments, cost assignment and handoff reconciliation in the existing Finance Control mode.
- Companion [data structure](data-structure.md), [screens](views.md) and [delivery/verification contract](verification.md).

### Non-Goals

- A statutory or general-ledger accounting system, authoritative financial chart of accounts, statutory account-type/report classification administration, tax treatment engine or tax calculation.
- Balance sheet, profit and loss, trial balance, annual closing, fiscal-period locks, general-ledger opening-balance conversion or accounting-currency conversion. The bounded operational opening-item import is explicitly included.
- Financial inventory valuation, cost of goods sold, depreciation, accruals, payroll, complete statutory bank reconciliation or tax filings. Bounded source-backed payout/transfer matching is included.
- Mandatory cost-center coding, percentage splits, budgets, allocation engines, cost objects or profitability claims.
- Arbitrary manual accounting journals, externally executing payments or automatic correction of another system's postings.
- A live vendor connector, a vendor-specific certified export, or fetching external financial statements. Those require a named target and a separate reviewed adapter contract.

### First delivery boundary

The first authorized delivery adds the managed five-role account catalog to existing gross operational postings and settlement commands. Newly created companies receive five editable reference accounts and defaults, without monetary entries. Users can create, rename, block/reactivate and choose role defaults through a confirmed settings action. Existing journal rows expose account identity and current display code/name. Changing a default does not reassign old entries or their invoice-bound settlements. Country/case mappings, cost centers, accepted deductions, opening imports, automation and external handoff remain later deliveries under the requirements below.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md), [ledger](../../docs/features/ledger.md).
- [Data model](../../docs/DATA_MODEL.md), [Web specification](../../docs/WEB_SPEC.md), [UX matrix](../../docs/WEB_UX_MATRIX.md).
- [Discount explanations](../088-early-payment-discount/spec.md): this feature adds the separately confirmed reduction previously excluded; rate-based calculation remains out of scope.
- [Reversals](../024-auditable-ledger-reversals/spec.md), [supplier credits](../089-supplier-credit-notes/spec.md), [unposted invoices](../092-invoice-unposted/spec.md).
- [Atlas metric meanings](../144-atlas-demo-contract/spec.md), [shared jobs](../../docs/features/scheduled-jobs.md).

The feature directory retains its original name to preserve links. This revision replaces the earlier accounting-foundation proposal entirely. No previous requirement to build a full financial chart, financial statements, period close or general-ledger opening-balance migration remains active. The later approved operational opening-item import does not restore those requirements. The subsequently approved minimal subledger account catalog is defined below and does not restore those responsibilities.

## User Scenarios & Testing

### User Story 1 - Record financial events once (Priority: P1)

An operator sees translated invoices, credits, payments and refunds in the operational subledger without having to recreate them manually.

**Why this priority**: Reliable operational financial state is Reality's responsibility.

**Independent Test**: Translate a synthetic invoice for EUR 119, record its existing gross operational posting, allocate a EUR 50 payment and replay the inputs.

**Acceptance Scenarios**:

1. **Given** supported evidence and explicitly enabled automatic recording, **When** translation completes, **Then** the shared service creates one balanced operational group and the invoice's gross claim is EUR 119. Its counterpart is labelled as an operational gross amount, not net revenue.
2. **Given** a EUR 50 payment allocated to that claim, **When** read, **Then** EUR 69 remains open; retries do not duplicate the payment, posting or allocation.
3. **Given** an order, goods movement or intake-only authorization, **When** translation runs, **Then** no financial entry is automatically created. Financial automation is disabled by default.
4. **Given** concurrent delivery/retry or an uncertain response, **When** processed, **Then** the same business effect is recorded at most once and its existing outcome is recoverable.
5. **Given** a changed already-recorded source version, **When** translated, **Then** evidence is preserved and correction needs review; no second original or automatic reversal is created.
6. **Given** supported credit/refund directions or a reviewed reversal, **When** recorded, **Then** existing control-side and allocation semantics hold and history remains immutable.

### User Story 2 - Keep supplied detail and optional attribution (Priority: P1)

An operator can explain received tax/net values and add operational cost responsibility without maintaining a financial chart.

**Why this priority**: The external accountant needs faithful inputs, while Reality should not invent them.

**Independent Test**: Retain a EUR 1,190 supplier invoice stating EUR 1,000 net and EUR 190 tax; assign EUR 600 net to Warehouse and EUR 400 net to Administration for handoff.

**Acceptance Scenarios**:

1. **Given** supplied line components and document tax summaries, **When** interpreted, **Then** both remain inspectable at their real granularity, with absent values distinct from zero and no summary/line double counting.
2. **Given** the explicit 600/400 assignments, **When** confirmed, **Then** they explain the stated net component without changing the EUR 1,190 payable or pretending that the assignment is a source statement.
3. **Given** missing net/tax data or no external account reference, **When** operational recording is otherwise valid, **Then** the operational subledger remains usable. Handoff readiness separately explains any required missing information; no values or account codes are guessed.
4. **Given** internal/external cost-center or account references, **When** edited after a package was prepared, **Then** that package retains its exact original revision and the new mapping affects only new preparation.
5. **Given** a split totaling 1,001 against the stated 1,000 or mixing net/gross bases or currencies, **When** confirmed, **Then** it is refused. Unassigned amounts remain explicit; no automatic residual assignment occurs.

### User Story 3 - Prepare and track accounting handoff (Priority: P1)

An operator prepares selected business evidence for external accounting and can explain what was included and what the receiving system actually confirmed.

**Why this priority**: Delivery and accounting acceptance must never be confused with operational recording.

**Independent Test**: Prepare a neutral package, repeat the same request and import synthetic source-backed item receipts for accepted, rejected and posted outcomes.

**Acceptance Scenarios**:

1. **Given** selected eligible evidence, **When** previewed, **Then** the operator sees exact items, versions, amounts, optional assignments, target profile and omissions before confirming preparation. Reading/previewing has no business write effect.
2. **Given** confirmed preparation, **When** downloaded, **Then** an immutable versioned package contains all selected items and stable identifiers. Download/preparation is not labelled transferred, accepted or externally posted.
3. **Given** external delivery/processing evidence, **When** imported, **Then** each receipt links to the exact target and item version, retaining source payload and distinct delivered/accepted/rejected/posted meaning. A bare success flag cannot prove external posting.
4. **Given** mixed outcomes, repeated receipts or a lost response, **When** inspected or retried, **Then** individual outcomes and unknown cases remain visible and no duplicate receipt/business effect is introduced.
5. **Given** source correction or a local reversal after handoff, **When** inspected, **Then** previous packages/receipts remain unchanged and a correction handoff is required. Reality never claims that the remote posting was automatically reversed.
6. **Given** a rejected or uncertain item, **When** a new package is requested, **Then** the system shows prior attempts and requires an explicit retry/correction decision. It does not silently generate another independent original delivery.

### User Story 4 - Control and explain the sidebooks (Priority: P2)

A finance user reviews operational balances, optional cost assignments and handoff discrepancies in the existing application.

**Why this priority**: Users need a coherent daily work surface rather than a second bookkeeping product.

**Independent Test**: Load more than a page of multi-currency events and compare Journal, Open Items, Payments and Handoff views with declared source/ledger/receipt facts.

**Acceptance Scenarios**:

1. **Given** journal filters and pagination, **When** totals are shown, **Then** they cover the entire selected scope, keep currencies separate and explain debit/credit direction and provenance. A filtered account/role need not balance and is not labelled a broken group.
2. **Given** optional cost assignments, **When** analyzed, **Then** assigned/unassigned amounts reconcile on their stated basis without being presented as recognized expense or cost-center profit. Missing net values remain missing.
3. **Given** operational recording plus package/receipt history, **When** reviewed, **Then** recorded, prepared, externally received and externally posted are separate evidence-backed statements, not one document status.
4. **Given** an empty tenant, errors, retired references or unsupported target requirements, **When** a screen opens, **Then** it gives the correct next action using existing shared patterns in both themes and all four UI languages.
5. **Given** a disposable local test database, **When** the new schema and fixtures are initialized, **Then** all entries use valid account IDs; new-model reversals and allocations preserve history. Old local test data need not be migrated.

### User Story 5 - Control permitted subledger accounts (Priority: P1)

An owner maintains a small catalog of valid operational accounts without adopting a full financial chart. Posting services validate these references consistently.

**Why this priority**: Free-form account strings cannot enforce which operational destinations are permitted.

**Independent Test**: Create or adopt the minimal accounts for the existing operational roles, record an invoice, block its counterpart account and attempt normal posting and exact reversal.

**Acceptance Scenarios**:

1. **Given** an empty tenant, **When** the owner previews and confirms the minimal built-in operational accounts, **Then** accounts and deterministic role destinations become available without a full external chart, statutory classifications or journal entries.
2. **Given** accounts entered manually or selected from external reference input, **When** saved, **Then** codes are unique within the tenant and active accounts have a supported operational role. Imported numbers do not determine roles automatically.
3. **Given** an unknown, wrong-tenant, blocked or role-incompatible account, **When** any normal posting is attempted, **Then** the shared service refuses the entire group with an actionable reason. Blocking after preview is rechecked at execution.
4. **Given** a supported event, **When** no account is explicitly selected, **Then** the service uses the uniquely configured active destination for each required role. Multiple eligible accounts are never resolved by guessing; a missing/blocked destination requires review.
5. **Given** a used account, **When** maintenance is requested, **Then** code/name edits retain its identity and audit context, deletion or reassignment of an established role is refused, and blocking affects new normal postings only. Exact reversal of historical entries may reuse the blocked account; replacement must meet current eligibility rules.
6. **Given** a target mapping, **When** an external reference changes, **Then** only new handoff preparation uses the new revision. The mapping neither changes a local gross amount into net revenue nor establishes target posting correctness.
7. **Given** a clean database, **When** minimal accounts and financial fixtures are created, **Then** explicit roles and required account IDs validate every posting. There is no old-string backfill or unresolved-role workflow.

### User Story 6 - Resolve declared cases for international handoff (Priority: P1)

An operator uses the same operational transaction logic across selling countries and maps explicitly declared cases to the external accounting target.

**Why this priority**: International handoff needs flexible supplied classifications without transferring tax determination to Reality.

**Independent Test**: Process an invoice containing two source-declared cases and a supplier component with an explicit Software coding group; resolve different target mappings while preserving the original gross subledger balances.

**Acceptance Scenarios**:

1. **Given** each of the eight financial transactions in posting-matrix.md, **When** recorded, **Then** the specified debit/credit roles and received amount basis apply through eligible explicit/default accounts. Drafts, orders and physical movements alone do not trigger recording.
2. **Given** supplied case codes on two components, **When** mapped through reviewed source references, **Then** each retains its actual scope and origin and resolves to its own target destination; the gross claim remains unchanged.
3. **Given** only customer country or missing tax data, **When** handoff is evaluated, **Then** no tax case is inferred. An explicit no-tax declaration remains distinguishable from unknown information.
4. **Given** case/group-specific mappings, **When** evaluated, **Then** exactly one eligible mapping is required for each profile-required component. Missing/ambiguous matches, conflicting assignments or invalid references create a review case; normal operational recording remains independent.
5. **Given** changed or retired case/group/assignment/mapping revisions after preview, **When** confirmed, **Then** stale preparation is rejected and earlier packages remain unchanged. Internal assignments disclose author/reason separately from source declarations.
6. **Given** a payment or a neutral profile without case-coded requirements, **When** prepared, **Then** absent invoice tax coding is not invented or made an unnecessary prerequisite. Competing simple-account and case mappings cannot silently select different destinations for the same component.

### User Story 7 - Resolve customer payment differences explicitly (Priority: P1)

An operator records actual money, distinguishes a claimed deduction from an accepted reduction and keeps excess payment available for allocation or evidenced refund.

**Why this priority**: Real cash, remaining claims and accepted concessions must not be conflated.

**Independent Test**: Use the 1,000 invoice cases in payment-differences.md: receipt 980 with accepted reduction 20, receipt 900 with disputed remainder 100, and receipt 1,020 with available credit 20.

**Acceptance Scenarios**:

1. **Given** receipt 980 against 1,000, **When** recorded without an accepted adjustment, **Then** actual payment is 980 and 20 remains open, even if discount terms explain it.
2. **Given** explicit accepted discount amount 20, **When** the reviewed adjustment is confirmed, **Then** cash remains 980, a separate evidenced reduction settles 20 and open balance becomes zero. No tax/discount amount is calculated.
3. **Given** receipt 900 and a customer claim withholding 100, **When** the explanation is recorded, **Then** 100 remains open. Accepting only 60 subsequently leaves 40 open and preserves the claimed-versus-accepted distinction.
4. **Given** actual receipt 1,020, **When** 1,000 is allocated, **Then** the invoice closes and 20 remains customer credit. It can be allocated to another same-party/currency invoice without another payment, or settled against an actual evidenced refund.
5. **Given** concurrent/duplicate adjustment, allocation or refund requests, **When** confirmed, **Then** no claim or available credit is over-consumed and no effect repeats. Existing credit evidence for the same reduction must be allocated rather than duplicated.
6. **Given** adjustment or refund reversal, **When** confirmed, **Then** the associated claim or credit reopens through existing allocation semantics. Reversing payment alone retains the separate accepted adjustment and exposes its correction option.
7. **Given** local accepted reduction lacking a tax breakdown required by the external target, **When** handed off, **Then** payment and reduction remain separate and missing required target data is explicit, without changing settled local balances.

### User Story 8 - Resolve supplier differences and see both credit positions (Priority: P1)

An operator handles supplier payment differences with the same control as customer receipts and sees available credits for both sides in one dedicated destination.

**Why this priority**: Neither supplier overpayments nor unallocated credit notes should disappear when an invoice closes; an unsupported deduction must not extinguish a payable.

**Independent Test**: Mirror the customer fixture with supplier cash paid 980/900/1,020 and documented supplier concessions; inspect payment and credit-note origins in both Available credits tabs.

**Acceptance Scenarios**:

1. **Given** supplier invoice 1,000 and actual payment 980, **When** recorded, **Then** 20 remains payable until a stated documented discount/reduction is explicitly confirmed. Withholding explanation alone never settles it.
2. **Given** payment 900 and supplier-agreed reduction 60, **When** confirmed, **Then** a separate payable-debit adjustment leaves 40 open. Internal intent alone cannot authorize a supplier liability reduction; a credit note already covering it is reused.
3. **Given** actual supplier payment 1,020 with allocation 1,000, **When** read, **Then** 20 is available supplier credit, reusable on another same-supplier/currency invoice or settleable against an actual received refund, without another payment or fake credit note.
4. **Given** customer/supplier unallocated payments and credit notes, **When** Available credits is opened, **Then** separate tabs show each party/currency's complete available totals and actual origins once, even with no open invoice. Dual-role parties and unlike currencies are never netted together.
5. **Given** a selected credit origin, **When** allocated/refunded or reversed, **Then** all linked views agree on availability and history. Concurrent or repeated actions cannot consume the same payment/credit-note origin twice, including multi-origin selection.
6. **Given** supplier payment, adjustment or refund reversal, **When** confirmed, **Then** payable or available credit is restored with the appropriate sign, while separately evidenced reductions remain independently correctable. Source, mapping and missing-tax-data rules mirror the customer side.
7. **Given** V09, **When** used in the supported languages, themes and viewport sizes, **Then** filters, full-scope totals, origin detail and direction-specific confirmed actions follow shared patterns and are reachable from partner/payment/open-item details.

### User Story 9 - Carry existing debts and credits into Reality (Priority: P1)

An owner imports existing customer/supplier open positions from a previous system without manufacturing new invoices, turnover or cash movement.

**Why this priority**: A company must be able to start with its actual outstanding items and subsequently settle them.

**Independent Test**: Import customer receivable 1,000, customer credit 100, supplier payable 800 and supplier credit 50; verify the four independent positions and their normal subsequent allocation/refund paths.

**Acceptance Scenarios**:

1. **Given** stated individual opening items and cutover/source identity, **When** previewed and confirmed, **Then** balanced control/neutral-counterpart entries are created without sales, expense or cash effects, with original references and supplied due dates retained.
2. **Given** only a supplied partner/direction/currency summary, **When** imported, **Then** it is labelled Summary opening item; absent due dates remain unknown and debts/credits are not netted. Overlapping later detailed imports require reconciliation.
3. **Given** imported receivables/payables/credits, **When** payments, eligible credit allocations, adjustments or evidenced refunds occur, **Then** the same shared limits and views apply and opening credits are visible in both V09 tabs without fake invoice/payment/credit-note evidence.
4. **Given** replay, changed snapshot, an already present local item or later receipt of the original source invoice, **When** processed, **Then** no second financial effect is automatically created. Ambiguous cutover coverage preserves evidence and holds posting for review.
5. **Given** an opening item with subsequent allocations, **When** reversed/corrected, **Then** history and actual later cash remain, allocation consequences are previewed, and replacement/reallocation is explicit and concurrency-safe.
6. **Given** a normal handoff or sales/cash activity report, **When** read, **Then** opening items are not represented as newly issued invoices or new cash. V10 shows exact direction/currency totals, provenance and duplicate/conflict state through the shared UI patterns.

### User Story 10 - Control complete trade-finance paths and explain them to agents (Priority: P1)

An operator or agent can distinguish actual money, provider-held balances, earmarked advances, held payables and the known goods/invoice/settlement chain without inventing missing evidence.

**Why this priority**: Correct invoice balances alone do not explain how a trading company's money moves or which action is currently safe and authorized.

**Independent Test**: Run the provider 100/3/97 fixture, advance 200 to order A, held supplier invoice, different-control-account allocation and incomplete legacy billing chain using the same public shared reads/actions.

**Acceptance Scenarios**:

1. **Given** completed PSP capture 100, stated fee 3, dispatched payout 97 and matched bank receipt 97, **When** recorded, **Then** the customer is settled once, bank receipt is 97 and provider/in-transit movements reconcile without invented fees or duplicate cash. Pending authorization/payout is not completed money.
2. **Given** a stated reserve, provisional chargeback or refund and later repeated statement/bank evidence, **When** processed, **Then** available/restricted/disputed provider positions and actual customer effects remain distinct; missing or ambiguous event identity/amounts require review instead of duplicate recording or invented customer debt.
3. **Given** customer or supplier advance 200 assigned to order A, **When** unrelated order B is invoiced, **Then** the earmarked amount is not freely usable. Confirmed settlement of A's linked invoice consumes the assignment and payment availability atomically; cancellation creates review rather than automatic refund.
4. **Given** a supplier payable hold placed after preview, **When** a new payment/allocation/run is confirmed, **Then** the shared policy refuses it. Actual bank evidence is still recordable and can be explicitly reconciled with a visible during-hold finding; no debt is erased.
5. **Given** available credit on control A and invoice on compatible control B, **When** matched, **Then** a reviewed balanced same-role reclassification and its two same-account allocations are atomic, preserve total role balance and create no cash; unsupported party/currency/role/account conditions fail.
6. **Given** partial/consolidated billing, returns and source-stated charges, **When** trade control is read, **Then** actual line relationships and financial allocations explain the stages without repeated whole-invoice attribution. A physical return is not automatically a credit/refund.
7. **Given** migrated or incomplete linkage, **When** evidence is inspected, **Then** Linked, Explicitly not applicable and Unknown are distinct. Missing coverage yields an unknown billing/receipt relationship rather than an authoritative unpaid/unbilled finding.
8. **Given** a paginated agent query or confirmed mutation, **When** explained, **Then** the structured contract provides exact full-scope measures, evidence/decision origins, cutoff, missing information, eligible actions and verified committed outcome. Reads create no duplicate Facts or authorization.

### Edge Cases

- Same account code in different tenants; duplicate codes within one tenant; multiple accounts sharing a role; stale account destination or blocked account at execution; reversal to a blocked historical account.
- Same human document number in different tenants or sources; ambiguous cross-source identity requires review.
- Gross-only evidence, mixed supplied tax codes, zero-rated versus unknown, document summaries versus line amounts, credits and rounding components.
- Gross-only invoices may be operationally valid while a target's net/tax requirement remains unmet.
- A gross counterpart named `sales_revenue` or `inventory` does not prove net revenue or inventory valuation.
- Source-only financial evidence must use the existing faithful evidence path before shared posting; unsupported translations remain explicit.
- Owner revocation or paused automation, concurrent retry, stale preview and successful evidence intake followed by posting failure.
- References retired after historical use; changed internal assignment after export; incomplete optional allocation.
- Correction after remote acceptance, receipts for older versions, partial package outcomes, unmatched remote identifiers and conflicting receipts.
- A receipt may arrive directly as posted without a separate delivered receipt; do not invent missing intermediate events.
- Multi-currency source history, date boundaries, tied ordering, empty scope versus unavailable data.
- Zero-effect evidence creates no zero-amount journal entries and remains distinguishable from a failed interpretation.

## Requirements

### Functional Requirements

- **FR-001**: Preserve current balanced operational posting roles and gross control balances for supported invoice, credit, payment and refund services; external chart configuration MUST NOT be a prerequisite.
- **FR-002**: Permit explicitly confirmed owner-scoped automatic recording by source, supported financial type and approved interpretation/service contract revision, disabled by default. Intake authority MUST NOT imply financial authority; execution rechecks permission and scope.
- **FR-003**: Successful translation MUST leave durable recoverable eligibility for shared operational posting. Posting failure preserves received evidence and exposes a separate outcome; retry cannot depend on an open browser.
- **FR-004**: Prevent duplicate effects across delivery replay, concurrent adapters and response loss using stable business-effect identity. Source/configuration changes MUST NOT authorize another original; ambiguous equivalence requires review.
- **FR-005**: Preserve current settlement, credit and complete-group reversal semantics. Corrections append records and never imply external correction or shipment/inventory changes.
- **FR-006**: Retain stated net/tax/gross/base amounts, currency and source account/tax/cost-center references at actual evidence granularity. Missing values remain distinct from zero; no missing tax, net or valuation amount is computed.
- **FR-007**: Distinguish document tax summaries from line components and select explicit handoff amount roles so the same received amount is not counted twice or allocated to unsupported lines.
- **FR-008**: Support optional internal cost-center references and explicit amount assignments to actual received components, recording basis, author, reason and revision. Splits cannot exceed the component, mix bases/currencies or silently fill a remainder; unassigned remainder remains visible.
- **FR-009**: External account, tax-code and cost-center references are target-specific handoff annotations/mappings, not a local authoritative chart or tax engine. Missing references block only the target requirements that actually need them.
- **FR-010**: Used references and prepared mapping/assignment revisions remain readable after changes or retirement. Internal assignment MUST NOT overwrite source-stated coding or change operational postings.
- **FR-011**: Provide separate operational-recording and handoff-readiness views with precise missing/conflict reasons; no operational or remote-posting status field is added to Document.
- **FR-012**: Provide a neutral, versioned export profile and immutable prepared package, containing selected evidence versions, exact amounts, direction/kind, related corrections, optional annotations and stable identities. It MUST identify its scope and omissions and MUST NOT claim vendor import compatibility.
- **FR-013**: Preview and confirmation MUST bind exact evidence, assignment and profile revisions; stale previews fail safely. Repeating completed preparation returns the same package, and download alone does not assert delivery.
- **FR-014**: Record external outcome evidence through lossless SourceRecords and shared interpretation, linked to exact target/item/version and external references where supplied. Distinguish delivered, accepted, rejected and posted by what the source actually attests.
- **FR-015**: Receipt ingestion MUST be idempotent and support partial, out-of-order, conflicting and unmatched receipts without discarding history or inferring successful booking. Unknown outcomes remain unknown pending evidence.
- **FR-016**: Subsequent corrections MUST retain prior packages/receipts, identify the original target item and expose correction readiness separately. Retries/corrections require explicit bounded review; no automatic remote reversal or blind resend is authorized.
- **FR-017**: Journal, operational role detail, Open Items and Payments MUST use complete-scope server-side filtering/totals, stable pagination, separate currencies and shortest-link inspection. Label existing gross role amounts honestly, not as P&L, net revenue or valuation.
- **FR-018**: Cost assignment analysis MUST retain the explicit net/gross/component basis, separate currencies and show unassigned and missing-information scope. It MUST NOT claim a complete expense ledger or profitability.
- **FR-019**: Handoff reconciliation MUST show local recording, prepared versions and external evidence independently; any totals compare only compatible amounts/currencies/versions actually supplied by both sides. Remote balance reconciliation is unavailable without matching external balance evidence.
- **FR-020**: Implement the screen/interaction contract in views.md using existing Finance Control, shared components, Inspector, localization and access policy. Configuration remains reachable in an empty tenant; no full-accounting navigation is added.
- **FR-021**: All mutations use shared tools/services and existing confirmation/access policy; automatic authority is narrowly scoped and never confirms Chat/MCP proposals. Account maintenance, posting-destination configuration and target/profile/automatic-authority activation require owner rights.
- **FR-022**: Use a clean local development cutover with regenerated disposable fixtures; preservation of the sole tester’s old account strings and financial test rows is not required. New-model evidence, ledger and allocation history MUST remain immutable and traceable. Do not build a second journal, fiscal periods or gross-to-net conversion.
- **FR-023**: Distinguish source document/event dates, local recording time and external occurrence/receipt times. Viewer timezone does not change the meaning of a source date; no fiscal period or period-lock claim is introduced.

- **FR-024**: Provide tenant-scoped subledger accounts with opaque ID, unique code, name, supported operational role and active/blocked state. Support manual maintenance, confirmed minimal operational setup and reviewed adoption of selected externally supplied references; account numbers MUST NOT imply a role.
- **FR-025**: Every normal posting path MUST resolve an existing same-tenant active account with the required role. For an invoice-bound control leg, resolve the existing invoice account first; a different control account requires FR-053 reclassification. For other eligible legs use an explicitly selected compatible account or the uniquely configured destination for that role; missing, ambiguous or blocked destinations fail without partial posting. Revalidate account/configuration revisions at execution, including concurrent blocking.
- **FR-026**: Used accounts MUST retain identity and any established operational role and cannot be deleted. Code/name changes are audited. Blocking refuses new normal postings but permits an exact historical inverse on the original account; a replacement is a new normal posting. Role-based operational balances MUST cover all matching accounts, preserving settlement after destination changes.
- **FR-027**: External account mappings MUST be target-specific, optional and versioned, referencing the stable local account ID when mapping a local account. Local recording MUST NOT depend on external mapping, and a gross operational counterpart MUST NOT be advertised as a valid net financial posting merely because a target account reference exists.
- **FR-028**: Create the minimal operational accounts with opaque IDs and explicit supported roles on a clean schema. LedgerEntry MUST use a required account_id with no retained legacy account-string authority, backfill or unresolved legacy classification flow. Update fixtures and callers to the new model; reset/reseed is explicit and limited to a positively identified disposable local/test database.

- **FR-029**: Implement the fixed eight-transaction role/side/received-amount matrix in posting-matrix.md through the shared services. Explicit/default account selection must preserve that matrix; draft creation, orders and physical movements alone do not post financial entries.
- **FR-030**: Provide defined tenant CaseCode references and source-code mappings plus confirmed internal assignments at actual received-component scope. Codes must be explicit and valid; country, rate, descriptions or missing tax must not infer a treatment. Unknown and explicit no-tax are distinct.
- **FR-031**: Support optional defined CodingGroup references and explicit component assignments when target destination discrimination requires them. Groups are distinct from cost centers and cannot be guessed from descriptions.
- **FR-032**: Resolve versioned target mappings by tenant, target, transaction, case and declared group mode as specified in posting-matrix.md. Exactly one match is required for each case-coded profile component; overlap is rejected and no/multiple matches produce review. Simple account mappings and case mappings must have explicit non-competing scopes.
- **FR-033**: Preserve source/internal case and group assignment provenance, audit owner mapping activation and freeze all selected revisions in prepared items. Stale or retired configuration prevents new preparation/assignment as applicable without changing historical packages or operational balances.
- **FR-034**: Expose the read-only transaction matrix, case/group/source-mapping and target-mapping editors, evidence preview and shared readiness explanations described in posting-matrix.md. No country tax engine or free-form operational posting editor is introduced.

- **FR-035**: The customer receipt flow MUST record actual cash independently of explicit bounded invoice allocations; overpayment remains unallocated customer credit. It MUST reuse standalone payment recording and not relax invoice allocation limits or record a second receipt when allocating existing money.
- **FR-036**: Claimed discount/withholding and ordinary underpayment MUST remain open unless an explicit accepted adjustment or existing credit settles them. Explanations alone do not change aging, balances, collection policy or document status; no tolerance auto-write-off is allowed.
- **FR-037**: Provide an explicitly confirmed customer settlement adjustment for a stated discount, agreed deduction or accepted small remainder, with immutable internal/source evidence, reason, actor and amount. Post a separate balanced non-cash reduction and allocate it to the invoice; never fabricate an external credit note or calculate missing discount/net/tax amounts.
- **FR-038**: Adjustment acceptance MUST validate remaining claim, account eligibility, source/effect identity and stale preview; reuse existing credit for the same reduction. Combined payment/allocation/adjustment confirmation MUST be atomic and idempotent, while standalone actual payment remains possible independently.
- **FR-039**: Available overpayment credit MUST be visible and may be explicitly allocated to another same-party/currency invoice or settled against an evidenced refund through shared primitives. No fake credit note, cross-party netting, currency conversion, automatic bank execution or excess refund is permitted.
- **FR-040**: Full adjustment/refund reversals MUST preserve history and restore claims/credit through effective-allocation rules. Payment reversal MUST NOT silently cancel a separately accepted reduction. Concurrent allocation/adjustment/refund commands MUST serialize availability checks and reject duplicate or over-consuming effects.
- **FR-041**: Extend the transaction matrix, shared action/read catalogs and V01–V06/V08/V09 screens as detailed in payment-differences.md. Views and handoff MUST distinguish cash, accepted reductions, unresolved claims and available credit, retain explicit external tax-data gaps and never report a non-cash adjustment as received money.

- **FR-042**: Provide supplier equivalents of FR-035–FR-040 with the explicit directions and authority rules in payment-differences.md: actual cash paid, bounded allocations, documented supplier-agreed reductions, open unaccepted withholdings, reusable overpayments and evidenced refunds received. Supplier liability reduction requires recorded entitlement/agreement, not unilateral intent; existing credit evidence is reused. Preserve direction-correct concurrency, reversal and handoff semantics.
- **FR-043**: Provide canonical V09 Available credits with Customers/Suppliers tabs, complete-scope party/currency totals, payment, credit-note and opening-credit origins, evidence drilldown and explicit allocation/evidenced-refund actions. Derive availability once from active control entries and effective allocations; never automatically net open invoices, currencies or dual-role party balances, duplicate origins or treat inverse/reduction entries as reusable credit.

- **FR-044**: Support explicitly confirmed opening customer receivables, customer credits, supplier payables and supplier credits using stated outstanding amounts and a neutral operational opening counterpart, as defined in opening-items.md. The import creates no revenue, expense or cash movement.
- **FR-045**: Opening evidence MUST retain partner, direction, currency, cutover/source identity and individual/summary mode, plus original reference/dates where supplied. Summaries remain separate by partner/direction/currency; missing due dates or historical allocations MUST NOT be invented.
- **FR-046**: Opening import MUST be owner-authorized, preview/revision bound, atomic per bounded batch and idempotent by stable source item/scope rather than filename/request alone. Replays, changed snapshots, existing items, later original documents and overlapping summary/detail coverage MUST prevent automatic duplicate posting and expose ambiguity for review.
- **FR-047**: Opening items MUST participate in shared settlement, adjustment and available-credit/refund reads/actions with preserved identity and current availability limits. Exact reversal/correction must expose downstream allocation effects, preserve actual cash history and require explicit replacement/reallocation without concurrency over-consumption.
- **FR-048**: Provide V10 Import opening items and V03/V09/Inspector origin detail. Exclude opening evidence by default from normal new-business handoff and sales/cash metrics; explicit supported opening-item transfer must retain its purpose and not assert external posting. Shared catalogs and planned verification must cover all four directions.

- **FR-049**: Support distinct recorded bank/cash/provider-clearing, in-transit, restricted and disputed money paths using explicit source-backed amounts/events as defined in trade-finance-controls.md. Pending authorizations and notifications cannot imply settled cash; a completed customer capture and provider payout are different effects.
- **FR-050**: Match provider captures, fees, refunds, retentions, chargebacks, payouts and bank evidence by explicit economic-event relationships with stable identity, current revision and same-currency scope. Never fabricate fees/amounts from discrepancies, double-count repeated sources or reopen customer debt from a provisional provider dispute alone. Incomplete/unsupported conversion cases remain explicit.
- **FR-051**: Permit confirmed source/internal advance earmarks against actual available customer/supplier payments and exact intended orders, with bounded amount/currency and explicit release/reassignment. Earmarks restrict unrelated consumption without changing ledger balance; matching invoice settlement must atomically consume the earmark and credit, with no double-use under concurrency.
- **FR-052**: Provide auditable payable holds with reason/responsibility and explicit release. Enforce them in shared new-payment/run/allocation eligibility and at confirmation, without changing debt/aging or suppressing actual cash evidence. Reconciliation of an already executed held payment is a separate evidence-bound action and visible exception.
- **FR-053**: Preserve same-concrete-account settlement. Invoice-bound operations select the original eligible control account; cross-account credit use requires the explicit balanced same-role reclassification and paired allocations defined in trade-finance-controls.md. No implicit role-only allocation, blocked-account bypass or cross-party/currency netting is permitted.
- **FR-054**: Provide shared trade-finance control across actual order/invoice lines, Commitments, delivery/receipt/return Movements, credits, settlements and accepted reductions. Cover partial and consolidated billing and unallocated charges without inferring financial effects from goods movements or repeating document amounts per line.
- **FR-055**: Distinguish linked, explicitly not-applicable and unknown evidence relationships with scoped source/interpretation/internal provenance. Existing missing-billing/receipt/credit checks must honor source coverage; unknown migration links cannot become proved absence or authorize financial actions.
- **FR-056**: Implement the structured shared finance explanation contract in agent-finance-contract.md with measure/basis/currency, full-scope totals and continuation/cutoff semantics, authoritative input IDs, evidence/decision provenance, missing/conflicting information and current eligible actions. No agent-only business calculation or duplicated Fact representation is allowed.
- **FR-057**: Extend capability catalogs and post-action verification for every new finance action, with explicit authority/preconditions, revision/idempotency boundaries and authoritative result reads. Distinguish committed internal effect, refusal, unknown execution and pending external evidence; agents cannot approve their own mutations or infer external success.
- **FR-058**: Deliver V11 Money accounts & settlements, V12 Advances and V13 Trade finance control with existing-view/settings/Inspector extensions and shared projection services as specified in trade-finance-controls.md. Apply the full localization, responsive, keyboard, theme, isolation and complete-scope UI/read verification matrix.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → operational Reality. External receipts have their own source/evidence chain; internal cost assignment is explicit classification, not a new financial authority.
- **DR-002**: Use opaque tenant-scoped IDs and shortest true links. An annotation on a received component reaches its document/source through that component; no duplicate document/line/source FKs merely for convenience.
- **DR-003**: Every business record, query, mapping, package, receipt and job enforces tenant scope and target identity, including colliding human references.
- **DR-004**: Keep source, ledger, prepared packages and receipt history immutable. Derived readiness, open amounts and external outcome summaries are not stored as new authoritative financial facts.
- **DR-005**: Use Decimal and exact balanced posting boundaries; mapping or assignment never recalculates a supplied total or invents missing evidence.
- **DR-006**: Shared services/tools own all behavior. Durable background work uses the existing registry/worker contract; this scope adds no direct external-effect handler or timer.
- **DR-007**: The later plan must justify each schema addition, migrate additively, extend data/isolation/event/command/Inspector catalogs and verify existing operational regression stories.

### Key Entities

- **SubledgerAccount / Role destination**: A permitted local account and its deterministic use by existing operational services; no statutory financial chart.
- **Existing LedgerEntry, LedgerReversal, SettlementAllocation**: Operational financial authority retained as-is in meaning.
- **Received financial component**: Explicit source-stated amount/coding information at document or line granularity.
- **CostCenterReference / Assignment revision**: Optional operational responsibility and assignment of a stated amount.
- **CaseCode / CodingGroup / Assignment revision**: Defined declared-case and optional classification references, with actual evidence scope and explicit source/internal authority.
- **Accounting target / Mapping revision**: Identity and explicit handoff requirements of the destination, not a financial chart.
- **HandoffPackage / Item**: Immutable prepared selection and payload linked to exact evidence versions.
- **Customer/supplier settlement-adjustment evidence**: An explicitly accepted/documented non-cash claim or liability reduction, posted and allocated through existing ledger primitives.
- **Opening-item evidence / Import coverage**: Stated carried outstanding positions with source/cutover identity, represented through the existing ledger and allocations.
- **Money-event/settlement matching**: Source-backed bank/provider relationships with recorded clearing, restriction and transfer purposes.
- **Advance assignment / PaymentHold / Link coverage assertion**: Explicit operational decisions and evidence coverage, not alternate financial balances or Document statuses.
- **External receipt evidence**: What a destination actually confirms for an identified item/version.
- **Recording authority / Outcome**: Narrow automatic authority and durable recovery facts, reusing existing mechanisms where possible.

## Success Criteria

- **SC-001**: Supported fixture events record exactly once; EUR 119 less an allocated EUR 50 remains EUR 69 under retry; reversing that payment reopens EUR 119 without deleting allocation history.
- **SC-002**: Optional 600/400 net assignment explains EUR 1,000 while leaving the EUR 1,190 payable unchanged; missing values and unassigned amounts remain explicit.
- **SC-003**: Preparation/download alone never produces an externally posted label; every positive external assertion in the fixture has exact receipt evidence.
- **SC-004**: A clean disposable database can be migrated, initialized and populated reproducibly using the new account IDs; new-model reversal/allocation history and currency/basis distinctions remain correct.
- **SC-005**: Every requirement has planned proof; screens pass shared-state, keyboard, four-language and both-theme checks at mobile, tablet and desktop widths before release.
- **SC-006**: Every normal posting rejects invalid account references consistently, while exact historical reversals and role-wide balances remain correct after blocking or changing a default destination.

## Assumptions and Dependencies

- The owner requested closure of the reviewed trade-finance and agent-traceability gaps; the concrete bounded rules are documented in the companion contracts.
- The owner accepted the subledger/external-accounting product boundary and explicitly requested the minimal managed account catalog. Detailed structures and proof remain subject to normal review and planning.
- No external accounting vendor has been selected. V1 provides an explicitly neutral downloadable package and importable evidenced outcomes; it does not send data directly or promise compatibility with an unnamed vendor.
- Existing operational postings remain gross-based. Source-stated net/tax components enrich explanation and handoff; they do not turn those postings into a net-accounting journal.
- Optional cost attribution belongs to the narrow received component it describes. It need not split an existing gross ledger line to assign a net cost; doing so would conflate different bases.
- Existing multi-currency operational behavior remains supported, without consolidated converted totals.
- An eventual live connector requires explicit vendor semantics, authorization, delivery idempotency and reconciliation design under the shared external-effect rules.
- Internal structures and views are included because the user explicitly requested them; they are not an approved physical schema or implementation plan.

## Open Questions

No unresolved clarification markers. Vendor selection is deferred scope, not a blocker for the neutral package contract. Product review should confirm the proposed first-release handoff and cost-assignment detail before technical planning.

## Requirement Traceability

Individual proof rows are in [verification.md](verification.md).

| Requirement | Scenario(s) | Planned proof |
|---|---|---|
| FR-001–FR-005 | US1.1–6 | Existing service parity, authorization and concurrent replay |
| FR-006–FR-010 | US2.1–5 | Received components, optional assignment and frozen mapping |
| FR-011–FR-016 | US2.3, US3.1–6 | Independent readiness, immutable packages and external receipts |
| FR-017–FR-020 | US4.1–4 | Complete-scope views, labels and UI matrix |
| FR-021–FR-023 | US1.3, US3.1–6, US4.5 | Access, clean local initialization and date semantics |
| FR-024–FR-028 | US5.1–7 | Account eligibility, role destinations, blocked reversal, mappings and clean initialization |
| FR-029–FR-034 | US6.1–6 | Fixed matrix, declared cases, exact resolution and revision/UI proof |
| FR-035–FR-041 | US7.1–7 | Actual cash, claimed/accepted reductions, excess reuse/refund and concurrent correction proof |
| FR-042–FR-043 | US8.1–7 | Supplier direction/authority parity, both credit tabs, exact origin availability and UI checks |
| FR-044–FR-048 | US9.1–6 | Four opening directions, snapshot identity/coverage, shared settlement and V10 proof |
| FR-049–FR-058 | US10.1–8 | Money-event identity, advance/hold constraints, cross-account conservation, coverage and agent proof |
| DR-001–DR-007 | US1–US10 | Provenance, tenant isolation, immutability, shared services and catalogs |

## Authorized active-stack integration — 2026-09-09

The owner approved continuing with integration into the actual local application, targeted rebuilding of disposable local test data and end-to-end sales/purchase verification. Preserve the newer unified shell, lot-expiry and subsequent read-performance work. Transfer only the implemented account slice. Use migration `0048_finance_accounts` after `0047_merge_demo_lot_expiry`; never apply the root migration chain to this database.

The account panel mounts in unified company settings using current `br-*` controls and theme tokens; the journal displays concrete account code/name. Existing services and proposal confirmation remain the authority. No new financial features or schema beyond the reviewed three-table slice are added.

Before local cutover, create a private backup and rehearse the combined schema on disposable PostgreSQL. Stop writers for the cutover. Rebuild only explicitly selected local business test data, preserving login/account access where practical; do not remove PostgreSQL or object-storage volumes. Seed through shared company/demo services. Verify the actual localhost application and sales/purchase invoice, partial/full payment, credit, refund and reversal paths. Retain a recoverable backup until verification completes.

Constitution review: PASS. Same account identity/evidence model, tenant-scoped services and confirmed actions; no derived Facts, financial accounting authority or external effects. Analysis: no unresolved requirements or critical integration finding; the exact target migration and UI mounting point supersede root-only limitations for this integration.

Account configuration is available to confirmed owners of active practice companies as well as ordinary companies. Temporary lessons and archived companies retain their existing mutation restrictions.

## Available-credit register slice (2026-09-09)

FR-039/FR-042 are delivered incrementally. The next read-only slice exposes customer
and supplier available credit from active payment and credit-note control entries,
even without open invoices. Amounts are derived from both endpoints of effective
allocations; reversed groups are excluded. Results retain separate currencies,
concrete accounts, party, original evidence and allocation IDs. Blocked accounts
remain visible as historical holdings. Existing credit-note-only and invoice views
keep their contracts. New adjustment, guided overpayment and refund actions remain
separate, unfinished tasks. No schema or monetary authority is added.

## Separate accepted-adjustment slice (2026-09-10)

Implement FR-036–FR-040/FR-042 for a separately confirmed, invoice-bound accepted
reduction after or independently of actual payment. Categories are early-payment
discount, agreed deduction and accepted small remainder. Require a positive stated
amount, nonempty reason, and supplier entitlement/agreement text. Never calculate
from a percentage or create cash. The owner reviews amount, currency, remaining
claim, original control account and reduction counterpart before confirmation.
Use dedicated customer/supplier adjustment Documents backed by an immutable internal
SourceRecord recording the entered decision and confirming actor. Optional external
source/effect identity cannot be consumed twice. An external credit-note source
must be allocated as existing credit instead. No new balance table is needed.
The accepted adjustment and allocation reverse together through the existing exact
posting reversal; real payments remain independent. New roles are explicitly
configured through account settings; missing configuration prevents acceptance.
Combined payment/adjustment editing, external reconciliation and guided excess
refunds remain subsequent slices.

## Guided payment and credit lifecycle slice (2026-09-10)

The owner approved continuing FR-035–FR-043 with a guided, explicitly confirmed
customer/supplier settlement flow. Record the actual stated payment, allocate an
explicit stated part to one selected invoice, and optionally accept a separately
stated reduction with the existing reason/agreement requirements. Missing reduction
configuration does not block ordinary payment. A shortfall stays open by default.
A payment above the allocation leaves available credit on the original payment.
Existing payment or credit-note credit can be allocated to a matching invoice without
new cash, or consumed by recording an actual refund. No bank execution is performed.

Preview separately shows actual cash direction/amount, allocation, reduction, remaining
invoice claim and remaining credit, with original evidence and concrete account links.
All effects and the receipt commit atomically after owner confirmation. The same
proposal replays its receipt; intervening finance changes invalidate its revision.
External source/effect identity is required as a pair when supplied and prevents
repeating the same payment/refund across source versions. Manual confirmations retain
entered reference, effective time, actor and decision as immutable source evidence.
No source amounts are inferred from invoice totals. Cross-party, cross-currency,
cross-account, blocked-account, reversed and over-consumed credit is rejected.

Acceptance: for both sides, 98 paid/100 open leaves 2 open unless an explicit 2
reduction is accepted; 102 paid/100 allocated leaves 2 credit. Reuse 1 credit on a
second invoice without cash, refund the remaining 1, and reverse that refund to
restore 1 credit. Reverse a reduction without reversing payment. Exercise stale,
concurrent and repeated confirmations, injected rollback and tenant isolation.
The existing strict invoice-payment commands retain their limits.

## Opening-position delivery slice (2026-09-10)

The owner approved implementing the next operational opening-position increment:
manual, bounded batches (1–100 items) for all four directions, with optional links
to already retained source evidence. The first screen supports adding/removing
explicit rows; a new file-upload subsystem is not part of this increment. Record
source namespace, snapshot key, cutover date, individual/summary coverage, stable
source item key, party, direction, currency, positive stated residual, reference,
reason and optional original document/due dates. Keep unknown aging explicit.

Use one neutral opening-counterpart role and dedicated opening evidence, never fake
invoices/payments. Reuse shared settlement, reduction, credit and exact reversal.
Each source/party/direction/currency scope owns one snapshot/cutover and coverage
mode. Additional individual items may extend that same scope; changed snapshots,
repeated item identities and any summary/detail overlap are refused for review.
A different source namespace does not silently replace an existing scope.

Prevent normal historical financial posting into covered positions: exact covered
source-item identity never posts twice; undated or pre-cutover invoices/credits/cash
require reconciliation. Cash after cutover requires an explicit observed timestamp.
Retained later original evidence remains inspectable without a new financial effect.
Existing apparently covered financial postings prevent opening import. Corrections
reverse the original group through the existing reviewed reversal, retain coverage
identity, and use an explicit new item identity for any replacement; no hidden
reallocation. Opening evidence remains excluded from new-sales/cash activity.

Opening coverage checks preserve whether an actual cash timestamp was supplied.
Where no opening coverage applies, a legacy default timestamp is captured once per
posting group so both sides retain the same provable occurrence time.

## Managed-reference delivery refinement (2026-09-10)

FR-008/010/021/030/031 are delivered incrementally through a tenant-owned catalog
of cost centers, case codes and coding groups. Each reference has an immutable
opaque identity and kind, a code unique within tenant and kind, a name, active or
blocked state, and a revision. Codes remain immutable in this slice to prevent
reuse of a historical business label; names may change. Owners review and confirm
creation, renaming, blocking and reactivation with a nonempty reason. Members can
read and search. Each accepted change preserves before/after values, reason, actor
and action in immutable BusinessEvent evidence. Replayed confirmation has one effect;
stale review and foreign, wrong-kind or blocked references are refused.

Acceptance: create one reference of each kind; preview has no catalog effect;
confirm and replay yield the same receipt; rename preserves identity and prior
name in history; block forbids new use while history remains readable; reactivate
permits use. Same code across kinds/tenants is valid, same kind/tenant is rejected.
List and history are paged (default 50, maximum 200), searched server-side and
tenant scoped. No automatic country/tax interpretation, assignments, amount
allocation or ledger changes are part of this increment.

## Component attribution delivery refinement (2026-09-10)

FR-006/007/008/010/021/030/031: customer/supplier invoices and credit notes expose
received document summaries and individual lines separately. Documents with lines
allow attribution only on those lines; line-less evidence uses its document amount.
The typed Document/DocumentLine gross amount remains authoritative. Optional explicit
`reality_finance_v1` source detail supplies nullable `net`, `tax`, `base`, optional
`gross`/`currency`, and unchanged `codes` for display. Document detail comes from its
SourceRecord payload; line detail comes from lossless DocumentLine payload. No other
source fields are guessed. Zero differs from missing. Contradictory gross/currency,
invalid decimals and unsupported detail versions refuse attribution, without changing
existing local postings. This is a declared extraction contract, not a tax engine.

Owners can assign a defined active case code and coding group plus up to 100 distinct
active cost-center shares to one component, selecting received net/gross/base.
Shares are positive exact decimals, at most the selected nonnegative received basis;
empty shares permit classification even with an unknown basis. Partial assignment
shows the unassigned amount, never fabricates a balancing share. Currency is inherited
from evidence. Replacing/clearing creates an immutable revision with reason, actor,
action and historical reference labels. Blocking/renaming references preserves old
revisions; new revisions must use currently active references of the right kind.

Preview and approval validate the same evidence fingerprint and finance revision.
A repeated approval returns its original receipt; stale or foreign references fail
atomically. The first accepted assignment normalizes its selected component into
`financial_component`; read/preview never persists component or assignment records.
Immutable components must still match underlying evidence before a later assignment.
No financial entry, allocation or invoice/payment balance changes.

Acceptance: received net 1000/tax 190/gross 1190, split net 600/400, gross remains1190;
partial 600 leaves400; missing net refuses shares, stated zero permits zero shares;
summary/line values never double count; case/group/center kinds cannot be interchanged;
clearing and replacing preserve history, and concurrent/stale confirmations cannot
overwrite an intervening decision. Members can inspect the same component/history.
Global cost-center reports, arbitrary source mapping, component intake UI and external
accounting handoff remain later slices.

## Operational transaction matrix slice

Expose the eight fixed invoice/credit/payment/refund directions, two accepted settlement
reductions and four opening directions as a shared read of configured local defaults.
For every debit/credit role show its account identity, code/name and configured, missing
or blocked status. Show the stated amount basis and explicit evidence/confirmation
requirements. These are default settings, not a preview or authorization for a specific
transaction: linked settlement controls retain their original account, explicit eligible
selection is validated by the existing action, and reversal uses the original group.
Orders, reservations, movements and allocation do not create financial postings here.
Read-only Company account settings, CLI, API and MCP must return the same matrix,
including empty-company missing defaults, without creating accounts or finance state.
Changing a default refreshes the matrix without changing prior postings. No schema,
new posting algorithm, country inference or external-target mapping is introduced.
Customer credit-note financial attribution must accept canonical `credit_note` evidence
created by the existing sales-credit service, restoring the prior four-direction promise.


Mobile register rows and their Financial detail actions must remain reachable when the filter and summary area is taller than the remaining viewport. Below 640px the existing in-flow footer must not be overridden by desktop fixed-footer measurement.


## Source classification delivery slice

FR-030, FR-033 and FR-034 deliver explicit source-code classification for case codes and coding groups. A mapping uses an existing tenant SourceSystem ID, an exact declared namespace and code, and one same-kind finance reference. Received `reality_finance_v1.codes.case` and `.group` must each be an object with nonempty string `namespace` and `code`; unsupported/malformed declarations remain visible and unresolved. SourceRecord.source_system resolves against the tenant SourceSystem.code, never another tenant. Document summary codes are not inherited by lines.

Owners review and confirm creation, replacement, blocking and reactivation with a reason. Saving a proposal has no classification effect. Each confirmed revision preserves source scope, destination snapshot, author/action and predecessor; one current active/blocked revision per exact scope. Finance revision guards stale previews and concurrent activation. Members read list/history and component resolution. No posting, internal assignment, amount or source payload changes occur.

Company settings exposes Source code mappings with bounded search/paging, existing source/reference selection, before/after review, reload recovery and history. Financial detail shows source resolution separately from internal classification, with missing, malformed, unmapped, blocked-source, blocked-mapping, blocked-reference, resolved and conflicting outcomes. Comparison is read-time and changes neither authority. External account routing, handoff freezing, source ingestion UI and cost-center code translation remain later slices.

Source revision refinement: `state` records the immutable active/blocked decision; `is_current` selects the current revision. Replacing a revision clears only its current marker, preserving the prior decision state. A partial unique index on `is_current` enforces the exact current scope.

## Finance workspace settings placement (2026-09-10)

FR-034 refinement: financial configuration belongs to the Finance workspace. Add a
Settings tab alongside Open items, Payments and Journal. It contains the existing
operational accounts and transaction matrix, managed cost-center/case/group references,
and source classification mappings. Company settings retains company and access
management; financial editors have one canonical location. Existing management action
links open Finance Settings. The selected company scopes every panel, and switching
company clears its local editor state. Owners retain reviewed mutation privileges;
members retain the existing read-only configuration views.

The settings route is bookmarkable and survives reload/back navigation. Settings does
not load an unrelated finance register or expose payment/posting actions, register
search, totals or pagination. Existing shared editor services and confirmation/history
behavior are unchanged. The layout follows the current shared Finance header/tabs and
responsive surface styles, with all four supported UI languages. No schema, financial
rule or new command is required.

## Finance settings area navigation

FR-034 refinement: replace the settings overview accordions with a vertical area menu
and one directly visible editor. Areas are Accounts & account mapping, Cost centers,
Case codes & coding groups, and Source code mappings. Accounts opens by default.
Mobile uses a labeled select instead of the vertical menu. Area selection is encoded
in the URL, survives reload/back, and preserves tenant scope. Cost centers has no
unrelated reference-type selector; classifications offers only case codes/groups.
Existing editors, confirmed operations and histories remain shared. Pending reference
reviews are scoped by area so switching areas cannot discard another area's proposal.

## Compact finance settings actions

FR-034 refinement: setting-form submit actions occupy their own full-width footer row,
with content-sized, normal-height buttons; grid/flex stretching must not enlarge them.
Apply consistently to accounts, cost centers/classifications and source mappings.
Cost-center review is labeled Review cost center. Account rows show a compact Edit
button and a More actions popover containing block/activate and eligible set-default
operations. Default is a status badge, never a disabled action. Reference row actions
are compact. Popovers remain usable within scrolling tables and dismiss with Escape
or outside interaction. Existing confirmation, permission and financial rules remain
unchanged. Touch targets remain accessible on coarse-pointer devices.

## External target mapping implementation slice

The owner approved implementing target-specific allowed accounts/tax codes, exact
transaction/case/group rules and real-evidence preview. The bounded behavior, screens,
edge cases and acceptance proofs are in [target-mappings.md](target-mappings.md),
refining FR-009/021/027/030–034. Mapping resolution is not export readiness.
External reference catalogs are target-scoped; local-account mappings and received
component mappings have explicit separate scopes. Persistent draft mapping tables
are unnecessary: the existing proposal is the draft and confirmation activates the
reviewed decision. Export packages, profiles and remote outcomes remain subsequent work.

## Finance settings usability refinement (2026-09-10)

FR-059: Finance settings must follow existing application settings and invoice-dialog
patterns: a clear named create action, a readable list, explicit row editing and
separate history. No create/edit form is permanently rendered below a list. Apply to
operational accounts, cost centers, case codes, coding groups, source mappings,
accounting targets, external accounts, tax codes and target mapping rules.
Dialogs have entity-specific titles, field labels, required/optional guidance,
examples and an explanation of immutable identifiers, account roles and mapping
conditions. Use existing br-control/br-btn, surface tokens and native modal behavior;
no new visual language. Preserve existing routes, shared tools, owner permissions,
review/confirmation, history and pending proposal recovery. Escape/Close dismisses
unsubmitted input without writes; a prepared review can be resumed without loss.
Errors remain visible in the active dialog and submissions cannot repeat while busy.
Use a clear empty state and keep list filtering distinct from editor choices.

## Operational account setup clarity

FR-060: The operational account page explains its purpose, uses an Operational accounts heading, and places a compact Add account action at the right of the list toolbar. Explain automatic default selection and distinguish external ledger numbers. Replace the Transaction matrix accordion with View account usage opening the existing native dialog, titled Accounts for business transactions. Show the existing fourteen operations and actual role/default/control-policy data. Each role offers Change default to owners through an eligible active-account picker and existing confirmed finance.account.set_default command. Explain that a role default is shared across transactions and never changes historical postings. Original-account policies remain visible. No new business rule, schema or account-number inference.

- **FR-061**: External accounting starts with a target list and explicit create/edit dialogs. A target row opens its account setup; a Back to accounting targets action returns to the list. No permanent target search/select form appears above the list. Empty lists explain the next setup step and omit unused search/pagination controls; filtered empty results retain search. Existing confirmed commands, permissions and pending-review recovery remain unchanged. User requested the existing application list/dialog pattern.

- **FR-062**: Every Finance settings list uses a common toolbar: contextual controls on the left and the named create action right-aligned, including on narrow screens when wrapped. Cards use consistent heading/help typography, spacing, filter widths and empty-state styling. Pagination appears only when multiple pages exist. Existing native dialogs and footer ordering remain consistent; all permissions, confirmation and recovery behavior is preserved.

- **FR-063**: Distinguish empty settings catalogs from filtered no-results. Empty catalogs show a placeholder and permitted create actions without table headers, list filters or pagination. Area/type navigation stays separate and available. Filtered no-results retain inputs and offer Reset filters. Reset clears query, status and paging; switching reference type clears its old filters. Unfiltered refresh updates emptiness rather than retaining a sticky historical nonempty state. Apply across operational accounts, references, source mappings and external accounting; preserve services and confirmations.
