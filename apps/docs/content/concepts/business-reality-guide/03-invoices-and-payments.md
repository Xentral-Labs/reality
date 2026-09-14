# Invoices and Payments

[Back to the guide overview](../business-reality-guide)

## Invoice, partial payment and credit {#payments-walkthrough}

Huber's delivery on order `SO-1001` is complete. Financially, that settles nothing yet. The related
invoice `INV-1001` states **EUR 1,470**. Its line is linked to the order line it bills. This
relationship is part of our example from the outset.

We take the amount from the invoice. We do not recalculate it from quantity and unit price. Tax
splits are outside this simplified posting example; it is not an invoice-authoring template.

### 1. Record the invoice: preserve the statement

An invoice arrives from the system issuing it or is entered through a supported Reality operation.
The invoice records the commercial statement that Huber is being billed EUR 1,470. As with the
order, the document and line are **Document** and **DocumentLine** records.

Recording an invoice is not posting it. Completing delivery does not create that invoice by itself
either. Delivery and invoice are linked but separate business events.

### 2. Post the invoice: establish the receivable

Acme posts `INV-1001`. This creates a group of **posting records (LedgerEntry)**:

| Account       |     Debit |    Credit |
| ------------- | --------: | --------: |
| Receivables   | EUR 1,470 |         — |
| Sales revenue |         — | EUR 1,470 |

An open item of EUR 1,470 now exists. The posting group is balanced. This financial statement
changes neither delivered quantity nor stock.

### 3. Record the payment: preserve the money received

Huber pays EUR 500. The received payment information produces its own payment document and a posting
debiting bank and crediting receivables. Reality records the stated actual receipt. A payment can
already be recorded while its intended invoice is still unclear.

The payment alone therefore does not establish that `INV-1001` is settled.

### 4. Allocate the payment: settle this invoice

EUR 500 of the payment is applied to `INV-1001`. This **settlement allocation** is a
**SettlementAllocation** in the model. It connects the appropriate payment and invoice posting
records.

The result is **EUR 1,470 receivable − EUR 500 allocated = EUR 970 open.** The original invoice
amount remains EUR 1,470. The outstanding amount is a current calculation.

An invoice can receive several payments; one payment can settle several invoices. Allocation records
how much actually belongs where. Equal amounts or the same customer name do not replace that
relationship.

### 5. Apply a credit note

Acme records and posts a EUR 100 credit note and applies it to `INV-1001`. With that relationship,
this invoice now has **EUR 970 − EUR 100 = EUR 870 open.** An unused credit note would remain
available credit rather than closing an arbitrary invoice.

The credit changes the receivable. It does not return a lamp to stock. If Huber sends goods back,
the actual receipt is recorded separately as a return.

### Keep the answers separate

| Question                                       | Answer at the end of the example                                        |
| ---------------------------------------------- | ----------------------------------------------------------------------- |
| What amount does the invoice state?            | EUR 1,470                                                               |
| How much money arrived?                        | EUR 500                                                                 |
| How much payment is allocated to this invoice? | EUR 500                                                                 |
| How much credit has been applied?              | EUR 100                                                                 |
| What remains open?                             | EUR 870                                                                 |
| Is the remainder overdue?                      | That requires a due date and assessment date; neither is supplied here. |

## What is allocated automatically and what needs a decision

A received payment is recorded first. If the source supplies an unambiguous reference to exactly one
suitable posted invoice for the same customer and currency, the existing allocation flow can apply
it. It allocates no more than the outstanding amount.

Without an unambiguous reference, Reality shows reasoned candidates. An authorised person checks the
allocation. An agent can read the situation and prepare an exact proposal. This grants no general
permission to confirm changes itself; [chapter 4](./04-working-as-process-owner) explains the
supported approval paths.

| Situation         | What remains visible                        | Next business decision                                       |
| ----------------- | ------------------------------------------- | ------------------------------------------------------------ |
| Partial payment   | Remainder on the invoice                    | Leave open or separately review a supported deduction        |
| Overpayment       | Invoice settled, surplus customer credit    | Allocate elsewhere or record a refund that actually occurred |
| Unclear reference | Unallocated payment and possible candidates | Check the reference and confirm a suitable allocation        |

No remainder silently disappears as tolerance. An accepted deduction needs its own reasoned posting.
Automatic matching on an exact reference and a confirmation-required agent action are different
paths; both use the shared application services' rules.

## Correct errors and check results

A wrong posting is reversed with a complete inverse posting group. The original remains visible.
Allocations attached to a reversed original posting become inactive; a previously settled item can
reopen. A replacement payment needs its own posting and allocation.

