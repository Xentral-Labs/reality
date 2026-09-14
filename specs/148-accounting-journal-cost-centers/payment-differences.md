# Customer and Supplier Payment Differences, Adjustments and Available Credit

**Status**: Available-credit register and separate confirmed invoice reductions implemented; combined payment/adjustment and guided excess-refund actions remain planned.  
**Feature**: [148](spec.md)

## Current capability and change boundary

The existing standalone `record_customer_payment` records the actual receipt; `allocate_settlement` allocates no more than the available credit or open invoice. The invoice-bound `post_customer_payment` rejects amounts greater than the invoice's open amount. The new guided receipt flow composes recording and allocation without weakening those amount limits or silently changing the existing strict command contract.

Spec 088 records discount terms and explains a qualifying residual but intentionally leaves it open. This feature adds an explicit evidenced operational claim reduction. It supersedes that earlier non-goal for reviewed customer and supplier settlement actions; automatic discount calculation, tax determination and hiding unadjusted residuals remain excluded. No general accounting journal editor or full chart is needed. The small accepted-adjustment service can use the existing LedgerEntry and SettlementAllocation foundation independently of case mappings or external handoff availability.

## Customer behavior by situation

All amounts below are explicitly supplied example facts or read-time residuals. They are not generated authoritative discount amounts.

| Situation on an invoice with 1,000 open | Actual receipt | Explicit decision | Result |
|---|---|---|---|
| Ordinary partial payment | 980 | Leave remainder open | Allocate 980; 20 remains owed |
| Claimed early-payment discount | 980 | No acceptance yet | 20 remains open with available discount context |
| Accepted early-payment discount | 980 | Confirm a stated reduction of 20 | Allocate payment 980 and separate adjustment 20; invoice settled, cash remains 980 |
| Customer withholds disputed amount | 900 | Record a stated withholding reason | 100 remains open; explanation does not extinguish the claim |
| Accepted partial withholding | 900 | Confirm agreed reduction 60 | Payment 900 plus adjustment 60; 40 remains open |
| Accepted full withholding | 900 | Confirm agreed reduction 100 | Claim settled with separate evidenced non-cash reduction |
| Overpayment | 1,020 | Allocate 1,000 | Invoice settled; 20 remains unallocated customer payment credit |
| Use overpayment later | Previously recorded excess 20 | Allocate to another eligible same-party/currency invoice | Existing credit settles 20; no second cash entry |
| Refund excess | Previously recorded excess 20 | Record actual evidenced refund 20 and settle against that credit | Cash outflow 20 recorded once; no invented credit note or automatic bank transfer |

A withheld amount is not automatically a discount, bad debt, tax withholding or accepted commercial concession. Source descriptions and operator explanations are retained; only an explicitly accepted amount reduces the receivable. Provider fees with explicit source evidence use the separate money-path contract in trade-finance-controls.md, not discount adjustments. Other deductions such as tax withholding require their own reviewed financial meaning and remain unsupported until specified; this feature must not relabel them as discounts.

No tolerance silently writes off a small amount. A user can explicitly accept a stated small remainder using the same evidenced adjustment mechanism and a reason. Dispute explanation alone does not change aging, due date, collection policy or document status; collection holds are separate scope.

## Actions and invariants

### Receive and allocate actual money

The shared guided action accepts the actual payment amount and explicit allocations to one or more customer invoices. A selected invoice may receive at most its current open amount; remaining money stays unallocated. Preview shows actual receipt, each allocation, invoice residuals and customer credit separately. Automatic suggestions are read-time observations and require confirmation, not stored derived payment amounts.

Existing received payment evidence can be selected for allocation without recording it again. All controls are same tenant, party and currency. No cross-customer netting, currency conversion or over-allocation is allowed. Multiple confirmations and concurrent allocation/refund attempts must preserve a single available-credit bound.

### Explain a deduction

A source payment advice can supply a deduction amount/reason; preserve it losslessly. An internal note records who said what and when, linked to the actual payment/invoice evidence. A read-time shortfall comparison is not proof of the customer's intent. Notes and claims do not create LedgerEntries or release receivables.

Use the existing evidence/annotation facilities where possible. Do not create a generic dispute workflow or store `disputed_amount` as a competing open balance.

### Accept a settlement reduction

A bounded action creates immutable internal settlement-adjustment evidence with an explicit entered/externally stated positive amount, currency, invoice/party context, reason category (`early_payment_discount`, `agreed_deduction`, `accepted_small_remainder`), reason text, actor and confirmation identity. Link payment advice/other source evidence where present; no fabricated external credit note is required.

