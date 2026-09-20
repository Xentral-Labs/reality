# Exceptions: what it would take to derive by change

Spec 181 FR-002 is delivered for eleven of twelve projections. `exceptions` is the
one left, and it is left for reasons the other eleven did not have. This note states
them, names the one decision that has to be made before any code, and proposes an
order of work. It is a proposal, not a specification.

## Why it is not simply the twelfth builder

**It stores a rank, and a rank is a property of the whole list.** Each stored row
carries `position`, its place in the company's canonical order. A narrowed refresh
knows the three rows that changed; it cannot know their place among four thousand
without deriving all of them, which is the thing being avoided.

The cause is one line in `OperationalException.to_dict()`: `value.pop("sort_at")`.
The derivation orders by `(severity, class rank, sort_at, record_id)` — every part of
that key belongs to the row — but `sort_at` is dropped before the row is stored, so
the order had to be preserved as a number instead of as a key.

There is a second, quieter consequence of that today. `attention_reads._canonical`
falls back to `(severity, class rank, record_id)` for rows written without a
position, which is **not** the derivation's order: within a class, the derivation puts
the oldest first and the fallback puts the lowest record id first. Two generations of
the same projection are ordered by two different rules.

**It is the only projection still on the clock.** `TIME_SENSITIVE_PROJECTIONS` holds
`exceptions` alone. A refresh the clock triggered has no change set to narrow by, so
narrowing alone would leave the minute-by-minute full evaluation of every company in
place — which is the cost FR-004 set out to remove.

**Half of it is about finished work.** Spec 181 FR-003 already records why the working
set cannot bound it: `billed and not received`, `received and not billed`, `shipped
and not billed` judge what happened *after* a promise was fulfilled. An open-work set
is not a cheaper version of that answer, it is a different one.

## Status (2026-09-20, third update)

Narrowing landed, by class rather than by record, and the measurement chose that shape:
the cost is not spread over thirty-five classes but concentrated in one read that five of
them share. The inputs are lazy now, so a class that does not run costs nothing, and a
movement skips the five money classes and the open-items read with them — 210 ms to 70 at
200 orders.

What remains is enlarging `CLASS_DEPENDENCIES`. Every class in it is a claim with a test;
every class out of it is evaluated whatever changed. Bounding a class to named *records*
is a further step that only the record-shaped classes can take, and the cost measurement
says it is worth little until the shared reads are already skipped.

## Status (2026-09-20, second update)

The clock is done, and it was the right thing to do first. `clock_due_at` on the
projection checkpoint records the earliest moment a verdict could change with no event,
the selection compares it, and the twenty-four hour cap bounds every ageing rule this
cannot see — including the twenty-eight classes with no scenario in the measurement, which
is why the cap exists rather than a list of records. One evaluation costs 75 statements and
65–179 ms; an idle company paid 1,440 a day and now pays one.

What remains of this note is narrowing by change set, class by class, each with its own
probe.

## Status

The decision below was taken on 2026-09-20: **store the key**. Step 1 of the proposed order
is done — the row carries `sort_at`, the readers order by
`(severity, class rank, sort_at, record_id)`, and the stored `position` is gone. Steps 2 to 4
are open.

## The decision needed first

**Store the key, not the rank.** Carry `sort_at` on the stored row and let the readers
order by the derivation's own key. Then a row's place is a property of itself, a
narrowed refresh can write three rows without consulting the rest, and the two
generations stop disagreeing about order.

This is reader-visible, which is why it is a decision and not a refactor: the order
users see today comes from the builder, and afterwards it comes from the reader. The
order itself is intended to be identical — and where it differs today (a
position-less generation) it becomes *more* correct, because `sort_at` returns to the
key.

The alternative is to keep the rank and accept that `exceptions` never narrows. That
is a defensible choice — its evaluation is company-wide by construction — but then
FR-002 should say so about this projection rather than leave it open.

## What the investigation of steps 2 and 3 found (2026-09-20)

The order below was written before the classes were counted, and two of its steps are in
the wrong place.

**Bounding the shared input scope buys little.** `exceptions.py` makes 43 direct database
reads and uses the shared scope in 11 places. Several classes read the session themselves —
`credit_limit_exceeded` loads the parties with a limit, `duplicate_supplier_invoice` asks
the service layer to group a supplier's invoices — so bounding `_exception_input_scope`
would narrow a handful of classes and leave the rest reading the company. Because the
projection is published as a whole, the company is read either way.

**Narrowing here is all-or-nothing.** A refresh may only skip a class if that class is
*provably unaffected* by the change set. So the saving appears when every class in the
window either narrows or is provably unaffected — not when the first few do.

**And the "is this class record-local?" property has no universal probe.** A first attempt
measured it by adding an unrelated record and looking for changed verdicts. It reported
`credit_limit_exceeded` and `duplicate_supplier_invoice` as record-local; both are
company-wide. "Unrelated" is exactly what each class defines differently — another invoice
of the same party, another invoice under the same number, any finished promise for a
learned threshold. That property therefore belongs with each class's own narrowing, tested
per class with its own probe, and not in a table filled in advance.

**What does have a universal probe is the clock**: same company, derived twice, four
hundred days apart. `tests/operational_exceptions/test_class_clock.py` measures it —
three classes read the clock today (`overdue_outgoing_customer_commitment`,
`overdue_incoming_supplier_commitment`, `overdue_receivable`) — and pins the twenty-eight
classes the fixture does not bring about at all, so that gap is visible and shrinks.

**Corrected order:** the clock first (it is the standing cost, and its list is now
measured), then per-class narrowing one class at a time with its own probe, and the bounded
input scope only where a narrowed class actually reads through it.

## Proposed order of work, if the decision is "store the key"

1. **Carry `sort_at`, drop `position`.** One field added to the stored row, one
   removed; `attention_reads._canonical` and `read_models`' order clause sort by
   `(severity, class rank, sort_at, record_id)`. A test holds the stored order against
   the derivation's own, which is the thing that is currently only approximately true.
2. **Let the input scope take a record set.** `_exception_input_scope` loads the
   company once and shares it across the classes — that is what made the derivation
   two seconds rather than 229. Narrowing needs the same scope bounded to named
   records, so that one read per company becomes one read per change set.
3. **Narrow the record-shaped classes.** The commitment and document classes name one
   record each; `covers` is `exc__{class}__{record}` over the classes that could name
   the records in the change set — enumerable, the same shape as the blockers' reason
   list. Every class that declines is visible in the narrowing report.
4. **Take the clock apart.** Classes that compare against a *stated* date are
   selectable by indexed date, which is what FR-002 asks for. Classes that compare
   against a threshold learned from finished promises move for every record at once;
   they need either a coarser cadence of their own or an explicit trigger when the
   threshold moves. Both are cheaper than evaluating every company every minute, and
   which one belongs where is a question for the measurement, not for this note.

## What this note does not claim

No measurement here. The cost of the minute-by-minute evaluation at the sizes SC-002
and SC-003 name has never been measured, because neither fixture exists yet. The
order above is worth doing on the strength of the structure alone — a rank cannot be
narrowed — but the *size* of the win is unmeasured, and step 4 should not be designed
in detail before it is.
