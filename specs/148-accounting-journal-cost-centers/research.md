## Local development cutover decision — 2026-09-09

The owner is the only current local tester and has no real account population to migrate. Build a clean new schema and regenerate disposable test fixtures. No old-account-string backfill, unresolved legacy-account state, dual account columns, old-binary compatibility or per-tenant migration rollout is required. Keep the repository Alembic chain coherent; do not rewrite unrelated migration history. A reset/reseed must target an explicitly identified disposable local/test database and must not occur automatically on application startup or against an arbitrary configured database. This planning change does not execute a reset.

This removes local development compatibility work, not business integrity: newly recorded evidence/entries remain immutable and tenant-scoped, with explicit reversals. Customer/supplier opening imports, external historical-source matching and coverage remain product features for customers moving from other systems.

# Research Decisions: Operational Finance

**Date**: 2026-09-09. Read-only repository investigation; no runtime verification claims. Product questions are resolved by the approved specification. Implementation gates remain explicit in plan.md.

## 1. Extend the existing ledger

**Decision**: Reuse LedgerEntry, SettlementAllocation and LedgerReversal, with stable account IDs and semantic role queries. Current strings `accounts_receivable`, `accounts_payable`, `cash`, `sales_revenue`, `inventory` map respectively to receivable, payable, cash, gross sales counterpart and gross purchase counterpart. The latter two are not net revenue or inventory valuation.

**Rationale**: `db/core.py` already owns posting group, amount, currency, evidence, party and effective time. `services/core.py` already posts both sides and handles credit/refund reversals. Replacing the ledger would duplicate authority and invalidate existing references.

**Alternatives considered**: A full journal/period/chart subsystem is outside scope. Leaving literal string filters unchanged would omit new accounts and break history after default changes.

## 2. Fix availability and transaction composition first

**Decision**: Generic control-entry availability counts effective allocations incident to either endpoint exactly once, excludes inverses and respects eligible origin types. Settlement requires opposite sides of the same concrete account, same tenant/party/currency. Explicit transfer creates paired entries and allocations for different accounts.

**Rationale**: Existing `allocate_settlement` relies on invoice-document discovery and does not provide sufficient row-lock/party protection. Payment-origin totals can miss credit consumed as the other allocation endpoint. Some supplier refund wrappers commit intermediate operations. These are blockers for safe compound actions.

**Alternatives considered**: UI-side bounds, account-role equality, or one more credit-balance table cannot enforce concurrency and would permit overconsumption.

## 3. One tenant finance coordination row

**Decision**: Lock a tenant-scoped FinanceState row for every affected financial mutation, then increment its revision in the same transaction. It stores coordination/rollout metadata only. Request/effect uniqueness is still enforced in PostgreSQL. Configuration changes use the same lock.

**Rationale**: One orderable boundary covers availability, accounts, holds, proposals, outbox and mapping races without initially designing a many-resource lock graph. Revision also supports stale previews and read continuation. Existing policy/worker claim locks precede finance; no finance service may acquire those outer locks in reverse order.

**Alternatives considered**: Advisory locks alone do not provide the revision needed by previews. Fine-grained row locks are a future optimization only if measured tenant write throughput requires them. Independent per-command locks do not protect cross-command races.

## 4. Two identities and supplemental evidence

**Decision**: Persist request key plus canonical request hash/result separately from economic effect key. A posting effect uses evidence identity and explicit event/leg identity; additional statement/bank/invoice evidence can match an existing effect.

**Rationale**: Transport retries, changed source versions and multiple sources observing one payment are different problems. Existing invoice duplicate checks based on a literal account balance are insufficient after role defaults change.

**Alternatives considered**: SourceRecord ID alone duplicates cross-source effects; amount/date matching is ambiguous and may only suggest review candidates.

## 5. Narrow evidence extensions

**Decision**: Reuse Document/Line evidence and existing source payloads. Add typed finance extensions only for components, adjustments, opening scope, money events and controls that services repeatedly validate or join. No new financial Fact predicates by default.

**Rationale**: Existing typed reality supplies balances and traceability; storing paid/open/available Facts would create a second authority.

**Alternatives considered**: Free-form JSON for every control cannot enforce critical joins. A second generic accounting document hierarchy adds unnecessary identity and provenance duplication.

## 6. Transactional outbox with the shared scheduler

**Decision**: Interpretation commits its financial eligibility outbox row with evidence. Owner activation configures a bounded recurring drain in the shared job registry/scheduler/worker. The drain calls transaction-bound financial services; no network effects.

**Rationale**: Existing generic import paths can commit independently. They must gain a bound financial interpretation path before automatic activation. Enqueue-only after commit has a crash gap; queue-capacity failure must not discard otherwise valid received evidence.

**Alternatives considered**: Per-process timers violate scheduling rules. A job that self-approves general proposals would bypass explicit authority.

## 7. Live read-only finance projections

**Decision**: Use shared read-only SQL services in REPEATABLE READ, complete filtered totals and stable `(effective_at, id)` pagination; continuation includes scope hash, finance revision and tenant BusinessEvent sequence. Any mismatch returns restart-required.

**Rationale**: Existing `projection_rows(refresh=True)` refreshes and commits. New agent finance reads must not mutate anything. Long-lived exported database snapshots are unnecessary for ordinary interactive pages.

**Alternatives considered**: Browser summation loses off-page rows. Stored operational balances duplicate authority. Event chronology alone does not promise arbitrary historical as-of balances.

## 8. Neutral local handoff