One adjustment addresses one invoice and is no greater than its remaining open amount after selected payment allocations. It can be accepted at payment review or later. For a later action, reference the existing payment/evidence rather than recording cash again. Show held discount percent/deadline as context; they never automatically compute or approve an adjustment. An out-of-window or unsupported claimed discount requires an explicit reasoned decision, not automatic eligibility.

The operational posting is debit Accepted settlement reduction counterpart, credit Receivable, using the existing balanced ledger and a valid compatible adjustment account role. Allocate that adjustment's control credit to the invoice through the shared settlement relation. It is not cash and is not an external net/tax accounting entry. The distinction remains visible in open-item closure: paid amount versus accepted reduction.

The evidence may be a minimal dedicated internal settlement-adjustment Document kind if the later plan proves that this is the shortest integration with existing settlement discovery. Never reuse the invoice as evidence of a separately authorized reduction or duplicate all its source/line FKs. No new independent balance table is justified. A reason category is retained on the evidence/coding context for explanation and handoff; each direction has its own operational counterpart role in V1 so customer concessions and supplier reductions are not conflated.

If an existing credit note already represents the same reduction, allocate that credit instead of creating another adjustment. Reject a duplicate referenced source adjustment/effect, a stale invoice balance or a correction already consumed through another path. After an accepted adjustment reduces the open amount to zero, overdue behavior ends because the balance is settled, not because an exception was suppressed.

### Refund or reuse excess

Unallocated customer payment credit is the existing payment control amount minus effective allocations. It is not revenue and requires no new credit or suspense balance table. Show it even when no invoice remains open.

Allocating it later uses the same control credit. Refund-from-payment-credit requires an explicit actual refund amount/evidence, records the supported refund debit Receivable / credit Cash once, and links that refund debit to the original payment credit. The current credit-note-bound refund action is not sufficient by itself; add a narrow shared wrapper accepting available payment credit and reusing recording/allocation primitives. Do not fabricate a credit note to satisfy the old signature.

Recording a refund never executes a bank transfer or claims money was sent without explicit recorded evidence. A mere refund intention is not a completed financial entry. The action preview must name Record refund, its evidence and actual amount, not Send money.

### Corrections and concurrency

A confirmed combined payment/allocation/adjustment action is atomic, idempotent and revision-bound. Evidence intake already committed separately remains preserved if financial confirmation fails. An operator can choose to record actual cash alone and resolve the deduction later; failure to accept a deduction must not require falsifying or discarding received bank evidence.

Adjustment reversal is a full exact inverse and deactivates its allocation, reopening the relevant claim while leaving the real payment intact. Payment reversal does not automatically reverse a separately accepted adjustment: show the remaining reduction and offer its own reviewed correction. Refund reversal restores the available original credit through existing reversal/allocation semantics. Corrected replacements require current account eligibility and new explicit confirmation; historical inverses may use the original blocked account.

Serialize invoice availability and payment-credit availability with allocation/adjustment/refund writes. Request replay, changing the reason text or retrying through a different adapter cannot duplicate the same approved effect. Unknown outcomes must be reconciled by identity before retry. Tenant, party, currency, amount, evidence and account compatibility are revalidated at confirmation.

## Handoff and transaction-matrix extension

Add the explicit `customer_settlement_adjustment` event to the handoff vocabulary and matrix: debit Accepted settlement reduction counterpart / credit Receivable, using the approved stated adjustment amount. Payments and adjustments are separate items with their shortest true relation to the invoice and each other where present. Do not export 1,000 as cash when only 980 was received.

External mapping may distinguish adjustment reason and an explicitly declared case through the existing target contract. No net/tax reduction is computed from the gross adjustment. If a target requires such amounts, retain the local accepted reduction and show handoff missing information until source-backed amounts are supplied. A later credit note or external receipt representing the same accepted reduction must be explicitly matched to the existing effect, not posted again.

## UI changes

