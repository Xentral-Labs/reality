# Experience a demo company

**Bring your demo company to life, one step at a time.** Your agent takes responsibility for
operational work; you add responsibilities gradually. Each mission has a short prompt and a visible
result. You can stop after any mission and return later.

You hand operational responsibility to the agent. It monitors, prioritizes and follows work through
independently. These missions configure its responsibilities one by one; they are not a list of
business tasks for you to perform. You review outcomes and answer genuine decision questions.
Reality currently requires confirmation of specific business proposals.

**Steps 1–5 are enough to begin:** create a company, connect an agent, understand an order and
review your first Decision. Then add purchasing, Finance and optional email. Each area gets its own
cadence immediately; finish by checking the combined plan. Use the same agent conversation; new
conversations need the saved assignment and access to the same company.

Reality supplies business records and tools. Your agent system coordinates work and recurring
execution. Live simulation supplies additional synthetic arrivals.

**When you pause:** Manual prompts do not keep running on their own. After each routine setup, pause
active agent tasks in your agent system. Control new synthetic arrivals separately through **Demo
Data** in Reality. You can still review or reject pending proposals in Reality.

## 1. Create your account

<ProductLink>Open Reality and create your account</ProductLink>. Confirm your email address and sign
in. If you already have an account, sign in with it.

Use the hosted app for this walkthrough. You do not need to connect your ERP to try the demo.

## 2. Create a demo company

On the company setup screen:

1. Enter a name, for example **My Reality Demo**.
2. Choose **Try demo data**.
3. Leave **Enable live simulation** selected.
4. Confirm **Create company** and wait for preparation to finish.

If you already work in another company, open **Companies** and create a separate demo company there.
Reality opens the new company automatically when it is ready. Its **Sandbox** label tells you that
you are working with test data.

The company already contains products, customers, warehouses and business history. Live simulation
also supplies new synthetic orders, followed by invoices and payments. It does not connect a real
ERP or move real goods or money. Preparation and new arrivals depend on the running background
services; you do not need to wait for a new order to explore the existing examples.

## 3. Connect your agent

Follow [Connect your agent](./connect-agent), then return here. Deliberately select your demo
Sandbox and approve access in the browser. This mission needs read tools and the required proposal
tools; a read-only connection cannot prepare a change.

Account registration, email confirmation and demo-company creation are human browser steps. The
agent begins after connection and authorization. You can also try the first round in Reality
**Chat** if AI is configured for your company. Later repetition needs an agent system that can run
the task regularly with access to Reality.

Keep Reality open alongside your agent: **Inbox → Welcome** shows activity and queues. Under **Sales
→ Orders**, find an open order. Your agent selects a suitable case and reads its current state; the
running demo may already contain further activity.

## 4. Your agent understands its first order

**Goal:** Hand over responsibility and begin with a concrete case. Copy this prompt:

```text
You are the operational agent for my selected Reality demo company. Use available
Reality tools to prioritize open orders: 09:00 recorded cancellations and holds;
11:00 and 12:00 delivery promises and blockers; 13:00 recorded shipments; 14:00 returns.
Explain one suitable open order using its current records and actual promised dates.
Obtain information yourself; ask only when you cannot resolve it. Invent no data or rules.
Read only for now; business changes require specific Decisions and my approval.
Continue other work while Decisions are pending.
Run once now. Then configure repetition in your agent system only if tools and saved
assignment and progress are available. Confirm time zone and working days; reuse existing
routines. Show the verified next run and how to pause. Report missing setup clearly.
```

**Your success:** The agent explains an actual open order through its current records, including
fulfilled and remaining quantities. For connection issues, use
[your first business question](./first-question).

**You can stop here:** Pause the configured read routine in your agent system. No business change
has been executed.

## 5. Your agent prepares its first business action

**Goal:** Experience a complete loop with a small reservation.

```text
Prepare a reservation proposal for the open order we inspected. Check available stock,
eligibility and pending proposals with Reality tools. Use actual record IDs and show
quantity, location, effect and the proposal_review tool call; include an optional review link.
Do not execute it or create duplicates.
If blocked, explain why and inspect one other suitable open order. Invent no stock.
```

Read `proposal_review` in your agent, or open the optional review link under **Decisions**. Check
records and effect, then approve only the specific change you want; otherwise reject it. Reserving
does not ship goods. [Prepare your first action](./first-action) explains the individual checks.

Then return to the agent:

```text
Check the reviewed proposal's execution status and affected records in Reality.
Explain what changed and what remains open. Do not create a replacement for a
rejected, pending or unclear result.
```

**Your success:** You see the difference between proposal, approval and executed effect. If stock or
permissions are missing, the evidenced blocker is your result.

**You can stop here.** Approval applies only to this proposal. The recurring read routine from step
4 still changes nothing; pause it in your agent system if needed.

## 6. Your agent discovers purchasing needs

**Goal:** A first purchasing overview without immediately ordering anything.