**Decision**: Immutable bounded canonical JSON packages and source-backed neutral receipts, version 1. Exact target/case/group mapping, no network adapter or statutory tax engine.

**Rationale**: External software remains the accounting authority. File preparation and remote posting must remain independent. Existing PostgreSQL storage can hold the bounded immutable package; no object-store deployment is needed.

**Alternatives considered**: Vendor-specific booking exports and country tax logic require separate contracts. Recreating package bytes on download loses reproducibility after reference changes.

## 9. Root integration baseline

**Decision**: Plan against the supplied root checkout, isolate web finance modules, and verify mounting paths at integration freeze. Reuse current design primitives and four locales. Do not migrate the running application as part of planning.

**Rationale**: Another inspected worktree contains a unified web shell; the root has a different App.tsx and concurrent company/demo changes. Those are parallel work, not implicit dependencies already merged.

**Alternatives considered**: Switching worktrees or copying an entire shell would broaden scope and risk unrelated changes.

## 10. Partial trade evidence

**Decision**: Replace the existing second-invoice rejection only for explicitly attributable partial/consolidated billing. Validate source-stated quantities/links and preserve unallocated charges separately. Coverage assertions are scoped and version-bound.

**Rationale**: `services/core.py` currently rejects another billed evidence row for an order line. Without changing that path, the accepted trade-finance story cannot be delivered. Missing migrated history must remain unknown rather than an invented mismatch.

**Alternatives considered**: Summing document totals into line attribution or inferring coverage from imported dates manufactures evidence.

## 11. Target-independent source classification

**Decision**: Add an exact, versioned source-system/namespace/field-kind/code → local reference mapping, independent of AccountingTarget. Freeze selected source revisions separately in package manifests.

**Rationale**: FR-030 requires source-code interpretation even when no accounting target exists. External destination mapping alone cannot express that relationship.

**Alternatives considered**: Making target mapping nullable would combine different authorities and scope rules. Inferring local case from a country/rate violates the specification.

## 12. Currency belongs to the event and entry

**Decision**: Remove the single-currency field from money-account detail. Preserve existing account IDs across currencies and filter/validate every availability or match by entry/event currency. Provider identity/purpose remains explicit.

**Rationale**: Existing multi-currency cash history must survive unchanged. A bank/provider identity describes where funds are held; the actual evidence states their currency.

**Alternatives considered**: Splitting historical account identities rewrites settlement context. Converting totals invents unsupported exchange semantics.

## 13. Introduce target schema before account mapping

**Decision**: Keep local account setup independent. Move its external target-mapping test and implementation into the received-detail slice, after target/profile schema exists; freeze-package verification still finishes with handoff.

**Rationale**: The previous task order referenced target tables before creating them.

**Alternatives considered**: Adding all handoff schema to basic account setup would enlarge the first usable increment unnecessarily.

## 14. Owner-approved local simplification

**Decision**: Supersede the earlier additive-account-adoption and compatible-reader rollback decisions. The only current user is testing locally; no real account population must survive migration. Use direct required account IDs and clean fixtures, without unresolved roles, legacy strings or rollout stages.

**Rationale**: Compatibility infrastructure has no current business use. Keep runtime correctness, concurrency and external opening imports because those are product behavior.

**Alternatives considered**: Supporting old binaries and test-only account strings adds complexity without protecting customer data. Resetting arbitrary environments or weakening new-model history would exceed the local exception. Earlier numbered research entries record prior investigation, not current adoption requirements.

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

## Authorized active-stack integration — 2026-09-09

The owner approved continuing with integration into the actual local application, targeted rebuilding of disposable local test data and end-to-end sales/purchase verification. Preserve the newer unified shell, lot-expiry and subsequent read-performance work. Transfer only the implemented account slice. Use migration `0048_finance_accounts` after `0047_merge_demo_lot_expiry`; never apply the root migration chain to this database.

The account panel mounts in unified company settings using current `br-*` controls and theme tokens; the journal displays concrete account code/name. Existing services and proposal confirmation remain the authority. No new financial features or schema beyond the reviewed three-table slice are added.

Before local cutover, create a private backup and rehearse the combined schema on disposable PostgreSQL. Stop writers for the cutover. Rebuild only explicitly selected local business test data, preserving login/account access where practical; do not remove PostgreSQL or object-storage volumes. Seed through shared company/demo services. Verify the actual localhost application and sales/purchase invoice, partial/full payment, credit, refund and reversal paths. Retain a recoverable backup until verification completes.

Constitution review: PASS. Same account identity/evidence model, tenant-scoped services and confirmed actions; no derived Facts, financial accounting authority or external effects. Analysis: no unresolved requirements or critical integration finding; the exact target migration and UI mounting point supersede root-only limitations for this integration.

## Bounded target mapping refinement

The current runtime has no accounting target or external reference catalog. Source
classification mapping is already implemented and remains target-independent.
The next slice therefore introduces explicit target/reference catalogs before exact
routing. Defer profiles until handoff: mapping preview cannot promise export readiness
and has no reason to introduce a profile engine now. This refines decision 13 above.

Rejected alternatives: free-text destination fields cannot constrain permitted
references; reusing internal finance references mixes external target namespaces
with internal case/group/cost-center meaning; a generic JSON rule engine weakens
shape/FK guarantees; country/rate inference violates the accepted product boundary.
The concrete proposal and its pending schema review are in target-mappings.md.

Finance settings UX decision: preserve the application's existing native modal,
spacing, surfaces and primary/secondary actions. Inline permanent forms obscure
create/edit intent. Dedicated dialogs resolve this without introducing a wizard,
new navigation architecture or alternative business services.
