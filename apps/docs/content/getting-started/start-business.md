# Build a company from scratch

Start with an empty company and let your agent help set up a small, coherent business. Your first
result is an order you can inspect, not just a list of newly created master data.

The example below describes a small desk-lamp business. Use your actual names and stated values in
your own company. To practice with the example data, choose an **empty Sandbox** instead.

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
I am setting up a small desk-lamp business in this Reality company. We sell stocked
items in pieces (pcs), using EUR. Read the setup records already held. Tell me which
company partner, item, customer and warehouse records we need for a first customer
order. Ask for missing information. Do not invent stock, prices or business activity,
and do not prepare changes yet.
```

**Check:** The agent distinguishes existing records from missing setup and asks for the actual
values it needs. A company description alone creates no business records.

## 4. Prepare the minimum master data

For the exercise, use these explicitly stated example values:

```text
First check whether these records already exist. Prepare separate creation proposals
for missing records: item START-LAMP, name Desk lamp, stock unit pcs, type stocked;
customer Example Customer, role customer; location Main Warehouse, type warehouse.
Resolve the company's own business partner from existing records. If it is missing,
ask me for the exact name before proposing it. Show each review link and its effect.
Do not execute any proposal or create duplicates.
```

Review and confirm the proposals in Reality. Ask the agent to read the created records and their IDs
before continuing. Missing permissions or unavailable actions are a reason to stop that step and
explain what is needed. See the [master-data playbook](/agent-playbooks/master-data-and-sources).

## 5. Record the first order

Use a real agreement in your own company. In the Sandbox exercise, explicitly state this fictional
agreement instead:

```text
For this exercise, Example Customer has ordered 5 pcs of START-LAMP. The stated unit
price is EUR 20 and the stated line gross amount is EUR 100. The stated gross order amount is also EUR 100. Prepare a sales-order
proposal numbered START-SO-001, using Main Warehouse and the actual company, customer,
item and location IDs. Ask for any remaining required inputs. Keep the amounts as
stated. Show the review link. Do not execute it or record a stock movement.
```

Review the order, confirm it and inspect its recorded result. An order records a delivery promise;
it does not establish physical stock. Record goods only from a stated opening count or an actual
receipt. If no stock is held, the first order may correctly show an uncovered demand.

## 6. Give the agent its first operating task

```text
Read our first order and explain its delivery promise, stock, reservations and open
quantity. Tell me the next action we can take, what evidence is needed and which
decision belongs to me. Do not change data. Show the records supporting your answer.
```

**Check:** You can follow the order into its delivery commitment and see what is still needed. When
an eligible action is available, follow the [proposal and verification loop](./first-action) in the
company you intentionally selected; the generic example there uses a demo Sandbox.

Repeat this task as orders arrive, then extend it with the
[operating rhythm](/agent-playbooks/operating-rhythm). Recurring agent execution is configured
separately; the prompt itself does not run tomorrow.

**Other paths:** [Experience the demo](./demo-company) ·
[Start with an existing company](./existing-business).
