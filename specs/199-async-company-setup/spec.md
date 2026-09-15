# Feature Specification: Company setup does not seed inside the request

**Language**: English

**Created**: 2026-09-15
**Status**: Accepted scope (owner: "ja mach spec 199", after the measurement below)

## Context and Intent
Creating a demo company seeds the whole canonical profile inside the HTTP request that
asks for it. Measured on a created playground company, that one request issues **6,447
SQL round-trips**: 3.2 s against a loopback database, and proportionally more wherever
the database sits on the network — roughly 13 s at 2 ms round-trip latency and 32 s at
5 ms. It is by far the longest request in the product, so it is the one that every
connection interruption lands on: an API restart or redeploy, a proxy read timeout, a
network hiccup. The browser reports those as `TypeError: Failed to fetch`, which the
web shows as "Could not load this view · Failed to fetch" on the preparing screen. The
work itself usually completed on the server, so a retry looked fine — which is why the
failure reads as intermittent.

The record model already carries everything an out-of-request seed needs: `start_run`
commits the tenant, membership and run metadata before initialization begins, the run
holds `initializing` / `initialization_failed` / `active`, and the read endpoints
already report those as the receipt's status.

### Non-Goals
The content of the profile, the live simulation, admission, quotas, archiving, the
choice of what a company starts with, and the number of round-trips the seed issues.
The measured hot spots are per-operation authorization re-reads (1,231 tenant rows,
791 playground runs, 287 tenant ids), not the inserts; reducing them touches every
guarded write in the product and is left to its own specification.

## User Scenarios & Testing
### US1 — Ask for a company and get an answer immediately (P1)
Creating a demo company answers as soon as the company exists, before its profile is
seeded. The answer reports the setup as initializing and names the company.

### US2 — Watch it become ready (P1)
The preparing screen follows the receipt until the company is ready and then opens it.
A slow seed shows continued progress, never an error.

### US3 — Recover an initialization that failed (P1)
A seed that fails leaves the existing failed receipt and its explicit retry, which
still completes the same company rather than creating a second one.

### Edge cases
A repeated creation request must not enqueue a second initialization. A retry while the
background initialization is still pending must not seed twice or produce two companies.
An empty company and the small execution fixture stay immediate. A deployment whose worker
is not running leaves the setup initializing; the explicit retry remains the escape
hatch and completes it in the request, as today.

## Requirements
- **FR-001**: Creating a company with profile content commits the tenant, membership and
  run metadata, enqueues exactly one initialization for that run through the shared job
  registry, and answers with the receipt reporting `initializing`.
- **FR-002**: The initialization runs in the shared worker under the existing job
  contract: one registered allowlisted job type, a closed configuration naming the run,
  authorization revalidated at enqueue and at claim, and all writes committed with the
  run's success. It performs the same seeding and live setup the request used to do.
- **FR-003**: A repeated creation request for the same request key enqueues no second
  initialization and returns the same receipt. Enqueue and seeding are idempotent per
  run, whichever happens first.
- **FR-004**: The existing explicit retry still initializes the same company in the
  request, so a company is recoverable even where no worker is running.
- **FR-005**: A company whose profile is small enough to seed in the request — an
  empty company and the two-order execution fixture — is still ready when the request
  answers. Only the international profile is deferred.
- **FR-006**: The preparing screens follow the receipt until it reports ready or failed,
  show the existing progress while it is initializing, and open the company exactly once
  when it is ready. Polling stops when the component leaves.
- **FR-007**: The reverse proxy states its own read timeout for the API instead of
  relying on an implicit default.

## Success Criteria
The creation request no longer carries the seed: it answers after the metadata commit
and reports `initializing`, and the seeded company becomes ready through the worker.
Repeated requests produce one company and one enqueued initialization. The explicit
retry still completes a failed or pending initialization in the request. Empty companies and the execution
fixture answer ready. The browser reaches a ready company by following the receipt.

## Assumptions and Dependencies
`apps/worker` is part of every supported deployment (Compose, the installer, Helm and
the documented Railway setup). The worker runs each handler in a child process with a
30-second wall-clock budget, inside a 60-second claim lease; the measured seed is 3.2 s
against a loopback database and stays inside that budget for a database in the same
region. A handler that exceeds it is terminated and retried, and after the retry budget
the company is recovered by the explicit retry, which still initializes in the request. Authorization for this job type follows the playground
run's owner, because a verified account pending admission may already create a Sandbox.
No schema change and no migration.

## Requirement Traceability
| Requirement | Proof |
|---|---|
| FR-001, FR-003, FR-005 | Service tests over the returned receipt, the enqueued run and a repeated request |
| FR-002 | Registry/parameter tests, authorization refusal at enqueue and claim, handler effect and re-run |
| FR-004 | Service test retrying a pending and a failed initialization |
| FR-006 | Web contract tests and a browser run following the receipt to ready and to failure |
| FR-007 | The proxy template states the timeout; site contract test |
