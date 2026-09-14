# Delivery and Verification: Operational Subledgers

**Status**: Planned scope/proof, not implementation tasks or completed acceptance.  
**Feature**: [148](spec.md)

## Delivery sequence

1. Confirm supported financial translation paths and current posting/settlement semantics; define the minimal account catalog, role destinations and clean required account links; specify received component fidelity and narrow automatic authority.
2. Add received financial detail and optional component-level cost assignment/reference mappings, with source preservation tests first.
3. Connect supported translations to existing operational posting services with durable identity/retry and review outcomes.
4. Add versioned neutral package preview/preparation and source-backed feedback ingestion; test stale revisions, duplicate requests and ambiguous outcomes.
5. Extend existing finance screens, Inspector and shared reads, then complete localization, visual, catalog and regression checks.

These are the original product slices. [plan.md](plan.md) now refines delivery order and migration/API design; [test-plan.md](test-plan.md) adds exact planned test modules. Schema review, tasks and Spec Kit analysis still precede implementation. The small account catalog is part of this feature; no general-ledger or closing subsystem is a dependency.

## Business fixture

- Source-stated sales invoice 119 EUR gross; existing operational gross receivable/counterpart postings.
- Customer payment 50 EUR allocated to that invoice; outstanding 69 EUR. Reverse the payment and the existing claim reopens to 119 EUR.
- Supplier invoice 1,190 EUR gross, explicitly stated 1,000 net and 190 tax; optional net assignments 600/400 leave gross operational balances unchanged.
- Partial assignment 600 of 1,000 leaves 400 unassigned; assignment 1,001 fails. Gross-only evidence remains valid locally but cannot satisfy a profile requiring stated net/tax.
- Mixed source treatments and document tax summaries alongside line components; no double counting or tax calculation.
- Both credit/refund directions, changed source version, replay/concurrent retry and zero-effect source evidence.
- Neutral package prepared/downloaded with no external receipt: externally posted remains unknown.
- Imported receipts: accepted-only, explicitly posted, rejected, partial batch, out-of-order, duplicate, conflicting, unmatched and wrong-version.
- Local correction after external acceptance; separate correction package and explicit remote outcome.
- Minimal account setup, duplicate codes, reviewed external-reference import, wrong role, blocked/unknown/wrong-tenant accounts, stale preview and concurrent block versus posting.
- Two accounts with the same role and a changed default: prior balances and original settlement targets remain valid; a reversal may reuse a blocked account but a replacement cannot.
- Clean schema, required account IDs and repeatable service-generated fixtures; reject invalid account roles and cross-tenant links.
- Two tenants with identical human codes; multiple currencies; more than one page and tied dates; immutable new-model IDs/amounts/allocations.

Expected amounts and assertions must be independently authored, not produced by the implementation's own calculation helpers. Synthetic tax amounts are received fixture facts, not applicable tax advice.

## Matrix and declared-case fixture extension

Use all eight directions in [posting-matrix.md](posting-matrix.md), with drafts/orders/movements as negative controls. Supply two distinct component cases on one invoice, case/group variations across two targets and tenants, country-only evidence, explicit no-tax versus unknown, missing/duplicate/retired mappings, conflicting internal/source assignments and a stale preview. Confirm unchanged gross balances and earlier package bytes. Payment handoff must not inherit invoice tax coding. Exact/no-group discrimination modes and competing simple mappings require explicit refusal/coverage tests.

## Individual requirement proof

