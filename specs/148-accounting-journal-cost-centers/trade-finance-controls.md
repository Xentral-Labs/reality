# Trade Finance Controls: Money Paths, Advances, Holds and Trade Evidence

**Status**: Owner-requested gap closure; requirements and design constraints, not implementation.  
**Feature**: [148](spec.md)

## 1. Money paths and payment-service-provider settlement

Separate a customer's settlement from the provider's balance and the eventual bank movement. Minimal tenant references identify the actual bank/cash/PSP account and its operational role/currency; opaque account identity and source namespaces prevent mixing accounts or counting one external event twice.

A payment authorization or pending capture is evidence, not settled money. A source-confirmed completed customer capture can settle a receivable against a provider-clearing asset rather than pretending the bank already received it. Preserve actual status and source event identity; normal automatic recording authority covers only explicitly supported completed events, never arbitrary source success flags.

The scenario below uses explicitly supplied amounts in one currency:

| Observed event | Debit | Credit | Meaning |
|---|---|---|---|
| Completed customer capture 100 | Provider clearing 100 | Receivable 100 | Customer settlement; no bank receipt yet |
| Explicit provider fee 3 | Provider fee counterpart 3 | Provider clearing 3 | Stated fee; not customer discount or open debt |
| Provider confirms payout dispatched 97 | Payout in transit 97 | Provider clearing 97 | Provider transfer initiated/completed on its side; no invented bank receipt |
| Bank confirms receipt 97, matched to payout | Bank 97 | Payout in transit 97 | Actual bank receipt, not another customer payment |

If evidence confirms both sides at once, a direct provider-to-bank transfer may represent the same effect, but a previously recorded in-transit leg must be completed, never duplicated by also recording a direct transfer. A notification of planned payout is not dispatched money. Bank-only unmatched receipt is retained as bank evidence and a matching case until its economic source can be identified; it cannot be blindly assigned to customer invoices.

Model source-backed provider statement lines, capture/refund/fee/retention/transfer identities and explicit matching relationships. A payout can aggregate many source events; preserve line contribution links and pagination rather than connecting the full payout amount to every invoice. Compare supplied statement totals with linked events to expose discrepancies; do not synthesize a fee as payout difference or silently balance missing rows. Partial statement coverage remains explicit.

Provider-held reserves move only explicitly stated amounts from available clearing to a restricted-provider balance and back on evidenced release. Restricted money is not available bank cash or a customer credit. A provisional chargeback may move an explicitly stated provider amount into a disputed-provider claim; it does not automatically prove that the customer owes the invoice again. Record an actual reversal of customer settlement only when the source evidence establishes that effect, with an explicit link to the original capture and its allocations. A lost provider claim that requires recognition of a loss is a separate evidenced adjustment, not a guessed customer receivable. Unsupported chargeback outcomes stay in review without automatic loss or tax calculation.

Refunds via a PSP record the actual source-confirmed customer refund against the provider account once. A later bank settlement of that provider balance is a transfer, not another refund. If fees or refunds are supplied by two sources, stable economic-event matching prevents duplicate booking; uncertain equivalence requires review. A later provider fee invoice may explain an already observed fee but must not create it again.

Support same-currency recorded bank/provider transfers and explicit fee/retention/chargeback evidence in the neutral source contract. Different-currency payouts remain explicit unsupported conversion cases until a separately reviewed contract supplies both currency amounts and exchange ownership. This extension does not calculate exchange gains, execute transfers, add a live PSP connector or reconcile an entire statutory bank ledger.

### Data and actions

Reuse SourceRecord → document/statement-line evidence → LedgerEntry with actual component ownership. Add only explicit provider-line/payout/match references, money-account purpose, and narrow event roles where required by these cases. No independent mutable PSP balance is stored. Explain/preview/record supported provider event, match payout legs, inspect statement completeness and propose correction are shared services/tools. Confirmed matching is revision-bound, tenant/account/currency scoped and idempotent. Each economic event has a durable identity across capture, statement and bank import paths; its explicitly different transfer legs use distinct effect identities under that event. Dispatch and bank receipt must each record once, while a direct combined transfer cannot coexist with the same already-recorded two-leg effect.