- **Payments (V03)**: actual receipt and allocation editor with open invoice rows, assigned/unassigned totals and customer credit. Separate sections Actual payment, Remaining claim and Accepted reduction. Default for a short payment is Leave open.
- **Difference review (V01/V03)**: choices Leave open, Record deduction explanation, Accept stated discount/reduction, or Allocate existing credit. Show actual amounts, source advice, discount terms where held and full effects before confirmation. No automatic tolerance or percent-to-money calculator.
- **Overpayment detail (V03)**: show Available customer credit with actions Allocate to invoice and Record evidenced refund. Both reuse the original payment, restrict same party/currency and show the current available amount.
- **Open Items (V03)**: distinguish actual payments, accepted reductions, claimed/disputed explanations and remaining claim. A settled invoice may show 980 paid + 20 accepted reduction; never label 1,000 received.
- **Journal/Inspector (V02/V04)**: separate cash and adjustment groups, internal/source evidence, author/reason, allocations and reversal paths.
- **Handoff (V05/V06)**: independent payment/adjustment/refund evidence and outcome; missing adjustment tax breakdown affects only target readiness.
- **Finance settings (V08)**: configure a permitted Accepted settlement reduction counterpart account. Missing/blocked configuration prevents new adjustment, not standalone recording of actual payment.

All actions use existing tenant mutation permissions and confirmation; no automatic source-recording authority also approves deductions, forfeits residuals or refunds excess.

## Supplier mirror and agreement authority

All shared amount bounds, identity, evidence, account eligibility, same-party/currency, confirmation, concurrency, correction and tax-data rules above apply on the supplier side. The customer examples use cash received and a receivable; the supplier flow uses actual cash paid and a payable. The following matrix is normative for supplier behavior, not optional follow-up scope.

| Situation on a supplier invoice with 1,000 open | Actual cash paid | Explicit evidence/decision | Result |
|---|---|---|---|
| Ordinary partial payment | 980 | Leave remainder open | Allocate 980; payable 20 remains |
| Discount claimed by our company | 980 | No documented entitlement/agreement accepted yet | Payable 20 remains, with claim explanation |
| Documented discount taken | 980 | Confirm stated reduction 20 with agreed terms or supplier evidence | Separate non-cash adjustment 20; payable settled, cash paid remains 980 |
| Our company withholds disputed amount | 900 | Record reason | Payable 100 remains; our claim alone does not discharge it |
| Supplier agrees to reduce part | 900 | Confirm documented supplier concession 60 | Payable 40 remains |
| Supplier agrees full reduction | 900 | Confirm documented concession 100 | Payable settled with separate non-cash adjustment |
| Our company overpays supplier | 1,020 | Allocate 1,000 | Invoice settled; 20 remains available credit with the supplier |
| Reuse supplier credit | Previously available 20 | Allocate to another eligible invoice of that supplier/currency | Existing debit control entry settles 20; no new payment |
| Supplier returns excess | Previously available 20 | Record actual evidenced refund received 20 | Cash receipt 20 recorded once and settled against the original supplier-payment debit |
| Unallocated supplier credit note | As stated by supplier | Use existing credit-note entry | Available supplier credit shown once, usable for allocation or evidenced refund |

An internal operator's wish to withhold is not authority to extinguish a supplier liability. A supplier reduction records the explicit stated amount plus supplier credit/advice, agreed terms or an internally recorded attestation of the supplier's agreement with author/reason and supporting context. Missing agreement remains a claim/open payable. No automatic calculation from the discount rate or unilateral small-remainder cancellation is introduced. Existing supplier credit notes representing the concession must be reused, not duplicated.

Supplier actions reuse standalone supplier-payment/refund recording and shared settlement primitives. The invoice-bound supplier payment/refund wrappers retain their current limits; new guided wrappers can allocate only part of an actual payment or refund an available payment credit without inventing a supplier credit note. All of these record observed money; none sends a payment or requests a bank transfer. Existing supplier payment-run preparation does not itself prove execution or settlement; merely approving a run cannot record actual cash or automatically approve a deduction under this feature.

### Symmetric adjustment and excess-refund postings

| Operation | Debit role | Credit role | Evidence amount |
|---|---|---|---|
| Customer settlement reduction | Customer settlement reduction counterpart | Receivable | Explicit accepted claim reduction |
| Supplier settlement reduction | Payable | Supplier settlement reduction counterpart | Explicit documented liability reduction |
| Refund customer excess | Receivable | Cash/payment | Actual amount refunded to customer |
| Receive supplier excess refund | Cash/payment | Payable | Actual refund received from supplier |

The supplier adjustment's payable debit is allocated to the invoice's payable credit. A supplier overpayment is the unallocated debit from its original payment; an incoming refund has the opposite payable credit. These directions must be preserved explicitly rather than forcing all available credits into credit-side LedgerEntries. Customer and supplier adjustment roles/destinations are separately configured. Missing or blocked adjustment configuration leaves ordinary actual-payment recording available.

