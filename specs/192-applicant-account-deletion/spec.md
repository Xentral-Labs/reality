# Feature Specification: Applicant Account Deletion

**Feature Branch**: `192-applicant-account-deletion`
**Created**: 2026-09-14
**Status**: Draft
**Language**: English
**Input**: Owner request (German, 2026-09-14): can Access applications also delete entries again,
ideally with a double question? There are many test entries and they should go including all the
data those accounts created.

## Context and Intent

### Problem

Platform administration lists every access application at `/admin/access` and offers exactly two
decisions: approve and reject (spec 189, `POST /api/admin/access-applications/{id}/review`). A row
never leaves the list. Rejecting keeps the account, its verification codes, its sessions and every
company it created, so a deployment that ran open signup for a while accumulates test accounts that
cannot be cleaned up from the product at all. The owner's deployment currently shows five
applications of which three are throwaway addresses.

Nothing else closes this gap. Company deletion (spec 186) removes one company that the acting user
owns; it neither removes the account nor reaches the practice companies a free-playground signup
creates. Worse, `permanently_delete_tenant` routes through `_require_business_mutation`, and
`require_business_operation` refuses every tenant whose `purpose` is not `business`. A
free-playground account's companies are `playground` tenants, so today there is no path — product,
API or CLI — that deletes them.

### Scope

- A **Delete** control on every row of Access applications, for platform administrators only,
  independent of the application's status.
- A deletion that removes the person and everything only they hold: the account, its access
  application, sessions, verification codes, storyline packages, playground runs, and every company
  in which they are the only active owner, including all records in those companies and including
  practice and demo companies.
- A company that still has another active owner survives. Only the deleted person's membership and
  their remaining references in it are removed.
- A **double confirmation**, matching the vocabulary spec 186 already established for companies: the
  dialog enables its confirm button only when the applicant's e-mail address and the word `DELETE`
  are typed exactly. The server re-checks both and is the authority.
- A preview the dialog shows before anything is destroyed: which companies vanish with how many
  records, which companies survive because someone else owns them, and how many sandboxes go.
- One audit tombstone written after the purge, so the deployment keeps a record that an
  administrator removed this address and what it cost.
- The fix the language requirement forced: `/admin` and `/admin/access` were the only authenticated
  routes rendered outside `LocalizationProvider`, so their translations never reached the DOM. Both
  are wrapped now, which also makes the existing Approve and Reject controls speak the reader's
  language for the first time.

### Non-Goals

- No self-service account deletion. This is a platform-administration action on someone else's
  account; a person deleting their own account is a separate feature with its own consent flow.
- No bulk selection. Each row is deleted on its own, with its own confirmation, so a mis-click
  cannot remove several accounts. Cleaning up five test entries means five confirmations on purpose.
- No grace period, no deferred purge, no restore window and no export before deletion. The purge is
  synchronous, exactly like company deletion, and the same follow-up recorded in spec 186 applies to
  both.
- No change to the automatic admission counter. `AccessAdmissionCounter.used_slots` counts automatic
  admissions and the deployment records no per-user evidence of whether a given account consumed a
  slot, so deleting an account cannot decrement it honestly. A deployment with a limit must adjust
  the counter deliberately; a deployment without a limit (the default) is unaffected.
- No MCP tool, CLI command or API-token path. Deletion stays an interactive, session-authenticated
  platform-administrator action.
- No new schema and no migration.

### Existing Contracts

- [Tenant access](../003-tenant-access/spec.md): membership grants company access; platform
  administration is a separate authority.
- [Open signup by default](../189-open-signup-default/spec.md): the access application list, its
  statuses and the review endpoint.
- [Free playground](../190-free-playground/spec.md): a free signup owns `playground` tenants through
  a playground run, not business companies.
- [Company danger zone](../186-company-danger-zone/spec.md): the confirmation vocabulary
  (exact name plus the literal word `DELETE`) and the synchronous tenant sweep this feature reuses.

## User Scenarios & Testing

