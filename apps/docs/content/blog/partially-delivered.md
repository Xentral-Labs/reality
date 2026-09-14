---
title: Your ERP says "partially delivered". Ask it what that means.
description:
  One status field answers four different questions at once, and keeps none of the inputs. That is
  the defect, and agents make it expensive.
date: 2026-09-04
author: Benedikt Sauter
draft: true
tags:
  - Business Reality
sidebar: false
---

# Your ERP says "partially delivered". Ask it what that means.

<PostMeta />

Open any conventional ERP and look at a sales order. Near the top there is a status field, and today
it reads _partially delivered_. Everyone in the company treats that as a fact. It is not one. It is
a summary that some code computed at some point, from inputs the system no longer keeps.

Try answering these from that single field:

- Did the customer receive goods, or did somebody click a button in the warehouse?
- Which quantity is still promised to the customer, and which is merely still typed on a line?
- If stock is held for this order, is it held because of the promise or because of the shipment?
- If the customer says tomorrow that they cancelled last week, what happens to the answer?

The field cannot answer any of them. It was never designed to. It was designed so that a human
looking at a screen could form a rough impression quickly, and for thirty years that was enough,
because the human standing in front of the screen supplied the missing context from memory.

## Four kinds of truth wearing one costume

Underneath that status there are at least four different claims, and they have different lifetimes,
different owners, and different consequences when they turn out to be wrong.

There is what an external system **said**. A shop, a marketplace, an EDI partner sent a payload. It
is a record of a statement, not a record of reality, and it can be superseded tomorrow by a newer
statement from the same sender.

There is what your company **promised**. A commitment to deliver twelve units at an agreed price. It
survives even if the source payload is later corrected, because you made it to a counterparty who
now expects it.

There is what **physically moved**. Eight units left a shelf and were handed to a carrier. This is
the only claim in the list that cannot be undone by editing a field, because it happened in the
world. Correcting it means recording another movement, not overwriting the first one.

There is what was **posted**. A revenue line, a receivable, and later a partial payment allocated
against it. Finance needs this to balance and needs it to stay balanced retroactively.

A conventional ERP collapses all four into one status string and one open-quantity column. It works
until two of the four disagree — and then nobody can reconstruct which of them moved, when, or on
whose authority. Every ERP team has spent a week of somebody's life on exactly that reconstruction.

## The reason this got urgent

For decades this was tolerable, because the consumer of the status field was a person who knew the
customer, remembered the phone call, and could tell a nonsense number from a real one.

That assumption just broke. The consumer is now increasingly an agent, and an agent reading
_partially delivered_ has no memory, no phone call, and no instinct for a nonsense number. It will
happily reserve stock against a promise that was withdrawn, chase a payment on an invoice that was
credited, or tell a customer a delivery date derived from a field that three subsystems have been
overwriting all morning.

You cannot fix this by making the agent more careful. A careful reader of an ambiguous field is
still a reader of an ambiguous field. The fix has to be in what the system stores.

## What the alternative actually looks like

Reality keeps the four claims apart and links them: **Source → Evidence → Reality**.

The source payload is stored losslessly and never edited. What it means is interpreted into evidence
— a document and its lines — and that interpretation is repeatable and replaceable. What the
business owes is a Commitment. What is physically held is a Reservation. What actually moved is a
Movement. What finance recognises is a LedgerEntry. None of these overwrite each other, and none of
them is a status string.

"Partially delivered" then stops being a stored field and becomes a derived answer, computed from
the commitment and the movements, with every input still on hand. Which means it can be _explained_
— you can ask why, and get back the specific movements and the specific commitment that produced the
number, not a guess.

The correction story changes too. Nothing is edited in place. A wrong movement is corrected by
recording the correcting movement, so the audit trail contains both what you believed and when you
stopped believing it. That is what makes a claim safe to hand to an agent: not that the agent is
trusted, but that every number it reads carries its own evidence, and every number it writes gets
proposed, approved, and verified against that same evidence.

## Where to go next

The rest of this argument is worked through in full, against one representative business month at a
fictional bicycle manufacturer, in the practical guide:

- [Foundations: from ERP documents to Business Reality](/concepts/business-reality-guide/01-from-erp-documents-to-business-reality)
- [Orders, reservations and inventory](/concepts/business-reality-guide/02-orders-stock-and-deliveries)
- [The Process Owner role](/concepts/business-reality-guide/04-working-as-process-owner)

Next in this series: what happens to all of this when the customer changes the order after it
shipped.

<Subscribe />
