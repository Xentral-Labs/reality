# Feature Specification: Incremental Business performance

**Feature Branch**: `feat/business-performance-projections`
**Created**: 2026-10-06
**Status**: Implementation authorized by the user's explicit request; merge requires review
**Language**: English
**Input**: Production read models for Activities → Business, following PR #377.

## Context and Intent

### Problem
Every dashboard viewer currently re-derives the company's complete order history every five seconds. Correspondence counts repeatedly search source JSON and reply relationships. Work grows with history and viewers, and calculation time is mistaken for processing freshness.

### Scope
Incremental, disposable order and correspondence projections, shared scheduler/worker upkeep, indexed filtered detail pagination, processing visibility, independent reconciliation and measured synthetic load evidence. Preserve all dashboard sections, metric definitions, reply history and Inspector references.

### Non-Goals
Production deployment, actual company data changes, a second booking/readiness implementation, transport delivery claims, new scheduling infrastructure, billion-scale claims, automatic business actions.

### Existing Contracts
`docs/features/scheduled-jobs.md`, `docs/WEB_SPEC.md`, `docs/DATA_MODEL.md`, `docs/TEST_STRATEGY.md`, specs 179/181/241 and 376. Reality remains the authority; caches never authorize a shipment or booking.

## User Scenarios & Testing

### User Story 1 - Read explainable company metrics (Priority: P1)
An owner opens Business and sees the same quantities and matching orders without a history calculation on each read.
**Independent Test**: Compare counters, duration samples and full filtered cohorts with the unchanged `services/business_performance.py` reference.
**Acceptance Scenarios**:
1. Given open, reserved, held, partial, complete and cancelled orders, when processed, then counters and detail identities match the reference.
2. Given corrections, quantity revisions, payment changes and stock blocks, when processed, then all affected orders use shared commitment terms and readiness rules.
3. Given a deadline with no new booking, when time passes, then risk, overdue and hourly cohorts change through worker processing.

### User Story 2 - Read actual correspondence (Priority: P1)
An owner inspects incoming, waiting and outgoing messages and their exact requests/replies.
**Independent Test**: Compare full mail cohorts and retained reply content to the reference.
**Acceptance Scenarios**:
1. Given acknowledgement only, waiting remains unchanged while unread decreases.
2. Given an exact reply, waiting decreases once and request/reply links remain present outside the current page.
3. Given ordinary provider mail, missing read/work-completion evidence stays unknown. A reply is neither completed work nor verified delivery.

### User Story 3 - Recover and observe processing (Priority: P1)
An owner sees explicitly delayed data and operators can rebuild after cache loss without affecting business writes.
**Independent Test**: Real PostgreSQL replay, restart, concurrent mutation and rebuild tests.
**Acceptance Scenarios**:
1. Given duplicate or delayed events, replay converges with no doubled contributions.
2. Given worker rollback/restart or concurrent writes during rebuild, durable progress resumes and subsequent processing includes every committed change.
3. Given a rebuild, the last published generation remains readable until replacement; initial bootstrap reports unavailable progress rather than claiming complete zero counts.
4. Given another tenant or revoked membership, reads do not disclose data; reads never enqueue or write.

### Edge Cases
Fully cancelled orders; source-less orders; corrected shipments on another commitment; item/location/party/payment fan-out; receipt after dispatch; multiple due dates; late reply before request processing; unknown event types; stale pages; empty tenants; failed shared jobs; cache generation cleanup.

## Requirements

