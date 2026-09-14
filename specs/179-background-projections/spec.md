# Feature Specification: Background projections and responsive Inspector

**Feature Branch**: `179-background-projections`
**Created**: 2026-09-12
**Language**: English
**Status**: Approved for implementation
**Input**: The owner requested a complete sequential plan and implementation for the slow Calculated views tab and event-driven background projection refresh, including visible freshness and verification.

## Context and Intent

### Problem
The Inspector rebuilds its global reference catalog on every request. Stored projections are refreshed by reads, often rebuilding unrelated projections. A reader consequently pays for work caused by earlier business changes. The catalog also groups stored projections, live screens and parameterized price queries without making the distinction clear.

### Scope
Make the reference catalog inexpensive to reopen. Update stored projections outside requests through the existing scheduler and worker. Keep the last completed result visible with honest freshness. Preserve canonical services, authoritative command validation and source traceability.

### Non-Goals
No broker, independent timer, alternate business calculations, automatic business actions, external effects, deployment, or merge. Do not turn every application view into a projection. Parameterized price resolution and explicitly live read contracts remain live and are identified as such. No inventory/payment authority is moved to caches.

## User Scenarios & Testing

### User Story 1 - Open the calculation directory promptly (Priority: P1)
Users can open and search the directory without rebuilding unchanged definitions or rendering unopened details.
**Independent Test**: Repeated catalog reads reuse one validated definition; native disclosure and search still reveal the same content.
**Acceptance Scenarios**:
1. **Given** a running application, **When** the directory is reopened, **Then** unchanged definitions are reused and no business data is calculated.
2. **Given** collapsed entries, **When** one is expanded or a hidden description is searched, **Then** its complete explanation, actions and traceability remain available.
3. **Given** a failed catalog validation, **When** it is requested again after correction, **Then** the failure has not become a permanent cached result.

### User Story 2 - Receive updated stored results without a blocking read (Priority: P1)
Committed business changes make the affected projections eligible for durable background refresh. Opening a screen only reads completed results.
**Independent Test**: Commit changes, run scheduler then worker, and read the result with all builders forbidden during reads.
**Acceptance Scenarios**:
1. **Given** several committed events and no open browser, **When** background processing runs, **Then** affected projections catch up, with events coalesced and unrelated builders skipped.
2. **Given** a rolled-back business transaction, **When** background processing runs, **Then** no result claims that rolled-back event.
3. **Given** concurrent business activity, duplicate dispatch or an interrupted worker, **When** refresh retries, **Then** checkpoints never claim unprocessed changes and published rows correspond to a consistent retained state.
4. **Given** a new company, old builder version or absent cache, **When** background processing runs, **Then** results initialize without a user read.
5. **Given** a stopped worker or a full queue, **When** a business action completes and a view is opened, **Then** the action remains independent and the last completed data is returned as pending/stale.

### User Story 3 - Understand whether displayed results are current (Priority: P2)
Users see when stored results are still updating, unavailable, or failed. They can distinguish stored results from live application screens and parameterized questions.
**Independent Test**: Exercise initial, ready, pending, failed and recovered responses in the Inspector and affected operational screens.
**Acceptance Scenarios**:
1. **Given** an uninitialized projection, **When** it is opened, **Then** it is shown as awaiting calculation, not a confirmed empty business result.
2. **Given** older completed results, **When** a new event arrives, **Then** those results remain visible with their completed time and an update notice until refreshed.
3. **Given** processing failure, **When** the screen is refreshed, **Then** it reports failure/staleness without revealing internal errors or implying that the business action failed.
4. **Given** time-sensitive obligations, **When** time passes without an event, **Then** their stored risk/overdue observations are refreshed through the shared scheduling mechanism.

### Edge Cases
Unknown events conservatively invalidate rather than silently leaving fresh-looking data. Archived companies are not processed. Cache upkeep does not impersonate a user or grant business permissions. Queue saturation, final failure and uncertain execution retain observable state. Cold deployment, builder changes and deletion of disposable caches recover through the same path. Views with live rows and cached totals must not silently combine different states. Price answers validate current inputs and time rather than relying on an old cached result. Read-only MCP contracts keep their existing live consistency guarantee.

## Requirements