```text
Check purchasing every three hours during agreed working hours, for example
09:00, 12:00 and 15:00. Use Reality tools to prioritize uncovered demand, recorded
receipts and overdue supplier promises. Connect each need to affected customer orders.
An order is not a receipt; missing promised dates do not prove lateness.
Obtain information yourself and ask only for unresolved inputs. Order and send nothing;
further changes need specific proposals and my approval. Avoid duplicate proposals.
Run once now. Then configure repetition in your agent system only if tools and saved
assignment and progress are available. Confirm time zone and working days; reuse existing
routines. Show the verified next run and how to pause. Report missing setup clearly.
```

**Your success:** You see a concrete need or supplier case. In current demo baselines, `PO-001` has
received two of five units and its remainder is overdue. `PO-003` has no promised date; `PO-006` has
five received and billed units after the invoice-backed receipt-cost setup. Inspect the current
invoice and line references; the initial purchase tuple alone does not describe the completed
profile. Older companies may contain different cases.

New sales orders change demand. **Live Demo does not generate new purchase orders or supplier
receipts.** If a supplier case remains unchanged, the agent can report that.

**You can stop here:** Pause the purchasing routine. Your success includes the first overview and,
where configured, the verified next run.

<details>
<summary>Optional: Walk through a replenishment order together</summary>

Select an evidenced need. Provide supplier, quantity, date and explicitly stated price and amount
values. The agent must not invent missing buying rules or supplier assignments.

```text
Prepare a purchase-order proposal for the selected need. Read existing records and
ask for missing supplier, quantity, date, stated prices, amounts or buying rules.
Use actual IDs and the values I provide; do not invent or recompute missing amounts.
Show the effect and review link. Execute nothing without my approval.
```

After approval, inspect the incoming commitment. An explicitly fictional counted receipt can then be
proposed in the Sandbox with `shipment_receive_propose`, purpose `supplier_delivery`, and confirmed
separately. Stock changes only on execution. This is an exercise initiated by you. A supplier
reminder stays a draft in your agent system; a Reality Decision does not send it.

</details>

## 7. Your agent understands the financial position

**Goal:** A small Finance round with one explainable case.

```text
Check Finance at 09:00, 12:00 and 15:00 during agreed working hours and report at 17:00.
Use Reality tools to show open amounts by currency, new or unallocated payments and
credits. Explain one relevant case with supporting records and prioritize next steps.
Ask only about unresolved matches. Change nothing and do not duplicate invoices or
payments. Combine this with existing purchasing checks where practical.
Run once now. Then configure repetition in your agent system only if tools and saved
assignment and progress are available. Confirm time zone and working days; reuse existing
routines. Show the verified next run and how to pause. Report missing setup clearly.
```

**Your success:** The agent explains a payment, partial payment, open position or credit. New
customer invoices and payments arrive with different delays; not every round has a new case to
clarify. Supplier cases such as `SINV-004` are already partly paid.

An allocation or adjustment comes afterwards as its own proposal with current context, evidenced
inputs and your approval. The agent asks when matches are ambiguous.

**Optional: your first payment preview.** First agree the date by which payment should occur:

```text
Add a daily payment preview at 15:00 to our Finance routine. Agree the payment cutoff
date or its rule with me. Use Reality tools to explain eligible payments and reasons.
Post and pay nothing. Run once now; schedule only with available tools and saved
assignment and progress. Confirm time zone and working days, avoid duplicate routines
and show the verified next run and pausing. Report missing setup.
```

The preview pays nothing. Even an approved Reality posting does not execute a bank transfer. A
customer dunning preview through `finance_dunning_run_context` requires a suitable dunning schedule;
it sends no message.

**You can stop here:** Pause the Finance check or combined purchasing/Finance routine. Inspect the
next run before leaving it active.

## 8. Your agent takes on test customer support

**Goal:** A first support round with an explainable customer case. Email is optional.

If your agent system supports email, connect a selected test mailbox there and check reading and
reply drafts. The Reality connection grants no mailbox access. Send this yourself and include a
reference to an actual order you selected so the agent can match the inquiry:

```text
Subject: Question about my order

Hello, when will my order arrive? Has anything shipped already?
```

```text
Check the selected test mailbox every 30 minutes during agreed working hours, for
example 09:00–17:00. Verify mailbox and Reality access. Match a test inquiry to its
actual order; ask me if the match is unclear. Draft a friendly reply from recorded
order and shipment information and show the supporting records internally. Invent no
delivery date. Avoid duplicate drafts and send nothing. Sending needs my separate
approval in the agent system; a Reality Decision does not authorize email.
Run once now. Then configure repetition in your agent system only if tools and saved
assignment and progress are available. Confirm time zone and working days; reuse existing
routines. Show the verified next run and how to pause. Report missing setup clearly.
```

**Your success:** A reply draft explaining the actual order state. Review recipient and content in
the agent system, then send it yourself or explicitly approve sending there. **This mission has no
Reality Decision for sending email.**

**You can stop here:** Pause the support routine. Recurring monitoring is active only after verified
setup with mailbox and Reality access. Without that capability, the first draft is your result.

## 9. Your agent checks how the routines work together

**Goal:** Existing tasks fit together. You do not configure a second daily plan.

