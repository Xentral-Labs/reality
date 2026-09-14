# Feature Specification: Company Danger Zone

**Feature Branch**: `186-company-danger-zone`
**Created**: 2026-09-13
**Status**: Implemented (archive, restore and company deletion; sandbox deletion open)
**Language**: English
**Input**: Owner request (German, 2026-09-13): there is no danger zone yet where a sandbox, a
demo company or a company can be deleted; how would a serious product place it? Answer first,
then build the first stage.

## Context and Intent

### Problem

The company lifecycle exists as service and API only. `archive_tenant`, `restore_tenant` and
`permanently_delete_tenant` (spec 003 lineage, `reality.services.core`) are exposed as
`POST /api/v1/companies/{id}/archive`, `/restore` and `/delete`, guarded by owner membership,
by the "keep one active company" rule and by two exact confirmations (company name and the word
`DELETE`). The web client even carries the matching helpers in `apps/web/src/api.ts` and the
label "Danger zone" in three dictionaries. No page renders any of it: an owner cannot archive,
restore or delete a company from the product, and an archived company is invisible everywhere
because the bootstrap only lists active companies.

### Scope

- A **Danger zone** section at the end of Companies settings (spec 016, spec 160 shell) for the
  company currently selected there. It carries the archive action for that company and lists the
  owner's archived companies with restore and permanent deletion.
- Archive, restore and permanent deletion call the existing endpoints unchanged. The browser
  mirrors the server guards only to explain a disabled control; the server stays the authority.
- Permanent deletion is a two-step ceremony: a company must be archived first, and the dialog
  enables its confirm button only when the company name and the word `DELETE` are typed exactly.
  The dialog states what is lost using the counts the companies endpoint already returns.
- Sandboxes and demo companies (practice companies, `Tenant.purpose = playground`) are archived
  and restored through their playground run, never through the tenant lifecycle: a new
  `archive_run` / `restore_run` pair flips the run status the way restart already does, so the
  company leaves the switcher while its records stay.
- After an action the client reloads the bootstrap and the companies list so the switcher, the
  current company and the archived list agree with the server. Archived sandboxes are listed from the account's run list.

### Non-Goals

- No new schema, no scheduled purge, no grace period and no tombstone record. The synchronous
  deletion path stays as it is; a deferred purge with a restore window is a follow-up
  specification that needs its own scenario and job design (see Assumptions).
- No deletion of sandbox or demo-company data. Practice tenants are refused by the tenant policy
  for every generic lifecycle operation (spec 104, spec 146); archiving a run hides the company
  and keeps every record. Purging a playground tenant is a follow-up on the run lifecycle.
- No MCP tool, CLI command or API-token path for archive or deletion of companies or sandboxes. These remain interactive,
  session-authenticated owner actions.
- No export-before-delete and no retention advice. The dialog only names the counts that vanish.
- No change to the "last active company" rule or to the confirmation vocabulary. The word
  `DELETE` stays literal in every UI language because the server compares it as a constant.

### Existing Contracts

- [Tenant access](../003-tenant-access/spec.md): owner membership guards company management.
- [Web product](../016-web-product/spec.md) and [docs/WEB_SPEC.md](../../docs/WEB_SPEC.md):
  Companies opens the active company's settings; destructive-action states use the shared
  interaction language.
- [Playground practice companies](../104-playground-practice-companies/spec.md) and
  [Company setup and demo profiles](../146-company-setup-demo/spec.md): practice companies are
  account-scoped and refuse generic lifecycle mutations.

## User Scenarios & Testing

### User Story 1 - Archive the selected company (Priority: P1)

An owner opens Companies, scrolls to the Danger zone, reads what archiving does, confirms, and
the company leaves the switcher for every member while nothing is deleted.

**Why this priority**: Archiving is the only reversible step and the precondition for deletion.

**Independent Test**: With two active companies, archive the selected one; the bootstrap no
longer lists it, the client opens the remaining company, and the archived list shows the first.

**Acceptance Scenarios**:

1. **Given** an owner with two active business companies, **When** they confirm "Archive
   company" for the selected one, **Then** the client posts to the archive endpoint, reloads the
   bootstrap, opens the remaining company and lists the archived one under Archived companies.
