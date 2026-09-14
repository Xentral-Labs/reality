# Unified ERP Table Standard

**Language**: English

## Context and Intent
### Problem
Unified registers currently vary in density, width and navigation. The owner approved the supplied ERP table defaults and their use across operational registers.
### Scope
A shared desktop-first table for Orders/deliveries, Warehouse, Finance, master data, Facts and received source/evidence records. Full content width,44px rows/36px compact, sticky headers/key column, bounded widths, single-line values, numeric alignment, row details, configurable persistent columns, useful resizing, header sorting/filter entry and25/50/100 server pages.
### Non-Goals
No change to Home, Analytics, Chat, business semantics, action confirmations, data schema, provider connections, deployment or legacy retirement. Do not manufacture columns to reach a target count. Registered-source system cards and detail views remain contextual presentations.

## User Scenarios & Testing
### US1 — Scan and open a register
At1440–1920px, use all available width, compact scan-friendly rows and7–10 useful columns where held data supports them. Headings stay visible during vertical scrolling; the first column stays visible during horizontal scrolling. Click a row or use its keyboard-accessible details action. Existing actions remain available without triggering the row action twice. Full truncated content remains inspectable.
### US2 — Shape the workspace
Switch44/36px density, hide optional columns and resize useful text columns. Restore defaults. Preferences persist in this browser per signed-in user and register variant, contain no business records and survive corrupt/unavailable storage safely. The key and action columns cannot be hidden. Hidden columns are absent from keyboard navigation.
### US3 — Find records across pages
Choose25/50/100 rows (default50), sort supported columns through their headers and use existing server filters through a header filter entry. Sorting applies to the full tenant-filtered dataset before pagination with deterministic ID ties. Unsupported sorts are rejected rather than silently sorting one page. URL state survives reload; dataset/company/filter changes reset page and incompatible sort context. Complete-result totals remain authoritative.

## Requirements
- **FR-001**: All scoped register surfaces use one reusable table presentation, full content width and semantic HTML. Default44px rows, compact36px,44px header,12px horizontal padding,14px/20px body text; single-line ellipsis. Sticky header and first key column inside the table scroll region.
- **FR-002**: Width defaults use70–100px IDs/status/qty,110–130px dates,100–130px amounts,120–150px document numbers,180–240px parties,220–320px descriptions and40–80px actions. Numbers right, text/date left, actions right. Fewer than7 columns are valid when appropriate. No overview text column exceeds320px after resizing.
- **FR-003**: Row click opens the existing exact detail/case/Inspector; Enter and explicit action remain available. Nested buttons/links preserve their own behavior. Status remains visible without requiring details. Truncated originals remain accessible without translation or HTML execution.
- **FR-004**: Per-user/register browser preferences preserve density, visible columns and widths; validate restored settings, bound widths, retain key/actions and provide reset. No business data is persisted for this feature.
- **FR-005**: Page size25/50/100 is server-side, default50. Allowlisted header sorting uses tenant-scoped SQL before offset/limit with stable ties and existing derived authorities. Filter entry in headers leads to existing server filters; search/filter changes reset page. No client-only dataset sorting/filtering or unbounded fetching.
- **FR-006**: Preserve URL context, tenant isolation, exact source/subject relationships, stored amounts, currency/unit separation, complete-result controls and existing confirmed action flows. No ORM writes or schema changes.
- **FR-007**: Four languages, light/dark,390/1440/1920px, keyboard focus, scroll behavior, empty/error states and persisted settings receive regression coverage. No page overflow; horizontal scrolling stays inside tables.

## Assumptions and Dependencies
The user's “ja” accepts the proposed shared-component implementation and these supplied defaults. Browser-local layout persistence is sufficient; account-wide cross-device sync is not requested. Existing bounded services and Inspector/actions remain authoritative. Row counts are density targets dependent on viewport height and necessary page controls, not fabricated data. Header filter entry can focus the existing typed/global server filter toolbar; only server-supported columns advertise sorting.

## Success Criteria
The same component governs all scoped registers. Backend tests prove sort/page-size correctness beyond the first page and tenant scope. Browser tests prove actual row dimensions, sticky positions, preferences/reload/user separation, keyboard actions, server query state and all register migrations. Full required backend, web, browser, docs and spec gates pass.


## Requirement Traceability
| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 FR-002 | T004 T007 | T005 T006 |
| FR-003 | T004 T007 | T005 T006 |
| FR-004 | T004 T007 | T005 T007 |
| FR-005 FR-006 | T002 T004 | T003 T006 |
| FR-007 | T004 T007 | T005 T006 T007 |