### User Story 1 - Delete a test applicant with everything they created (Priority: P1)

A platform administrator opens Access applications, presses Delete on a throwaway address, reads in
the dialog that one sandbox company with 412 records will vanish, types the e-mail address and
`DELETE`, confirms, and the row disappears together with the account and its company.

**Acceptance scenarios**

1. **Given** an approved applicant who owns one playground company with records, **When** the
   administrator completes the confirmation, **Then** the account, its application, its sessions, its
   playground run and the company with every record in it are gone, and the list reloads without the
   row.
2. **Given** the same applicant, **When** the administrator types the e-mail with a different case,
   **Then** the confirmation is still accepted, because e-mail comparison is normalized the way
   sign-in normalizes it.
3. **Given** a typed word other than `DELETE`, **When** the administrator submits, **Then** the
   confirm button stays disabled in the browser and the server refuses the same payload with a clear
   message.

### User Story 2 - A shared company survives its deleted member (Priority: P1)

An applicant is a member of a company that another person owns, and the owner of another company
alongside a second owner. Deleting the applicant removes neither company.

**Acceptance scenarios**

1. **Given** a company with two active owners, **When** one of them is deleted, **Then** the company
   and its records stay, the deleted person's membership is gone, and references to them inside that
   company are cleared where the schema allows and removed where it does not.
2. **Given** a company the deleted person only joined as a member, **When** the deletion completes,
   **Then** the company is untouched apart from that membership.

### User Story 3 - The administrator cannot delete themselves or a colleague administrator (Priority: P1)

**Acceptance scenarios**

1. **Given** the acting administrator's own application, **When** deletion is attempted, **Then** the
   server refuses and the browser offers no Delete control for that row.
2. **Given** another platform administrator, **When** deletion is attempted, **Then** the server
   refuses with a message naming platform administration as the reason.

### Edge Cases

- An application deleted in another session between the preview and the confirmation returns 404 and
  the dialog shows the message; the list reloads without the row.
- A company whose only other owner was deactivated still counts as solely owned by the applicant,
  because the sweep counts active owner memberships only.
- An applicant with no company at all deletes cleanly; the preview states that no company is
  affected.
- The preview counts are a snapshot. Records added between preview and confirmation are deleted too;
  the dialog never claims the counts are a guarantee.

## Requirements

### Functional Requirements

- **FR-001**: Access applications MUST render a Delete control on every row for platform
  administrators, for every application status, and MUST omit it for the acting administrator's own
  row and for any row whose account is a platform administrator.
- **FR-002**: The client MUST load a deletion preview before the dialog can confirm, naming every
  company that will be deleted with its record count, every company that survives because another
  owner holds it, and the number of sandboxes affected.
- **FR-003**: The dialog MUST enable its confirm button only when the typed e-mail matches the
  applicant's address after normalization and the typed word equals `DELETE` exactly; the word MUST
  be displayed literally and MUST NOT be translated.
- **FR-004**: The server MUST re-check both confirmations and MUST refuse a mismatch with
  `InvalidOperation`, independently of what the browser allowed.
- **FR-005**: Deletion MUST remove the account, its access application, its sessions, its e-mail
  verification codes, its storyline packages and its playground runs.
- **FR-006**: Deletion MUST permanently delete every tenant in which the account holds the only
  active owner membership, including all tenant-scoped records, regardless of the tenant's purpose,
  so practice and demo companies are removed as well.
- **FR-007**: Deletion MUST keep every tenant that another active owner holds, removing only the
  account's membership; remaining references to the account in surviving tenants MUST be set to NULL
  where the column is nullable and the referencing row MUST be deleted where it is not.
- **FR-008**: Deletion MUST refuse the acting administrator's own account and any account with
  `is_platform_admin`, in both cases before anything is removed.
- **FR-009**: Deletion MUST be one transaction: either every affected row is gone or nothing is.
- **FR-010**: After the purge the deployment MUST retain one audit event of type
  `access.deleted` recording the acting administrator, the deleted address and the number of
  companies and records removed, with no foreign key to the deleted account.