## 2. Earmarked customer and supplier advances

An actual payment before invoicing is still a recorded payment, not revenue or a fictional invoice. An explicit advance assignment links an available payment control entry to the intended customer/purchase order's stable evidence identity (or its exact supported commitment where no order document exists), with stated amount/currency, author/source authority and reason. It is not a financial settlement allocation: there is no invoice yet.

Assignments are bounded by the payment's currently available amount and support partial/multiple targets without over-committing it. The same available-credit origin shows Free and Earmarked portions. Earmarked money cannot be offered for unrelated allocation/refund without explicit release/reassignment. No amount is counted twice in total available credit; earmarking changes permitted use, not the ledger balance.

When an invoice actually bills the referenced order, preview an explicit conversion from advance assignment to SettlementAllocation, consuming the earmark and credit atomically. Require real order/invoice links, same party/currency and sufficient open amount; do not guess by dates or document numbers. For mixed-order invoices, enforce the declared amount attributable to the intended order; missing monetary attribution requires review, not a whole-invoice fallback. Partial invoicing consumes only the explicitly confirmed eligible amount.

Order cancellation releases no cash and does not refund automatically. It creates review work to release/reassign or record an actual evidenced refund. Payment reversal invalidates affected earmarks and allocations through explicit effect relationships, without silently making money available twice. Concurrent earmarking, allocation, release and refund share one availability boundary. Source-supplied advance restrictions remain visible alongside internal decisions.

## 3. Payable holds and review

Add a durable operational PaymentHold decision linked to the payable control item, with actor, reason, responsibility, placement time and explicit release history. It is not a Document payment state or a financial reduction. In V1 it blocks the entire selected payable item; partial disputed amounts remain explanatory context rather than a hidden reduced payable. Holds are set/released by authorized tenant finance actions with preview/confirmation; a read or agent explanation cannot create one.

Shared payable selection excludes held items with a visible reason. Payment-run preview, individual invoice-bound payment proposals, allocation of outgoing money to that held item and automatic planned-payment paths must all enforce the hold at confirmation, including a hold placed after preview. No silent override; release is explicit and auditable. Unknown/not-yet-recorded invoice evidence cannot be assigned a fake payable to attach a hold; retain review context until a real control item exists.

A bank or provider statement proving money actually moved must still be retained and can be recorded as actual standalone cash evidence. A hold cannot erase reality. Matching an already executed payment to a held item is a distinct explicit reconciliation action, showing the hold and actual execution evidence, preserving an occurrence-during-hold finding. It does not authorize a new payment. Ordinary allocation cannot claim this exception without actual movement evidence.

No hold forgives debt, stops due-date aging, changes financial totals or sends a payment. Customer dispute explanations similarly do not imply collection suppression; a separate customer collection-hold product is not required by this payable-hold scope.

## 4. Explicit cross-account settlement rule

The current allocation service requires opposite sides of the same concrete control account. Retain that invariant. Merely sharing a role must not silently authorize direct cross-account allocation.

For invoice-bound payment, resolve the receivable/payable control account from the existing invoice first, rather than blindly using a newly changed default. If a historical account is blocked, an actual standalone payment can still be recorded to an allowed account; matching then requires reviewed correction/reclassification, not a covert block bypass.

For credit already on another active compatible control account, provide a bounded explicit same-party/currency/role control reclassification with its own internal evidence and unchanged total role balance:

- Customer credit on A to invoice on B: debit control A / credit control B for the explicitly selected amount; allocate original A credit to transfer A debit, and transfer B credit to invoice B debit.
- Supplier credit on A to invoice on B: credit control A / debit control B; allocate original A debit to transfer A credit, and transfer B debit to invoice B credit.

