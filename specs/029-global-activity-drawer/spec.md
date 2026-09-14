# Feature Specification: Global Activity Drawer

**Created**: 2026-09-02
**Status**: Approved
**Language**: English

## Context and Intent

Operators need a fast, page-independent view of recent tenant activity without leaving their current task.

### Non-Goals

- Replacing or removing the existing Activity/Timeline page. The drawer is a
  page-independent companion for recent activity; the page remains the surface for
  filtering, KPIs, and the hourly chart over a chosen window.
- Cursor or offset paging through activity history. The timeline event stream returns
  only the newest bounded result set, as recorded in the large-tenant read contract in
  `docs/WEB_SPEC.md`. Real paging requires a separate specified read contract.
- Raising the timeline window beyond the 30 days the endpoint and service already
  support.
- Any new activity derivation, projection, schema field, or mutation.
- Notifications, unread state, or per-user activity acknowledgement.

## User Scenarios & Testing

### User Story 1 - Review recent activity (Priority: P1)

As an operator, I can open a right-side activity drawer from any workspace page and scroll through recent events.

**Acceptance Scenarios**:

1. **Given** an active tenant, **When** the activity control is selected, **Then** a tenant-scoped feed opens without navigation.
2. **Given** the feed is open, **When** the user filters or reaches its end, **Then** the same timeline service returns filtered or older activity.
3. **Given** an activity, **When** it is selected, **Then** its subject opens in the Reality Inspector.

## Requirements

- **FR-001**: A global activity control MUST be available on desktop and mobile.
- **FR-002**: The drawer MUST use the existing tenant-scoped timeline API.
- **FR-003**: The feed MUST distinguish attention events and support area filters.
- **FR-004**: Scrolling or explicit loading MUST widen the requested time range up to
  the timeline endpoint's declared maximum of 720 hours (30 days) and MUST NOT request
  a wider range. Each widening re-reads the same bounded newest result set; the drawer
  MUST NOT claim to page through older activity beyond that bound.
- **FR-005**: Activity selection MUST delegate to the existing Reality Inspector.
- **FR-006**: Escape, backdrop, and close controls MUST dismiss the drawer.
- **FR-007**: Global controls MUST occupy reserved existing shell chrome, MUST NOT float over page content, and MUST NOT add a new page-wide bar.

## Assumptions and Dependencies

- `GET /api/tenants/{tenant_id}/timeline` remains the single tenant-scoped activity
  read path, with `hours` bounded to 720 and `limit` defaulting to 100 newest
  activities. The drawer sends no `limit` and therefore inherits that default.
- Because the result set is bounded to the newest activities, a wider window changes
  which events fall inside the range, not how many rows are returned. A tenant with
  more than 100 activities in the current window will see no additional rows from
  widening it.
- The Reality Inspector remains the authoritative subject viewer, addressed by
  `subject_type` and `subject_id` from the first event of the selected activity.
- Localized count phrases rely on the existing `translatedText` pattern list, which
  matches a complete `<count> <noun>` text node.

## Edge Cases

- Empty, loading, and error states remain visible and usable.
- Changing tenant reloads the feed within the current tenant boundary.
- The widening control stops at the endpoint maximum instead of requesting a range
  the API rejects, which would otherwise replace the feed with an error state.

## Success Criteria

- **SC-001**: Recent activity is reachable in one action from every workspace page.
- **SC-002**: Users can widen the feed to the full supported 30-day timeline window
  without leaving the drawer, and the drawer never requests a window the API rejects.
- **SC-003**: Every selectable feed item opens its authoritative subject inspector.

## Requirement Traceability

| Requirement | Evidence |
|---|---|
| FR-001–FR-006 | Frontend contract, production build, desktop/mobile review |
| FR-007 | Existing-shell collision regression and responsive review |

No schema, domain rule, mutation, or alternative activity derivation is introduced.
