# Prepare your first action

You have [read an order and its position](./first-question). Now let the agent prepare a small
business change: reserve available stock for an outstanding delivery commitment.

Keep your **demo Sandbox** selected. For an external agent, explicitly authorize the required
proposal tools first. The demo uses the same permissions and confirmation boundary as other
companies; a read-only connection cannot prepare a mutation.

## 1. Ask for a proposal

```text
Stay with the order we just examined. Check whether stock can be reserved for its
open delivery commitment. If there is an eligible quantity and location, prepare a
reservation proposal using the actual record IDs. Explain the quantity, location and
effect on availability, and give me the Reality review link. Do not execute it.
If the action is unavailable or the records are insufficient, explain why and stop.
```

**You should see:** Either a proposal for a concrete reservation or an explanation of why the action
cannot be prepared. A proposal is not an executed reservation. Do not assume that every demo order
has suitable stock or that every Sandbox action is permitted.

## 2. Review and confirm in Reality

Open the proposal's review link. Check the company, delivery commitment, item, location and
quantity. Read the proposed effect. Confirm only if that is the change you want; otherwise reject
it.

A reservation allocates stock to a commitment. It does not ship goods or change physical stock. Your
confirmation applies to this proposal, not to future actions the agent might suggest.

## 3. Verify what happened

After execution, return to the same conversation:

```text
Read the proposal execution status and the order's current reservations and stock
availability. Tell me whether the reservation was actually recorded, what changed
and what remains open. Show the underlying records. Do not make further changes.
```

**You should see:** The execution result and current records. The delivery remains open until goods
are actually shipped. If execution is still running or its outcome is unknown, inspect its status
before submitting another proposal.

You have now followed the operating loop: **read → propose → review and confirm → verify**.

Continue with [Sales and fulfilment](/agent-playbooks/order-to-cash-fulfilment) for more operational
questions, or [play a storyline](/storylines/) to follow a complete guided process.
