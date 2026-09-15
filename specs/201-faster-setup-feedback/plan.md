# Implementation Plan: A new company is picked up at once and says where it stands

## Technical Context
`services/scheduled_jobs.py` (discovery), `jobs/runtime.py` (the worker sweep),
`apps/worker/Dockerfile` (the default interval), `services/company_setup.py` (the
reported preparation state), `unified/setupProgress.ts` and the two preparing screens.
No schema, migration or new infrastructure.

## Constitution Check
All principles PASS. Discovery reads identity metadata of runs that already exist and
changes nothing about authorization: `claim_next` still locks, authorizes and claims
each run. The reported preparation state is derived at read time from the run that
seeds the company and is stored nowhere. No new table, timer or queue.

## Design
`due_tenants` selects distinct tenant ids from runs matching exactly `claim_next`'s
eligibility — pending or retrying with a reached attempt time, or running past the
lease — ordered and paged like `tenant_catalog`. `ProcessLoop.sweep` uses it for the
worker role and keeps the full catalog for the scheduler, whose job is to materialize
schedules that no run represents yet. An idle worker sweep then costs one query
regardless of how many tenants exist, which is what makes a one-second interval
affordable; the worker image states that interval.

`_result` reports `preparation`: `queued` while the seeding run waits, `preparing`
once it is claimed, and `null` when no run is pending — the claim commits before the
child process starts, so the transition is observable. The receipt keeps its existing
fields; this is one more derived field, not a new authority.

`followSetup` reads before its first wait and keeps the existing attempt bound, so the
elapsed bound stays roughly the same while the first answer arrives immediately. The
preparing screen renders three steps from the receipt's status and preparation state,
marks the current one and falls back to today's spinner when nothing is reported.

## Verification / rollback
Service tests first: discovery returns only tenants with claimable work, includes an
expired lease, excludes a finished run and pages; the scheduler's catalog is untouched;
the reported preparation state moves queued → preparing → none. Web contract tests for
the immediate first read and the step derivation; a browser run over the three steps in
four languages; then the focused suites, the web checks and the full PostgreSQL suite.
Rollback is a code revert; no stored state changes.