2. **Given** the selected company is the owner's only active business company, **When** the
   zone renders, **Then** the archive button is disabled and the row explains that another
   company must be created or restored first.
3. **Given** the selected company is a sandbox or a demo company, **When** the zone renders,
   **Then** the row offers "Archive sandbox" instead and explains that the records stay.
4. **Given** the current user is a member but not an owner, **When** the zone renders, **Then**
   the archive button is disabled and the row says only owners can archive.
5. **Given** the server refuses the archive, **When** the response arrives, **Then** the dialog
   stays open and shows the server message as an alert.

---

### User Story 2 - Restore or permanently delete an archived company (Priority: P1)

An owner sees their archived companies with the date, restores one with a click, or opens the
deletion dialog, reads what is lost, types the company name and `DELETE`, and deletes it.

**Why this priority**: Without this the archived state is a dead end.

**Independent Test**: Archive a company, then delete it with a wrong name (button stays
disabled), then with the right name and word; the row disappears and the server received the
exact confirmation payload.

**Acceptance Scenarios**:

1. **Given** an archived company owned by the user, **When** the zone loads, **Then** the row
   shows its name, the archive date, and the source, evidence and reality counts, with Restore
   and Delete permanently actions.
2. **Given** the deletion dialog is open, **When** the name or the word differ from the exact
   values, **Then** the confirm button stays disabled; **When** both match, it enables.
3. **Given** the owner confirms, **When** the server answers 204, **Then** the row is removed
   from the list and the dialog closes.
4. **Given** the owner clicks Restore, **When** the server answers, **Then** the company reappears
   in the switcher and leaves the archived list.
5. **Given** the archived list cannot be read, **When** the zone renders, **Then** it reports the
   failure and offers a retry without hiding the archive row.

### User Story 3 - Archive and restore a sandbox (Priority: P1)

An owner whose switcher fills up with practice companies (storyline runs, demo companies, quick
experiments) archives the selected sandbox from the same zone, sees it under Archived sandboxes
and restores it later.

**Why this priority**: This is the owner's original request; without it the switcher only grows.

**Independent Test**: Archive a practice company; it leaves the bootstrap and the switcher, its
tenant stays unarchived, its records remain; restore brings it back.

**Acceptance Scenarios**:

1. **Given** an owner with a selected practice company and at least one other entry, **When**
   they confirm "Archive sandbox", **Then** the client posts a confirmed archive to the run,
   reloads the bootstrap, opens another company and lists the sandbox under Archived sandboxes.
2. **Given** an archived sandbox, **When** the owner clicks Restore, **Then** the run is active
   again and the company reappears in the switcher.
3. **Given** the archive or restore is sent without confirmation, or by another account, **When**
   the API answers, **Then** it refuses with 403 or 404 and nothing changes.
4. **Given** the sandbox is the owner's only entry, **When** the zone renders, **Then** the
   button is disabled with the last-active reason.
5. **Given** a storyline company is archived and another active run already carries the same
   storyline, **When** restore is attempted, **Then** the API refuses with a conflict.

### Edge Cases

- Archived companies of which the user is only a member are listed without actions and with a
  note that only owners restore or delete them.
- A company archived by another owner between two reads shows up on the next reload; the client
  never caches lifecycle state beyond a single page visit.
