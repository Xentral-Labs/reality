# Playbook: Receivables and payments

From a shipped order to a settled invoice. Reality records every payment that reaches it and
allocates only what the source states unambiguously. Everything about differences, short and over
payments, payments without a usable reference, one transfer for several invoices, credits and
refunds, is prepared by an agent and decided by a person.

Each situation is one line of context and a few numbered steps: what you pull up, what you say, what
the agent prepares, what you decide, what you check. The tool behind a step stands at the end of its
line after an arrow.

Read [Run a business on Reality with agents](./) first, and the product guide
[Record, match and settle customer payments](/concepts/business-reality-guide/03-invoices-and-payments#payments-walkthrough)
for the three tiers a payment passes on its own.

## What Reality holds and derives

- A sales invoice is a Document whose lines name the order lines they bill. Recording and booking
  are two steps; only a booked invoice is an open item.
- A payment is its own Document with a balanced cash/receivable posting. A SettlementAllocation
  links a payment's receivable entry to an invoice's receivable entry. Open amount, paid, partial
  and available credit are derived at read time.
- `finance_balances` gives receivable and payable positions per currency.
  `finance_settlement_context(document_id)` reads one invoice (open amount, discount terms) or one
  payment (available credit, matching invoice choices, each with the reasons it is a candidate).
  `finance_adjustment_context` reads what may be reduced on an invoice.
- Every finance proposal carries `expected_revision` from the context read; a stale revision is
  refused instead of applied.

Exceptions that belong to this area: `shipped_not_billed`, `sales_invoice_unposted`,
`overdue_receivable` (with the tag `early_payment_discount_taken` when the invoice's terms explain a
short payment), `unmatched_financial_event`, `credit_limit_exceeded`, `credit_note_unposted`,
`credit_note_unsettled`.

The examples use one customer, Müller GmbH, and small round numbers so the steps stay visible.

## Situations

### Bill what shipped

Goods left the warehouse, no invoice names them yet. Reality lists what is billable; it does not
invoice.

1. **List:** "Show me everything shipped and not billed." → `exceptions_list` · `shipped_not_billed`
   · App: Exceptions SO-1042 Müller, 5/5 shipped, 240.00 · SO-1043 Müller, 3/5 shipped, 150.00
2. **Say:** "Bill SO-1042 in full, SO-1043 for the three that shipped." Shipped quantity checked
   first → `order_explain`
3. **Agent:** two invoice drafts, RE-0917 240.00 and RE-0918 150.00, prices from the order lines,
   nothing recomputed → `sales_invoice_record_propose`
4. **You:** approve the draft, then approve the booking → `sales_invoice_post_propose`. Only a
   booked invoice is an open item.
5. **Check:** list empty · Open items shows both invoices · receivables +390.00 → `finance_balances`

### A payment matches an invoice exactly

Money for exactly what is open. A bank line or provider that names the invoice is allocated by
Reality itself; this is for a payment that reached you by hand.

1. **Say:** "Müller paid 240.00 for RE-0917, received today." →
   `finance_settlement_context(invoice)`: open 240.00
2. **Agent:** one payment of 240.00, allocated in full; preview received 240.00, allocated 240.00,
   remaining 0.00 → `finance_settlement_propose` mode `payment`
3. **You:** approve.
4. **Check:** RE-0917 paid in Open items · receipt fully allocated in Payments → `finance_payments`
   · receivables −240.00

More than open is refused; that is [Overpayment](#overpayment-and-using-the-excess-later).

### Short payment

Invoice 1,000.00, bank 980.00. Two decisions: book the money, settle the rest.

1. **See:** Open items RE-0920 partially paid, 20.00 open; Payments 980.00 allocated →
   [tier 2 of the payment intake](../concepts/business-reality-guide/03-invoices-and-payments#the-three-tiers-of-payment-intake).
   Paid by hand instead: "980.00 arrived for RE-0920", approve; the 20.00 stays open by itself.
2. **Ask:** "Why 20 short?" → agent: 2 % discount within 7 days, money came day 4, 2 % of 1,000 = 20
   → `finance_settlement_context`, `finance_adjustment_context`
3. **Say:** leave open · accept as early-payment discount · accept as agreed deduction or small
   remainder, with a reason
4. **Agent:** reduction of 20.00, category early-payment discount, your reason as text →
   `finance_adjustment_propose`
5. **You:** approve. Nothing is written off silently; the reduction is its own posting.
6. **Check:** 980 paid, 20 accepted reduction, 0 open. Nowhere "paid 1,000".

Reality never computes a discount from a rate; the agent states what the customer kept.

### Overpayment, and using the excess later

Invoice 1,000.00, customer sent 1,020.00. Invoice paid; 20.00 is customer credit, not revenue.

1. **See:** Payments shows 1,020.00 for RE-0921: 1,000.00 allocated, 20.00 _available_ →
   `finance_settlement_context(payment)`. By hand: "1,020.00 arrived for RE-0921", agent allocates
   1,000.00 and keeps 20.00 as credit → `finance_settlement_propose` mode `payment`,
   `allocation_amount` < `amount`
2. **Ask:** "Who paid too much?" → one row per customer: Müller, credit 20.00, balance −20.00 →
   `finance_party_balances` `credit_only` · App: Finance → Balances · per receipt →
   `finance_credits`
3. **Use later:** RE-0930 open 300.00. "Use Müller's 20.00 on RE-0930." →
   `finance_settlement_propose` mode `allocate_credit`. Approve; RE-0930 280.00 open, credit 0.00.
4. **Or refund:** transfer first, then "we refunded Müller 20.00, reference RF-77" → mode
   `refund_credit`. Reality records that money left; it never sends it.
5. **Check:** Müller gone from the credit list.

### A payment nobody can match

Bank line 1,250.00 from Müller, text "payment invoices September". Recorded, allocated to nothing.

1. **List:** "Which payments are unmatched?" → `finance_payments` unallocated · `exceptions_list` ·
   `unmatched_financial_event`
2. **Ask:** "What could it be for?" → candidates with reasons: RE-0925 open 1,250.00, _amount equals
   open_; RE-0922 + RE-0923, 800 + 450, _sum equals amount_ → `finance_settlement_context(payment)`
   `candidates`
3. **Say:** "Match it to RE-0925." Or: "Leave it as credit, I'll ask Müller." Only the first changes
   the books.
4. **Agent:** allocation 1,250.00 to RE-0925, reason written into the proposal →
   `finance_settlement_propose` mode `allocate_credit`
5. **You:** approve.
6. **Check:** unmatched list empty · RE-0925 paid.

The agent never picks by amount alone when several fit; it presents all candidates or asks the
customer.

### One transfer for several invoices

1,000.00 once, advice lists RE-0926 400.00, RE-0927 350.00, RE-0928 250.00. One step per invoice
today.

1. **Say:** "Müller paid 1,000.00 for RE-0926, 0927, 0928."
2. **Agent:** receipt against RE-0926: 400.00 allocated, 600.00 credit →
   `finance_settlement_propose` mode `payment`. Approve.
3. **Agent:** offers 350.00 to RE-0927, then 250.00 to RE-0928 → mode `allocate_credit`, one
   proposal each. Approve each; credit 600 → 250 → 0.
4. **Check:** three invoices paid · receipt 0.00 available. A shortfall would stay as credit.

### Credit notes and refunds against them

Something was wrong or came back; the customer is owed money. Credit note, booking, settlement:
three steps.

1. **See:** _Returned and not credited_ for SO-1042: 2 of 5 back, invoiced on RE-0917 at 48.00 →
   `exceptions_list` · `returned_not_credited`
2. **Say:** "Credit Müller the two returned units on RE-0917."
3. **Agent:** credit note GS-0041, 96.00, line names the invoice line →
   `sales_credit_record_propose`. Restocking fee: a charge line, goods credited in full
   ([Returns](./returns)).
4. **You:** approve the note, then its booking → `credit_note_post_propose`
5. **Settle:** "Net it against RE-0917" → `credit_note_allocate_propose` · or, after your transfer,
   "refunded 96.00, RF-78" → `customer_refund_post_propose` · or leave it available →
   `finance_credits`
6. **Check:** exception gone · Open items shows netting, refund, or the credit as available.

### Watch the money

The daily glance before deciding anything.

1. **Ask:** "How does the receivables side look?" → open per currency, overdue, unmatched payments,
   available credit, new cases → `finance_balances`, `exceptions_list`, `finance_payments`,
   `finance_credits` · per customer: open, overdue, credit, balance → `finance_party_balances` ·
   App: Finance → Balances
2. **Order:** unmatched payments first (money already here), then today's differences, then overdue.
3. **Evening:** same question; the agent reports what changed, not what it intended.

## How an agent should phrase results

- "Invoice `doc_…` open 20.00 EUR after a receipt of 980.00; the terms allow 2 % within 7 days and
  the payment came on day 4" is a read with context.
- "Prepared acceptance of a 20.00 discount on `doc_…`; decision `prp_…` pending" is a proposal.
- "Approved; Open items shows 980.00 paid, 20.00 accepted reduction, 0.00 open" is verified.
- Never say "the customer paid 1,000" when 980 arrived.

## Not possible yet

- Payments from Stripe, PayPal or Shopify Payments are not received; only the bank statement file
  and Demo Data deliver payments today. The shared intake core exists for those providers; their
  normalisers do not.
- No single action distributes one receipt over several invoices; use the steps above.
- No dunning run and no automatic delivery hold from `credit_limit_exceeded`; the hold is a proposal
  in the fulfilment playbook.
- No supplier-side matching in this playbook; supplier invoices and the payment run are in the
  [purchasing playbook](./purchasing-and-replenishment).
