# Implementation Plan: Signup Adopts the Browser's Presentation Defaults

**Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)

## Summary and Technical Context

Signup already creates `AppUser` with column defaults. The smallest coherent change is one
shared presentation vocabulary in `web/auth.py` that both the existing profile validation
and the new signup defaulting use, plus two optional request fields and one small browser
module that states what the browser knows. Python 3.12+, Pydantic v2, existing FastAPI and
React adapters. No dependency, no schema, no migration, no domain or service change.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Account presentation metadata only; no source, document or reality record touched | PASS |
| Reality owns operational state | No operational status derived or stored; instants stay UTC | PASS |
| Proven schema only | Existing `app_user.timezone`, `language`, `locale` columns; no migration | PASS |
| Tenant + shared service boundaries | Pre-tenant account creation; membership and verification guards untouched | PASS |
| Spec/test traceability | Every FR/DR mapped in the test strategy below; tests first | PASS |
| Explainable web behavior | The detected value is visible and changeable in Settings | PASS |
| Received values not recomputed | The browser's zone is stored as stated, never inferred from another value | PASS |
| Smallest coherent design | Two optional fields and one pairing table, not a preferences subsystem | PASS |

## Repository Structure and Layer Changes

- `packages/reality-core/src/reality/web/auth.py`: `SUPPORTED_LOCALES` pairing, `presentation_defaults()`, optional `timezone` and `language` on `SignupBody` (inherited by `InvitationSignupBody`), applied in both signup endpoints; `validate_preferences()` reuses the same vocabulary.
- `apps/web/src/signupPreferences.ts`: new. Resolve the browser's zone and language into the optional hint.
- `apps/web/src/api.ts`: send the hint with `signup` and `invitationSignup`.
- `apps/web/src/Auth.tsx`: pass the resolved language choice into the hint.
- `packages/reality-core/tests/test_user_access.py`: signup defaulting and fallback proof.
- `apps/web/scripts/signup-preferences.test.mjs`: new. Browser resolution contract.
- `docs/WEB_SPEC.md`: record that signup adopts the browser's presentation defaults.

## Design

`presentation_defaults(language, timezone)` returns the triple `(language, locale, timezone)`
an account starts with. An unsupported language falls back to `en`; the locale is never taken
from the client, it is the supported pairing of the accepted language. A time zone is accepted
only when `zoneinfo` resolves it, otherwise `UTC`. `ZoneInfoNotFoundError` and the `ValueError`
that malformed keys raise are both treated as "unknown", because a presentation hint must never
turn a valid registration into an error. Field length caps keep an oversized value at the
request boundary, where Pydantic already rejects it before any account exists.

In the browser, `signupPreferences()` takes the already-resolved page language (the `?lang`
choice from the shared language contract) and falls back to the browser's requested languages,
then reads `Intl.DateTimeFormat().resolvedOptions().timeZone`. Both parts are omitted when they
are unusable, so the server applies its defaults. The function is pure and takes its inputs as
arguments, so the contract is testable without a browser.

## Test Strategy and Traceability

| Requirement | Test |
|---|---|
| FR-001 | `test_user_access.py`: signup and invitation signup store the sent hint |
| FR-002 | `test_user_access.py`: absent, empty, unknown and malformed hints keep `UTC`/`en`/`en-GB` and return 201 |
| FR-003 | `test_user_access.py`: each supported language stores its paired locale; a client-sent locale is not accepted |
| FR-004 | `signup-preferences.test.mjs`: explicit choice, browser languages, unsupported languages, missing `Intl` resolution |
| FR-005 | Existing `test_user_access.py` suite: verification, admission, invitation, duplicate address, disabled signup |
| DR-001 | No migration in the diff; `git diff` review over `migrations/` |
| DR-002 | `test_user_access.py`: profile update and signup reject/accept the same language and locale set |

## Rollout and Rollback

Additive optional request fields; an older browser bundle that sends nothing keeps today's
behavior. Rollback is a revert of the diff, with no data migration: accounts created in the
meantime keep the preference they were given, which their owners can change in Settings.

## Review Risks

- A browser zone the server's `zoneinfo` does not know must fall back, not fail. Covered by FR-002 tests.
- The language hint must not become an authorization or identity value; it stays presentation only.
- The pairing table must not drift from the Settings locale options. Both now read one vocabulary.

## Complexity Tracking

No constitutional exception is required.
