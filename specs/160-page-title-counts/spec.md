# Feature Specification: Consistent Page Headers

**Language**: English

**Created**: 2026-09-10
**Status**: Approved compact-header refinement
**Input**: Show main-list totals beside the page title consistently with Commitments.

## Context and Intent

Operators currently find the same kind of list total in different places. The owner approved moving register totals to the title after reviewing the page inventory.

### Scope
Sales/Purchasing, Warehouse, Finance, master data, data sources, Inspector records/Facts, Fact rules, exception rules and catalogs. Existing daily-work title counts remain unchanged.

### Non-Goals
No new counts for dashboards, detail pages or activity timelines; no changes to counting, APIs, business data, permissions or pagination. Category, report-detail and nested-list counts remain local.

## User Scenarios & Testing

### User Story 1 — Find the list total (Priority: P1)
An operator opens a register and reads its total beside the page title.

Acceptance: A filtered list of 37 records shows one title badge with 37 and no count line above the table. A zero-result list shows 0. The total describes all matching results, not only the current page.

### User Story 2 — Navigate without mixing totals (Priority: P1)
An operator changes a tab, filter or company and sees the total belonging to the displayed results. Opening a nested technical list does not add a second page badge or replace the main total.

Acceptance: Loaded tab/filter results update the title total; failed reads do not present an invented zero. A page without a main list has no leftover badge. Nested counts and catalog categories retain their local meaning.

## Requirements

- **FR-001**: Show existing main-register totals beside the page title with the same badge appearance as daily work.
- **FR-002**: Remove the duplicate count line above main-register tables.
- **FR-003**: Preserve original total/filter/pagination meaning, localized numbers, explicit zero, loading/error behavior and cleanup on navigation.
- **FR-004**: Keep nested catalogs and standalone surfaces local; opening one must not overwrite or duplicate a main-list title total.

## Assumptions and Dependencies
Existing services already provide authoritative totals. The current table and count continue sharing the same read result. Owner approval is the latest affirmative reply; no clarification remains.

## Success Criteria
Every covered register displays exactly one main total beside its title after loading. No covered register retains an above-table duplicate. Nested list opening preserves the main total, and narrow screens retain readable headings.

## Requirement Traceability

| Requirements | Scenario | Tasks | Proof |
|---|---|---|---|
| FR-001–002 | US1 | T002–T004 | page-title-counts-browser.mjs register matrix |
| FR-003 | US2 | T002–T004 | zero, tab and navigation checks |
| FR-004 | US2 | T002–T004 | nested technical catalog check |

## Approved page-tab refinement

The owner approved using the Commitments navigation pattern consistently.

- **FR-005**: Sales, Purchasing, Warehouse, Finance, Master data, Integrations and the four Inspector sections place their existing view tabs between the page introduction and content. Use compact text tabs, an accent underline and a shared separator; preserve labels and selection behavior.
- **FR-006**: The global header contains global controls; the content introduction provides the single visible page heading. Tab strips scroll horizontally on narrow screens without widening the page. Pages without tabs reserve no tab space. Existing Commitments direction badges remain unchanged; no new count queries are added.

Acceptance: Every tabbed destination places exactly one strip below its introduction, with no tabs in the global header; tab clicks still change URL, selected state and list count. Mobile navigation keeps every tab reachable, and routes without tabs show no stale strip.

| Requirements | Scenario | Tasks | Proof |
|---|---|---|---|
| FR-005–006 | Consistent view navigation | T006–T008 | page-introduction-browser.mjs and page-title-counts-browser.mjs |

## Approved single-row header refinement

FR-007 supersedes the earlier placement of the introduction card: the owner approved moving its title, count, description and page actions into the existing top row. The card is removed. Tabs remain immediately above page content.

- **FR-007**: Keep the global header at a compact 60px on desktop and narrow screens; show a single title with its count there and remove the large introduction card.
- **FR-008**: Show the localized description at all times as a compact second line. Keep the title count visually subordinate and separated from that description. Long titles and descriptions may truncate visually but remain available in full through native accessible text.
- **FR-009**: Keep page actions, company switching and global controls accessible; compact them into an overflow menu when width is insufficient. No duplicate action instances, new queries or navigation changes.

Acceptance: At 390px and 1440px the header remains 60px without horizontal overflow; the description is visible without interaction; compact controls expose page actions, company switching and global actions; view tabs and current totals continue working.
All main header counts, including Daily work counts, use the same compact superscript badge geometry: a single digit may appear circular, while longer values expand horizontally with fixed padding. Counts inside tabs retain their smaller tab-local meaning and placement.

| Requirements | Scenario | Tasks | Proof |
|---|---|---|---|
| FR-007–009 | Single-row page context | T009–T011 | page-introduction-browser.mjs; page-title-counts-browser.mjs; register-footer-browser.mjs |
