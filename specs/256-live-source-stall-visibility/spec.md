# Feature Specification: Live Source Stall Visibility and Recovery

**Feature Branch**: `256-live-source-stall-visibility`
**Created**: 2026-09-23
**Status**: Approved
**Approved**: 2026-09-23
**Language**: English
**Input**: "A live source that has stopped producing must say so, say why, and be recoverable by its owner. A missing scheduler or worker must be visible where the source is operated, not only inferable from a timestamp that stopped moving."

## Context and Intent

### Problem

On 2026-09-19 the live simulation of a production demo company stopped and stayed stopped for four days without anyone noticing. The Demo Data page showed everything it was designed to show: a badge reading `Execution needs attention`, `Next scheduled arrival: —`, and a last successful import that no longer moved. None of these say what happened, that nothing will ever resume by itself, or what to do.

Three distinct defects produced that outcome.

1. **The reason is read but not shown.** The status read returns `scheduler_error` (`database_error` in the observed case: one transient database failure in the job child process). No interface renders it. The user sees a badge that asks for attention and no way to learn what needs attending to.
2. **An absent background role is indistinguishable from an idle one.** When a run fails hard, the schedule is disabled and `next_arrival` becomes empty. When the scheduler or worker is simply not running, the schedule stays enabled, `next_arrival` keeps pointing at a moment in the past, and the badge keeps reading `Running`. Nothing marks an occurrence as overdue. Role readiness exists (spec 149) but is probed only on Home, and reports `unknown` when the probe URLs are unconfigured — a silent result that reads like health.
3. **The recovery path is blocked, and refuses without saying why.** The owner's only restart path is pause followed by resume. In the observed company, resume is refused with HTTP 403 and the body "Demo Data changed; reload its current status." The real cause is that the live source re-authorizes against the current code's canonical reference catalog: items added to the profile after the company was created cannot be matched in it, so the compatibility check refuses. The company is permanently unable to resume or restart its live simulation, and no interface says that or why.

Stated as one sentence: a live source can die from a transient infrastructure blip, never recover on its own, never explain itself, and refuse every recovery attempt with an error that names neither the cause nor a next step.

### Scope

- Make the stall reason of a live source durable, readable and visible wherever the source is operated.
- Distinguish an overdue occurrence and an absent background role from normal idle operation.
- Make a stopped live source recoverable by its owner in one confirmed action, or refuse with a reason a person can act on.
- Separate a transient infrastructure failure from a permanent authorization refusal in the policy that disables a schedule.

### Non-Goals

- Retrying a permanently unauthorized occurrence forever, or re-enabling a schedule that was disabled for an authorization reason.
- Automatically repairing, rewriting or re-seeding an existing company's reference catalog.
- A new alerting, paging or notification channel, an operator console, or a second health mechanism beside the probes of spec 149.
- New scheduling infrastructure, per-subsystem timers, browser timers or a second queue.
- Changing what a handler does, what synthetic intake generates, or any business rule of the records produced.

### Existing Contracts

- [Scheduled jobs](../../docs/features/scheduled-jobs.md)
- [Company setup and demo profiles](../../docs/features/company-setup-demo.md)
- [Home activity and readiness](../../docs/features/home-live-status.md)
- [Web product](../../docs/WEB_SPEC.md)

## Clarifications

### Session 2026-09-23

- **Q1 (retry budget)** → A transient infrastructure failure never ends a live source. After the fast attempts are exhausted the source is suspended and retried on a recovery attempt every four to eight hours until the failure has cleared, then it continues on its own.
- **Q2 (incompatible references)** → Existing companies must run again. Compatibility is judged by the references the live source actually uses, taken together with the profile version the company was created with; catalog entries added afterwards are not required of an existing company.
- **Q3 (signal outside the source page)** → The integrations overview carries the signal: an attention badge on a source whose live execution is stopped or overdue, plus its live state in the overview itself, and the source's settings lead to the live simulation controls.

### Session 2026-09-23 (after first delivery)

- **Where a source's settings live** → Each source has one place where that source is configured, and everything settable about it belongs there, including the state, the rate and the controls of a simulation it owns. Sending a person from that place to another page was the wrong reading of FR-016. What the source *observes* — arrivals, order to cash, live activity — is not a setting and stays on the simulation's own page.
- **A narrow column states the state** → The live state in the source table is one word; the reason travels with it rather than being cut off.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Learn why a live source stopped (Priority: P1)

