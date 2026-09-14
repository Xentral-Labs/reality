---
aside: false
---

# Storylines

Storylines are the playground for getting to know Reality. Pick one, press Start, and play a real
business flow step by step in a sandbox of your own, an order from creation to the month-end review,
or a purchase from the order to the discounted payment. Nothing you do here touches a real company,
so try things: confirm, discard, take the other branch, leave the story and poke around in the
sandbox, come back. Every step is an ordinary command or an ordinary read. You see the situation,
prepare the step, read the preview, confirm, and then read what Reality recorded: which events,
records and Facts were added and which findings a rule raised or cleared, and why. That is the point
of a storyline, watching the rules work on evidence instead of reading about them.

Open **Storyline** in the navigation of the app. The library shows the storylines and where you are
in each; a card starts or continues one. While playing, the step card on the left tells the story,
the middle shows the view the step names in the app itself, and the protocol on the right lists
every call with its input, result and catalog entry, and below it what the step added. Click any
call, record or finding and you land on its ordinary page. Free play lets you leave the story and
work in the sandbox; the protocol keeps recording. Autoplay runs the steps on a timer for a
presentation and stops at any click.

Build your own and pass them around. The files below are the packages Reality ships, plain YAML with
symbolic references: download one, change the texts, amounts or steps, and import it into your
library. A run you played by hand can be exported as a draft storyline, so the fastest way to a new
one is to play it once and fill in the texts. Send a package to a colleague, a customer or us; it is
checked against the catalogs on import and runs under exactly the rules a built-in one runs under.
The schema lets an editor complete the format.

Automatically generated from `packages/reality-core/storylines/*.storyline.yaml`. Do not edit this
page by hand.

- [Package schema (JSON Schema)](/storylines/storyline.schema.json)

## Order to close {#storyline-order-to-close}

One customer order, a short delivery, a blocked shipment, an overpayment and a month-end review.
Play it step by step and read what each step recorded.

- [Download the package](/storylines/order-to-close.storyline.yaml) (`order-to-close` v1)

### Steps

| Step                                                     | Kind    | Command or reads                                           | View                        | Findings expected                                            |
| -------------------------------------------------------- | ------- | ---------------------------------------------------------- | --------------------------- | ------------------------------------------------------------ |
| 1. Create the order                                      | command | `order_create`                                             | `view:orders`               | ▲ `outgoing_commitment_at_risk`                              |
| 2. Note the customer reference                           | command | `fact_observe`                                             | `view:documents`            |                                                              |
| 3. Receive a short delivery                              | command | `movement_create`                                          | `view:movements`            |                                                              |
| 4. Reserve the stock                                     | command | `reserve`                                                  | `view:reservations`         | ✓ `outgoing_commitment_at_risk`                              |
| 5. Try to ship                                           | command | `movement_create`                                          | `view:fulfillment_blockers` |                                                              |
| 6. Explain the hold                                      | read    | `exception_explain`, `finance.party_balances.list`         | `view:open_items`           |                                                              |
| 7. Look at the balance (Alternative reached by a branch) | read    | `finance.party_balances.list`, `commitments`               | `view:commitments`          |                                                              |
| 8. Record an overpayment                                 | command | `finance.settlement.apply`                                 | `view:payments`             | ▲ `unmatched_financial_event`, ✓ `overdue_receivable`        |
| 9. Release the hold                                      | command | `party_delivery_hold_release`                              | `view:fulfillment_blockers` |                                                              |
| 10. Ship the goods                                       | command | `movement_create`                                          | `view:movements`            | ▲ `shipped_not_billed`                                       |
| 11. Bill the order                                       | command | `sales_invoice_record`                                     | `view:open_items`           | ✓ `shipped_not_billed`                                       |
| 12. Allocate the credit                                  | command | `finance.settlement.apply`                                 | `view:open_items`           | ✓ `unmatched_financial_event`                                |
| 13. Refund the credit (Alternative reached by a branch)  | command | `finance.settlement.apply`                                 | `view:payments`             | ▲ `unmatched_financial_event`, ✓ `unmatched_financial_event` |
| 14. Keep the credit (Alternative reached by a branch)    | read    | `finance.credits.list`                                     | `view:payments`             |                                                              |
| 15. Check the stock                                      | read    | `inventory`, `commitments`                                 | `view:inventory`            |                                                              |
| 16. Reorder 40                                           | command | `order_create`                                             | `view:orders`               |                                                              |
| 17. Reorder 20 (Alternative reached by a branch)         | command | `order_create`                                             | `view:orders`               |                                                              |
| 18. Month-end review                                     | read    | `exceptions`, `finance.party_balances.list`, `commitments` | `view:activity`             |                                                              |

