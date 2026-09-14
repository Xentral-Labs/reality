# Quickstart: A Return Is Not Finished When It Arrives

**Language**: English

Two independent acceptance stories, run against PostgreSQL as part of `tests/test_returns.py`
and `tests/operational_exceptions/test_derivation.py`.

## Story 1 — Say what happened to the goods

Record a return of six into the returns area. Move four back to the shelf naming that return
and the link is stored; write off the other two and the return is fully settled by two
movements of different kinds. Nothing else needs to say what happened, because each movement
already is what happened.

A movement naming a shipment rather than a return is refused. So is one naming another
tenant's return, one concerning a different item, and one that does not take the goods out of
the place they came back to. Settling exactly what came back is accepted; one more is refused.
A settlement recorded as happening before the return is accepted, because movement instants
are caller-supplied everywhere in this product and nothing else polices their order.

**Result**: passes.

## Story 2 — See the returns nobody dealt with

Give a company six returns it settled within two days, then leave one of six sitting for
sixty. One entry with six outstanding, sixty days standing, against a fortnight. Settle four
and it reports two. Settle the rest and it clears.

A return two days old says nothing. A company with only four settled returns is not judged at
all. Voiding a settlement puts the goods back on the list — a settlement recorded in error
settled nothing — and voiding the return itself removes it entirely, because nothing came back.

**Result**: passes.

## What the stories taught

**The cheap version was specified and thrown away, which was the point of specifying it.**
Reading what is left standing in the returns location needs no schema and cannot work: five
back and five out later says nothing about whether those were the same five. Writing that
down as the problem statement is what made the column arguable rather than assumed. A feature
whose no-schema alternative has not been written out is a feature whose schema has not been
justified.

**The outcome did not need a field.** Restocked, scrapped, sent back to the supplier — the
obvious design is an enum on the return. It would be a second authority for something the
settling movement already states, and the two could disagree. What happened to the goods is
what the movement is.

**One physical check does the work of a workflow.** Requiring that a settlement leave the
location the goods came back to is the only check available, and it stops the link from
meaning nothing. It also decides how a two-step returns process is recorded — a business that
inspects elsewhere first will see its transfer counted as the settlement — and that is written
into the non-goals rather than discovered later.

**Absence is now load bearing in three classes.** This concludes from a missing settlement
exactly as Spec 076 concludes from a missing bill and Spec 079 from a missing credit. Each
rests on the contract that every settling movement sets its reference, and nothing enforces
it. That is worth watching: the day a path creates settlements without the link, three classes
go quietly wrong at once.

**The learned rule now has four users and its constants are still unmeasured.** Reusing Spec
080's helper cost nothing and made the same untested multiple and floors govern four classes.
If those numbers are wrong, they are now wrong in four places.