### Functional Requirements
- **FR-001**: Preserve every existing order count, open quantity, dispatch sample/average, hourly cohort and detail trace; compute from shared Reality readers in the worker.
- **FR-002**: Recompute affected entities from current Reality, replacing their contributions atomically; event replay must not increment effects twice. Large scopes must progress in bounded durable chunks.
- **FR-003**: Process clock transitions for risk/overdue and hourly membership without a new event; normal-load lag target is below ten seconds.
- **FR-004**: Preserve incoming/outgoing/waiting/unread definitions, original/reply content and exact Source identity. Expose read acknowledgement separately; work completion remains unknown without evidence.
- **FR-005**: Filter on the server before limits; paginate orders and mail using deterministic tenant/generation-bound cursors, indexed cohort and ordering fields, and bounded page sizes.
- **FR-006**: Return/display processed and target sequence, completion time, rebuild progress and explicit delayed/unavailable/failed state. A read must not rebuild/enqueue/write. Preserve stale snapshots on network failure.
- **FR-007**: Rebuild disposable generations through the existing shared projection job, preserve the published generation while building, resume durable cursors after restart and catch committed writes made during rebuild.
- **FR-008**: Keep the previous full calculation unchanged as an independent oracle; compare every counter and matching detail cohort in synthetic business stories and recovery tests.
- **FR-009**: Document/run reproducible synthetic measurements with hardware, distribution, booking rate and 100 viewers; plan one million orders in one tenant plus multiple active tenants. Report actual p95 and lag against provisional 500 ms/10 s goals and limitations.

### Domain and Traceability Requirements
- **DR-001**: Preserve Source → Document/Line → Commitment/Reservation/Movement and shortest Inspector links; projections are disposable observations, never business authority.
- **DR-002**: Retain owner API authorization and tenant scope in every cache and Reality query, cursor and worker transaction.
- **DR-003**: Reuse canonical commitment terms and `_open_work_rows`; use `projections.refresh` and its claim fencing, transaction boundaries, deadlines and tenant fairness.

### Key Entities
Order observation (document identity, flags, timing, contributions); correspondence observation (source identity, direction, waiting/read evidence, reply lineage); published generation and resumable processing checkpoint.

## Success Criteria
- **SC-001**: Zero counter/cohort discrepancies against the unchanged oracle for all recorded acceptance fixtures.
- **SC-002**: Duplicate delivery/restart/concurrent rebuild tests show no missing identities or doubled contributions.
- **SC-003**: Dashboard reads perform no complete Reality order/mail scan and no writes; first and subsequent filtered pages cover the matching cohorts exactly.
- **SC-004**: Measured API p95 and processing lag include workload/hardware; provisional targets are p95 <500 ms and lag <10 seconds in normal load. An unmet target remains an explicit open acceptance item.
- **SC-005**: Required spec, backend, migration, lint, web/localization and applicable browser checks are reported truthfully, with no red item marked complete.

## Assumptions and Dependencies
PR #377 was merged at 2026-10-06T06:34:42Z, merge commit `4a4dec95a846180ee72df4793d04e73124c008ec`. This branch starts at that merged main. No unmerged dependency remains. The user's request authorizes this scope and the necessary additive disposable-cache schema; final PR review is still required. Business writes use the existing tenant-serialized committed event sequence. Synthetic local databases only; shared deployment remains unchanged.

## Requirement Traceability
| Requirement | Scenarios | Planned proof |
|---|---|---|
| FR-001, FR-002, DR-001, DR-003 | US1.1-2, US3.1-2 | `tests/test_business_projection.py` oracle, replay and correction tests |
| FR-003 | US1.3 | clock-only transitions |
| FR-004 | US2.1-3 | mail acknowledgement/reply/lineage |
| FR-005, DR-002 | US1.1, US3.4 | indexed pages, invalid/foreign cursor and owner API tests |
| FR-006 | US3.3-4 | cold/stale/failed/read-only/API/UI tests |
| FR-007 | US3.2-3 | restart, bounded rebuild, concurrent commits |
| FR-008 | US1/US2/US3 | independent full reference comparison |
| FR-009 | SC-004 | synthetic benchmark and documented million-order plan |

### Main compatibility reconciliation — 2026-10-07
The feature is rebased onto `fcb1d0bb` without expanding product scope. Main already allocated spec 378 to the enterprise cockpit and migration 0146 to shipping inputs. This feature now owns spec 380 and migration `0147_business_performance`, directly following `0146_shipping_plan_inputs`. Business downgrade removes only its derived caches and retains source-backed shipping-plan tables. Both catalog/service families and all translations remain present.