| Requirement | Scenarios | Planned proof |
|---|---|---|
| FR-001 | US1.1–2/6 | Existing balanced-role services, no full external chart prerequisite, gross labels |
| FR-002 | US1.3 | Owner activation, source/type/revision scope, pause/revoke and no intake authority inheritance |
| FR-003 | US1.1/4 | Evidence survives posting error; durable handoff crash/retry proof |
| FR-004 | US1.4–5 | PostgreSQL replay/concurrency, lost response, changed version and cross-source ambiguity |
| FR-005 | US1.6, US3.5 | Existing settlement/reversal regression plus remote outcome independence |
| FR-006 | US2.1/3 | Source fidelity, absent versus zero, coding namespace and no inferred amounts |
| FR-007 | US2.1 | Summary/line roles and no repeated document amount attribution |
| FR-008 | US2.2/5 | 600/400 and partial assignment, over-allocation, mixed bases/currencies and immutable revision |
| FR-009 | US2.3–4 | Target-specific references, no tax determination, local posting survives missing mapping |
| FR-010 | US2.4 | Retire/rename and frozen package assignment/mapping history |
| FR-011 | US2.3, US4.3 | Independent readiness axes, reason counts and no Document status fields |
| FR-012 | US3.1–2 | Exact package manifest/components/identities, neutral profile label and explicit omissions |
| FR-013 | US3.1–2/4 | Stale preview, repeat preparation/download and no remote success inference |
| FR-014 | US3.3 | Lossless receipt chain and target/item/version/outcome evidence |
| FR-015 | US3.4 | Idempotent, partial, conflicting, unmatched and out-of-order receipts |
| FR-016 | US3.5–6 | Correction/retry identity, unchanged prior packages, no blind resend or remote reversal |
| FR-017 | US4.1 | Filter-before-total/pagination, operational role balance, currencies and exact provenance |
| FR-018 | US4.2 | Assigned/unassigned/missing basis, no recognized expense or profit labels |
| FR-019 | US4.3 | Local/prepared/remote facts independent; compare only like-for-like evidence |
| FR-020 | US4.4 | V01–V13 route/state/keyboard/localization/visual matrix |
| FR-021 | US1.3, US3.1–6 | Shared tools, owner configuration, tenant mutation policy and unchanged Chat/MCP confirmation |
| FR-022 | US4.5 | Clean database initialization, service-generated fixtures and immutable new-model entry/allocation history |
| FR-023 | US4.1/3 | Source/local/remote date distinction, timezone boundaries and tied pagination |
| FR-024 | US5.1–2 | Minimal setup, manual/imported references, unique codes and no number-derived role |
| FR-025 | US5.3–4 | All shared posting paths, role/default resolution, tenant checks and concurrent block/revision race |
| FR-026 | US5.5 | Immutable used role, audited rename, blocked exact reversal, replacement refusal and role-wide balances |
| FR-027 | US5.6 | Optional per-target mapping revisions, frozen exports and unchanged gross basis |
| FR-028 | US5.7 | Clean account initialization, required IDs, no legacy-string authority and currency-separated reads |
| FR-029 | US6.1 | Eight-direction service/adapter matrix, explicit/default accounts and non-posting triggers |
| FR-030 | US6.2–3/5 | Defined source/internal cases, multi-case scope and no country/rate inference |
| FR-031 | US6.4 | Defined optional groups, no guessed classification and wrong-tenant/retired refusal |
| FR-032 | US6.4/6 | Exact target resolution, group modes, overlap rejection and competing-path refusal |
| FR-033 | US6.5 | Immutable revisions, owner activation, stale preview and unchanged prior package/local balances |
| FR-034 | US6.1–6 | V01/V04/V05/V08 additions, shared resolver parity and read-only matrix |
| FR-035 | US7.1/4 | Actual receipt 1,020, allocation 1,000, excess 20; strict legacy invoice action preserved |
| FR-036 | US7.1/3 | Unaccepted skonto/withholding stays open; explanatory note has no financial/aging effect |
| FR-037 | US7.2/3 | Stated adjustment 20 or 60, separate evidence/non-cash entries, no fake source or calculation |
| FR-038 | US7.2/5 | Stale/duplicate/source-credit rejection; atomic combined action and independent cash recording |
| FR-039 | US7.4/5 | Reuse/refund existing excess, no duplicate payment; tenant/party/currency and available-credit bounds |
| FR-040 | US7.5/6 | PostgreSQL concurrent allocation/refund/adjustment and independent payment/adjustment/refund reversals |
| FR-041 | US7.7 | Catalog/matrix/UI parity, 980 cash plus 20 adjustment wording and external missing-tax readiness |
| FR-042 | US8.1–3/5–6 | Supplier cash/control signs, agreement authority, partial/full reduction, excess allocation/refund and PostgreSQL race/reversal parity |
| FR-043 | US8.4–5/7 | Both credit tabs, payment/credit-note origins counted once, same-party/side/currency bounds, no-open-invoice discoverability and V09 UI matrix |
| FR-044 | US9.1 | Four exact opening directions and no revenue/expense/cash effect |
| FR-045 | US9.1–2 | Source-stated residual, summary mode, separate directions/currencies and unknown aging |
| FR-046 | US9.4 | Bounded atomic import, owner/stale checks, re-upload, changed snapshot and coverage/backfill conflicts |
| FR-047 | US9.3/5 | Opening allocation/adjustment/refund parity, V09 origin identity and concurrent reversal/consumption |
| FR-048 | US9.6 | V10 shared state/visual/catalog proof and no accidental normal-business handoff/activity |
| FR-049 | US10.1–2 | 100 capture / 3 stated fee / 97 payout-bank receipt; pending events, reserves and disputed funds distinct |
| FR-050 | US10.1–2 | Capture/statement/bank economic identity, partial batch coverage, refund/fee duplication and unsupported FX |
| FR-051 | US10.3 | Both advance directions, partial orders/invoices, cancellation and PostgreSQL earmark-versus-consumption race |
| FR-052 | US10.4 | Hold-after-preview refusal across individual/run paths, explicit release and evidenced during-hold reconciliation |
| FR-053 | US10.5 | Both control-side transfer directions, atomic paired allocations, unchanged role balance and reversal/blocked checks |
| FR-054 | US10.6 | Partial/consolidated order-goods-invoice-credit-settlement trace and source-stated unallocated charges |
| FR-055 | US10.7 | Linked/not-applicable/unknown, scoped coverage invalidation and migrated-history false-positive refusal |
| FR-056 | US10.8 | Complete/paginated structured explanation, cutoff change/restart, exact provenance and no financial Fact writes |
| FR-057 | US10.8 | Public capability parity, stale/permission refusal, authoritative result re-read and no invented external success |
| FR-058 | US10.1–8 | V11/V12/V13 and existing-screen shared read/UI/isolation/locale/visual proof |
| DR-001 | US1–US3 | Source/evidence/Reality and separate receipt provenance |
| DR-002 | US2.1–2 | Shortest-link schema review; no duplicated line ownership |
| DR-003 | All | Isolation catalog and PostgreSQL cross-tenant/target refusal tests |
| DR-004 | US1.5–6, US2.4, US3.5 | Immutable source/ledger/package/receipt history and read-only derived state |
| DR-005 | US1.1, US2.1–5 | Decimal balance, no source amount recomputation or silent split residual |
| DR-006 | US1.3–4, US3.1–6 | Tool/service/adapter parity, existing worker registry, no direct external-effect handler |
| DR-007 | US4.5 | Reviewed clean-schema initialization/reseed, data/event/command/Inspector catalogs and existing regressions |

