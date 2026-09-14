# Run a business on Reality with agents

Reality ships no agents of its own and no workflow editor. What Reality provides is the structure
agents can work on: records with a clear origin, read tools that show the need, proposal tools that
prepare a change, and the **Decisions** page where a person approves it. The agents and workflows
themselves you build outside Reality, with whatever framework or orchestrator you prefer. They work
through MCP, the API or the CLI with exactly these tools, and with no other path into the data.

On its own, Reality receives only two things: orders from a shop or a synthetic source, and money
from a bank statement, a payment provider or the Demo Data source. Everything else that keeps a
trading business running, reserving stock, shipping, billing, matching money, buying, taking
returns, is triggered from outside: by a person in the app, by your workflow, or by your agent. All
three use the same governed tools, and all three follow the same loop of read, propose, decide and
verify.

These playbooks are written for the engineer who builds those agents and workflows. They say, per
business area, which work must happen, which read tool shows the need, which proposal tool prepares
the change, what the clerk decides, and how the agent verifies the result without claiming it. How
the agent itself is built or hosted they do not prescribe; that is your side of the work. The
technical reference for every tool is the [Tool Usage reference](../tool-usage/commands); the mental
model is the [agent capabilities chapter](/tool-usage/#choosing-a-tool) and the
[Process Owner guide](../concepts/business-reality-guide/04-working-as-process-owner).

## Playbooks

- [Analytics](../analytics/#how-an-agent-operates-it): discover the vocabulary with
  `analytics_catalog`, answer with `analytics_query`, explain a number with
  `analytics_contributors`, and hand the definition to the visual Explorer.

- [Operating rhythm](./operating-rhythm): what has to happen every day, every week and every month,
  as concrete tasks with their signals.
- [Sales and fulfilment](./order-to-cash-fulfilment): from an incoming order to a shipped promise,
  including partial shipments, revised promises, holds and stale promises.
- [Receivables and payments](./receivables-and-payments): from a shipped order to a settled invoice,
  including short, over, unmatched and lump-sum payments, reductions, credits and refunds.
- [Purchasing and replenishment](./purchasing-and-replenishment): from a shortage to a paid supplier
  invoice, including purchase orders, receipts, the three-way check, the payment run, supplier
  differences and credits.
- [Returns](./returns): from an announced return to restocked goods and a settled credit note,
  including restocking fees, write-offs, netting and refunds.
- [Master data and sources](./master-data-and-sources): customers, suppliers, items, units, prices
  and payment terms, registered sources, silent sources and failed interpretations.

## The loop every playbook follows

```text
read  ──►  prepare a proposal  ──►  a person decides  ──►  verify
tools      *_propose tools           Decisions page          read again
```

1. **Read.** Reads run immediately and change nothing: `fulfillment_queue`, `exceptions_list`,
   `finance_settlement_context`, `order_explain` and the others. Every read names the records it is
   based on; a read is also how an agent proves a claim.
2. **Prepare.** Every mutation is a `*_propose` tool. It validates the input, shows the exact effect
   and stores a proposal. Nothing in Reality changes yet.
3. **Decide.** The proposal appears under **Decisions** in the app with its preview, the affected
   records and the expected effect. A person approves or rejects it. An agent may approve through
   `proposal_approve_and_execute` only where your company has explicitly given it that authority for
   a class of cases; a conversational "go ahead" is not approval.
4. **Verify.** `proposal_execution_status` returns the receipt and checks it against the records
   that now exist; a following read (`order_explain`, `finance_balances`) shows the new picture. An
   agent reports what the read shows, not what it intended.

Two rules make the loop safe. Amounts and quantities are stated, never computed by Reality from a
rate or a formula; the proposal carries the value someone stated. And a read-time observation, a
candidate, a shortage, an exception, is never stored as a decision.

## What arrives by itself and what does not

![Outside systems on top; orders and payments arrive in Reality by themselves; deliveries, return parcels, customer mail and calls reach the layer above, which books them; the layer reads, proposes, decides and verifies against Reality; availability is reported outward by the layer, not by Reality](/agent-playbooks-layers-en.svg)

Only orders and payments come in on their own (green). Deliveries at the ramp, return parcels,
customer mail and calls reach the layer above (grey), which books them: goods receipts, returns,
announcements, holds, credit notes, open questions. Nothing leaves Reality by itself either
(orange): availability for the shop or marketplace is read by a workflow and sent by it. The blue
layer is yours and sits outside Reality: your agent or workflow. Reality gives it guardrails,
proposal, preview, refusal and decision; how much of the routine runs without asking is set in your
agent, and a person decides in doubt and on anything new. Reality keeps the records, derives the
state and reports the exceptions.

| Arrives by itself                                                                                                            | Must be orchestrated                                                                                                                                                                                               |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Sales orders from a connected shop or Demo Data, as order documents with one delivery promise per line                       | Reserving stock, shipping in full or in parts, revising or holding a promise, closing stale promises                                                                                                               |
| Customer payments from a bank statement, a provider or Demo Data, recorded and, when the reference is unambiguous, allocated | Invoices for shipped goods, decisions on short and over payments, matching payments without a usable reference, credit notes and refunds                                                                           |
| Exceptions derived from all of the above                                                                                     | Purchase orders, goods receipts, supplier invoices, the payment run, return handling, master data                                                                                                                  |
| Nothing else: deliveries at the ramp, return parcels, customer mail and calls reach the layer above, not Reality             | Booking goods receipts and returns, turning mail and calls into announcements, holds, credit notes or open questions; reporting availability to the shop or marketplace by reading stock and demand and sending it |

## The daily minimum

An agent or a workflow that does these six things every day keeps a small merchant running on
Reality:

1. **Clear the fulfilment queue.** Read `fulfillment_queue`; reserve what is available, ship what is
   ready, hold what must wait. See [Sales and fulfilment](./order-to-cash-fulfilment).
2. **Bill what shipped.** Read `exceptions_list` for `shipped_not_billed` and
   `sales_invoice_unposted`; record and post the invoices. See
   [Receivables and payments](./receivables-and-payments).
3. **Work the money.** Read `exceptions_list` for `unmatched_financial_event` and
   `overdue_receivable`; propose allocations for payments with candidates; leave the decision on
   residuals and credit to a person. Same playbook.
4. **Watch supply.** Read `item_supply_demand` for `uncovered_demand` and prepare purchase orders.
   See [Purchasing and replenishment](./purchasing-and-replenishment).
5. **Decide.** Read `proposals_awaiting_approval`; make sure a person sees every open proposal, or
   approve the classes your company delegated.
6. **Verify and report.** Read what you changed. Report the read.

## How to read a playbook

Each playbook has the same shape. A situation is one line of context and a few numbered steps with
fixed keywords: **List** or **See** (what you pull up and what it shows), **Say** (what you tell the
agent), **Agent** (what it prepares), **You** (what you decide), **Check** (what proves it). The
read, exception class or proposal behind a step stands at the end of its line after an arrow.
Proposals are approved under Decisions in the App (`proposals_awaiting_approval`), by a person, or
by your agent for the routine you have handed to it. A closing section lists what is not possible
yet, so an agent does not promise it.
