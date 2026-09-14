# Quickstart: An Invoice Somebody Can Actually Book

**Language**: English

Three acceptance stories, run against PostgreSQL as part of `tests/test_master_data_api.py` and
`tests/test_application_tools.py`.

## Story one — book a sales invoice

Record a 1,000 sales invoice through the API. Ask what it owes and the service refuses: nothing
in the ledger answers for it yet, because recording is not booking. Book it through the API and
it owes 1,000.

Booking it twice is refused. So is a supplier invoice through the sales operation, an unknown
document, and a document belonging to another tenant. Then a credit note is recorded, booked and
netted against it, and what is owed falls to 850 — through the settlement relation that already
existed and had nothing to settle against.

**Result**: passes.

## Story two — book a supplier invoice

The same on the buying side. The positive control for the type guard is worth naming: a sales
invoice is refused by the supplier operation and accepted by its own, on the next line.

**Result**: passes.

## Story three — the claim the whole specification rests on

Record a sales invoice and a supplier invoice through the API, both under a payment term granting
two per cent within ten days. Read the queue: **neither `overdue_receivable` nor
`purchase_discount_available` appears.** That was the state of every tenant that had never run
the demo.

Book both through the API. Read the queue again: both appear, on the right documents.

**Result**: passes. Two of the five conditions driven end to end through the API alone.

## And an agent can now do both

`document_create` records, `sales_invoice_post` books, both as confirmation-required proposals
like every other mutation. Before this, an agent could create an order and nothing else on this
path: recording a document was HTTP-only and booking an invoice was reachable from nowhere.

A second test diffs the invoice against the credit note in the three places a drift would show —
the agent tools, the MCP proposal schemas and the command catalog — because the two documents
drifted apart precisely because nobody was comparing them.

## What the story taught

**Changing the question found more than another reading of the model would have.** Six
specifications in a row asked *what can the operational queue not see*. This one asked *what can
a person not do*, and the first answer was that the money half of both process chains was
reachable only from the demo. Five classes had been specified, tested, documented and shipped
against a posted invoice that no surface could produce.

**The tests passed because the tests did the unreachable thing themselves.** Every derivation
test calls `post_sales_invoice` directly. That is the same failure as the dependency-override
leak fixed in #130 and as the "absence is load bearing" risk recorded about three exception
classes: a contract that holds everywhere it is checked, and is never checked where it matters.

**The diff is YAML and transport, and it is the most valuable change in a while.** Nothing under
`services/` moved and no migration was added — deliberately, and asserted rather than hoped for,
because a service change here would have meant the scope was misjudged.

**The first measurement was wrong and saying so was cheap.** "85 mutating endpoints against 44
commands" overstates the declaration gap, because endpoints share commands. Counting services
gives 18 undeclared, half of them reads that shape a response. The corrected number is in the
specification, and it makes the remaining gap look small and gateable rather than daunting —
which is the more useful conclusion.
