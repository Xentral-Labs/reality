# Start with an existing company

Give the agent one useful task from your current business before expanding its responsibility. A
good starting question is: **Which customer orders still need delivery, and what prevents it?**

## 1. Choose a question and its boundaries

Pick a task your team already understands and can check. Agree which source system holds the orders,
which stock and shipment records are needed, and who will review the agent's answer.

```text
Help me scope a read-only Reality pilot for open customer deliveries. Inspect available
records and ask which company, period and source systems we should cover and who
will verify the result. List missing order, stock and shipment data. Do not claim
unverified source connections or change any data.
```

**Check:** You have a bounded question and a list of required data, not a promise to connect every
system or automate the whole company.

## 2. Create a separate pilot company

<ProductLink>Open Reality</ProductLink>, complete account signup and email confirmation, then create
or select the company for this pilot. Keep demo records separate from the business records being
compared. Use **Start your own company** to start empty rather than selecting demo content.

## 3. Arrange the first data intake

Agree the source connection and interpretation with the person implementing the integration.
Registering a source does not connect an ERP. An integration catalog entry for Shopify, Xentral or
Odoo does not establish a working live connector.

Start with a small set of known cases: an open order, a partial delivery and a blocked order. Keep
the pilot read-only towards the upstream system. See the [pilot guide](/integrations/parallel-test)
and the [ERP integration entry](/development/connectors) for the implementation path.

## 4. Connect the agent and compare an answer

[Connect your agent](./connect-agent) to this pilot company with the reads it needs. Once the
records have arrived and been interpreted, use this prompt:

```text
Explain open deliveries in our agreed pilot scope using Reality records. Show ordered,
fulfilled and open quantities, promised dates and evidenced blockers. Prioritize urgent
cases and show supporting records, missing sources and outdated information.
Change nothing and do not replace missing data with assumptions.
```

Compare a known order with your source system. Check the delivery commitment, related movements and
available provenance in Reality. Missing or uninterpreted data must remain an explicit gap; an empty
result does not prove that all upstream work is complete.

## 5. Optional: give the agent one bounded action

After the read agrees with the business case, choose one action, such as preparing a reservation for
eligible stock. Deliberately grant the proposal tools needed. Ask for an explanation and review
link, confirm the exact effect in Reality and read the resulting records.

Use the [proposal and verification loop](./first-action), keeping your pilot company selected. Its
worked example uses demo records; your proposal must use the actual pilot records. A proposal in
Reality does not authorize write-back to your ERP.

## 6. Turn the pilot into a repeatable task

```text
Monitor open deliveries in our agreed pilot scope daily at 09:00. Use Reality records
to prioritize blockers and overdue promises. Report what changed, what needs attention
and which source data is missing or outdated. Read only; change neither business data
nor permissions and write nothing back to source systems.
Run once now. Then configure repetition in your agent system only if tools and saved
assignment and progress are available. Confirm time zone and working days; reuse existing
routines. Show the verified next run and how to pause. Report missing setup clearly.
```

**Check:** Review the task and its limits. The daily 09:00 check is an example. Monitoring is active
only after verified setup in the agent system, with source coverage and freshness still checked on
each run. Without scheduling support, repeat the read manually. External actions require separate
authorization. Expand one task at a time using the
[operating rhythm](/agent-playbooks/operating-rhythm).

**Other paths:** [Experience the demo](./demo-company) · [Build from scratch](./start-business).
