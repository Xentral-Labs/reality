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