The invoice leads to postings, payments and deductions. The payment leads to its original bank or
provider information. An agent can explain the outstanding amount from these records. It must not
replace a stated invoice or payment amount with its own recalculation.

### Check your understanding

The EUR 500 payment is posted but not yet allocated to any invoice. Can you already show EUR 970
open on `INV-1001` just because that money arrived?

<details>
<summary>Show answer</summary>

No. Allocating the payment to this invoice reduces its outstanding amount. Recorded money and a
settled invoice are separate statements.

</details>

<details>
<summary>Further detail: reference types, automatic matching and partner balances</summary>

### The three tiers of payment intake

Every customer payment that reaches Reality, from a bank statement, a payment provider or Demo Data,
passes the same three tiers. Each tier has a precondition, a fixed action and things it may never
do.

| Tier           | Requires                                                                                                    | Reality does                                                                           | Never                                                                 | You see                                                       |
| -------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------- |
| **1 Record**   | A payment arrived. Nothing else                                                                             | A payment Document and a balanced cash/receivable posting, linked to the source record | Interpret, allocate, refuse money                                     | A new line in Payments, _unallocated_                         |
| **2 Allocate** | The source states a reference that resolves to exactly one posted invoice of the same customer and currency | Allocates the smaller of amount and open amount to that invoice                        | Guess, over-allocate, write off, accept a discount, invent an invoice | Invoice _paid_ or _partially paid_; excess as customer credit |
| **3 Propose**  | Money is unallocated and no unambiguous reference exists                                                    | Computes candidates at read time, each with its reason; a person or agent confirms one | Store candidates, rank them as truth, allocate without confirmation   | The payment with a candidate list in Payments and over MCP    |

**What a stated reference must be.** Tier 2 knows what each number is for and follows it to the
invoice; human numbers are used to look up, never stored as the link.

| The payment names                                   | Reality resolves                                    | Tier 2 allocates                             |
| --------------------------------------------------- | --------------------------------------------------- | -------------------------------------------- |
| your invoice number                                 | the posted invoice                                  | yes, if exactly one                          |
| the shop's order id (card, PayPal, wallet payments) | the order, then the invoice that bills it           | yes, if exactly one invoice bills it         |
| the shop's order number (`#1001`)                   | the order, then its invoice                         | yes, if exactly one                          |
| the customer's purchase-order number                | the order carrying that reference, then its invoice | yes, if exactly one                          |
| only your customer number                           | the customer                                        | no; it narrows tier 3 candidates             |
| a provider transaction id                           | the payment itself                                  | no; it identifies the money, not the invoice |
| nothing usable                                      | nothing                                             | no; tier 3                                   |

Two invoices for one order, or one invoice for several orders, are not errors; they yield candidates
instead of an allocation.

**Outcomes of tier 2.** No tolerance closes a residual quietly; every reduction of a receivable is a
separate, confirmed posting with a reason, never part of matching.

| Paid versus open | Allocation      | Result                                                                                                        | Left to decide                                             |
| ---------------- | --------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| equal            | full            | invoice _paid_                                                                                                | nothing                                                    |
| less             | the paid amount | invoice _partially paid_; `overdue_receivable` after the due date, tagged when the terms explain the residual | leave open, accept a stated deduction, or explain it       |
| more             | the open amount | invoice _paid_; the excess is customer credit, reported as `unmatched_financial_event`                        | allocate the credit to another invoice, or record a refund |

The [base sequence at the start of this chapter](#payments-walkthrough) follows Huber’s invoice; the
[receivables playbook](../../agent-playbooks/receivables-and-payments) shows the desk work behind
each outcome.

### Balances per customer and supplier

The balance list answers where one party stands. It is derived at read time, one row per party and
currency: open amount (the sum of that party's open items), of which overdue (the open items whose
due date from the aging register lies before the read's instant), available credit (the sum of that
party's unused payments and credit notes), and the balance, open minus credit. Nothing is stored,
nothing is converted between currencies, and nothing is netted in the books: using a credit against
an invoice stays a confirmed settlement. Every row opens the party's open items and credits, which
are the exact documents that were summed. In the App the list is Finance → Balances; for agents it
is the read `finance_party_balances`. A balance proves a position at an instant, not that a customer
will pay.

</details>

For daily handling:
[Receivables and payments playbook](../../agent-playbooks/receivables-and-payments). Next in the
learning sequence: [Working as a Process Owner](./04-working-as-process-owner).
