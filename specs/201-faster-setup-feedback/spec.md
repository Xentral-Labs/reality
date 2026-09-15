# Feature Specification: A new company is picked up at once and says where it stands

**Language**: English

**Created**: 2026-09-15
**Status**: Accepted scope (owner: the spinner runs a while — show roughly how long it
takes, and make it faster)

## Context and Intent
Since feature 199 the creation request answers in 44 ms and the shared worker seeds the
company. Measured on a created playground company, the remaining wait is mostly spent
waiting to look rather than working:

| | |
|---|---|
| Creation request | 0,04 s |
| Waiting for the worker's next poll | up to 5 s |
| Seeding and live setup | 2,7 s |
| Waiting for the screen's first read | 2 s |

Roughly half of the wait is polling latency. The worker polls every five seconds
because an idle sweep asks every tenant in the installation whether it has work, which
is the reason the interval cannot simply be shortened. The preparing screen meanwhile
shows one spinner for the whole wait, so nothing distinguishes "queued" from "being
prepared" and nothing says how far along it is.

### Non-Goals
The cost of the seed itself (roughly sixteen statements per created record; its own
specification), the content of the demo profile, and any change to what the creation
request does. No new scheduling infrastructure: the worker keeps polling, it just stops
asking tenants that have no work.

## User Scenarios & Testing
### US1 — The company is picked up at once (P1)
A queued initialization is claimed on the worker's next poll, and that poll is one
second rather than five, because an idle sweep costs one query instead of one per
tenant in the installation.

### US2 — The screen looks immediately (P1)
The preparing screen reads the receipt as soon as the creation request answers, and
keeps reading on a short interval, so a company that is already ready opens at once
instead of after a fixed delay.

### US3 — The screen says where it stands (P1)
The preparing screen shows three steps taken from real state — the company is created,
its data is being prepared, it is ready — with the current one marked. No invented
percentage and no estimated remaining time.

### Edge cases
A worker restricted to one tenant keeps that scope. An installation with no queued work
must not be swept tenant by tenant. A run whose lease expired is still discovered. The
step display must degrade to the existing spinner when the preparation state is unknown,
and must never claim "being prepared" for a company nobody is preparing.

## Requirements
- **FR-001**: The worker discovers the tenants that actually have claimable runs —
  pending, retrying, or running past their lease — instead of every tenant. The
  scheduler keeps its full catalog, because it materializes schedules.
- **FR-002**: The worker's default poll interval is one second.
- **FR-003**: The preparing screens read the receipt immediately and then on a one-second
  interval, keeping the existing bound and stopping on ready, failure and unmount.
- **FR-004**: A company setup receipt reports its preparation state — queued, being
  prepared, or none — derived from the run that seeds it.
- **FR-005**: Both preparing screens — the first entry and the company setup dialog —
  render the three steps from that state in all four interface languages, mark at most
  one as current, and fall back to the plain spinner when no state is reported.

## Success Criteria
A queued initialization is discovered by a sweep that issues one query on an otherwise
idle installation, and a tenant without work is never visited. The measured wait between
the creation request and a ready company drops from roughly seven seconds to roughly
three, without changing what the seed does. The screen names the current step.

## Assumptions and Dependencies
`claim_next` already defines what makes a run claimable; discovery must use exactly that
predicate or a run could be enqueued and never seen. The worker commits the claim before
the handler runs, which is what makes "being prepared" observable to a reader. One
second is the smallest interval `ProcessLoop.run` accepts. No schema change and no
migration.

## Requirement Traceability
| Requirement | Proof |
|---|---|
| FR-001, FR-002 | Service tests over discovery: only tenants with claimable work, expired leases included, scheduler unchanged; worker command default |
| FR-003 | Web contract tests for the immediate first read and the retained bound |
| FR-004 | Service and API tests over the reported preparation state across queued, running and finished |
| FR-005 | Web contract tests and a browser run over the three steps and four languages |