## Verification gates

For this specification revision: check required sections, local links, placeholder absence, individual requirement coverage and consistency across companion files; run `make spec-check` and report unrelated workspace failures honestly.

Before implementation: product/domain review of revised detail, mandatory plan with passing Constitution Check, exact schema and migration/rollback proof, tasks and analysis. The accepted product boundary does not imply approval of an arbitrary live connector or physical schema.

For implementation: planned unit/service/business-story/adapter tests, actual PostgreSQL concurrency/isolation/migration proof, complete required backend suite, lint/spec gates, Web build/localization gates and V01–V13 visual verification. Run any other repository-required affected gates. No runtime acceptance is complete while required checks are red.

## Future adapter boundary

A named external accounting integration must separately specify supported document/event types, exact export/API format, amount and coding ownership, destination identifiers, receipt semantics, retries/corrections, authorization and direct external-effect handling. This feature's neutral package must not be marketed as a working vendor connector.

External report display may later consume source-backed balance sheet/P&L output with origin and reporting date. It is not a reason to implement those calculations in Reality. The authoritative chart, tax treatment, periods, valuation and financial statements remain external responsibilities.

## Payment-difference proof extension

Exercise every row of [payment-differences.md](payment-differences.md), including 980 + accepted 20, 900 + disputed 100, partial acceptance 60, 1,020 with excess 20, later allocation/refund, exact inverse and independently reversed payment. Race acceptance against incoming payment and race allocation against refund in real PostgreSQL. Repeat a confirmed request and deliver the same reduction later as credit evidence. Verify no doubled financial effect, same-party/currency isolation, actual cash unchanged by reductions and missing target tax detail independent from operational settlement. Update spec 088/ledger durable contracts at implementation to describe this explicit bounded extension without removing their original no-automatic-calculation behavior.

