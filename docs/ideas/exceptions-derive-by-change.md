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
