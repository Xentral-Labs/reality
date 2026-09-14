# Working as a Process Owner

[Back to the guide overview](../business-reality-guide)

## “Can Huber's order ship today?” {#process-owner}

Return to the point where LightWorks has delivered the first ten lamps. The eight opening-stock
lamps are allocated to Huber; the ten new arrivals are not. Acme still owes Huber all 30 lamps.

An agent is asked whether a partial shipment of 18 can leave today. An answer needs more than the
order header. It must separate four questions:

| Check                       | Result at this point                                                     |
| --------------------------- | ------------------------------------------------------------------------ |
| What is still promised?     | Thirty lamps remain open.                                                |
| What is physically present? | Eighteen lamps are in Augsburg.                                          |
| What is allocated to Huber? | Eight; ten still need allocation for the intended partial shipment.      |
| What might block execution? | Current holds, permissions and other execution conditions need checking. |

The agent can explain the missing allocation and propose reserving the ten available lamps. It
cannot yet claim a completed reservation or shipment. A proposal does not change stock.

### What you check

Compare the preview with the intent. Is this Huber's correct delivery promise? Is it the right item,
Augsburg and ten units? Are the goods still available? Is there a hold?

After authorised confirmation, the application service executes the reservation and rechecks the
current conditions. Only the subsequent read establishes that 18 lamps are now allocated to Huber.
That still proves no shipment. The physical warehouse event and its recording happen later.

## The Process Owner Role

The Process Owner is the accountable business person who decides which information supports a
decision and who may perform which action. Depending on the case, that responsibility can sit in
consulting, order handling, warehouse work, purchasing, finance or integration. It need not be a new
job title.

Your ERP experience matters: you understand shipping readiness, holds, partial invoices and
postings. You also check whether an agent uses the appropriate records for its answer and respects
the boundary between reading, proposing and executing.

### The governed operating loop

1. **Clarify the question:** Is it about readiness, an actual shipment or an outstanding payment?
2. **Read the basis:** Check the promise, allocation, movement or posting and its evidence.
3. **Propose a change:** Inspect the tool, affected records and exact effect in the preview.
4. **Decide and execute:** Authorised confirmation applies to that exact proposal.
5. **Check the result:** Read the current operational records and work lists again.

A read-only question needs no approval. A mutating Chat or MCP action first prepares a **change
proposal (ChangeProposal)**. Successful preparation proves only that the proposal exists, not that
its business effect occurred.

### Who confirms, and what may be claimed?

An authorised person confirms in the Chat flow shown here. An agent must not infer approval from
what it thinks the conversation intended. Confirmation applies to the specific preview; different
arguments are not silently included.

Any explicitly delegated decision authority must fit the execution path and case class actually
supported. It is not general self-approval for Chat or MCP proposals. Automatic payment allocation
in chapter 3 follows its own limited intake rules; it grants an agent no extra rights. Current tool
permissions and server checks govern the action, not a sentence in a prompt.

An agent may say “18 reserved” after checking active reservations. “18 shipped” requires the
corresponding recorded shipment movements. “Arrived at Huber” needs suitable delivery evidence in
turn. The same order supports different statements with different limits.

## Exceptions, Approvals and Responsibility {#exceptions-and-approvals}

A work list shows what deserves attention. Reality calls an operational finding derived from current
data an **Exception**. For example, open delivery demand without sufficient allocation can appear at
risk. The specific condition is explained and documented in the
[exception catalog](../../tool-usage/exceptions).

| Entry type       | Its question                                  | How it is resolved                                                         |
| ---------------- | --------------------------------------------- | -------------------------------------------------------------------------- |
| Exception        | Which recorded condition needs investigation? | Normal business action addresses the cause; the condition no longer holds. |
| Pending approval | Should this exact change be executed?         | An authorised person confirms or rejects the proposal.                     |
| Decision history | What was decided and executed?                | The audit trail remains; execution and outcome must be distinguishable.    |

An exception is not a ticket you can close independently of its cause. A proposal is not proof that
a problem has been resolved. Either can exist without the other.

After the ten new lamps are reserved for Huber, twelve still remain unreserved. A warning about that
remaining gap does not disappear just because you approved the first reservation. Read the
quantities and the exact derivation condition again. When the next twelve arrive and are allocated,
that allocation gap can be closed.

## Decision guide for daily work {#decision-guide}

When a case changes, first identify which business statement is affected:

| Case                            | Appropriate operation                                      | What does not happen automatically |
| ------------------------------- | ---------------------------------------------------------- | ---------------------------------- |
| Customer cancels open delivery  | Cancel the delivery promise and release active allocations | No physical goods issue            |
| Goods come back                 | Record actual return receipt                               | No financial credit note           |
| A recorded receipt was wrong    | Record inverse and, where needed, replacement movements    | No deletion of the original record |
| Customer receives a credit note | Post the financial credit and apply it where appropriate   | No return transport of goods       |

A stock count difference also differs from a recording error. For a difference observed today,
record that difference. If a particular historical movement was wrong, correct that recording. Equal
final stock can have different explanations.

<details>
<summary>Technical detail: shared tools and audit trail</summary>

Web, CLI, API, MCP and Chat use the same application services. Agents do not write directly to the
database or introduce independent inventory or posting rules. Services enforce tenant scope,
permissions, relationships and current execution conditions.

A ChangeProposal holds the tool, normalised arguments and server-generated preview. Rejection does
not execute the proposed effect. Confirmation and execution are traceable; after errors or an
unclear result, the actual effect must be checked. A Reality change proves no automatic change in an
ERP or payment provider.

Find tools and their assertion limits in [Tool Usage](../../tool-usage/#choosing-a-tool). The
[Chat contract](https://github.com/Xentral-Labs/reality/blob/main/docs/features/chat.md) and the
respective tool and finance contracts define the binding details.

</details>

### Check your understanding

`reservation_propose` returns successfully. An exception remains visible beside it. Has the
allocation gap been resolved?

<details>
<summary>Show answer</summary>

No. Initially there is only a proposal. Authorised confirmation, successful execution and a fresh
quantity check establish an actual allocation. Whether the exception disappears depends on its
complete condition.

</details>

### Learning outcome

You can now distinguish what an agent read, proposed and actually changed. You assess its answer
against evidence and results, not just whether it sounds plausible.

Next: [One Order End to End](./05-one-order-end-to-end).