Reversing a supplier reduction reopens the payable while retaining actual payment. Reversing the payment alone does not cancel separately evidenced supplier agreement. Reversing an incoming refund restores available supplier credit. The original payment/credit-note identity is retained throughout. Neither direction may exceed invoice/credit availability under a race or repeated confirmation.

## V09 — Available credits: Customers and Suppliers

Add one canonical **Available credits** destination in Finance Control with two tabs:

- **Customers**: amounts owed back to customers or available to settle their invoices.
- **Suppliers**: amounts owed back to us by suppliers or available to settle supplier invoices.

Rows aggregate by exact party, side and currency. Columns: partner code/name, currency, unallocated-payment amount, available-credit-note amount, total available, oldest contributing evidence date and Details. Optional zero/fully-used history is separate from the default available-only scope. Search/filters and totals apply server-side before pagination. Totals keep currencies and sides separate.

The available amount is derived from eligible active control entries and effective allocations. Include unallocated actual payments (including overpayments/prepayments) and existing credit notes; do not create a new credit balance table. Count each control entry once even when both payment and invoice/credit registers expose it. Reversed originals and inverse technical entries must not create spendable credit. Invoice-linked settlement reductions are not reusable customer/supplier credit; their reversal follows their own correction flow.

Do not hide available credit by netting it against open invoices automatically. Show available credit and an optional separate open-invoice total; explicit allocation is the business action. A party with both customer and supplier roles has separate tab scopes; no automatic cross-role netting is allowed.

Details show every contributing payment/credit note, original amount, effective allocations/refunds, available residual, source evidence and correction history. Users can select one or more eligible origins, with explicit per-origin consumption in the preview. Actions:

| Tab | Allocate action | Refund action |
|---|---|---|
| Customers | Allocate to customer invoice(s) | Record refund paid |
| Suppliers | Allocate to supplier invoice(s) | Record refund received |

Use existing credit-note allocation/refund behavior for credit-note origins and the new payment-credit wrappers for payment origins. One operation must not consume the same available item twice through these paths. Multi-origin previews identify each consumed item and share atomic available-credit validation. No fake intermediary note or payment is inserted to make origins look uniform.

The detail remains accessible when no invoice is open. Partner detail, Payments, Open Items and Inspector link into the same canonical available-credit read. Empty/loading/error/unknown execution/confirmation states follow the existing shared matrix. V09 is included in keyboard, four-language, two-theme and mobile/tablet/desktop verification, including the German label Guthaben.

## Supplier and credit-view action/hand-off parity

Expose supplier equivalents for actual payment with allocations, deduction explanation, documented settlement adjustment, allocate available credit and record evidenced refund received. The shared services revalidate authority and tenant/party/currency/account references; no automatic financial-source authority approves supplier deductions or refunds.

Handoff has distinct customer/supplier adjustment kinds and direction-specific reason/evidence. Frozen mapping revisions, missing stated tax data and external receipt semantics apply equally. The action catalog, role destinations, previews and journal must never label an outgoing supplier payment as money received or a supplier concession as our customer discount expense.

## Opening-credit origins

The [opening-item extension](opening-items.md) adds explicitly imported customer/supplier credits to V09 and the same bounded allocation/refund actions. Show an Opening credit origin/subtotal separately from payment and credit-note origins; count the control entry once and never its neutral counterpart. Imported receivables/payables can receive the same supported subsequent payment/adjustment actions. Opening evidence is not a fake payment or credit note, and its import does not execute cash movement.

## Advances, holds and money-path interaction

[trade-finance-controls.md](trade-finance-controls.md) restricts consumption of earmarked credits, adds durable payable holds without deleting actual-payment evidence, and preserves same-account settlement through an explicit paired cross-account reclassification where required. Its PSP fee/capture/payout handling is separate from customer/supplier deductions. V09 reports total, free and earmarked credit from the same availability service and cannot spend reserved-for-order money through refund or ordinary allocation accidentally.


## Guided lifecycle implementation update (2026-09-10)

The combined payment/allocation/optional-reduction flow and guided customer/supplier
credit allocation/refund are implemented in the active checkout. Existing invoice-bound
payment commands retain their strict limits. The new flow records actual money separately,
leaves unallocated credit on its original payment, and keeps unaccepted shortfalls open.
Available-credit rows support both payment and credit-note origins. Refund records actual
money only; it does not send payment instructions. Separate posting groups preserve
independent reversal. Complete verification/rollout evidence is tracked in
verification-results.md; opening balances, automated source interpretation and external
accounting handoff remain outside this slice.
