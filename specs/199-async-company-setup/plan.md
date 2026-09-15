# Implementation Plan: Company setup does not seed inside the request

## Technical Context
`services/company_setup.py`, `services/playground.py:start_run`, the shared job
registry and `services/scheduled_jobs.py`, a new handler under `jobs/handlers/`, the
two React preparing screens, and the reverse proxy template. No schema, no migration.

## Constitution Check
All principles PASS. The seed keeps running through the same services with the same
tenant scope, confirmation and request-key identity; only the process that executes it
moves. The handler obeys the existing job contract: it commits nothing of its own, its
writes commit with the run, its configuration is closed and it revalidates
authorization. No new scheduling infrastructure, no API-process loop, no browser timer,
no second demo queue.

## Design
`start_run` gains `initialize: bool = True`. With `initialize=False` it returns right
after the commit that already separates durable metadata from initialization, which is
the seam this feature needs.

`create_company` uses that seam for the international profile: it enqueues one
`company_setup.initialize` run through `scheduled_jobs.create_manual_run`, keyed by the
playground run so a repeated request replays the same queued run instead of adding a
second, and returns `_result(...)`, which already reports the run's `initializing`
status. An empty company and the two-order execution fixture keep initializing in the
request, because neither is large enough to be worth deferring.

`jobs/handlers/company_setup.py` registers one definition whose configuration names the
run. Its authorization resolves the playground run for the tenant and actor and refuses
anything else; `scheduled_jobs._owner` routes this job type to that same check instead
of `require_company_owner`, because a verified account pending admission may create a
Sandbox and must be able to have it seeded. The handler calls `initialize_profile` and
`_finish_live_setup` in their new transaction-bound form (`_commit=False`), so handler
writes and run success commit together; an already active run is a no-op, which is what
makes a re-run and a concurrent explicit retry safe.

`initialize_profile` and `_finish_live_setup` keep their committing behaviour by default
for the explicit retry path, which stays synchronous and is the recovery route where no
worker runs.

The two preparing screens follow the receipt: `TrialEntry` reads
`GET /api/company-setup/playground` and `CompanySetup` reads the request receipt, on a
bounded interval, stopping on ready, on failure and on unmount. Ready opens the company
exactly once, as it does today.

The proxy template states `proxy_read_timeout` and `proxy_send_timeout` for `/api/`
rather than relying on the implicit 60-second default.

The worker executes the handler in its usual child process, so this job inherits the
same 30-second budget and durable settlement as the four existing ones.

## Verification / rollback
Service tests first: the receipt reports initializing and one run is queued; a repeated
request queues nothing further; the handler seeds the company and a second execution
changes nothing; enqueue and claim refuse a foreign actor; the explicit retry completes
a pending and a failed initialization; empty content is ready immediately. Then the job
registry, company setup, demo data and free playground suites, the web contract and
browser runs, and the full PostgreSQL suite. Rollback is a code revert; queued runs are
ordinary rows and the retry path completes any company left initializing.
