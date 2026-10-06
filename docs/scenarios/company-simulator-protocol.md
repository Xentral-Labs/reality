# Company month protocol

The authoritative script is [complete.yaml](../../packages/reality-core/scenarios/company_simulator/profiles/general_company/complete.yaml), profile `general_company_complete_v2`. This readable guide summarizes its released sources, causal barriers and selected **prompt-operator** checkpoints. Other operators are reconciled against their own accepted actions; these prompt numbers are not forced onto delayed/idle runs.

## Start and daily rhythm

Day 0 creates an ordinary named local test company with normal admission, two customers, one supplier, two items, two warehouses and stated opening quantities A6/B6 in W1. W2 and financial balances start at zero. The initial checkpoint must pass before the first customer request is released.

Each ordinal day releases scheduled external sources, receives due goods for actually accepted purchases, records actual package arrival/failure evidence for dispatched shipments, releases due payment/refund sources and known stock evidence, then lets the operator act. Accepted effects pass through normal proposal tools (or canonical reviewed Shopify intake). The read-only observer verifies stock, commitments, invoice balances, allocations, postings and shipment evidence before the next day.

Application timestamps remain real; the simulator's ordinal day is held in the run journals. This proves ordering, booking and scenario delivery targets, not a global virtual application clock or every date-sensitive production exception.

## Customer script

| Request | Released day | Item / quantity | Stated total | Required delivery day | Additional source behavior |
|---|---:|---|---:|---:|---|
| S01 | 1 | A / 4 | EUR40 | 5 | Dispatch at most 2 per action; customer pays 10 then 30 |
| S02 | 2 | B / 3 | EUR30 | 6 | Customer pays 10 then 20 |
| S10 | 3 | A / 5 | EUR50 | 8 | Remaining quantity cancelled on day4; prompt ships2, bills stated20 |
| S03 | 4 | A / 5 | EUR50 | 11 | After accepted invoice and payment, customer announces return1; credit10 and refunds4/6 remain separate |
| S04 | 6 | B / 8 | EUR80 | 16 | Shortage requires purchase and partial receipts; customer pays20/60 |
| S05 | 8 | A / 2 | EUR20 | 12 | Cancelled before dispatch by prompt operator; no invoice |
| S06 | 11 | B / 4 | EUR40 | 19 | First attempt explicitly undeliverable; physical stock returns, obligation reopens, then operator re-dispatches |
| S07 | 15 | A / 3 | EUR30 | 22 | Overflow transfer and arrived return affect available picking stock |
| S08 | 19 | B / 5 | EUR50 | 27 | Carrier tracking exception delays observed arrival; it does not restore inventory |
| S09 | 24 | A / 4 | EUR40 | 30 | Customer pays20 within the run; final20 arrives beyond the month |

Supplier pack quote: quantity8, stated amount40, two physical receipts of4 after2 and4 days from an accepted purchase. B receipts are delayed one further day by private world behavior; the operator sees quoted dates and actual received quantities, not future actual delay schedules until the supplier releases a notice one day after purchase. Supplier invoice follows completed accepted receipts; supplier payment follows the accepted invoice.

External warehouse sources: day12 verified count loss A1; day14 transfer A2 W1→W2; day16 transfer A2 back. These sources are blocked/reportable if the required physical stock does not exist under a different operator.

## Selected prompt checkpoints

Signed financial balances below mean debit minus credit. Negative payable/revenue balances are normal credit balances. All quantities are pieces; balances are EUR. Every day has its own complete machine-readable checkpoint.

| End of ordinal day | Physical A | Physical B | Cash | Receivable | Payable | Inventory posting balance | Revenue |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| 1 | 4 | 6 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 3 | 20 | 70 | 0 | 0 | -90 |
| 8 | 3 | 0 | 90 | 0 | -40 | 40 | -90 |
| 14 | 2 | 0 | 80 | 60 | 0 | 80 | -220 |
| 17 | 0 | 3 | 130 | 30 | 0 | 80 | -240 |
| 30 | 4 | 2 | 190 | 20 | 0 | 160 | -370 |

Day14 A2 is in W2; the pending return is not physical stock. A return never decreases the original delivered/fulfilled quantity. The credit's remaining balance is10 on its accepted day,6 after the first refund and0 after the second refund.

Prompt end state: 10 sales orders, 4 purchase orders, 72 ledger entries; 8 fulfilled customer commitments and 2 cancelled commitments (one cancellation retains its already-shipped quantity). Last sales invoice has20 open; all other authored invoice/credit obligations are settled. Gross operational posting balances do not claim opening-stock valuation or complete statutory accounting.

These final cardinalities and balances are executable assertions in `tests/scenarios/test_complete_company.py`, in addition to the independent dynamic daily oracle.

## Synthetic Shopify observation script

The [Shopify script](../../packages/reality-core/scenarios/company_simulator/profiles/shopify_company/scenario.yaml) releases three authored Shopify-shaped orders and one refund through existing reviewed intake. Provider statements arrive on days3,5,11 **regardless of agent invoices**. Their stated totals are charges90, refunds10, fees4 and bank deposits76.

One10 charge deliberately has an unknown shop reference. It remains unmatched and explains clearing -10; the operator must not invent a customer association. Prompt invoices settle except10 on the last invoice. Idle mode still receives every bank deposit: known incoming80 and refund10 are recorded but unallocated, distinct from the unmatched10 source line. There are no invented warehouse receipts, credit notes or invoice allocations just because a payout arrives. Provider statement replay cannot duplicate accepted records/postings.

These are explicitly synthetic examples and generic supported provider statements, not original Shopify Payments exports.

## Reports and operators

See [launch, file map, live review contract and coverage boundaries](../../packages/reality-core/scenarios/company_simulator/README.md). `report.json` gives separate core status, quantity/destination/deadline goals, coverage exercised and exact opaque references. `checkpoints.jsonl` holds independent expected versus actual state. `events.jsonl` retains exact proposal/receipt evidence; `messages.jsonl` retains locally simulated correspondence and its SourceRecord IDs.

## Correspondence release protocol (complete v2)

Customer order messages release on each order day; cancellations release when requested, returns when announced, and status enquiries one day before each deadline. One day after an accepted purchase the supplier confirms the quantity/quoted schedule and, for delayed SKU B, states revised dates. A receipt notice follows each actual partial warehouse receipt. These are local synthetic Sources, not mailbox delivery evidence.

Prompt/delayed fixture agents acknowledge released messages and record factual updates after accepted dispatch, cancellation, invoice, credit and supplier-payment actions. Delayed responses respect the same four-day customer delay. Idle/custom operators receive no automatic replies; custom `reply` commands record drafts only. Threads and explicit parties let the spectator show both sides without treating a message as a stock movement or payment. The original business milestones above are unchanged; v2 adds six planned communication families, so full prompt coverage is 28 rather than the original 22.

Verified prompt-month communication milestone: 106 messages = 37 incoming + 69 simulated replies; zero drafts. Incoming: ten orders, ten deadline enquiries, two cancellations, one return request, four supplier confirmations, two delay notices and eight partial-receipt notices. Customer views contain 74 messages (37 per customer); supplier view contains 32. These counts apply to the full complete-v2 prompt run, not other horizons/operators or historical v1 journals.
