# Quickstart: The Link Nothing Enforced

**Language**: English

Nine gates in `tests/test_reference_integrity.py`, two recordings in the derivation suite. No
migration.

## Story one — the map

Every nullable foreign key on the four records the queue reasons about is declared either
load-bearing or trace-only, and the set is discovered from the mapper. A migration adding one
fails the build until somebody says what it is for. A declaration for a reference that no longer
exists fails too, because a stale entry hides the next real one.

For a load-bearing reference, the classes declared to read it are exactly those whose derivations
do — walked from the derivation registry through the source. Each names how it reads it: reporting
work that was done, never looking at the record, or only naming it in evidence.

Validation lives in the loader, not only in the test, so anything reading the catalog gets the
same refusal.

**Result**: passes. The measured figures are pinned: 4 references, 16 classes reading one, 11
reasoning from one, 25 pairs — 6 crying wolf, 13 going blind, 6 tracing.

## Story two — the writers

Every construction of a document line, movement, commitment or return announcement in the source
either passes the load-bearing references for that record or is declared exempt with a reason.
Found by syntax tree, so a keyword spread over several lines still counts, and keyed by the
function that builds the record rather than the file.

Six exemptions, each with an argument: a correction's compensating movement settles no return and
fulfils no announcement, and order ingestion builds order lines, which are what a billing line
points *at*.

**Result**: passes.

## Story three — the surfaces

Every adapter of a command whose service builds one of those records can carry the references —
composed with the writer exemptions, so a movement correction is not asked to be able to claim it
settles a return. And every load-bearing reference is described in the shared input glossary, with
no exemption available, because that glossary is what the generated developer reference and the
capability guidance expose.

**Result**: passes, after fixing what it found.

## What the gates found on their first run

**MCP never named `billed_document_line_id`.** `document_create_propose` declared `lines` as
`{"type": "array", "items": {"type": "object"}}`, so the field had always passed through if sent —
and no agent had ever sent it, because nothing told an agent it exists. That is the most
transferable idea here: **a passthrough is a capability for a person and an absence for an agent.**
It is why an MCP schema may never be exempted for forwarding, and there is a test asserting exactly
that.

**The shared input glossary never described it either.** Nine classes read the reference and the
one place the command reference and the agent guidance look it up had no entry.

**The web app had no box for it.** `ManualLine` carried ten fields and not this one, so a person
recording a manual invoice in the Cockpit could not say what it bills. The API model accepted it,
the service validated it, and the only human surface had nowhere to type it. Same shape as Spec
091: the operation existed and nothing reached it.

## What the measurement changed

The recorded risk said *"absence is load bearing in three classes"*. Every number in that sentence
was wrong.

- **Four references, not three.** Discovering them from the mapper turned up
  `Commitment.document_line_id`, which eight classes conclude from through one inner join. A
  hand-written list would have been wrong on the day it was written.
- **Sixteen classes read one; eleven reason from one.** A third of the catalog.
- **Two directions, not one.** "Quietly wrong" is half the story and the less important half. Six
  pairs conclude from absence and **cry wolf** — reporting work that was done, until the queue
  stops being believed. Thirteen start from the reference and **go blind**; `billed_not_received`
  going blind means a company is billed for goods that never arrived and nothing reports it. Both
  directions are recorded: one test deletes the reference and watches ten billed pieces reported
  as unbilled, the other deletes it and watches the entry vanish.

## What this deliberately does not do

**A gate cannot make a person type.** Every path will be able to carry a reference and nobody is
forced to set one, because each of the four records legitimately exists without its link. What the
gates buy is that the next writing path and the next surface cannot silently lack the ability.
Saying that plainly is better than a gate whose name promises more than it does.

**`traces_only` is where the gate stops being mechanical.** Six pairs are declared as evidence
rather than reasoning, and only a person's reading says so — discovery cannot tell a conclusion
from a mention, because both are the same attribute access. Every such entry carries a reason a
reviewer can disagree with.

**A plain identity box is poor interaction design.** Pasting an order line id into a text field is
not what a good form does. A reference picker for document lines is a separate piece of work; the
box was chosen over continuing to have nothing.

Existing tenant rows are out of scope. This gate is about paths, not rows.
