# Quickstart: An Operation Nobody Declared

**Language**: English

Two gate tests and one declaration test, in `tests/test_application_catalog.py` beside the
isolation gate they mirror.

## The gate, run before anything was declared

Written first, on purpose. A completeness gate that has never failed is not evidence of
completeness. Its first run named fourteen:

```
These mutating services are reachable from a surface and are neither declared as
commands nor explained: ['add_chat_assistant_message', 'create_chat_session',
'create_items', 'create_locations', 'create_parties', 'delete_chat_session',
'process_pending_import_jobs', 'release_reservation', 'restore_chat_session',
'send_chat_message', 'update_items', 'update_locations', 'update_parties',
'update_party_group']
```

## Eight of them were commands all along

**Releasing a reservation** is the one worth naming. It has had the `reservation_release` agent
tool since reservations existed and has never been in the catalog — an agent could do it and the
catalog said the product could not. Declaring it turned up a second thing: the release tool was
mapped onto the *reserve* command, because there was no release command to own it. It has its own
owner now.

**Updating a pricing group** was missing while creating one was a command.

**Six bulk master-data operations** are now related services of the single-record commands they
belong to, the way `update_payment_term` already sits beside `create_payment_term`.

None of the eight changes behaviour. They became describable, not new.

## Six of them are not commands, and say why

Five are chat session handling and one is the import worker step. Each is one line with a reason,
because that is a claim somebody can disagree with — and one line in a reviewed file is the whole
difference between this and the absence that produced spec 091.

## The gate fails in both directions

An undeclared operation fails it. So does an exemption whose service is no longer a reachable
mutation, an exemption with an empty reason, and a service that is both declared and exempt.

That last direction matters most: a stale exemption is how a list like this rots. The operation
it named goes away, the entry stays, and the next operation with that name inherits a silence
nobody chose.

**Result**: all three tests pass, for the right reason.

## What the story taught

**Three populations were measured before one was chosen.** Gating every mutation gives 28,
mostly exemptions reading "this is internal" — `post_ledger`, `emit_business_event` — that would
bury the six that say something. Gating everything any surface touches adds fourteen reads.
Gating HTTP alone gives 17 and misses the agent tools, where the most telling omission lived. The
numbers are in the plan rather than an assurance that the choice was careful.

**The gate composes two facts that are already gated**, so it introduces no third list of what
exists. That matters more than it sounds: a hand-maintained list falling behind is precisely the
failure being fixed, and a gate that needed its own list would have the same disease.

**An exemption list is an obvious way to silence a gate, and nothing can fully prevent that.**
A reason is required and a stale entry fails the build; neither stops somebody writing "not a
command" and moving on. Saying so plainly is better than implying the gate is airtight.

**The drift gates that already existed did the rest.** Declaring one command broke the agent
coverage map, then the tool mapping (the release tool had a duplicate owner), then two parameter
descriptions, then a count. None of it was subtle; all of it would have been easy to forget.
