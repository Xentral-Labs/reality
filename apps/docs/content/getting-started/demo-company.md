# Experience a demo company

**Bring your demo company to life, one step at a time.** Your agent takes responsibility for
operational work; you add responsibilities gradually. Each mission has a short prompt and a visible
result. You can stop after any mission and return later.

You hand operational responsibility to the agent. It monitors, prioritizes and follows work through
independently. These missions configure its responsibilities one by one; they are not a list of
business tasks for you to perform. You review outcomes and answer genuine decision questions.
Reality currently requires confirmation of specific business proposals.

**Steps 1–5 are enough to begin:** create a company, connect an agent, understand an order and
review your first Decision. Then add repetition, purchasing, Finance, a daily plan and optional
email. Use the same agent conversation; new conversations need the saved assignment and access to
the same company.

Reality supplies business records and tools. Your agent system coordinates work and recurring
execution. Live simulation supplies additional synthetic arrivals.

**When you pause:** Manual prompts do not keep running on their own. After daily-plan setup, pause
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
→ Orders**, find **SO-006**. The baseline has five units ordered, three shipped and two open. The
agent must read its current state; the running demo may already contain further activity.

## 4. Your agent understands its first order

**Goal:** Hand over responsibility and begin with a concrete case. Copy this prompt:

```text
You are the operational agent for my selected Reality demo company. You own monitoring,
priorities and next steps instead of waiting for assignments. Your example rhythm:
09:00 recorded cancellations and holds; 11:00 and 12:00 upcoming deliveries and
blockers; 13:00 recorded shipments; 14:00 existing returns. Use actual commitment
dates. 13:00 is an example pickup time, not evidence of a DHL handover. New cancellation
requests and returns require additional sources. Discover Reality tools and schemas.
First read SO-006 using actual IDs and explain its current state. Obtain information
yourself and ask me only unresolved questions. Invent no data or business rules.
This first routine only reads; business changes require specific Decisions and my
approval. Continue other executable work while decisions are pending.
You run a first round now, then configure repetition in your agent system if scheduled
runs have the required tools, assignment and working state. You clarify missing time
zone and working days with me, inspect existing routines and prevent overlaps.
You show the configured task, next run and how to pause it. If setup or verification
is unavailable, you explain what is missing rather than claiming active operation.
```

**Your success:** The agent explains a real order through its records. The baseline has three of
five units shipped and two open; the current read is authoritative. For connection issues, use
[your first business question](./first-question).

**You can stop here:** Pause the configured read routine in your agent system. No business change
has been executed.

## 5. Your agent prepares its first business action

**Goal:** Experience a complete loop with a small reservation.

```text
You as the agent now prepare our first business action. You read stock and our order's
open delivery commitment in Reality. You use existing tools to check whether a
reservation is permitted and look for pending proposals. Where possible, you create
a reservation proposal with actual IDs and show company, item, location, quantity,
effect and review link. You do not execute it. If unavailable, you explain the
evidenced reason and inspect at most one other open demo order. You invent neither
stock nor a permitted action.
```

Open the review link or proposal under **Decisions**. Check records and effect, then approve only
the specific change you want; otherwise reject it. Reserving does not ship goods.
[Prepare your first action](./first-action) explains the individual checks.

Then return to the agent:

```text
You as the agent now verify the reviewed proposal. You read its execution status
and affected records again in Reality. You explain what actually happened and what
remains open. For rejection, pending execution or unknown outcome, you create no
replacement proposal.
```

**Your success:** You see the difference between proposal, approval and executed effect. If stock or
permissions are missing, the evidenced blocker is your result.

**You can stop here.** Approval applies only to this proposal. The recurring read routine from step
4 still changes nothing; pause it in your agent system if needed.

## 6. Your agent discovers purchasing needs

**Goal:** A first purchasing overview without immediately ordering anything.

```text
You as the agent own purchasing checks every three hours during agreed working hours,
for example 09:00, 12:00 and 15:00. Discover schemas for item_supply_demand,
fulfillment_blockers, commitments_list, inventory_read and exceptions_list. Show
uncovered demand, evidenced receipts and overdue supplier commitments with customer
orders; movement readers provide receipt evidence. Inspect PO-001, PO-003 and PO-006
where present. An order is not a receipt; without a promised date it is not overdue.
Prioritize independently and ask me only for inputs unavailable from existing sources.
Order and send nothing yet. Further changes require specific proposals and approval;
report unchanged cases without duplicate proposals.
You run a first round now, then configure repetition in your agent system if scheduled
runs have the required tools, assignment and working state. You clarify missing time
zone and working days with me, inspect existing routines and prevent overlaps.
You show the configured task, next run and how to pause it. If setup or verification
is unavailable, you explain what is missing rather than claiming active operation.
```

**Your success:** You see a concrete need or supplier case. In current demo baselines, `PO-001` has
received two of five units and its remainder is overdue. `PO-003` has no promised date; `PO-006`
shows a receipt without an invoice. Older companies may contain different cases.

New sales orders change demand. **Live Demo does not generate new purchase orders or supplier
receipts.** If a supplier case remains unchanged, the agent can report that.

