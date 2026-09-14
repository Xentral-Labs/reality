# Review

## Before implementation

The owner asked for the browser's time zone as the signup default and approved taking the
language with it. Requirements, non-goals and assumptions are recorded in `spec.md`; the
Constitution Check in `plan.md` is PASS on every principle with no exception requested.
Tests were written first and observed failing.

## Completion review

- **FR-001**: `/api/auth/signup` and `/api/auth/invitations/signup` accept `language` and
  `timezone` and create the account with the resolved triple. Both endpoints call the one
  function; neither duplicates the rule.
- **FR-002**: `presentation_defaults` falls back to `en`, `en-GB` and `UTC` for absent, empty,
  unsupported and unresolvable values. `ZoneInfoNotFoundError` and the `ValueError` a malformed
  key raises are both treated as unknown, so no hint can turn a valid registration into an error.
- **FR-003**: the locale is the server's pairing of the accepted language. A client-sent
  `locale` is ignored, proven by a test that sends a contradicting one.
- **FR-004**: the browser sends what it states, and omits what it cannot state. A real-browser
  run confirms the request body in three time zones and three language situations.
- **FR-005**: verification, admission, invitation, duplicate-address, terms-acceptance and
  disabled-signup behavior are untouched; the existing suite passes unchanged. Settings still
  edits all three preferences.
- **DR-001**: no migration, no schema change, no business record, no tenant-scoped data. The
  diff touches only `app_user` columns that already exist. Instants remain stored in UTC.
- **DR-002**: `SUPPORTED_LOCALES` is the single vocabulary; `validate_preferences` now reads it
  instead of repeating two literal sets, and a test asserts both paths agree.

The hint is unverified client input and is treated as such: it is presentation only, never
identity or authorization, it is length-capped at the request boundary, and an unusable value
degrades to the established default rather than raising.

## Rollback

Revert the diff. No data migration is involved. Accounts created in the meantime keep the
preference they were given, which their owners can change in Settings.

## Not done here

Existing accounts keep their stored `UTC`. Offering them a one-time "your browser says
Europe/Berlin" correction in Settings is a separate, smaller change and is listed as a
non-goal in `spec.md`.
