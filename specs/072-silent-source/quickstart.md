# Validation Quickstart: Silent Source Detection

## Prerequisites

- Python 3.12+ development environment
- Local PostgreSQL test service on the port used by the test configuration
- Approved Spec 072 scope decisions and its four product constants

Run the suite from `packages/reality-core`. In a git worktree the virtual environment lives
in the main checkout, so the worktree source has to take precedence:

```bash
PYTHONPATH=$PWD/src ../../.venv/bin/pytest
```

## 1. Prove the Rhythm Is Learned, Not Configured

Give a capability a history that pauses every weekend and read the queue on a Monday
morning. Nothing may appear: the weekend pause is part of what that source does. Read the
same history a week later with nothing delivered since Friday and the entry must appear,
reporting the pause it learned rather than one anybody typed in.

This is the case that decided the rule. An average gap multiplied by a factor reports a
failure every night for any source that works business hours, which is why the longest
observed pause is used instead.

## 2. Walk the Boundaries of Silence

Confirm the floor with a source that delivers every minute: twice its longest pause is
minutes, and it must still not be reported for a short interruption. Confirm the degenerate
history where every record shares one instant, so no pause was ever observed and the floor
alone decides. Confirm that a receipt ahead of the evaluation instant produces no entry
rather than a negative silence, and that receipts written out of order still yield the same
rhythm.

## 3. Stay Quiet Where Nothing Can Be Known

Create capabilities with no records, with fewer than the minimum history, and one that is
inactive. None may appear. Put a fourth capability beside them that does qualify and assert
that exactly that one is reported — an assertion that only counts an empty set proves
nothing, because an underived class produces an empty set too.

## 4. Prove Clearing, Ordering and Isolation

A new record must remove the entry on the next read with nothing persisted. Two silent
capabilities must appear longest-silent first, identically across repeated reads. One
tenant's records must never feed another tenant's rhythm, in either direction.

## 5. Prove the Catalog and the Pair

The class must carry the description, owner and clearing path that Spec 071 made mandatory,
and it must name `source_interpretation_failure` as the case where something did arrive
while that class names this one as the case where nothing did. Re-run the cross-reference
review over every class afterwards; five pairs must be mutual and only the unexplained
movement may stand alone.

## Recorded Results

| Step | Date | Result |
|---|---|---|
| 1 — learned rhythm | 2026-09-04 | Pass. A weekday history is quiet on Monday and reports after a real stoppage, with an expected pause of 72 hours. |
| 2 — boundaries of silence | 2026-09-04 | Pass. Floor, zero-pause history, future receipt and out-of-order receipts all behave as specified. |
| 3 — quiet without history | 2026-09-04 | Pass. Empty, sparse and inactive capabilities produce nothing while a qualifying one beside them is reported. |
| 4 — clearing, ordering, isolation | 2026-09-04 | Pass. |
| 5 — catalog and pair | 2026-09-04 | Pass. Five mutual pairs; only `unexplained_movement` stands alone, by decision. |

Full suite after implementation: 493 passed, 7 skipped. `apps/docs`: 37 passed, Prettier
clean.

## Findings Worth Keeping

A test that asserts an empty result proves nothing while the class it tests does not exist.
The first version of the insufficient-history story passed before the derivation was
written and would have kept passing if the derivation had silently returned nothing. It now
places a qualifying capability beside the excluded ones, so it proves exclusion rather than
absence. The clue was that it never appeared in the list of expected failures.

The risk here runs opposite to Specs 068 and 069. Those two could flood a queue and were
measured for volume before merge. This class cannot: it says nothing until a capability has
five records and has then fallen silent, so an import of historical data leaves it cold.
The danger is that it is too quiet to notice, which is why the stories carry realistic
rhythms — weekends, minutes, identical timestamps — rather than minimal fixtures.
