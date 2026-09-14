# Opening Subledger Items: Customers and Suppliers

**Status**: Owner-approved scope addition; specification only.  
**Feature**: [148](spec.md)

## Purpose and boundary

Allow a company arriving from another system to carry existing customer/supplier debts and credits into Reality's operational subledgers. This is an import of outstanding items at a stated cutover date, not a general-ledger opening balance, financial restatement or historical revenue/cash import.

The migration amount is the explicitly supplied outstanding/available amount at the cutover, not necessarily the original invoice total. Preserve an original total separately if supplied; do not reconstruct historical settlements or subtract guessed payments. Nothing about importing an opening item proves it was posted in the external accounting software.

## Four supported directions

| Opening item | Meaning | Debit role | Credit role | Normal subsequent use |
|---|---|---|---|---|
| Customer receivable | Customer owes us | Receivable | Opening subledger counterpart | Allocate customer payment or eligible customer credit |
| Customer credit | We owe customer / credit available for their invoices | Opening subledger counterpart | Receivable | Allocate to customer invoice or record evidenced refund paid |
| Supplier payable | We owe supplier | Opening subledger counterpart | Payable | Allocate supplier payment or eligible supplier credit |
| Supplier credit | Supplier owes us / credit available with supplier | Payable | Opening subledger counterpart | Allocate to supplier invoice or record evidenced refund received |

Each item creates one balanced group using its stated positive amount and the selected direction. Opening subledger counterpart is a dedicated neutral operational role, not cash, revenue, expense, inventory valuation or statutory opening equity. It exists to balance imported control positions without inventing a current business transaction. The operation requires active compatible configured accounts under the same account policy as other normal postings.

## Evidence and entry detail

Prefer individual open documents/credits with stable upstream item identity. Permit an explicitly labelled summary when the source supplies only a total per partner, direction and currency. A customer with a receivable and a credit has separate items even if the amounts could be netted; the same applies to suppliers and dual-role partners.

Required information: tenant-owned party, one of the four directions, stated positive outstanding amount/currency, cutover date, source-system namespace and stable item/import identity, individual-versus-summary mode, external reference where available, and evidence origin. Manual entry creates immutable internal opening-item evidence with actor/reason; file import retains a lossless SourceRecord and exact row identity. Local opaque IDs remain the actual relation keys.

Optional received information: original document date, original document reference/total, due date, source explanation and supporting source links. Missing due date is explicitly unknown; do not apply today's payment terms or cutover date as a fabricated original due date. Summaries without individual due dates are not assigned invented aging buckets. Show their amount under Due date unknown.

The minimal evidence representation can be a dedicated internal/imported Document kind if the later plan proves it fits existing settlement discovery. It must not be a fake newly issued invoice, credit note or payment. One explicit opening-item kind/direction and control entry is sufficient; no standalone running balance table is justified.

## Confirmation, identity and cutover coverage

Provide Preview opening items and Confirm opening items through shared services, with a bounded manually entered or uploaded batch. Preview shows source/cutover, partner matches, directions, amounts by currency, account resolution, duplicate/overlap findings and aging limitations. Confirmation is owner-authorized and revision/idempotency bound; one bounded confirmed batch either records all selected items or none. Larger input is divided into explicit batches, never silently partially imported.

The source item's business identity, namespace, cutover scope and selected direction are retained independently of the delivery/request ID. Re-uploading the same file under another filename or changing the confirmation key cannot recreate an opening effect. A changed snapshot for an already imported scope is a conflict requiring reconciliation, not another opening batch to add on top.

Opening items are a snapshot of amounts still open, not a replay of historical transactions. Later receipt of the original invoice/credit must be matched to the retained source item and attached as explanation without another financial posting. Source invoices and payments already represented in the snapshot must not be replayed into balances. Only explicitly established post-cutover movements/allocations create new effects. If reliable item coverage/time boundaries cannot establish that distinction, preserve the new source evidence and hold financial processing for review.