An owner opens a live source that is no longer producing. The page states that execution stopped, when it stopped, what kind of failure stopped it, and whether anything will resume on its own.

**Why this priority**: The observed outage lasted four days because the page showed a symptom and withheld the cause it already had in hand.

**Independent Test**: Plant a failing occurrence of each failure kind on a connected live source, then read the source through Web, MCP, CLI and API and compare the stated reason, the stop time and the recovery statement.

**Acceptance Scenarios**:

1. **Given** a live source whose latest occurrence failed, **When** the owner opens its page, **Then** the page states the failure kind in business language, the time of the last successful production, the time of the failure, and that nothing will resume without an explicit action.
2. **Given** a live source stopped by an exhausted retry budget after a transient infrastructure failure, **When** its state is read, **Then** the stated reason distinguishes an infrastructure failure from a refusal to authorize the work.
3. **Given** a live source stopped by an authorization refusal, **When** its state is read, **Then** the stated reason names the refused precondition rather than a generic changed-state message.
4. **Given** a stall reason is shown, **When** the same source is read through MCP, CLI or API, **Then** the same failure kind, times and recovery statement are returned.
5. **Given** a live source that is producing normally, **When** it is read, **Then** no stall reason is stated and the next expected occurrence is shown.

### User Story 2 - Notice that nothing is running at all (Priority: P1)

An owner whose scheduler or worker is absent sees that fact where the source is operated, instead of a badge that reads `Running` above a next arrival that silently drifts into the past.

**Why this priority**: The state where the schedules are healthy and the roles are gone is the one state the product currently describes as normal operation.

**Independent Test**: Stop the worker, then the scheduler, on a company with an enabled live source; observe the source page, Home readiness and the API reads at the first overdue occurrence and after several missed ones.

**Acceptance Scenarios**:

1. **Given** an enabled schedule whose next occurrence is materially overdue, **When** the source is read, **Then** it is stated as overdue with the expected and observed times, and not as running normally.
2. **Given** a configured background role that does not answer its readiness probe, **When** the source page is opened, **Then** the page states which role is unavailable and that arrivals will not continue until it returns.
3. **Given** background readiness probes are not configured, **When** readiness is read, **Then** the unconfigured result is presented as unknown and is visually and textually distinct from a confirmed healthy result.
4. **Given** the roles return and the backlog is processed, **When** the source is read again, **Then** the overdue statement clears without any user action.
5. **Given** a tenant reads readiness, **When** the response is produced, **Then** it contains no probe URL, credential or other deployment detail.

### User Story 3 - Recover a stopped live source (Priority: P2)

An owner of a stopped live source restarts it in one confirmed action, or is told in business language why it cannot be restarted and what would make it restartable.

**Why this priority**: The observed company cannot be restarted at all, and the refusal it produces names neither cause nor remedy. Visibility without a recovery path only documents the dead end.

**Independent Test**: Restart a live source stopped by a transient failure; then attempt the same on a source whose company predates the current reference catalog and compare the refusal text, its identified cause and its stated options.

**Acceptance Scenarios**:

1. **Given** a live source stopped by a failed occurrence while every precondition still holds, **When** the owner confirms the restart, **Then** the source resumes production and the next expected occurrence is shown, without requiring a preparatory pause.
2. **Given** a restart is refused because the company's references no longer match the current profile catalog, **When** the refusal is presented, **Then** it names the changed catalog as the cause, identifies the incompatible reference scope, and states the available options.
3. **Given** a source that owns a live simulation, **When** its configuration is opened, **Then** its state, reason, rate and controls are there and can be changed there, while its arrivals and activity remain one step away.
3. **Given** a restart is refused, **When** the same restart is attempted again unchanged, **Then** the refusal is identical and no state, revision or schedule was altered by the attempt.
4. **Given** a live source is restarted, **When** the restart is confirmed, **Then** every schedule belonging to that source is re-enabled together, or none is and the refusal states the incomplete scope.
5. **Given** a live source owned by another tenant, **When** a restart is attempted against it, **Then** it is refused without revealing whether that source exists.

### Edge Cases

