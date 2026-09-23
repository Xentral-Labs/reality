# Summary

[Back to the guide overview](../business-reality-guide)

## A shared business journal

Think of Reality as a shared business journal that grows with your company. Original inputs,
recorded documents and operational entries remain linked. You can inspect what was agreed,
allocated, moved or posted and the information supporting those statements.

People, agents and workflows work from this shared state. With appropriate permissions, they read it
through Reality tools, decide on the next step and record its result through those tools. The next
person or process can build on that work.

**Read → understand → decide → act through a tool → check the result.**

The journal grows with each order, allocation, delivery and payment. A list presents the current
position; the linked records explain how it arose.

## A few core concepts with distinct jobs

| Record                      | What to remember                                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------- |
| **SourceRecord**            | “This is the original input we are referring to.”                                            |
| **Document / DocumentLine** | “We recorded this order or invoice and its lines.”                                           |
| **Commitment**              | “We should deliver this quantity to the customer” or “the supplier should deliver it to us”. |
| **Reservation**             | “This existing stock is allocated to this delivery promise.”                                 |
| **Movement**                | “We recorded this actual goods receipt or issue.”                                            |
| **LedgerEntry**             | “We posted this financial event.”                                                            |
| **Fact**                    | “A source stated this additional supported observation about an existing record.”            |

Records do more than sit next to one another in time. They refer to one another: the reservation
belongs to the delivery promise, and the promise to the relevant order. A payment has its own
posting; a **SettlementAllocation** applies it to an invoice. Those relationships turn a sequence of
entries into an explainable business case.

## A short strip of Northstar's business

```text
Northstar orders 30 lamps
  → Input and order are recorded; the delivery promise is created.

Eight lamps are set aside for Northstar
  → A reservation is recorded. Nothing has shipped yet.

Northstar writes: “Use the side entrance”
  → The source is preserved; a supported Fact adds context to the promise.

Acme ships goods and records the shipment
  → A goods movement is created; matching reservations are consumed.

Someone asks: “What do we still need to deliver?”
  → Reality reads the promise and recorded shipments to calculate the open quantity.
```

Whether the next question comes from an employee, workflow or agent does not change its business
basis. All use shared tools and rules. New external information must first be recorded traceably
before it can serve as supported evidence. An agent needs the relevant records for its question, not
the entire database.

## Important information gets the appropriate home

When an additional order field matters to you, start with its meaning. Northstar's delivery
instruction can become a Fact on the promise because a suitable predicate supports that observation.
An unused source field initially remains preserved in the original input.

A new operational delivery date, reservation or payment settlement belongs in the respective
purpose-built record. Facts add context; they are not a second home for stock or delivery state
already held elsewhere. If a needed meaning is missing, describe the gap under Open questions and
choose the appropriate extension path.

## History remains explainable

The journal is a mental picture: Reality is not one endless table, and not every record is
immutable. A reservation can change from active to consumed. Original SourceRecord records remain
unchanged; wrong warehouse movements and postings are corrected with traceable inverse and, where
needed, replacement entries. Earlier statements do not simply disappear.

The rule is therefore not “everyone may only append to a table”. It is: **Business operations use
the designated Reality tools and retain their audit trail.** Permissions and required confirmations
also apply to agents and workflows. History explains recorded events; it does not promise a full
reconstruction of every past system state.

## The core idea

You build your business on shared, traceable business records. People, agents and workflows can
understand the situation, decide their next step and continue through the same rules. The resulting
entries become the basis for the next question. **Reality holds that shared foundation together.**

To apply it: [Tool Usage](../../tool-usage/). For reference: [Table map](../../reference/table-map).
Return to [Facts and Open Questions](./06-facts-and-open-questions).

[Explore the building blocks, their fields and actions](/tool-usage/#model:commitment).
