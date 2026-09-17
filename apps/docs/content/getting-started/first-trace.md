# Trace Your First Result

A useful result is not only visible; it is explainable. Start from an operational answer and move
backward through the shortest true links.

Start in **Business Facts** with an individual record, follow its relationships and timeline in
**Business Graph**, and use **Tools** for relevant queries, calculations or confirmed actions. The
three areas work with the same business reality.

## 1. Start with an operational question

Choose a Commitment, Reservation, Movement, Fact, or LedgerEntry that affects today's work. Ask:

- What requires attention?
- What is the current operational or financial position?
- What changed?
- Which action is available?

## 2. Inspect the Reality record

Open Inspect from the page, table, Activity entry, or Ask Reality answer. Confirm the tenant,
business time, quantity or amount, type, state, and direct relationships.

In the [lamp example](./index), 10 promised minus 4 shipped leaves 6 open; 2 are reserved. Check
payment separately: LedgerEntry records the posting; SettlementAllocation assigns the payment to the
invoice. Paid does not mean delivered.

## 3. Follow evidence

When a Document or DocumentLine supports the record, inspect it as evidence—not as the owner of
fulfilment, reservation, inventory, or payment state. The evidence should explain what Reality
observed without becoming a competing operational state machine.

## 4. Reach the source

Open the SourceRecord and its original payload. The payload is immutable and lossless. A changed
upstream record creates another version or event rather than rewriting history.

Not every manually created Reality record has an external source. Inspect its actual provenance. A
new source version does not prove the corresponding Reality has already been updated.

## 5. Explain the result

You should now be able to state the answer, the Reality record that owns it, the evidence that
supports it, and the source payload from which it came. If expected evidence is missing, investigate
the missing evidence rather than filling the gap with an assumption.

> **Normative invariant:** Human order, invoice, shipment, and payment numbers help people search.
> They are never identity; opaque IDs and tenant-scoped foreign keys maintain identity and
> relationships.
