# Feature Specification: Signup Adopts the Browser's Presentation Defaults

**Created**: 2026-09-14
**Status**: Draft
**Language**: English
**Input**: A new account always starts in the wrong time zone. Take the time zone, and the
language with it, from the browser as the default.

## Context and Intent

### Problem

Every account is created with the stored column defaults `timezone = "UTC"`,
`language = "en"` and `locale = "en-GB"`. Signup never asks for them and never reads what
the browser already knows. A registrant in Berlin therefore sees UTC instants and English
number and date formats everywhere the account preference is applied - chat presentation,
the authenticated web surface, exported presentation - until they find Settings and correct
it by hand. The correction is available, but it is offered after the first impression is
already wrong, and someone who registers from the German entry page is silently moved to
English.

The browser states both values without being asked: `Intl.DateTimeFormat().resolvedOptions().timeZone`
resolves an IANA zone, and the requested language is already resolved for the signup page
itself. Signup is the moment the account is created, so it is the moment to record them.

### Scope

- Public signup and invitation signup accept an optional presentation hint: time zone and language.
- The browser supplies that hint; the account stores it as its initial preference.
- An absent, unsupported or unknown hint keeps today's defaults and never fails registration.
- The display locale follows the accepted language, as the public entry pages already pair them.

### Non-Goals

- Changing existing accounts. A wrong stored zone stays until its owner changes it in Settings.
- Making time zone or language part of the signup form. This is a default, not a question.
- Deriving language from the time zone, or a country, or the request address.
- Changing how instants are stored. Storage stays UTC; this is presentation only.
- Adding locales or languages beyond the supported set, or letting the browser choose a
  locale independently of the language.
- Company, tenant or business-record time zones. This is the personal account preference.

### Existing Contracts

- [Web contract](../../docs/WEB_SPEC.md)
- [Shared language contract](../176-shared-language/spec.md)

## User Scenarios & Testing

### User Story 1 - Register and see local time (Priority: P1)

Someone registering from a browser in a known time zone reaches the product with instants
presented in that zone, without visiting Settings first.

**Independent Test**: Register with a browser time zone of `Europe/Berlin` and read the
stored account preference and the authenticated presentation.

**Acceptance Scenarios**:

1. **Given** a browser resolving `Europe/Berlin`, **When** an account is created,
   **Then** the account's stored time zone is `Europe/Berlin`.
2. **Given** an account created this way, **When** its owner opens Settings,
   **Then** the detected zone is shown as the current value and remains changeable.
3. **Given** a browser that states no zone, **When** an account is created,
   **Then** the account's time zone is `UTC` and registration succeeds.

### User Story 2 - Register in the language of the entry page (Priority: P1)

Someone registering from the German entry page receives an account whose stored language
and display locale are German.

**Independent Test**: Register with `?lang=de` and with a browser that requests Dutch
without an explicit choice.

**Acceptance Scenarios**:

1. **Given** an explicit language choice on the signup page, **When** an account is created,
   **Then** that language is stored with its paired locale.
2. **Given** no explicit choice and a browser requesting a supported language,
   **When** an account is created, **Then** that language is stored with its paired locale.
3. **Given** a browser requesting only unsupported languages, **When** an account is created,
   **Then** the account stores `en` and `en-GB`.

### User Story 3 - A hostile or broken hint changes nothing (Priority: P1)

A client-supplied hint can never block registration or widen what an account may hold.

**Independent Test**: Register with unknown, malformed, oversized and empty hint values.

**Acceptance Scenarios**:

1. **Given** an unknown or malformed time zone, **When** an account is created,
   **Then** registration succeeds with `UTC`.
2. **Given** an unsupported language value, **When** an account is created,
   **Then** registration succeeds with `en` and `en-GB`.
3. **Given** an oversized hint value, **When** registration is attempted,
   **Then** the request is rejected by the existing request-validation boundary before
   any account is created.

### Edge Cases

Invitation signup, repeated signup for an existing address, disabled public signup, a
browser without `Intl` resolution, a zone the browser knows and the server's zone database
does not, a language query parameter with an unsupported value, and locale and time zone
hints arriving on an endpoint that also enforces terms acceptance.

## Requirements

### Functional Requirements

- **FR-001**: Public signup and invitation signup MUST accept an optional time-zone and
  language hint and MUST store them as the new account's initial preference.
- **FR-002**: An absent, empty, unsupported or unresolvable hint MUST leave the established
  defaults (`UTC`, `en`, `en-GB`) in place and MUST NOT fail registration.
- **FR-003**: The accepted language MUST determine the stored display locale from the
  supported pairing already used by the public entry pages; the client MUST NOT select a
  locale independently.
- **FR-004**: The browser application MUST send the zone resolved by the browser and the
  language already resolved for the signup page, falling back to the browser's requested
  languages when no explicit choice was made.
- **FR-005**: Existing verification, admission, invitation, terms acceptance, duplicate
  address and disabled-signup behavior MUST remain unchanged, and the preference MUST stay
  changeable in Settings afterwards.

### Domain and Traceability Requirements

- **DR-001**: The hint is account presentation metadata on the existing `app_user` columns.
  No schema change, no business record, no source payload and no tenant-scoped data is
  involved, and instants remain stored in UTC.
- **DR-002**: One shared validation vocabulary MUST decide which languages, locales and
  zones an account may hold, used by both signup defaulting and the existing profile and
  application updates.

## Success Criteria

- **SC-001**: A registration from a browser in a supported zone produces an account whose
  presented instants are local from the first authenticated page, with no Settings visit.
- **SC-002**: No hint value, including unknown, malformed or hostile ones, can prevent a
  registration that would otherwise succeed.

## Assumptions and Dependencies

- The browser's resolved zone is a presentation hint, not an identity or authorization
  value, and needs no verification.
- The supported languages remain `en`, `de`, `nl`, `es`, each paired with exactly one
  display locale, as the authenticated Settings surface already presents them.
- The server's `zoneinfo` database is available, as the existing profile validation already
  requires.
- Existing accounts are out of scope; their stored preference stays until changed.

## Requirement Traceability

| Requirement | Scenarios | Planned evidence |
|---|---|---|
| FR-001 | US1.1, US2.1-2 | Signup and invitation signup HTTP tests |
| FR-002 | US1.3, US3.1-2 | Hint fallback tests over unknown and empty values |
| FR-003 | US2.1-3 | Language and locale pairing tests |
| FR-004 | US1.1, US2.1-2 | Browser preference contract test |
| FR-005 | Edge cases | Existing access, invitation and admission suites |
| DR-001 | All | Schema diff review; no migration |
| DR-002 | US2.3, US3.1-2 | Shared validation used by signup and profile tests |