## Symmetric supplier and available-credit proof

Run the complete payment-difference cases in both directions with explicit expected signs: supplier 1,000 less cash paid 980 leaves payable 20; documented reduction 20 clears it; withheld 100 remains owed until supplier-agreed reduction; paid 1,020 leaves available supplier credit 20. A recorded supplier refund received settles that debit without another outgoing payment. Preserve the strict existing invoice-bound command bounds while adding guided wrappers.

For both sides, combine unallocated payments, partly consumed credit notes, reversed origins, technical inverse groups and invoice-linked adjustments; assert exactly the eligible origin residuals appear once. Exercise a dual-role party, multiple currencies, more than one page and no open invoices. Race allocating a payment/credit note against refunding it, including multi-origin confirmation. Verify all register/detail/Inspector reads agree and that a supplier payment-run intention is not actual cash evidence. V09 is included in the four-language/two-theme/three-width keyboard/visual proof.

## Opening-position proof

Run the four-direction fixture and all duplicate/coverage/correction cases in [opening-items.md](opening-items.md). Verify retained outstanding rather than original gross amount, both V09 tabs, unknown due date, same-party dual roles, currency separation, historical versus post-cutover evidence, replay under a different filename/request and overlapping summary/detail refusal. Race consuming opening credit against reversal; verify effective allocations and explicit replacement. Do not label operational import a statutory opening balance or record new sales/cash. V10 joins the complete shared UI verification matrix.

## Trade-finance gap closure and implementation ordering

The two contracts [trade-finance-controls.md](trade-finance-controls.md) and [agent-finance-contract.md](agent-finance-contract.md) are mandatory scope, not optional future recommendations. Plan the common account/settlement/coverage/explanation invariants first, then money paths and advance/hold services, then adapters and projections. V01–V13 and all 58 functional requirements belong to the complete proposed scope; staged implementation must name its delivered subset without claiming the whole operational finance system is complete.

Add independent expected-value fixtures for every US10 branch. Run actual PostgreSQL races for matching the same provider event through multiple sources, paired control reclassification, earmark consumption and hold placement after preview. Verify source-stated chargeback versus actual settlement reversal, transfer-in-transit versus confirmed bank receipt, and no invented missing fee/FX data. Run agent tool stories through the shared services; a fluent response is not test evidence without exact result/provenance assertions.

Before implementation reconcile docs/features/procure_to_pay.md and existing payment-run guidance with the hold and observed-cash rules, specs/076-invoice-order-link and relevant exception contracts with tri-state migration coverage, and settlement equality/catalog contracts with the explicit control transfer. Existing facts/source/confirmation contracts remain authoritative. These are required plan integration tasks, not permission to weaken those contracts silently.
