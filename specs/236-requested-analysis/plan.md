# Implementation Plan

## Constitution Check
All eight principles PASS. No derivation changes and no answer changes: the same
canonical services produce the same rows, in a different process. A stored result is
evidence of one answer at one moment, never an authority another read derives from, which
FR-005 states and T004's tests hold. Tenant scope travels with the run and is revalidated
at execution rather than trusted from the request. No new scheduling infrastructure — the
registry, queue and worker of spec 147 are used as written. The one schema addition is the
table that holds a requested question and its answer, which has no home today.

## Design

### The budget is the cap that already exists
The specification says a declared budget decides immediate against deferred. Reading the
code, inventing a second number would be the wrong move: the derivations already carry
input caps — `MAX_FINANCE_DOCUMENTS`, `MAX_INVENTORY_ITEMS`, `MAX_ROWS` — and today those
caps produce a refusal. This feature changes what that refusal means rather than adding a
threshold beside it.

So: `graph.ask` runs exactly as it does now. If it raises `TraversalRefused` with
`finance_limit`, `inventory_limit` or `position_limit` — the three codes that say "this
company is too large for one request", and only those — the request is offered as a
deferred run instead. Every other refusal (`unknown_node`, `fan_out`, `unit_mismatch`,
`not_additive`, `snapshot_date_required`, …) is a judgement about the question and still
arrives immediately, unchanged. That is US3, and it falls out of the existing codes rather
than needing a new rule.

The consequence worth stating: the set of questions that defer is exactly the set that is
refused today. Nothing that works now becomes slower.

### Raising the cap where the worker runs
The deferred path needs the derivations to accept more than the immediate path does. The
caps are module constants, and threading a parameter from `execute` through
`derivations.read` into each relation is a lot of plumbing for one flag. `budget.py`
already carries `CANCELLED` as a contextvar for exactly this kind of cross-cutting
request property, so the deferred ceiling joins it there: set by the job handler, read by
the relations, absent everywhere else. A contextvar that changes a limit is only
acceptable because it cannot change an answer — it decides whether the work is attempted,
never what it returns.

### What is stored
One table, `analysis_request`: the checked question, the model version that gave it
meaning, the requesting user, the run it became, its state, and — once ready — the rows,
the moment they were answered and the SQL that produced them. Idempotent on
`(tenant, requester, request_id)` like `analytics_report` and `create_manual_run` already
are, so a retried request finds its own run rather than starting a second one.

Retention is a stated column rather than a policy elsewhere: a result nobody collected is
removed after it expires, and the row says when that is. The rows column is bounded by the
existing `result_rows` limit, so a result cannot grow without a limit somebody declared.

### Who may ask
`_owner` in `scheduled_jobs.py` falls through to company owner for unknown job types,
which is wrong here: anyone who may ask a question interactively may ask it deferred.
The analysis job registers its own rule, an active membership, mirroring how company setup
and demo data register theirs. The handler revalidates that membership at execution,
because the minutes between request and run are exactly when access changes.

### Order
Tests first (T001), because the thing most likely to go wrong is a refusal arriving late
instead of immediately, and that is invisible unless a test asks for it. Then the job and
its authorization, then the budget branch, then storage, then the caps, then the surfaces.

## Alternatives considered
**Running the analysis in the request with a longer deadline.** Rejected: it holds a web
worker for minutes and still fails at the memory ceiling spec 235 measures.

**Storing the result as an `analytics_report`.** Rejected: a report is a saved *question*,
re-asked on every read. A requested analysis is a saved *answer*. Putting them in one
table would make it a matter of which column is set whether a row is a question or a fact,
which is how the two would eventually be confused.

**A cache keyed by question.** Rejected for the reason FR-005 names: the moment a stored
answer is served to someone who did not ask for it, at a moment they did not choose, it
has become a standing figure and a second authority.