- Deletion of a company that was restored in another session fails server-side ("Archive the
  tenant before permanently deleting it") and the message is shown in the dialog.

## Requirements

### Functional Requirements

- **FR-001**: Companies settings MUST render a Danger zone section after the company list for the
  currently selected company, visible to every member, with the archive control enabled only for
  owners of an active business company that is not the user's last active business company.
- **FR-002**: A disabled archive control MUST state its reason in place (not an owner, practice
  company, last active company).
- **FR-003**: Archiving MUST require an explicit confirmation dialog that names the company and
  states that nothing is deleted and that the company can be restored from this page.
- **FR-004**: The zone MUST list the archived companies visible to the user from the companies
  endpoint, showing name, archive date and the source, evidence and reality counts, with Restore
  and Delete permanently for owners only.
- **FR-005**: Permanent deletion MUST be confirmed in a dialog whose confirm button is enabled only
  when the typed company name and the typed word match the exact server constants; the dialog
  MUST show the counts that will be lost.
- **FR-006**: The client MUST call the existing archive, restore and delete endpoints with their
  existing payloads and MUST show a server refusal as an alert without changing local state.
- **FR-007**: After a successful archive or restore the client MUST reload the bootstrap and open
  the selected company if it is still listed, otherwise the default company.
- **FR-008**: Every new string MUST be available in English, German, Dutch and Spanish; the
  confirmation word `DELETE` MUST be displayed literally and not translated.
- **FR-010**: The playground service MUST offer `archive_run` and `restore_run` for the run owner
  only, confirmed explicitly, flipping only the run status and `archived_at`; the tenant and its
  records stay untouched and an archived run no longer counts as a practice company.
- **FR-011**: The playground API MUST expose `POST /api/playground/runs/{id}/archive` and
  `/restore` with a `confirmed` flag, refusing unconfirmed calls (403), unknown or foreign runs
  (404) and wrong states (409).
- **FR-012**: For a selected sandbox or demo company the zone MUST offer "Archive sandbox" and list
  the account's archived sandboxes with Restore; it MUST say that deleting sandbox data is not
  available yet.
- **FR-009**: The archive, restore and delete endpoints MUST keep refusing non-owners with 403;
  the zone never grants a capability the API does not already enforce.

## Success Criteria

- **SC-001**: An owner archives, restores and permanently deletes a company end to end in the
  browser without touching the API directly.
- **SC-002**: The delete confirm button cannot be enabled with a wrong name or word; the fixture
  run proves the payload the server receives.
- **SC-003**: The zone renders at 1440px and 390px in English and German without horizontal
  overflow of its own.
- **SC-004**: No new table or migration; the backend adds two run-lifecycle functions and two
  endpoints that reuse the existing status vocabulary.
- **SC-005**: A practice company archived from the zone leaves the switcher and comes back on restore
  without any tenant-level change.

## Assumptions and Dependencies

- Depends on the existing lifecycle services and endpoints and on `GET /api/v1/companies`,
  which already returns archived rows with usage counts for tenants the user is a member of.
- The client counts "active business companies" from the bootstrap the user sees. The server
  rule counts across the deployment; the client rule is stricter on purpose so a user never
  archives their only reachable company.
- Follow-ups recorded here for the owner's decision, not part of this feature: a deferred
  purge with a restore window and a batched background job (the synchronous delete scans every
  tenant-scoped table); a platform-level tombstone of who deleted which company and when;
  re-authentication before deletion; permanent deletion of a playground tenant behind an archived
  run; an
  export-before-delete offer for companies with posted ledger entries.

## Requirement Traceability

| Requirement    | Evidence                                                                                                                                                         |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-001, FR-002 | `apps/web/src/unified/companyLifecycle.ts` (`archiveGuard`), `apps/web/scripts/company-lifecycle.test.mjs`, `apps/web/scripts/company-danger-zone-browser.mjs`   |
| FR-003         | `CompanyDangerZone.tsx` archive dialog; browser script archive flow                                                                                              |
| FR-004         | `CompanyDangerZone.tsx` archived list; browser script archived rows                                                                                              |
| FR-005         | `companyLifecycle.ts` (`deleteConfirmationValid`), contract test, browser script delete flow                                                                     |
| FR-006, FR-007 | browser script recorded requests and bootstrap reload                                                                                                            |
| FR-008         | `localization.tsx` de/nl/es entries; `npm run i18n:audit`                                                                                                        |
| FR-009         | `packages/reality-core/tests/test_master_data_api.py` owner guard test; existing `test_tenant_lifecycle.py`                                                      |
| FR-010         | `reality.services.playground.archive_run` / `restore_run`; `test_playground_practice_companies.py::test_practice_companies_archive_and_restore_without_deleting` |
| FR-011         | `reality.web.playground` archive and restore routes; `test_playground_api.py::test_sandbox_archive_and_restore_are_confirmed_owner_actions`                      |
| FR-012         | `CompanyDangerZone.tsx` sandbox row and archived sandboxes; browser script sandbox flow                                                                          |