## Purchase to pay {#storyline-purchase-to-pay}

One purchase order, a short delivery, an invoice that bills more than arrived at a price nobody
agreed, the same invoice a second time, and a discount with a deadline. Play it step by step and
watch the rules raise and clear their findings.

- [Download the package](/storylines/purchase-to-pay.storyline.yaml) (`purchase-to-pay` v1)

### Steps

| Step                                                                       | Kind    | Command or reads                  | View               | Findings expected                                               |
| -------------------------------------------------------------------------- | ------- | --------------------------------- | ------------------ | --------------------------------------------------------------- |
| 1. Place the purchase order                                                | command | `order_create`                    | `view:orders`      |                                                                 |
| 2. Record the shipping notice                                              | command | `shipment_notice_record`          | `view:commitments` |                                                                 |
| 3. Receive what arrived                                                    | command | `movement_create`                 | `view:movements`   |                                                                 |
| 4. Record the supplier invoice                                             | command | `document_create`                 | `view:documents`   | ▲ `billed_not_received`, ▲ `invoice_price_differs`              |
| 5. Book the invoice                                                        | command | `supplier_invoice_post`           | `view:open_items`  | ▲ `purchase_discount_available`                                 |
| 6. Set up the reduction accounts                                           | command | `finance.account.initialize`      | `view:journal`     |                                                                 |
| 7. Read the three findings                                                 | read    | `exception_explain`, `exceptions` | `view:open_items`  |                                                                 |
| 8. The invoice arrives a second time                                       | command | `document_create`                 | `view:documents`   | ▲ `duplicate_supplier_invoice`                                  |
| 9. The copy gets booked too                                                | command | `supplier_invoice_post`           | `view:open_items`  | ▲ `purchase_discount_available`                                 |
| 10. Reverse the wrong posting                                              | command | `ledger_reverse`                  | `view:journal`     | ✓ `duplicate_supplier_invoice`, ✓ `purchase_discount_available` |
| 11. The missing ten arrive                                                 | command | `movement_create`                 | `view:movements`   | ✓ `billed_not_received`                                         |
| 12. Pay inside the discount window                                         | command | `supplier_payment_post`           | `view:payments`    |                                                                 |
| 13. Take the discount, on the record                                       | command | `finance.adjustment.accept`       | `view:open_items`  | ✓ `purchase_discount_available`                                 |
| 14. Month-end review                                                       | read    | `exceptions`                      | `view:open_items`  |                                                                 |
| 15. Record the supplier's credit note (Alternative reached by a branch)    | command | `document_create`                 | `view:documents`   |                                                                 |
| 16. Book the credit note (Alternative reached by a branch)                 | command | `supplier_credit_note_post`       | `view:open_items`  | ▲ `supplier_credit_unclaimed`                                   |
| 17. Net the credit against the invoice (Alternative reached by a branch)   | command | `supplier_credit_note_allocate`   | `view:open_items`  | ✓ `supplier_credit_unclaimed`                                   |
| 18. Pay the net amount inside the window (Alternative reached by a branch) | command | `supplier_payment_post`           | `view:payments`    |                                                                 |
| 19. Take the discount, on the record (Alternative reached by a branch)     | command | `finance.adjustment.accept`       | `view:open_items`  | ✓ `purchase_discount_available`                                 |