The two allocation links and transfer group commit atomically. The reclassification does not create cash, revenue, expense or a fake payment/credit note. It consumes the selected source amount and settles the target directly; it is not an unbounded journal editor. If either account is blocked, normal reclassification is refused until an explicit account/reactivation or other supported correction decision is reviewed. Exact inverse correction still follows the historical blocked-account rule.

Reverse the complete transfer with preview of both allocation consequences; the source credit and target invoice availability are restored through effective-allocation semantics. Transfer entries cannot appear as new independent spendable credit in V09 while their atomic links are active. No cross-customer, cross-supplier-role, cross-currency or cross-tenant transfer is supported. A new role default never relabels existing entries.

## 5. Integrated goods, evidence and money control

Reuse existing invoice-line → order-line links, Commitments, shipment/receipt/return Movements and financial allocations. Define one shared trade-finance explanation covering ordered, delivered/received, returned, invoiced, credited, actually paid, accepted reduction and remaining obligation, each with its proper quantity or monetary basis.

Include partial deliveries, partial invoices, consolidated invoices covering several orders, source-stated freight/discount/fee lines not attributable to an order, customer/supplier returns awaiting credit and credits awaiting settlement/refund. Whole-invoice money must not be repeatedly attributed to each product or shipment. Received charges can be classified and handed off, but this does not calculate landed cost or margin.

An invoice or credit does not itself move goods. A physical return does not itself create a financial credit. Existing missing-invoice/receipt/price/return-credit checks become consumers of the same links and coverage contract, not alternative business rules. Preserve the existing executable cases while adding migrated/incomplete-data cases.

## 6. Missing link versus known absence

Existing code/contracts sometimes treat a null invoice-order link as a known non-order charge and the absence of a billing link as unbilled goods. Migration and incomplete sources require a third explicit state.

For applicable evidence relationships distinguish Linked, Explicitly not applicable and Unknown. Retain source/interpretation or confirmed human provenance for the relationship assertion. Unknown is not a financial status and must not be inferred to mean unbilled/not received. Where the relationship is relevant and typed queries repeatedly distinguish these states, a minimal relationship assertion/coverage field is justified; exact placement is a later schema decision.

Coverage is scoped to the source/evidence kind, relevant identities, time window and known completeness assertion. A single tenant-wide complete flag cannot prove that a particular order's invoices are complete. User confirmation of completeness is a recorded internal assertion, not fabricated external proof. New source evidence and changed scope invalidate stale readiness/certainty claims.

An exception may say Definitely shipped but not billed only with sufficient linked/coverage evidence. Otherwise it says Billing relationship unknown and names the missing information. The latter must not trigger an automatic claim, supplier payment, dunning action or shipment refusal. Same principle applies to missing credit after return and missing receipt behind a bill. Financial balances still derive from held ledger entries and disclose that source coverage may be incomplete.

## Screens and shared read models

- **V11 Money accounts & settlements**: per-account/currency bank/provider position from held postings; provider available/restricted/disputed and in-transit balances are separate. Statement/payout detail shows event contributions, bank matching, missing rows and duplicates. Account positions are labelled recorded scope, not guaranteed bank balances.
- **V12 Advances**: Customers/Suppliers tabs, originating payment, intended order, assigned/free/consumed amounts, cancellation/unknown-link review and confirmed release/settle/refund paths. V09 shows earmarked/free portions from the same service.
- **V13 Trade finance control**: order/line register with goods, invoices/credits and settlement context; expose known versus unknown linkage. Detail traces related orders/documents/movements/financial groups without multiplying totals.
- **Existing V01/V03**: payable hold placement/release and visible held-item exclusions; actual-payment-during-hold reconciliation is a separate action. Journal and V09 explain control reclassification and atomic allocation paths.
- **Settings**: supported money-account roles, provider/source identity and statement interpretation configuration; no live-send or tax-engine controls.

All new views use the existing shared component, locale, keyboard, theme, responsive and complete-scope pagination contract. Add route/catalog/Inspector coverage. Disposable projections may accelerate reads but cannot own balances, available-credit limits, hold authority or confirmation decisions.
