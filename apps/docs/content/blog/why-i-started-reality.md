---
title: Why I started Reality
description:
  Seven hundred tables, and I could never say where a number came from. Why I build this for myself,
  why it is open, and why you should give it three weeks.
date: 2026-09-04
author: Benedikt Sauter
order: 1
tags:
  - Founder note
sidebar: false
---

# Why I started Reality

<PostMeta />

I spent years building ERP on relational databases. By the time I stopped counting, the schema I
lived in had passed seven hundred tables — every one added by someone solving a real problem under a
real deadline. That is how schemas grow.

What I could never do was say where a number came from. Not for lack of logs — we had change logs,
and they tell you that a field changed: who, when, from what to what. What they never tell you is
what the change meant. A quantity went from twelve to eight at 14:03; was that a cancellation, a
partial delivery, a corrected typo, or a rounding fix? Answering that meant correlating three logs
and reasoning backwards, and two careful people could reach different conclusions. The history was
always the field's history, never the promise's.

Then I looked at what it takes to let an agent operate a company, and something reordered itself in
my head. For as long as I have done this work, ERP has been an instrument panel for people, and
whoever read a dial supplied everything it left out: the customer, the phone call, the instinct for
a number that cannot be right.

An agent supplies nothing.

Designing for a reader with no memory and no instinct changes what the system has to store. And this
is the part I still find hard to believe: stop storing conclusions, store the claims instead, and
the business truth fits in about a dozen tables. [That is its own post](/blog/eleven-tables) — but
it is why I could not let this go.

So I started Reality, and I started it for myself. I cannot think clearly about this without
building it. I wanted to know whether a company can genuinely run on evidenced claims instead of
stored statuses, and the only way I know to find out is to write it and see what breaks.

It is open because that is the useful form for it: not a product to buy, but a core to read, run,
extend and argue with. Take it apart, and tell me where I am wrong — that would be the most useful
thing you could do with it.

## One warning, and I mean it

Give yourself time.

When I first understood object orientation it did not click in an afternoon. I read about it, I was
sure I had it, and then wrote procedural code with classes around it for weeks without noticing.
Knowing an abstract model is not the same as thinking in it.

Same shape here. You will read this, it will sound reasonable, and then you will sit down to model
something and catch yourself reaching for a status field. That reflex is thirty years deep.

So plan for two to three weeks, not of study but of coming back to it. The moment it lands is not
when you finish reading. It is when you stop looking for the status field.

## Where to start

- [Foundations: from ERP documents to Business Reality](/concepts/business-reality-guide/01-from-erp-documents-to-business-reality)
- [The Process Owner role](/concepts/business-reality-guide/04-working-as-process-owner)

Next in this series: [the eleven tables](/blog/eleven-tables), and what is deliberately missing from
them.

<Subscribe />