- **FR-011**: The endpoint MUST be `POST /api/admin/access-applications/{application_id}/delete`,
  MUST require platform administration, and MUST return the removal summary; the preview MUST be
  `GET /api/admin/access-applications/{application_id}/deletion-preview`.
- **FR-012**: Every new string MUST be available in English, German, Dutch and Spanish.
- **FR-013**: The platform administration routes MUST render inside `LocalizationProvider`, so the
  strings their dictionaries already carry reach the page; the confirmation word stays literal.

## Success Criteria

- **SC-001**: An administrator deletes a free-playground test account end to end in the browser, and
  neither the account nor its practice company is reachable afterwards.
- **SC-002**: A company with a second active owner survives the deletion of one owner with all its
  records intact.
- **SC-003**: No foreign key to `app_user` remains anywhere after a deletion; a schema-driven test
  proves it rather than a hand-written table list.
- **SC-004**: The confirm button cannot be enabled with a wrong address or a wrong word, and the
  server refuses the same payload independently.
- **SC-005**: No new table and no migration; the feature adds one service module, two endpoints and
  one dialog.
- **SC-006**: The dialog fits a 390px viewport in German. The page's own 2px overflow at that width
  comes from its 44px heading, predates this feature and is measured unchanged with every delete
  control withheld.

## Assumptions and Dependencies

- Depends on the access application list and the platform-administration guard from spec 189, and on
  the tenant sweep that spec 186 introduced in `permanently_delete_tenant`. That sweep is factored
  into a private helper so both paths delete a tenant the same way.
- The deletion bypasses `require_business_operation` deliberately. That policy governs *business*
  operations inside a tenant and refuses practice tenants by design; platform administration removing
  an account is not a business operation, and its authority is the platform-admin guard plus the two
  confirmations. Every other caller keeps the policy.
- The audit tombstone keeps the deleted e-mail address in its detail. It is the only remaining trace
  of the person and exists so a deployment can answer who removed which address. A deployment that
  must not retain it can clear `security_audit_event` rows of type `access.deleted`; the owner is
  asked to confirm this trade-off during review.
- Follow-ups recorded here, not part of this feature: bulk selection for cleaning up many test
  entries at once; a deferred purge with a restore window shared with spec 186; self-service account
  deletion; decrementing the admission counter once the deployment records how a slot was claimed.

## Requirement Traceability

| Requirement    | Evidence                                                                                                              |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| FR-001         | `apps/web/src/Auth.tsx` delete control; `apps/web/scripts/access-deletion.test.mjs`                                    |
| FR-002         | `account_deletion.account_deletion_preview`; `test_account_deletion.py::test_preview_names_owned_and_shared_companies` |
| FR-003         | `apps/web/src/accessDeletion.ts` (`deletionConfirmationValid`); `apps/web/scripts/access-deletion.test.mjs`            |
| FR-004         | `test_account_deletion.py::test_confirmations_must_match_exactly`                                                      |
| FR-005, FR-006 | `test_account_deletion.py::test_deletes_account_with_its_sole_owned_companies`                                         |
| FR-007         | `test_account_deletion.py::test_shared_company_survives_its_deleted_owner`                                             |
| FR-008         | `test_account_deletion.py::test_refuses_self_and_platform_administrators`                                              |
| FR-009         | `test_account_deletion.py::test_refusal_leaves_every_row_in_place`                                                     |
| FR-010         | `test_account_deletion.py::test_writes_a_tombstone_without_a_user_reference`                                           |
| FR-011         | `test_access_application_admin_api.py` delete and preview routes                                                       |
| FR-012         | `apps/web/src/localization.tsx` de/nl/es entries; `npm run i18n:audit`                                                 |
| FR-013         | `apps/web/src/Auth.tsx` route wrapping; `access-deletion-browser.mjs` German dialog and list                           |
| SC-001, SC-004 | `apps/web/scripts/access-deletion-browser.mjs`                                                                         |