```text
Review our sales, purchasing, Finance and connected support routines now. For each,
show task, time or interval, time zone, working days, tools, next run and pausing.
Distinguish verified active routines, manual checks and missing setup. Verify an actual
run if available; report if none has run yet. Check gaps, overlaps and pending Decisions.
Propose corrections without creating a second daily plan or bypassing approvals.
Report briefly: What is running? What needs my decision? What is missing?
```

**Your success:** A verifiable combined plan with actual next runs. Example times are not company
settings: time zone and working days must fit your exercise. The 13:00 shipment check is not a
pickup confirmation. The demo evidences no real DHL pickup and supplies no new cancellation requests
from a mailbox.

**You can stop here:** Pause the desired routines in your agent system. Pending Reality proposals
remain separately reviewable. For tasks without suitable automation, you can repeat the first round
manually whenever you want.

## What runs live and what needs further input

| Area                      | Existing demo cases                                        | Continuous arrivals                               |
| ------------------------- | ---------------------------------------------------------- | ------------------------------------------------- |
| Sales                     | Open commitments, reservations, partial shipment and holds | New sales orders; no automatic shipment           |
| Purchasing                | Orders, partial receipts, supplier invoices                | No new purchase orders or supplier receipts       |
| Finance                   | Open, partly paid and paid positions, credits              | Customer invoices and synthetic customer payments |
| Returns and cancellations | Existing return, credit and cancellation cases             | No new returns or cancellation requests           |

Continuous purchasing simulation would require extending the live source with purchase orders,
partial receipts and supplier invoices. New customer requests, returns and carrier pickups likewise
need additional sources or demo events. The demo does not claim these effects without evidence.

Explore [Purchasing and replenishment](/agent-playbooks/purchasing-and-replenishment),
[Receivables and payments](/agent-playbooks/receivables-and-payments) or your
[operating rhythm](/agent-playbooks/operating-rhythm). You can also
[explore the demo company](./demo-data) or [play a storyline](/storylines/).

**Choose another path:** [Build from scratch](./start-business) ·
[Use an existing company](./existing-business).

## Evidence and decisions through MCP

Start with `company_context`, then use `capability_catalog` for the tools this connection may call.
Read `proposals_awaiting_approval` as cursor pages (up to 100 summaries per page); filter by the
stored application tool name, such as `reserve`. An agent must inspect matching pending proposals
before preparing another change. Read the exact ID with `proposal_review`.

Before requesting a decision, explain the company, affected order/commitment IDs and human numbers,
item, location and quantity; current state versus proposed effect; prerequisites, blockers and any
matching pending proposal. Use the retained review evidence and state missing evidence explicitly. A
proposal does not reserve or move stock. Only after explicit authorized approval call
`proposal_approve_and_execute` with `approved: true`, the exact proposal ID and the returned
`confirmation.review_token` when present. Use `proposal_execution_status` to reconcile execution,
then read the named operational records. A read/propose-only connection cannot confirm; review does
not elevate its rights. A browser review link is optional; the decision cycle works through MCP.

Use the complete `confirmation.arguments` only after that decision; it includes the required
`approved: true`. Fresh demo reservations already retain their full review. If an older proposal
reports `confirmation.review_preparation_required`, the first approved call only prepares the
review. Follow `confirmation.after_preparation`, inspect the new exact review and obtain a new
explicit decision before execution. Reads never prepare or refresh a review.

Execution and status responses expose current callable MCP reads in `next_step.verification_reads`.
The receipt keeps its original `verification_reads` projection names; use the separate guidance for
tool calls. Check current connection permissions as well: `confirmable` describes proposal state,
not a grant of confirmation rights.

Internal Chat honors explicit current-turn read-only instructions for both advertised tools and
execution. Shipping questions receive a bounded company-wide sample of retained shipment Movements;
follow its completeness and `has_more`, and use `order_explain` for the exact order. This context
does not guarantee every model answer or establish a company shipment total.

`shipments_list` holds consignments and packages. An empty list does not exclude shipment Movements;
use `order_explain` and discovery family `movement` to inspect held shipping evidence. For invoice
lines, discover `document_line` with the exact `document_id`; preserve stated amounts and
distinguish missing information from zero. This does not provide a complete allocation explanation.

New Demo Data source records can await interpretation/admission approval. Their arrival alone does
not create an accepted order, invoice or payment. Inspect the source and pending interpretation, and
follow its existing review boundary before claiming a business effect.

For a support case, cite the current stored evidence. Do not invent a cause, guarantee a delivery
date or claim that a future customer message was sent. New promises or outgoing payloads require
their own exact proposal and explicit approval.

Recurring work belongs to the external agent system. A working MCP chat connection does not prove
scheduled execution; inspect the client's actual scheduling controls and saved task state. Qualify
Claude Chat and Cowork separately rather than transferring a scheduling claim between them. Check
company time zone separately from the routine's time zone (for example UTC versus Europe/Berlin),
workdays, actual next run, any displayed scheduling delay/jitter, device availability and how to
pause. A prompt restricting tools does not disable other connectors: verify the external agent's
enabled connections separately. If those controls cannot be verified, report the missing setup.
