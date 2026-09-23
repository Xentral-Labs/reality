# Feature Specification: Inbox decision badge

**Feature Branch**: `253-inbox-decision-badge`
**Language**: English
**Created**: 2026-09-23
**Status**: Approved
**Input**: Show a counter badge on the Inbox navigation entry with the number of pending decisions, without a performance cost. Keep the Decisions tab count visible from the other Inbox tabs.

## Context and Intent
### Problem
Pending decisions wait silently in the Inbox's Decisions tab. Nothing in the navigation tells a person that approvals are waiting unless they open the Inbox.
### Scope
A count badge on the Inbox sidebar entry, showing the number of change proposals awaiting a decision in the current company, and the same count next to the Decisions tab while another Inbox tab is open.
This supersedes spec 225 FR-013 in two places, by the owner's decision: the Inbox entry carries a badge (a single queue, not an aggregate of all three), and the Decisions tab states its count while inactive.
### Non-Goals
No new API, service, index or schema; no push channel; no badge on other entries; no change to the Decisions register itself. Always-visible counts for the Commitments and Exceptions tabs, or for tabs of other registers, are out of scope here and specified in spec 254 (work counts on workspace tabs).

## User Scenarios & Testing
### User Story 1 — See that decisions are waiting (P1)
A person working anywhere in the app sees how many decisions await them next to Inbox, and the number follows when they approve, reject or when new proposals arrive.
Acceptance: with three pending decisions the Inbox entry shows 3, and the Decisions tab shows 3 while Exceptions or Commitments is open; with none it shows no badge; more than 99 shows 99+. Approving or rejecting a proposal updates the badge without reload. Switching companies shows the other company's count. The collapsed rail still shows the count on the icon. The accessible name of the entry includes the count in all supported languages.

## Requirements
- **FR-001**: The Inbox navigation entry shows the pending-decision count taken from the same decision queue count the Decisions register pages (`GET /change-proposals?status=pending`, `page.total`); the badge never computes its own rule.
- **FR-002**: The badge is absent when the count is zero or unknown (still loading, request failed); counts above 99 read 99+.
- **FR-003**: The count is read with a page size of one, once on company change, when the tab becomes visible again, at most once a minute while visible, and immediately after an approval, rejection or chat message in this browser. Hidden tabs do not poll.
- **FR-004**: The entry's accessible description and tooltip state the count; collapsed navigation keeps the badge visible on the icon.
- **FR-005**: While another Inbox tab is open, the Decisions tab shows the same count in the header count style. The open Decisions tab shows only its own register count.

## Assumptions and Dependencies
The existing count uses the tenant index on `action` and measures 1–2 ms on the largest local tenants. Searches and previews sent as POST do not count as writes. A partial index on `status = 'proposed'` is a follow-up only if tenants grow to very large action histories. Existing translations of "Pending decisions" are reused.

## Success Criteria
A person sees waiting decisions from any page. The badge adds one small read per minute per visible tab and no extra work on the server beyond the query the Decisions register already runs.

## Requirement Traceability
FR-001–005 → US1 → T002–T004. Verified by `apps/web/scripts/inbox-decision-badge-browser.mjs`, `apps/web/scripts/pending-decisions.test.mjs`, frontend build, i18n audit and a live check against the local stack.
