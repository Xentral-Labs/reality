# Feature Specification: Home activity and readiness

**Created**: 2026-09-09
**Status**: Implemented and verified locally
**Language**: English

## Context and Intent
### Problem
Home is static and gives users little sense of recorded activity or whether background services are available.
### Scope
A readable company activity line and plain-language readiness for the connection, scheduler and worker.
### Non-Goals
No monitoring platform, uptime history, automatic business actions, invented events, new business persistence, Docker socket access, or claim that all integrations/jobs are successful.
### Existing Contracts
[Web](../../docs/WEB_SPEC.md), [scheduled work](../../docs/features/scheduled-jobs.md), existing timeline/Inspector and spec 147 process boundaries.

## User Scenarios & Testing
### US1 — See what happened (P1)
Home displays the newest recorded company events with actual recording time, business context and a details action. New events appear automatically while visible. Older activity remains available through the existing Activity view.
Acceptance: new recorded event appears once within one refresh interval; empty history is explicit; failed refresh preserves rows and marks stale; changing company cannot show old-company responses.
### US2 — Know the system is ready (P1)
Home shows Connection, Automatic scheduling and Background processing using user-facing labels. A combined ready state requires positive evidence from every displayed component.
Acceptance: a successful idle scheduler/worker sweep is ready; never-started, stale, failed or unreachable processes are not ready; absent configuration is unknown. A failed Home status read never preserves a green overall claim.

## Requirements
- **FR-001**: Show latest 20 held events, newest recorded sequence first, with recorded timestamps, existing business titles/context and Inspector links. No synthetic activity or inferred history.
- **FR-002**: Refresh activity and readiness every 10 seconds only while visible, avoid overlapping reads, retain stale rows, and discard old-company responses. A control opens existing fuller activity history. Keep previous business rules and confirmation.
- **FR-003**: Show nontechnical readiness for API/database connection, scheduler and worker; all-ready only when all are positively verified. Unknown/unavailable/checking states are explicit and never green. Do not imply job success or external connector health.
- **FR-004**: Each background process optionally serves a minimal internal readiness read based on completed loop sweeps. Starting, failed, stopped and >90-second stale sweeps are not ready. The health request does not run jobs or migrate/write the database.
- **FR-005**: API reads only operator-configured bounded health URLs with timeouts; return no URLs, credentials, exceptions, tenant lists or job payloads. Tenant admission still guards Home reads.
- **FR-006**: Document portable container/private-network configuration and disabled/unconfigured behavior. No schema migration or new broker.
- **FR-007**: Support four languages, both themes, mobile, keyboard and accessible status; polling must not disrupt reading or focus.
- **DR-001**: Existing BusinessEvents and shortest Inspector links preserve Source → Evidence → Reality; readiness is volatile infrastructure observation, not business authority.
- **DR-002**: Timeline remains tenant-scoped and read-only; no writes are authorized by viewing Home.

## Success Criteria
- **SC-001**: Newly recorded activity appears within 10 seconds plus read latency while Home is visible.
- **SC-002**: No tested unknown/stale/unreachable component produces all-ready.
- **SC-003**: Existing company creation, business reads and scheduler/worker tests remain green.

## Assumptions and Dependencies
Use the existing timeline projection/Activity drawer. Readiness covers the three named components, not every third-party integration. A successful loop, including an idle loop, proves availability; a failed business job does not itself mean the worker is down. Optional private HTTP probes avoid new database writes and work across containers. Feature number149 avoids148 already present in the root checkout; next_feature_number.py there returns149.

## Open Questions
None. User requested both features; bounded implementation stays within that scope.

## Requirement Traceability
FR001/002/007/DR001/002 → T003/T004/T005. FR003/004/005/006 → T001/T002/T004/T005. SC001–003 → T005.

## Approved activity graph refinement
The owner approved replacing the default event list with a right-to-left rolling
activity graph on 2026-09-09. This supersedes FR-001's default list presentation;
event inspection and fuller history remain available.
- **FR-008**: Default to a rolling24-hour graph, with24-hour/7-day/30-day selection.
  UTC-aligned30-minute source buckets count distinct new orders (sales/purchase
  documents), new reservations, stock movements and other recorded documents.
  Source receipt/processing and commitment creation do not multiply an imported order.
  Counts measure recorded entities, never quantities, money or successful jobs.
- **FR-009**: Aggregate adjacent buckets only for available display width, summing
  counts and exposing the displayed interval. Time moves right-to-left even with no
  activity; zero means no counted records during a successfully read interval.
  Pre-company time and failed/unobserved time are gaps, never inferred zeroes.
  Preserve stale history and label it; no fabricated samples or persisted analytics.
- **FR-010**: Hover/focus/click shows actual interval and category counts; click opens
  bounded matching underlying recorded events with existing Inspector links. Data
  queries are tenant-scoped, use recording time and half-open intervals; results are
  complete aggregates rather than the first20 events. Latest partial bucket is explicit.
- **FR-011**: Compact service status above the graph retains existing honest readiness.
  Poll every10seconds while visible, abort stale requests, reset selection on range/
  company changes, preserve keyboard focus. Four languages, both themes and mobile.

FR-011 hover stability correction: the activity summary must retain the same height
when switching between its hint and any hovered/focused bar. Both presentations
share an intrinsically sized layout so surrounding content does not jump; narrow
screens and translations remain readable without clipping.


FR-012 — Remember the Home time range per authenticated user in this browser. Choices are 1, 7 and 30 days; absent, invalid or inaccessible storage falls back to 1 day. Explicit selection persists across reloads, navigation and company changes, never to another user's key. Storage failures must not prevent switching. Browser-local preference only; device synchronization is out of scope. Approved by the owner's 2026-09-09 request.


## Approved Home and navigation naming refinement
- **FR-013**: Daily work lists Home, Commitments, Exceptions, Decisions in that order.
  Home cards use the same three category labels. German UI labels are the localized
  equivalents of obligations, deviations and decisions, as approved in conversation.
  Each card shows a localized lowercase open qualifier below its existing count.
- **FR-014**: Matching navigation and cards use one destination definition: commitments
  opens existing open customer deliveries, exceptions opens the unfiltered attention
  view, and decisions opens existing decisions. Clear stale search/detail filters;
  preserve company context. No new route, count, business logic or schema.
Acceptance: compare English and German menu/cards, including zero counts; follow each
card/menu link after a previously filtered view and verify equal target selections.
Product review: owner approved the exact naming and addition on 2026-09-09; no open
clarifications. Other languages use the existing localization contract.

FR-015: Home renders its work overview, metric cards and activity in their final order before dashboard data arrives. Unknown totals use loading placeholders, never zero. Dashboard failure preserves activity access and exposes retry.