- A transient failure repeats across the whole retry budget within a database outage lasting minutes.
- A run is claimed, its worker is killed, and the occurrence settles as unresolved rather than failed.
- A schedule is disabled while an occurrence is still unfinished.
- The scheduler runs while the worker does not, so occurrences are materialized and never executed.
- Readiness probes are configured for one role only.
- A stall reason is produced for a company whose owner has since lost admission.
- A company created under an earlier profile version is read after the canonical catalog has grown.
- Both the arrival and the settlement schedule of one source stop within the same outage.
- Clock skew between the recorded occurrence time and the reading process.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The state of a live source MUST expose a stall reason derived at read time from the retained schedule and occurrence records, comprising the failure kind, the error identity, the time of the failure, the time of the last successful production, the number of attempts made, and whether any automatic recovery remains.
- **FR-002**: The stall reason MUST distinguish at least: a transient infrastructure failure with an exhausted retry budget, an authorization or precondition refusal, an unresolved occurrence of unknown outcome, and a throttled source awaiting user resolution.
- **FR-003**: Every interface that presents a live source — Web, MCP, Chat, CLI and API — MUST present the stall reason and MUST NOT present a source as merely needing attention without it.
- **FR-004**: A live source whose next occurrence is overdue by more than a bounded multiple of its own interval MUST be stated as overdue, with expected and observed times, in place of a normal running state.
- **FR-005**: Where a live source is operated, the readiness of the background roles that execute it MUST be presented, reusing the existing readiness service; an unconfigured probe MUST be presented as unknown and MUST NOT be presented as healthy.
- **FR-006**: The policy that halts a schedule MUST distinguish a transient infrastructure failure from a permanent refusal. A transient infrastructure failure MUST NOT end a live source: after its immediate attempts are exhausted the schedule MUST be suspended rather than stopped, and MUST carry the next recovery attempt.
- **FR-007**: A suspended schedule MUST attempt recovery every four to eight hours; when the transient failure has cleared the schedule MUST continue production by itself without any user action, and when it has not the suspension MUST persist with a new recovery attempt. A schedule stopped by an authorization refusal or by an owner control MUST NEVER be re-enabled automatically.
- **FR-007a**: While a schedule is suspended it MUST NOT accumulate missed occurrences; recovery MUST resume production from the moment it succeeds rather than replaying the suspended interval.
- **FR-008**: An owner MUST be able to restart a stopped live source in one confirmed action, regardless of the connection state the stop left behind, without a preparatory pause.
- **FR-009**: A refused restart MUST return a specific reason naming the failed precondition and the affected reference scope, and MUST NOT alter connection state, schedule state or revision.
- **FR-010**: A restart that spans several schedules of one source MUST be all-or-nothing; a partial result MUST be refused and MUST state which schedule could not be restarted.
- **FR-011**: Reference compatibility for an existing company MUST be judged by the references its live source actually uses together with the profile version the company was created with. A catalog entry added after the company was created MUST NOT be required of that company and MUST NOT make its live source unrecoverable. A newly connected source is unaffected and MUST still be established against the current catalog.
- **FR-012**: When compatibility cannot be established, the system MUST state the options available to the owner and MUST NOT silently modify the company's references.
- **FR-013**: Readiness and stall information presented to a tenant MUST NOT contain probe URLs, credentials, host names, stack traces or other deployment detail.
- **FR-014**: Reads introduced by this feature MUST NOT execute, materialize, claim or repair any job.
- **FR-015**: The integrations overview MUST mark every source whose live execution is stopped, suspended or overdue with an attention badge and MUST state its live state there, so that a stalled source is visible without opening it.
- **FR-016**: The place where a source is configured MUST contain everything settable about that source, including the state, rate and controls of a simulation it owns; it MUST NOT send the person elsewhere to change them. What the source observes MUST NOT be duplicated there, and MUST stay reachable from it in one step.
- **FR-017**: A failure MUST retain a bounded failure category and human-readable message, free of payloads, credentials and connection detail, so that the reason survives the process boundary that produced it.

### Domain and Traceability Requirements

- **DR-001**: The stall reason MUST be derived at read time from retained schedule and occurrence records; it MUST NOT be stored as a new authority or duplicated onto the connection.
- **DR-002**: Overdue detection MUST compare recorded occurrence times with the reading time and MUST NOT rewrite the schedule's next occurrence.
- **DR-003**: Role readiness is volatile infrastructure observation and MUST NOT be recorded as a business fact or mixed into any business record.
- **DR-004**: Every query and control introduced or extended MUST enforce tenant scope; a foreign identity MUST behave as not found.
- **DR-005**: Web, MCP, Chat, CLI and API MUST call the same application services; no adapter may implement its own stall, overdue or restart rule.
- **DR-006**: Correlation MUST use opaque tenant-scoped connection, schedule, occurrence and reference identities, never a display label, SKU or document number.
- **DR-007**: The feature MUST reuse the existing schedule, occurrence, connection and readiness records unless planning proves a repeated core need they cannot express.

