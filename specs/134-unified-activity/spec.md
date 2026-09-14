# Feature 134: Unified activity drawer

## Context and Intent
### Problem
Operators need to inspect what was recorded after actions across orders, stock and money without leaving their current unified workspace. The retained C1 history capability is still in the legacy UI.
### Scope
A read-only global activity drawer in the unified header, using existing tenant timeline reads and the shared Inspector. Continued migration is authorized by the owner's repeated instruction to continue; this is a bounded part of the retained C1 capability.
### Non-Goals
No unread counter, notifications, polling, action execution, process grouping, derived totals, area filters, new storage, technical explorer replacement or legacy retirement. Historical attention is not a current exception or fulfillment status.

## User Scenarios & Testing
### US1 — Review recent activity (P1)
From any workspace, open Activity, read recorded events and close it without changing the route or losing workspace input. Search, choose 24 hours, 7 days, 30 days or all time, and refresh explicitly. Only the selected company's events appear.
### US2 — Inspect and read older evidence (P1)
Load older events without duplicates, even if related events cross page boundaries. Inspect an event or a supported subject. Technical details preserve exact identifiers and payload. A failed older-page read keeps the already loaded history.

## Requirements
- **FR-001**: Header opens a keyboard-accessible modal side drawer on desktop and mobile. Escape/backdrop/Close dismiss it and restore focus; the route and workspace inputs remain unchanged. Company change dismisses the drawer.
- **FR-002**: Reads use the current company's existing timeline API only, default 24 hours, optional query and attention filter, with windows 24/168/720/0. No mutations or polling occur. Refresh and filter changes reset paging.
- **FR-003**: Show individual events in descending recording sequence, not complete correlated processes. Load older uses the last returned sequence and server has_more; deduplicate IDs. Stale responses after changed filters/company/unmount cannot replace current results. Older-page failures preserve loaded rows and support retry. Empty/loading/error/end states are explicit.
- **FR-004**: Titles and labels are localized in EN/DE/NL/ES for known event types; names/references/quantities retain their original values. Unknown types have an honest server-title/type fallback. Attention marks historical event classification, never current business status. Show recorded time and expose event time; the window applies to event time.
- **FR-005**: Every event opens the shared business_event Inspector. Supported subject families may open their Inspector directly; unsupported types keep event inspection and technical details. Payload renders escaped. Closing the nested Inspector returns to the drawer.
- **FR-006**: Fit 390px mobile and 1440px desktop in both themes with accessible controls and scrolling inside the drawer. Do not claim a loaded event count is a company total.

## Requirement Traceability
US1/FR-001,002: browser opens from work and facts, checks unchanged route/input/focus, filter URLs, refresh and no writes. Company switch resets visibility and rejects stale results.
US2/FR-003: browser pages through split correlations, duplicate IDs, failed older reads, delayed obsolete search, and empty/end/error/retry states. Existing timeline PostgreSQL tests prove cursor and tenant semantics.
US2/FR-004,005: browser checks business context, unknown type, historic attention wording, escaped payload, event/subject Inspector and nested Escape. Localization audit checks every literal label.
US1/FR-006: browser screenshots and overflow assertions in four languages, two themes and two viewport sizes.

## Edge Cases
Backdated events are ordered by recording sequence; occurrence window does not imply occurrence ordering. New events require refresh. A correlated action may span pages. Empty page with has_more cannot spin indefinitely. No events or unsupported subject types remain understandable. Unknown event titles may retain server language.

## Assumptions and Dependencies
**Language**: English. Existing timeline_activity enforces tenant scope and bounded cursor paging. Existing Inspector supports business_event and an explicit subset of subject families. Original business text is never machine-translated. Specs 029, 061 and 070 describe legacy history; this specification replaces only their navigation/presentation rules in the unified app.

## Success Criteria
All six FR have executable browser coverage; existing timeline tests and required repository gates remain green. No shared business data is changed during verification.
