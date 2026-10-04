# Build a company from scratch

Start with an empty company and let your agent help set up a small, coherent business. Your first
result is an order you can inspect, not just a list of newly created master data.

Describe your own business and supply its actual names and stated values. To practice, choose an
**empty Sandbox** and explicitly provide fictional values for the exercise.

## 1. Create the empty company

<ProductLink>Open Reality</ProductLink>, create an account, confirm your email and sign in. Enter
your company name, select **Start your own company** and confirm **Create company**. Existing users
can create it through **Companies**. The creation service also records the company's own business
partner in an ordinary business company.

For an exercise, select **Create an empty Sandbox**. Keep that Sandbox selected throughout the
exercise. The agent should inspect which setup records and actions are available there.

## 2. Connect your agent

Follow [Connect your agent](./connect-agent), or use configured Reality **Chat**. Authorize the
reads and proposal tools needed for master data and order creation. Registration and company
creation happen in the browser; the agent works inside the company you authorized.

## 3. Tell the agent what your business does

```text
Help me set up a small business in this selected Reality company. Read existing setup
records and ask what we sell, which units and currency we use, and which customer
and warehouse we need for a first order. Distinguish existing records from missing
information. Invent no stock, prices or business activity. Do not prepare changes yet.
```

**Check:** The agent distinguishes existing records from missing setup and asks for the actual
values it needs. A company description alone creates no business records.

## 4. Prepare the minimum master data

Have your business values ready; the agent asks for missing inputs:

```text
Prepare separate proposals for the missing item, customer, warehouse and company
business partner. Check existing records first to avoid duplicates. Ask for required
names, item codes, units and other missing values. Use only the information I provide.
Show each proposal's effect and review link. Execute nothing without my approval.
```

Review and confirm the proposals in Reality. Ask the agent to read the created records and their IDs
before continuing. Missing permissions or unavailable actions are a reason to stop that step and
explain what is needed. See the [master-data playbook](/agent-playbooks/master-data-and-sources).

## 5. Record the first order

Use a real agreement in your own company. In a Sandbox, explicitly provide fictional order values
for the exercise, including prices and line and order amounts:

```text
Prepare our first customer order as a proposal. Ask for the customer, item, quantity,
warehouse, agreed date, required order reference and explicitly stated prices and
line and order amounts. Resolve actual record IDs and preserve stated amounts; do not
calculate missing values. Show the effect and review link. Do not execute the proposal
or record goods movements.
```

Review the order, confirm it and inspect its recorded result. An order records a delivery promise;
it does not establish physical stock. Record goods only from a stated opening count or an actual
receipt. If no stock is held, the first order may correctly show an uncovered demand.

## 6. Give the agent its first operating task

```text
Monitor our open orders daily at 09:00. Explain delivery promises, stock, reservations,
open quantities and blockers using Reality records. Prioritize the next steps and ask
only for information you cannot obtain yourself. Invent no data or rules. Read only;
business changes need specific proposals and my approval.
Run once now. Then configure repetition in your agent system only if tools and saved
assignment and progress are available. Confirm time zone and working days; reuse existing
routines. Show the verified next run and how to pause. Report missing setup clearly.
```

**Check:** You can follow the order into its delivery commitment and see what is still needed. When
an eligible action is available, follow the [proposal and verification loop](./first-action) in the
company you intentionally selected; the generic example there uses a demo Sandbox.

Extend this task with the [operating rhythm](/agent-playbooks/operating-rhythm). The daily 09:00
check is an example, not a company setting. Recurring execution is active only after verified setup
in your agent system; without scheduling support, repeat the read manually.

**Other paths:** [Experience the demo](./demo-company) ·
[Start with an existing company](./existing-business).