### Key Entities *(when data is involved)*

- **Stall reason**: The read-time observation of why a live source stopped producing: failure kind, error identity, failure time, last successful production, attempts, remaining automatic recovery.
- **Overdue occurrence**: An enabled schedule whose expected occurrence time has passed by more than its permitted multiple without a recorded occurrence.
- **Role readiness**: The ready, unavailable or unknown observation of a background role, valid only at its observation time.
- **Restart request**: One idempotent, confirmed, tenant-scoped owner action that returns a stopped live source to production or refuses with a stated reason.
- **Reference compatibility result**: The comparison of a company's retained references against the profile version it was created with, naming every incompatible scope.

## Success Criteria *(mandatory)*

- **SC-001**: For each of the four stall kinds in FR-002, a planted occurrence produces a stall reason that names the kind, its times and its recovery statement in Web, MCP, CLI and API, with no interface omitting it.
- **SC-002**: With the worker stopped, an enabled live source is stated as overdue within one permitted interval multiple, and is never presented as running normally while no occurrence is executed.
- **SC-003**: With readiness probes unconfigured, no interface presents a background role as healthy.
- **SC-004**: An infrastructure interruption never ends a live source: the schedule is suspended, its recovery attempt lies between four and eight hours ahead, and once the failure clears the source produces again without user action and without replaying the suspended interval.
- **SC-005**: A live source stopped by a failed occurrence is restarted by its owner in one confirmed action in 100% of acceptance runs, and a repeated identical restart produces no second effect.
- **SC-006**: A company created under an earlier profile version, on a system whose canonical catalog has since grown, restarts its live source and produces again; a refusal for a reference the source does not use fails the criterion.
- **SC-007**: A planted cross-tenant source, schedule or restart is refused without revealing whether the foreign identity exists, and no tenant-visible payload contains deployment detail.
- **SC-008**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The readiness probes of spec 149 are the only health mechanism; making them visible where sources are operated is a presentation change, and configuring `REALITY_SCHEDULER_HEALTH_URL` and `REALITY_WORKER_HEALTH_URL` in each deployment remains operator work outside this feature.
- The existing schedule and occurrence records already retain every fact the stall reason needs; planning must confirm this before proposing any schema change.
- Disabling a schedule after a genuine permanent refusal remains correct behaviour; only the classification, the visibility and the recovery path are in question.
- The recorded 2026-09-19 outage of tenant `ten_576f39f9b0` is the reference case: `scheduler_error` `database_error`, both demo schedules disabled, `next_arrival` and `next_settlement` empty, resume refused with HTTP 403 and the body "Demo Data changed; reload its current status.", caused by the reference catalog having grown past the company's creation-time profile version.

## Open Questions

None. The three questions of the draft were answered on 2026-09-23 and are recorded under Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 scenarios 1–5 | Stall-kind service tests, interface parity matrix, browser proof of the source page |
| FR-004–FR-005 | US2 scenarios 1–4 | Overdue detection tests with a stopped worker, readiness presentation proof including the unconfigured case |
| FR-006–FR-007 | US1 scenario 2; edge cases | Retry-budget test across a simulated interruption; no-auto-resume regression test |
| FR-008–FR-010 | US3 scenarios 1, 3, 4 | One-action restart story, idempotent replay test, all-or-nothing multi-schedule test |
| FR-011–FR-012 | US3 scenario 2 | Creation-time profile-version compatibility test against a grown catalog |
| FR-013–FR-014 | US2 scenario 5; edge cases | Payload inspection test and a read-only assertion over the job tables |
| FR-015–FR-016 | US1 scenario 1; US2 scenario 2 | Integrations overview badge and state tests, settings-to-simulation browser proof |
| FR-017 | US1 scenarios 1–3 | Failure-category retention test across the process boundary |
| DR-001–DR-003 | US1–US2 | Derivation-at-read-time assertions; no new stored authority |
| DR-004–DR-006 | US3 scenario 5; edge cases | Tenant-isolation family and opaque-identity checks |
| DR-007 | US1–US3 | Schema-stability check |
