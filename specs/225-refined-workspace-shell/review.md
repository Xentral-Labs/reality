# Requirements analysis and implementation review

## Pre-implementation analysis (2026-09-17)
Seven functional requirements, nine ordered tasks, 100% requirement coverage.
No unresolved clarifications, duplicate requirements, constitutional conflicts or
critical/high findings. The owner approved the scope through the concept and the
instruction to implement in a worktree. Both requirements-quality checklists passed.
No extension hooks were registered. Domain, services and tools need no changes.

| Requirements | Implementation tasks | Acceptance proof |
|---|---|---|
| FR-001/002 | T005 | Shell placement, aligned headers, description and count tests |
| FR-003/004 | T006 | Activity, actions, profile, simulation state/tenant tests |
| FR-005/006/007 | T005/T007 | Rail/mobile matrix, persistence, keyboard and touch |

## Implementation review

- Existing components retain identity while the grid changes; company-keyed chat,
  action launcher and activity handling preserve tenant boundaries.
- Company, description and action popovers use the top layer; resizing dismisses
  them rather than leaving stale off-screen anchors. Sidebar utilities do not scroll
  away with navigation links. Mobile drawer dismissal restores opener focus.
- Removed HeaderControls and its obsolete global-header CSS. The only ActionLauncher
  placement now uses its existing catalog in the sidebar, without a second menu path.
- Existing route names, original business labels, theme storage and simulation
  polling/eligibility remain unchanged. No business source or data-model edits.
- The shell acceptance entrypoint now delegates to the consolidated spec225 browser
  suite; legacy action-form browser selectors point to the new launcher button.
- Older page-introduction fixtures needed explicit company context to avoid the
  unrelated automatic trial entry. The action-discovery launcher-only mode preserves
  old finance-toolbar checks while testing this feature independently of their stale
  primary-button assumptions; current package actions are reflected in expectations.
- The title-count test uses keyboard activation for the lower technical disclosure,
  avoiding pointer interception by the existing fixed register footer. Its count,
  filter, paging and mobile assertions remain intact.

Final gate results and screenshot inspection are recorded in verification.md.

## Activities consolidation review (2026-09-17)
FR-008 is covered by T010–T012. Requirement review and Constitution Check passed
before implementation; no unresolved clarifications or critical findings. The
navigation contract failed on the old Event history label before the change and
passed afterwards. Removed the Shell import, state, reset effect, trigger and drawer
instance. There is no backend exclusive to this entry: tenant_timeline/timeline_activity
and ActivityDrawer also serve the Inspector, Home, graph and projection consumers.
These remain; the shared drawer browser now enters through Home and verifies retained
page selection, focus, paging, retry, stale responses and tenant isolation.
The history route and localization of unrelated graph event history remain unchanged.
German desktop screenshot confirms one Activities destination and only Actions/Profile
in the utility area. No additional business rules, writes or dependencies.

## Action translation regression review
FR-007 restoration uses existing `t(entry.label)` calls. All five reported labels
were absent from German, Dutch and Spanish dictionaries; canonical English fallback
worked as designed. The source-only localization audit did not enumerate labels
loaded from the backend discovery JSON. The new regression reads that executable
catalog directly, covering categories, groups and entries in all three dictionaries.
Observed the five missing keys in each language before adding translations. No
business payloads, catalog definitions, APIs or action execution paths were changed.
Browser search assertions cover translated package labels, excluding the permanent
catalog shortcut from filtered action results. No unresolved review findings.

## Command palette review
FR-009/T016–T018 stay within the requested presentation/shortcut scope. The launcher
uses the existing permitted global discovery entries, grouping, translated search,
forms and catalog destination; no command, service or business behavior was added.
The initial placement assertion failed before implementation. Browser evidence now
covers both modifier shortcuts, focused/cleared search, centered geometry, Escape
restoration, mobile access with closed navigation and precedence of open forms.
The native popover is portaled to document.body to escape hidden mobile navigation.
Listener cleanup follows the company-keyed launcher lifetime. Resize dismissal and
pointer/touch entry remain. Shortcut notation is an explicit localization invariant;
German Control-key notation uses Strg. Inspected desktop and mobile screenshots:
compact company-area search, quiet backdrop, bounded list and no lower Actions item.
No unresolved review findings; richer palette capabilities remain out of scope.

## Quiet shell boundaries review
FR-010/T019–T020: four decorative border declarations removed. The active tab's
2px indicator and chat dock's subtle border-left remain. No selectors, sizes,
focus indicators, content separators or business logic changed. The existing
responsive shell browser and full frontend gates are sufficient for this CSS-only
change; no new implementation-mirroring unit test was added.

## Sidebar head grouping review
FR-011/T021–T023 follow the approved grouping. Logo is inside the company-switcher
button; the separate redundant logo home link is removed, with Home retained as the
first navigation link. Collapse moves beside the company switcher; the rail stacks
it below without losing company access. Search uses existing translated Search copy
with the explicit Search actions accessible name. Daily work remains an accessible
landmark. Removed obsolete heading/initial styles. No service, route, permission or
simulation changes. Placement contracts failed before implementation and pass now.
Desktop and rail screenshots reviewed: aligned controls, truncated long names, compact
context, visible search field and no redundant visible heading. Browser coverage
confirms company switching, draft persistence, focus, mobile and coarse-pointer targets.

## Unified tab header review
FR-012/T024–T026 implement one header via existing shared portals. Multiple direct
register tab controls select tab-header mode; pages without them keep their title.
Tab controls retain their identity and accessible names; count is a separate adjacent
portal, avoiding duplicate labels or additional read paths. The accessible heading
and information disclosure remain. Actions sit outside the tab overflow container.
Horizontal visibility adjustment observes the strip/count and changes only scrollLeft,
never page position. Nested integration documents now mark Received data as parent.
No action eligibility, routing, confirmation, data calculation or chat state changes.
The initial header-placement contract failed before implementation. Route/count
browser regressions cover tab changes, title-only transitions and nested documents.
Desktop screenshot confirms the table begins directly below the single header;
mobile uses a compact action icon and retains horizontally scrollable tab labels.