**You can stop here:** Pause the purchasing routine. Your success includes the first overview and,
where configured, the verified next run.

<details>
<summary>Optional: Walk through a replenishment order together</summary>

Select an evidenced need. Provide supplier, quantity, date and explicitly stated price and amount
values. The agent must not invent missing buying rules or supplier assignments.

```text
You as the agent prepare a purchase order for the selected need with
order_create_propose, direction purchase. You first ask me for missing required
inputs and buying rules. You use my explicitly stated values and do not recompute
missing document amounts as new authority. You show the review link and wait for
my approval before any change is executed.
```

After approval, inspect the incoming commitment. An explicitly fictional counted receipt can then be
proposed in the Sandbox with `shipment_receive_propose`, purpose `supplier_delivery`, and confirmed
separately. Stock changes only on execution. This is an exercise initiated by you. A supplier
reminder stays a draft in your agent system; a Reality Decision does not send it.

</details>

## 7. Your agent understands the financial position

**Goal:** A small Finance round with one explainable case.

```text
You as the agent own Finance checks every three hours during agreed working hours,
for example 09:00, 12:00 and 15:00, and report the day's position at 17:00.
Discover finance_balances, finance_payments, finance_credits, finance_party_balances
and exceptions_list and their schemas. Show open amounts per currency, new or
unallocated payments and credits. Explain one case with finance_settlement_context;
ask me only if uncertainty remains. Change nothing yet and create no duplicates
of live invoices or payments. Where possible, integrate this into the purchasing
round instead of starting parallel work.
You run a first round now, then configure repetition in your agent system if scheduled
runs have the required tools, assignment and working state. You clarify missing time
zone and working days with me, inspect existing routines and prevent overlaps.
You show the configured task, next run and how to pause it. If setup or verification
is unavailable, you explain what is missing rather than claiming active operation.
```

**Your success:** The agent explains a payment, partial payment, open position or credit. New
customer invoices and payments arrive with different delays; not every round has a new case to
clarify. Supplier cases such as `SINV-004` are already partly paid.

An allocation or adjustment comes afterwards as its own proposal with current context, evidenced
inputs and your approval. The agent asks when matches are ambiguous.

**Optional: your first payment preview.** First agree the date by which payment should occur:

```text
You as the agent also own a daily payment preview at 15:00. Clarify the pay_by date
or its rule with me and read payment_run_preview. Explain the selection and reasons;
post and pay nothing. Run a first preview now and add it to the existing Finance
routine only with available tool access. Show the next run and how to pause this subtask.
```

The preview pays nothing. Even an approved Reality posting does not execute a bank transfer. A
customer dunning preview through `finance_dunning_run_context` requires a suitable dunning schedule;
it sends no message.

**You can stop here:** Pause the Finance check or combined purchasing/Finance routine. Inspect the
next run before leaving it active.

## 8. Your agent takes on test customer support

**Goal:** A first support round with an explainable customer case. Email is optional.

If your agent system supports email, connect a selected test mailbox there and check reading and
reply drafts. The Reality connection grants no mailbox access. Send this yourself:

```text
Subject: Question about my order SO-006

Hello, when will my order SO-006 arrive? Has anything shipped already?
```

```text
You as the agent own test customer support: check the selected mailbox every
30 minutes during agreed working hours, for example 09:00 to 17:00. Verify email access
and tools; ask me only for missing access. Start with the test request about SO-006
and read the current order in Reality. Create a friendly evidenced reply draft and
show me the supporting records internally. Invent no delivery date and send nothing.
Check the message and existing drafts to avoid handling the same request repeatedly.
Ask me only for unresolved matches. Drafts and sending approval belong in the agent
system, not in Reality Decisions.
You run a first round now, then configure repetition in your agent system if scheduled
runs have the required tools, assignment and working state. You clarify missing time
zone and working days with me, inspect existing routines and prevent overlaps.
You show the configured task, next run and how to pause it. If setup or verification
is unavailable, you explain what is missing rather than claiming active operation.
```

**Your success:** A reply draft explaining the actual order state. Review recipient and content in
the agent system, then send it yourself or explicitly approve sending there. **This mission has no
Reality Decision for sending email.**

**You can stop here:** Pause the support routine. Recurring monitoring is active only after verified
setup with mailbox and Reality access. Without that capability, the first draft is your result.

## 9. Your agent checks how the routines work together

**Goal:** Existing tasks fit together. You do not configure a second daily plan.

```text
You as the agent review your configured routines for sales, purchasing, Finance and,
if connected, support. For each task show responsibility, time or interval, time zone,
working days, tools, next run and pausing. Distinguish active routines, manually tested
tasks and missing setup. Check gaps, duplicate work, overlaps and pending Decisions.
Verify at least one actual run and obtain missing information yourself. Propose
necessary corrections instead of creating a second daily plan. Bypass no approvals
and claim no active operation for unverified routines. Give me a short report:
What is running? What waits for me? What is still missing?
```

**Your success:** A verifiable combined plan with actual next runs. Example times are not company
settings: pickup time, time zone and working days must fit your exercise. The demo evidences no real
DHL pickup and supplies no new cancellation requests from a mailbox.

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
