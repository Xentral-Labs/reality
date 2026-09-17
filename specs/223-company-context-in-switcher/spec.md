# Feature Specification: Company Context in the Switcher

**Created**: 2026-09-17
**Language**: English
**Status**: Scope approved by the user request

## Context and Intent

The Company navigation group carried four entries: Integrations, Companies, Storyline
and Demo Data. Two of them do not belong there. Companies repeats the company list that
the switcher beside the wordmark already shows, so the same list is offered twice in one
screen. Demo Data names a mechanism rather than a destination, and the header already
carries a live indicator that opens the same route.

Company context moves to the company switcher, and the simulation is presented where it
belongs: among the systems that feed records into the company. This supersedes the
Companies navigation entry and spec 146 FR-029's Demo Data navigation entry.

### Non-Goals

No change to company creation, membership, tokens, AI configuration, the danger zone,
the simulation's own controls, service eligibility, tenant scope or any write path.
Routes `/app/settings` and `/app/demo-data` are kept, not replaced.

## User Scenarios & Testing

### User Story 1 - Manage companies where companies are switched (Priority: P1)

Given any company, opening the switcher beside the wordmark lists every company with its
sandbox marking, its live simulation state when it has one, and, below the list, Manage
companies and New company. Manage companies opens the existing company page; New company
opens the creation form directly. The Company navigation group no longer offers Companies.

### User Story 2 - Reach the creation form by address (Priority: P2)

Given `settings_view=new`, the company page opens with the creation form already open.
Reloading or returning through history lands on the same form; switching company or
closing the form returns to `settings_view=company` without creating anything.

### User Story 3 - Find the simulation among the systems (Priority: P1)

Given a demo or practice company, or any company with a Demo Data connection state,
Integrations → My integrations opens with a Demo data simulation card above the
preparation drafts, reporting connection state, rate and last successful import, and
linking to `/app/demo-data?tenant=…`. Given an ordinary company, no such card appears.
The Company navigation group no longer offers Demo Data; the header live indicator is
unchanged.

## Requirements

- **FR-001**: Remove the Companies and Demo Data entries from the Company navigation
  group. Integrations and Storyline remain, in that order, with their routes, icons,
  active indication, collapsed tooltips and mobile drawer dismissal unchanged.
- **FR-002**: The company switcher lists each company's live simulation state when the
  company carries one, and ends with Manage companies and New company, both reachable by
  keyboard and both real links that preserve company context.
- **FR-003**: Accept `settings_view=new` as a bounded settings section that opens the
  company page with the creation form open. Unknown sections still fall back to company.
  Closing the form or switching company returns to `settings_view=company`.
- **FR-004**: Integrations → My integrations presents a Demo data simulation card for
  demo companies, practice companies and companies with a Demo Data connection state.
  It reports the state, the rate and the last successful import, refreshes on
  `reality:demo-data-changed`, and links to the existing simulation route. Integrations
  does not embed the control panel.
- **FR-005**: Every new label exists in English, German, Dutch and Spanish. German uses
  Unternehmen for companies and Demodaten for demo data, matching the app's own wording.

## Assumptions and Dependencies

The explicit user request authorizes this bounded navigation change. `Tenant` already
carries `demo_data_state`, `company_kind` and `sandbox_run_id` in the bootstrap payload,
so the switcher needs no new read. The simulation card reads the existing demo-data
status endpoint and falls back to the bootstrap state when that read fails. Existing
unrelated workspace edits must be preserved. No unresolved clarifications.

## Success Criteria

The Company group has exactly two entries. The company list appears once per screen.
Company management and company creation are reachable from the switcher, by address and
after a reload. The simulation is reachable from Integrations and the header indicator,
and is absent for ordinary companies. All four languages render the new card without
horizontal overflow at 390px.

## Requirement Traceability

| Requirement | Tasks | Proof |
|---|---|---|
| FR-001 | T001, T003 | Navigation group assertions in demo-live and retirement browsers |
| FR-002 | T001, T003 | Switcher footer reaches management and creation with company context |
| FR-003 | T002, T004 | Settings section round-trip; creation form survives reload |
| FR-004 | T001, T005 | Simulation card content, link and absence for an ordinary company |
| FR-005 | T005, T006 | Four-language audit and localized card rendering without overflow |
