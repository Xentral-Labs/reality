# Implementation Plan

## Constitution Check
All eight principles PASS. No stored derivation is added and nothing is recomputed
outside its canonical service; the shared cache lives inside one request and holds what
that service already returned. Documents gain no operational status field — the date
column changes type, it does not change meaning. Tenant scope is unchanged and the
identity query carries the same tenant predicate as the answer. Mutating tool
confirmations are untouched. The one schema change is a column type and two indexes, all
justified by measurement recorded in verification.md.

## Design
The compiler already holds everything needed to know which rows a question can reach —
it just applied that knowledge after the derivation instead of before it. The frame
construction (root, joins, existence tests, filters) is factored out of `build` into
`_compose`, and used twice: once by the answer, once by `reachable_identities`, which
substitutes the plain anchor table for each derived node and selects distinct anchor
keys. Conditions the plain table cannot express — the derived amounts — are dropped by a
`keep` predicate, and any existence test that loses a condition is dropped whole. The
result can therefore only be too generous, which is safe because every condition is
conjunctive: a row the identity query excludes is one the final WHERE would drop.

Where nothing narrows, or the set exceeds the bind limit, the function returns None and
the derivation reads the company exactly as before. Push-down is an improvement that can
always be declined, never a precondition.

The canonical readers gain an optional identity filter — `party_ids` on the open-item,
aging and credit reads, `item_ids` on both inventory reads. Each one selects rows; none
of them changes how a row is derived, because every position is summed within one party,
article or document and never across them. A shared dict threaded through one `execute`
keys each canonical read by exactly what was asked for, so a narrower answer is never
served to a wider question, and nothing survives the request.

`document.document_date` becomes a `date`. The column previously accepted any text and
three tests recorded that as deliberate; the owner's decision is that free text in a date
field is not a date, and the tests now record the rule that replaces it. A source payload
remains lossless, so nothing a sender said is discarded — only the typed field stops
pretending to hold something it cannot mean. The wire format stays ISO text everywhere:
`reality.domain.calendar` holds the two conversions, `as_day` at the writes and
`day_text` at the reads, with absent spelled `""` outside and NULL inside as before. The
compiler already asked `isinstance(value.type, Date)` before emitting its `substr`
validity cascade, so a real date column removes that per-row work with no change to the
declaration. Services route writes through `_document_day`, which turns an unreadable
day into the business error the surfaces already map to 422.

`statements_per_traversal` keeps its honest meaning for an ordinary path and gains
`statements_per_derivation`, checked against the reads the existing listener already
counts; exceeding it refuses as a regression rather than serving slowly. The declared
`max_recursive_depth`, until now read by nobody, is enforced against every recursive
edge at load.

## Alternatives considered
A persisted or cross-request cache would beat all of this and is refused: it puts a
second, ageing authority beside the canonical services, which is the failure this
architecture exists to prevent. A generated date column beside the text one was
considered and rejected for the same reason — two fields stating one fact.
