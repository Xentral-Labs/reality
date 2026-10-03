# Start with an existing company

Give the agent one useful task from your current business before expanding its responsibility. A
good starting question is: **Which customer orders still need delivery, and what prevents it?**

## 1. Choose a question and its boundaries

Pick a task your team already understands and can check. Agree which source system holds the orders,
which stock and shipment records are needed, and who will review the agent's answer.

```text
Help me scope a first Reality pilot for our existing business. The task is to explain
open customer deliveries. Ask which systems hold the orders, stock and shipments,
which period and company we want to cover, and who can verify the answer. List the
records needed. Do not claim that a source is connected or change any data.
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
Using only the records held in this Reality company, explain the open delivery work
for our pilot scope. Show ordered, fulfilled and open quantities and any evidenced
blockers. Name the underlying records and the source coverage or freshness gaps.
Do not change data or fill gaps with assumptions.
```

Compare a known order with your source system. Check the delivery commitment, related movements and
available provenance in Reality. Missing or uninterpreted data must remain an explicit gap; an empty
result does not prove that all upstream work is complete.

## 5. Give the agent one bounded action

After the read agrees with the business case, choose one action, such as preparing a reservation for
eligible stock. Deliberately grant the proposal tools needed. Ask for an explanation and review
link, confirm the exact effect in Reality and read the resulting records.

Use the [proposal and verification loop](./first-action), keeping your pilot company selected. Its
worked example uses demo records; your proposal must use the actual pilot records. A proposal in
Reality does not authorize write-back to your ERP.

## 6. Turn the pilot into a repeatable task

```text
Describe our agreed open-delivery check as a repeatable task: scope, required source
records, trigger, permitted reads and proposals, decisions requiring my approval,
verification and the point where you must stop and ask for help. Do not schedule
anything or change permissions.
```

**Check:** A person can review the task and its limits. Run it again when the sources change and
check the new result. Recurring execution, source monitoring and external actions need separate
configuration and authorization. Expand one task at a time using the
[operating rhythm](/agent-playbooks/operating-rhythm).

**Other paths:** [Experience the demo](./demo-company) · [Build from scratch](./start-business).
