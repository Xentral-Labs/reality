# Feature Specification: Remove Analytics Overview

**Created**: 2026-09-17
**Language**: English
**Status**: Scope approved by the user request

## Context and Intent

Remove the first Analytics tab, Overview, including its exclusive backend. Explore
and My reports remain. This supersedes the Overview portions of specs 108 and 185.

### Non-Goals

No changes to analytical datasets, private reports, operational reads, business
records, database schema, permissions or confirmation semantics.

## User Scenarios & Testing

### User Story 1 - Open useful analytics directly (Priority: P1)

Given Analytics navigation, a default URL, or a former Overview bookmark, opening
Analytics displays Explore with only Explore and My reports in the tab bar.
Given a saved report link, My reports still opens and can hand a report to Explore.
Given Home, Open analytics opens Explore without requesting removed metrics.

### User Story 2 - Retire exclusive reads (Priority: P1)

Given the former overview HTTP reads, they are no longer registered. The shared
analytics catalog, query, contributor POST and private report APIs remain available.

## Requirements

- **FR-001**: Remove Overview, its cards, activity chart and supporting-record list.
- **FR-002**: Default and legacy Overview/invalid links open Explore; retain company
  context and My reports routing. Stop emitting obsolete days/metric/day parameters.
- **FR-003**: Replace Home's overview metrics preview with its existing Open analytics
  link to Explore; it must not call retired reads.
- **FR-004**: Remove the exclusive company_insights service, GET /analytics and GET
  /analytics/contributors endpoints, their types and client methods. Preserve the
  composable analytics services including POST /analytics/query/contributors and all data.

### Sidebar placement refinement (US1)

Given any supported language and expanded, collapsed or mobile navigation, Analytics
is the final Workspaces link after Master data. No separate Analytics navigation
group remains. The link label, accessible name and collapsed tooltip are exactly
Analytics in every language. Selecting it retains the existing analytics route,
company context, active indication and mobile drawer dismissal.

- **FR-005**: Move the former Reports sidebar link to the end of Workspaces, name
  it Analytics across languages, and remove the standalone Analytics group.
  Page headings, report names, routes and business behavior are unchanged.

## Assumptions and Dependencies

The explicit user removal request authorizes this bounded product change. Home's
metric preview is an Overview entry point and must be simplified to retire its backend.
Existing unrelated workspace edits must be preserved. No unresolved clarifications.

## Success Criteria

Two analytics tabs remain. Default/legacy navigation opens Explore. No production
references to company_insights or the retired GET reads remain. Existing analytics
and company-access regression checks remain green.

## Requirement Traceability

| Requirement | Tasks | Proof |
|---|---|---|
| FR-001 | T001, T003 | Rendered Analytics tab contract |
| FR-002 | T001, T003 | Routing default/legacy/report round trips |
| FR-003 | T001, T003 | Home link and no retired client methods |
| FR-004 | T002, T004 | HTTP retirement and retained analytics suites |

| FR-005 | T006, T007 | Sidebar group/order/label browser assertions across languages and widths |
