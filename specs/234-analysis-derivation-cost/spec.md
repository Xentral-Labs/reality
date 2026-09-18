# Feature Specification: What an analysis costs

**Language**: English

## Context and Intent
Analysis answers questions in two very different ways, and until now the difference
was invisible and unbounded. An ordinary path compiles to one SQL aggregate. A path
that reaches a derived position first runs a canonical service over the whole
company, ships the result back into PostgreSQL as a bound JSON value, and aggregates
that. The second kind was measured at 50 to 100 times the first, and — the part that
surprised the reader rather than the author — it cost the same whether the question
asked about one customer or all of them. The filter was applied to what came back,
never to what was derived.

This feature makes the narrowing arrive before the work, stops one request deriving
the same register twice, gives the document date a column the database can index,
and replaces a limit that was declared but never enforced.

### Non-Goals
No persisted or materialized derivation, no cache that outlives a request, no new
analysis object, measure or edge, and no change to any answer. Every number this
feature touches must come back identical; only what it costs to obtain may change.

## User Scenarios & Testing
### US1 — A narrow question costs what a narrow question should (P1)
Given a company with many customers, asking for one customer's balance derives the
register for that customer, not for the company. The answer equals what the
unfiltered question reports for that customer.
### US2 — A broad question is unchanged (P1)
Given no narrowing in the question, the derivation reads the company as before and
returns every party. Push-down never removes a row the question still reaches.
### US3 — One register, derived once (P2)
Given a question that reaches two positions resting on the same canonical read, the
request derives it once.
### US4 — A document date is a day (P1)
Given an impossible or unreadable date — an invalid calendar day, or free text such
as a period label — recording the document is refused as a business error naming the
expected format. Given no date at all, the document is recorded and reported under an
explicit unknown group. What a source actually sent is unaffected: its payload is
stored verbatim as before, which is where losslessness belongs.
### US5 — A derivation that regresses is caught (P2)
Given a canonical derivation that comes to read more statements than the model
declares, the traversal is refused as a regression instead of served slowly.

## Requirements
- **FR-001**: Before a canonical derivation runs, compile the identities the question
  can still reach from the conditions the answer itself applies, and pass them to the
  canonical service. Conditions the anchor table cannot express are omitted, so the
  set may be too generous and never too small.
- **FR-002**: Where no condition narrows, or the reachable set exceeds the binding
  limit, derive the company as before. The absence of push-down is never an error.
- **FR-003**: Extend the canonical finance, credit and inventory readers with an
  optional identity filter that selects rows without altering how one is derived.
  Tenant scope, Decimal arithmetic and opaque identity are unchanged.
- **FR-004**: Share canonical reads within one traversal, keyed by exactly what was
  asked for, so a smaller answer is never reused for a larger question. The share
  does not outlive the request.
- **FR-005**: Store `document.document_date` as a calendar date. Callers, tools, MCP
  schemas, the web API and fixtures keep sending and receiving ISO text; an absent
  day remains the empty string on every surface and NULL in the column. An
  unreadable day is refused at the boundary as a business error.
- **FR-006**: Index `document` by tenant, type and day, and `document_line` by tenant
  and document, so the sixteen and eight analysis objects sharing those tables stop
  paying for each other's rows.
- **FR-007**: Replace `statements_per_traversal`'s false claim of one with an
  enforced `statements_per_derivation` ceiling, and enforce `max_recursive_depth`
  against every declared recursive edge at load.
- **FR-008**: Pin the cost in statement counts and derivation inputs, not wall-clock,
  so the regression test means the same thing on any machine.

## Assumptions and Dependencies
Every narrowing condition the answer applies is conjunctive, so a row the identity
query excludes is one the final WHERE would have dropped. Canonical positions are
summed within one party, one article or one document and never across them, so
selecting fewer of them returns fewer rows of identical arithmetic. Existing surfaces
keep ISO text for the document date; no caller is asked to change. Shared services
remain the single authority for every number, and no answer is derived a second time
beside them.

## Success Criteria
Identical answers before and after on real company data; a narrowed question reaches
the canonical service already narrowed; an unnarrowed one still reaches every row; one
register derived once per request; an impossible day refused and an absent one still
reported as unknown; the declared statement ceiling and recursive depth enforced; the
full backend suite, Ruff and the spec policy green.

## Requirement Traceability
| Requirement | Story | Tasks | Tests |
|---|---|---|---|
| FR-001 | US1 | T001,T002 | Filter reaches the derivation; narrowed answer parity |
| FR-002 | US2 | T001,T002 | Unfiltered question still reaches every party |
| FR-003 | US1 | T002 | Finance, credit and inventory reads under an identity filter |
| FR-004 | US3 | T003 | Two positions on one register derive it once |
| FR-005 | US4 | T004,T005 | Impossible day refused, absent day grouped, migration |
| FR-006 | US1,US4 | T005 | Index migration and model declaration agree |
| FR-007 | US5 | T006 | Statement ceiling, recursive depth at load |
| FR-008 | US1–5 | T001–T006 | Cost pinned in statements and derivation inputs |

## Evidence and risks
Measured on a 10,233-document, 13,590-ledger-entry company, before and after, on the
same machine and the same data; see [verification](verification.md).

Converting the column is the one irreversible step. On 37,311 real documents it moved
6 rows to NULL, and all 6 already held the empty string: no row carried a day that was
lost. The migration refuses to invent one, checking the round trip rather than trusting
`to_date`, which answers 2026-03-02 for 2026-02-30 without complaint.

One behaviour changes visibly and deliberately, and it is the reason this feature needed
a decision rather than a refactor. The column accepted any text, and three tests recorded
that as intended: a period label, `"not-a-date"` and `"whenever"` could all be stored, and
each reader decided again on every read whether the value was a date. That left two
different things — a document stating no date, and a document stating a date that does not
exist — indistinguishable in every report, and it left the answer to what a value meant
with whichever reader looked at it. Both are now refused where they are written, and the
three tests record the new rule instead. Nothing is lost: what a source sent is still
stored verbatim in its payload, which is the record that is meant to be lossless. The
pre-existing `ix_document_tenant_date` index becomes a date index rather than a text one
as a side effect.

Push-down does not help a question that narrows nothing, which is the shape the
unfiltered register pages ask. Those still derive the company, and the remaining cost
sits in the input-bound counts and the JSON round trip rather than in the filter.