For summary mode, retain declared coverage (source namespace, partner, direction, currency, cutover and scope description) and prevent an overlapping detailed import from posting automatically. A detail import cannot silently subtract itself from a summary or replace a partly settled summary. V1 offers review/refusal for ambiguous decomposition, not automatic historical reconstruction. An approved non-overlapping scope may be imported separately.

Do not activate a source's historical backfill/automatic recording in a way that bypasses these coverage checks. An existing local open item apparently matching the import is likewise a reconciliation case, not a second balance. Human reference alone is insufficient proof of duplication or equivalence.

## Settlement, available credits and corrections

Imported receivables/payables participate in the same allocation, adjustment, payment and open-item services. Imported credits participate in V09 Available credits even when no current invoice exists, with origin Opening credit. Customer/supplier refund wrappers accept eligible opening-credit control entries as well as payment/credit-note origins; they do not fabricate a credit note to satisfy an old signature.

All actions retain tenant, party, direction, account and currency checks and current availability limits. Per-direction totals never net customer/supplier roles or currencies. Customer and supplier opening credits are counted once alongside other available origins; their neutral counterpart entries are not spendable credit.

Confirmed opening entries and evidence remain immutable. Correction appends an exact reversal and explicitly reviewed replacement where needed. Preview identifies all downstream allocations: reversing an opening group makes those allocations inactive under existing rules, can release actual payment/credit for reallocation and can reopen affected counterpart claims. It never deletes a real later payment/refund. Reallocation to a replacement is a separately explicit effect, not hidden editing of allocation history. Concurrent consumption and reversal must serialize.

## Accounting handoff

Opening imports are labelled opening subledger evidence, excluded by default from ordinary new-invoice/payment handoff and operational sales/cash activity metrics. Do not export them as newly issued invoices or received money, or assume external posting confirmation. If a target explicitly supports opening-item transfer, a separately enabled profile may include the declared direction, cutover and origin with its own reviewed scope; the neutral package can expose them only through explicit opening-item selection. No live vendor opening import is claimed.

## V10 — Import opening items

Finance settings offers **Import opening items**, with links from empty Open Items and Available credits.

1. Select source/cutover and Individual items or Summary balances; show why individual items provide better aging/provenance.
2. Enter or upload rows: partner, direction, currency, outstanding amount, source item/reference, optional original date/due date and evidence context.
3. Review partner resolution, configured neutral/control accounts, totals by direction/currency, unknown due dates, duplicates and coverage conflicts. There is no single net balance input hiding all four directions.
4. Confirm the exact bounded import with explicit effect text: these are carried open positions, not new sales or cash movements.
5. Show the resulting items and import provenance, linking to Open Items, Available credits and Inspector. A lost response reconciles the same import identity before retry.

Open Items adds origin Opening item and original date/due-date availability. V09 adds Opening credits as an origin category/subtotal alongside payments and credit notes. Partner details use the same shared read. Journal identifies the neutral opening counterpart and cutover date without claiming a financial annual opening balance. The standard keyboard, language, theme, viewport and state matrix applies to V10.

## Planned proof

Use four explicit items: customer receivable 1,000; customer credit 100; supplier payable 800; supplier credit 50. Verify separate control/credit views, no cash/revenue/expense activity, customer payment 400 leaving receivable 600, explicit use of customer credit 100 leaving receivable 500, supplier-credit allocation 50 leaving payable 750, and actual refunds of unused opening credits in independent fixtures.

Also test original invoice total 1,000 but imported outstanding 600, unknown due date, same-party dual roles, unlike currencies, re-upload under a new request/file name, changed snapshot, later original invoice, overlapping summary/detail import, already-present local records, post-cutover payment and pre-cutover replay ambiguity. Race allocation/refund against opening reversal and verify effective allocation history, released available credit and explicit replacement reallocation. No test may call a generated net/tax amount or financial opening conversion correct merely because the journal balances.

## Migration relationship coverage

[trade-finance-controls.md](trade-finance-controls.md) requires explicit unknown relationship/coverage handling for migrated orders, invoice lines and source windows. An absent historical link does not prove unbilled goods or missing receipt. Opening scope and later evidence must use that shared contract, and agent explanations disclose the uncertainty rather than reconstructing unsupported historical states.
