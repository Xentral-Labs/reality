---
title: Eleven tables
description:
  Eleven kinds of thing that can be true about a business, answering four questions. And four
  answers that are deliberately not among them.
date: 2026-09-04
author: Benedikt Sauter
order: 2
tags:
  - Business Reality
sidebar: false
---

# Eleven tables

<PostMeta />

The model has eleven kinds of claim. Not eleven tables in a database — eleven kinds of thing that
can be true about a business.

They exist because a business has to answer four different questions, and mixing the answers is what
makes a conventional schema grow without limit. One claim, one question.

## What did somebody say?

- `source_record` — the payload an external system sent. Kept verbatim, never edited. Not yet truth
  about your business: the record that somebody said something.

## What did we understand it to mean?

- `document` and `document_line` — your reading of that payload. An order for twelve wheels.
  Repeatable: read it again later and you get a new interpretation, not a mutated old one.

## What is true in the business?

- `commitment` — what you promised. Twelve wheels at the agreed price. Yours now, not the sender's:
  correct the payload tomorrow and the promise stands, because a customer expects it.
- `reservation` — what is held against that promise. Eight on the shelf. Held is not shipped and not
  promised; it is a third thing, and it can be released.
- `movement` — what physically moved. Eight left the shelf. The only claim that happened in the
  world, so no edited field undoes it. You correct it by recording another movement.
- `ledger_entry` — what finance recognised. Rows that balance, and keep balancing retroactively.
- `settlement_allocation` — which payment settled which receivable, and how much. Not a paid flag:
  one payment can settle several invoices, one invoice can take several payments.
- `fact` — an observed attribute no other kind of claim owns. That this order ships priority.

## What happened, and what follows from it?

- `business_event` — that something occurred, and when.
- `projection_row` — an answer derived from everything above. Everything you read on a screen is
  one.

## One order, start to finish

Twelve wheels ordered, eight shipped, part of the invoice paid. Nothing overwrites anything.

| What happens                  | What gets written           |
| ----------------------------- | --------------------------- |
| The shop sends the order      | `source_record`             |
| We read it as an order for 12 | `document`, `document_line` |
| We promise 12                 | `commitment`                |
| The warehouse holds 8         | `reservation`               |
| 8 leave the shelf             | `movement`                  |
| We invoice the 8              | `ledger_entry`              |
| The customer pays part of it  | `settlement_allocation`     |
| "How much is still open?"     | `projection_row`            |

The last row is the point. "Four still open" is not stored anywhere. It is the commitment of twelve
compared with the movement of eight, computed when asked, with both inputs still on hand.

The guide walks the same order through a full business month, including a shortage, a partial goods
receipt and a final delivery:
[Orders, Reservations and Inventory](/concepts/business-reality-guide/02-orders-stock-and-deliveries).

## The four answers that are not in the list

No order status. No open quantity. No stock balance. No paid flag.

Each of those is a conclusion, not a claim. "Partially delivered" is the commitment compared with
the movements. Open quantity is that same comparison as a number. Stock is the sum of movements at a
location. Paid is the receivable compared with its allocations.

Store them and you own four copies of the truth that are free to disagree. Derive them and the
question "where did this number come from" answers itself: from those inputs, which are still there.

## Why they stay apart

Because they have different lifetimes and different owners. A payload can be superseded by whoever
sent it. A promise outlives the payload. A movement outlives everything, because it happened.

Collapse any two of them and you lose a question you will need to answer.

## Where to look

- [The data model](/concepts/business-reality-guide/01-from-erp-documents-to-business-reality#data-model)
  — each kind of claim and what it is responsible for
- [The Tool Usage reference](/tool-usage/) — generated from the running code, including the detail
  and infrastructure that sits around these eleven

Next in this series: what your ERP actually means when it says "partially delivered".

<Subscribe />