### Functional Requirements
- **FR-001**: Reuse validated global catalog definitions for the running application version, with uncached validation still available to build/verification tooling. Failed construction is retryable and callers cannot corrupt the cached definition.
- **FR-002**: Render collapsed directory details on demand while preserving full-definition search, counts, accessible native disclosure, links and tenant admission.
- **FR-003**: Durable committed events MUST drive background refresh independently of browser activity; coalesce events and refresh only affected stored projections, with conservative handling of unknown dependencies.
- **FR-004**: Use the shared scheduler, queue, allowlisted job registry and worker with tenant scope, bounded work, existing retry/claim protection and queue backpressure. Cache upkeep is a database-only infrastructure capability, never user impersonation or business authorization.
- **FR-005**: Publish projection rows and their completed checkpoints atomically from a consistent read state. Concurrency, rollback and retry MUST not lose changes, regress progress or duplicate rows.
- **FR-006**: Stored-projection reads MUST perform no refresh, enqueue, commit or cache write. Keep an explicit rebuild service for maintenance; retain existing response shapes where compatible.
- **FR-007**: Expose per-projection state (`uninitialized`, `ready`, `pending`, `failed`), completed time, processed event sequence and relevant event target. Never label initial missing data as a confirmed empty result. Unknown upstream freshness remains unknown.
- **FR-008**: The Inspector and operational consumers of stored data MUST display pending/failure state, retain prior results, and support read-only refresh. Rows and totals in one response MUST use the same completed snapshot or remain wholly live.
- **FR-009**: Initialize new/existing companies and rebuild outdated/missing caches without a read. Time-sensitive stored observations MUST become eligible at least once per minute; unchanged non-time-sensitive projections MUST not rebuild on that timer.
- **FR-010**: Pricing MUST use the current canonical parameterized calculation without triggering unrelated projection work. Explicitly live read contracts and authoritative action checks retain their semantics. The directory MUST explain these distinctions.
- **FR-011**: Cover the change with test-first service, PostgreSQL concurrency, migration, HTTP and browser proofs; regenerate executable reference documentation and run applicable complete quality gates.

### Key Entities
- Business Event: existing immutable tenant-local outbox and committed change marker.
- Projection row/checkpoint: existing disposable result and completed processing position, never business authority.
- Scheduled job run: existing durable execution identity, frozen configuration, claim and retry state; infrastructure execution needs to be distinguishable from a user-authorized job.

## Success Criteria

### Measurable Outcomes
- **SC-001**: Warm directory metadata reads are at least 80% faster than the measured repeated-build baseline, and unopened detail bodies are absent from the rendered page.
- **SC-002**: All stored-projection read proofs complete with builders and writes forbidden; repeated committed events are coalesced into bounded work.
- **SC-003**: Under an available, idle scheduler/worker and the representative test dataset, committed changes become visible within 30 seconds; time-only changes within 90 seconds. These are healthy-path targets, not promises during outage or overload.
- **SC-004**: Every tested interruption, rollback, concurrent writer and cross-tenant request preserves authority and correct progress; missing/old/failed results are never presented as current.

## Assumptions and Dependencies
The owner's instruction accepts the product scope above and sequential implementation. The owner explicitly approved the concrete internal-job schema in data-model.md on 2026-09-12, satisfying the separate human schema-approval gate. Existing scheduling contract (spec147), company setup boundaries (spec146), Home health (spec149), ADR0004 and docs/WEB_SPEC.md remain dependencies. No production deployment is included. Explicit live v2 MCP reads and parameterized calculations remain available. UTC is the internal clock. The browser does not run background business work.

## Requirement Traceability

All repository content and implementation artifacts use English. Conversation may remain German.

| Requirement | Acceptance story | Planned evidence |
|---|---|---|
| FR-001 | US1.1, US1.3 | Runtime cache identity, retry, mutation-isolation and timing tests |
| FR-002 | US1.2 | Inspector disclosure/search browser proof |
| FR-003 | US2.1, US2.2 | Outbox/coalescing/dependency and rollback tests |
| FR-004 | US2.3, US2.5 | Registry/authorization/capacity and PostgreSQL queue tests |
| FR-005 | US2.3 | Concurrent snapshot publication, retry and stale-claim tests |
| FR-006 | US2.5 | HTTP/service builders-and-writes-forbidden tests |
| FR-007 | US3.1–3 | Metadata/initial/stale/failure/recovery tests |
| FR-008 | US3.1–3 | Browser freshness and consistent rows/totals tests |
| FR-009 | US2.4, US3.4 | Bootstrap/version/clock tests |
| FR-010 | US3 | Pricing/live MCP regression and directory mode tests |
| FR-011 | All | Complete applicable gates and final diff review |

## Documentation clarification (2026-09-12)

FR-010 and FR-011 also cover a visible calculation-mode label per concrete read in the English and German public reference and interactive explorer. Explain stored snapshots, live reads and parameterized live calculations, event-driven/background refresh, time-only refresh, initial/pending/failed state and unknown upstream freshness. Distinguish default MCP page reads from explicit legacy reads and catalog projection reads from operational Web reads. A projection's name or catalog kind must not imply the mode of every consumer. This clarifies documentation of existing behavior; no read execution or schema changes.

Acceptance: every projection and catalog view has a concrete read path and mode; all read-only MCP tools have mode guidance; inventory default MCP page/live versus legacy/stored and Web stock/live are explicit; financial stored open items and live credit/balance paths are distinct; parameterized price resolution is never labeled stored. The generator, JSON explorer data and both language pages must agree.
