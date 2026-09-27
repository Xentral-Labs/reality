# Feature Specification: Service refusals speak the user's language

**Feature Branch**: `286-localized-service-errors`
**Created**: 2026-09-27
**Status**: Draft
**Language**: English
**Input**: "Create the spec for translated service error messages." It comes from the spec 284
live walk-through: the German invoice form refused a contradiction with the English sentence
"Net plus tax differs from the invoice gross."

## Context and Intent

### Problem

When a service refuses a request, the person sees the refusal exactly as the service wrote it,
in English, whatever their language. The German invoice form shows "Net plus tax differs from
the invoice gross."; a Dutch clerk recording a receipt sees "Invoice quantity exceeds the
remaining billable quantity."

The cause is the contract, not missing translations:

- Services raise `InvalidOperation`, `NotFound` or `Conflict` with an English sentence and
  nothing else (`services/core.py`). About 1,130 distinct sentences exist, 113 of them built
  with interpolated values.
- The API turns them into `{"detail": "<English sentence>"}` (`web/api.py` `api_error`), with no
  identity the web could translate. The web shows `error.message` as it is.
- Translating the sentence itself is fragile: the dictionaries are keyed by exact English text,
  so every wording change silently breaks a translation, and sentences with values never match.

Two patterns in the product already solve this for their areas:

- Analytics refusals carry a code (`AnalyticsError(message, code=...)`); the web maps the code
  to a translated sentence (`unified/analytics/errors.ts`).
- Spec 279 resolution guidance: services emit codes only, an English catalog
  (`config/resolution_guidance.json`) holds the wording, the web translates it, and a contract
  test requires German, Dutch and Spanish for every entry.

### Scope

- **Refusal identity:** a service refusal can carry a stable code and named values next to
  its English sentence. The code, not the sentence, identifies the refusal.
- **One catalog:** the English wording of every coded refusal lives in one catalog, with named
  placeholders for its values.
- **Transport:** the web API, the chat stream and failed proposal receipts carry the code and
  values next to the unchanged English sentence.
- **Web:** decision and entry forms and the chat panel show a coded refusal in the person's
  language, with its values in place. An uncoded refusal is shown as today.
- **First increment:** every refusal reachable from the web's decision and entry forms (see
  "In-scope forms") is coded and translated into German, Dutch and Spanish.
- **Gate:** a contract test fails when a catalog entry lacks a translation, and when an
  in-scope service raises a refusal without a code.

#### In-scope forms

The forms whose submit or confirmation calls an application service and shows its refusal:
orders, deliveries and shipments, goods receipts, invoices (single, multi-position,
consolidated), payments and allocations, credits and refunds, financial reversals, corrections,
customer holds, supply assignments, opening stock, master data, cost review drafts and
proposal decisions (`apps/web/src/unified/*Card.tsx`, `CostReviewDraftDialog.tsx`,
`ProposalReviewCard.tsx`). The plan lists the exact service entry points behind them.

### Non-Goals

- Changing what a refusal means or when it happens. The same requests are refused as today.
- Translating refusals for MCP clients or the chat model. They keep the English sentence and
  gain the code; the model already restates refusals in the conversation language.
- Translating refusals outside the in-scope forms in this increment: analytics (already coded),
  authentication and invitations, integrations and source configuration, Playground, storyline
  import, background jobs, the CLI. They keep their English sentence and move over area by
  area in later specs.
- Translating FastAPI request validation errors (422 with a field list). They remain generic.
- Server-side translation by the user's language. The server stays language-neutral for
  refusals; stored proposal receipts keep English.
- Rewording existing English sentences beyond what a placeholder requires.

### Existing Contracts

- `services/core.py` refusal classes; `web/api.py` `api_error`; `web/chat_stream.py`;
  `agent/mcp_chat.py`; `mcp/server.py` (MCP already sends a class-level code).
- Spec 279 resolution guidance catalog and its localization contract test.
- `apps/web/src/localization.tsx` dictionaries (key is the English source; du/je/tú register;
  protected terms such as "Evidence" stay untranslated).
- Constitution IV (shared services; adapters add no business rules) and the English-only
  repository rule.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A refusal in a form is shown in my language (Priority: P1)

A German clerk records an invoice with gross 60.00, net 50.00 and tax 9.50. The form refuses
it with "Netto plus Steuer weicht vom Rechnungsbetrag ab." instead of the English sentence.
Nothing is recorded, as before.

**Why this priority**: Every person who does not work in English meets refusals daily in the
forms that change their business records.

**Independent Test**: Trigger a coded refusal from an in-scope form with the account language
set to German, Dutch and Spanish. The form shows the translated sentence; with English it shows
the unchanged English sentence.

**Acceptance Scenarios**:

1. **Given** an account in German, **When** an in-scope service refuses with a coded refusal,
   **Then** the form shows the German sentence for that code.
2. **Given** an account in English, **When** the same refusal happens, **Then** the form shows
   exactly the sentence the service states today.
3. **Given** a refusal whose code the web does not know (for example a newer server), **When**
   it is shown, **Then** the English sentence the service sent is shown.
4. **Given** an uncoded refusal from an out-of-scope service, **When** it is shown, **Then** it
   behaves exactly as today.

---

### User Story 2 - Values stay in their place (Priority: P1)

A Dutch clerk enters an order whose third line has no amount and reads "Regel 3 heeft een
opgegeven bedrag nodig; het wordt nooit berekend." In master data, a payment term code that
already exists is refused with "Betalingstermijncode 'NET30' bestaat al." The line number and
the code are the ones the service named.

**Why this priority**: Refusals with values are the most actionable ones; a translation that
drops or garbles the value is worse than English.

**Independent Test**: Trigger a refusal with values in each supported language; the shown text
contains every value the service sent, and numbers use the language's number format.

**Acceptance Scenarios**:

1. **Given** a refusal with named values, **When** it is shown in any language, **Then** every
   value appears exactly once in its placeholder's position.
2. **Given** a value the catalog declares as a number or amount, **When** it is shown in German,
   **Then** it uses the German decimal format (59,50), without rounding.
3. **Given** a value that is an English field name (for example "{label} must be a decimal
   value." with "Credit amount"), **When** it is shown in Spanish, **Then** the field name is
   translated too.
4. **Given** a translation that lacks one of the entry's placeholders, **When** the contract
   test runs, **Then** it fails.

---

### User Story 3 - Chat errors are shown in my language (Priority: P2)

A Spanish owner asks the chat to record a payment. A tool call is refused, and the stream
ends with an error. The panel shows the Spanish sentence for the refusal; the model still
receives the English sentence and the code and explains it in Spanish.

**Why this priority**: The chat is a main entry point, but the model already restates most
refusals; the raw stream error is the remaining English surface.

**Independent Test**: Force a coded refusal as a chat stream error with the account in Spanish;
the panel shows the Spanish sentence; the tool result given to the model contains the English
sentence and the code.

**Acceptance Scenarios**:

1. **Given** a coded refusal ending a chat stream, **When** it is shown, **Then** the panel shows
   the translated sentence.
2. **Given** a refused tool call inside the chat, **When** the model receives the result,
   **Then** it contains the English sentence, the code and the values.
3. **Given** an MCP client, **When** a tool is refused, **Then** the English message is unchanged
   and the code is the refusal's code instead of only its class.

---

### User Story 4 - New refusals cannot ship untranslated (Priority: P2)

A developer adds a refusal to an in-scope service. Until it has a code, a catalog entry and
German, Dutch and Spanish, the contract test fails and names it.

**Why this priority**: Without a gate the English sentences come back with the next feature.

**Independent Test**: Add an uncoded refusal to an in-scope service, or a catalog entry without
a Dutch translation; the respective test fails and names the file and line or the code.

**Acceptance Scenarios**:

1. **Given** an in-scope service module, **When** it raises a refusal without a code, **Then**
   the gate fails and names the file and line.
2. **Given** a catalog entry, **When** a language lacks its translation or a placeholder,
   **Then** the localization contract fails and names the code and language.
3. **Given** a code raised in code, **When** it has no catalog entry, **Then** the gate fails.

### Edge Cases

- **Same sentence, different causes:** two call sites with identical wording but different
  meaning get different codes; identical meaning shares one code.
- **Refusals built from another error:** services that re-raise a domain error as
  `InvalidOperation(str(error))` pass the domain refusal's code and values through; an uncoded
  domain error stays uncoded and falls back to English.
- **Sensitive values:** values carry only what the English sentence already shows; the code
  adds no data, and tenant scope is unchanged.
- **Conflict (stale state) refusals** keep their HTTP status and their existing behaviour in
  the forms (reload prompts); only the wording is translated.
- **Web code that compares message text** (the chat page compares "ChatSession not found.")
  compares the code instead.
- **Protected terms** ("Evidence", "Reality", ...) stay untranslated in refusal translations,
  as elsewhere.
- **Old stored receipts** keep their English text without a code and are shown as today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A service refusal MUST be able to carry a stable code and named values in
  addition to its English sentence, for `InvalidOperation`, `NotFound`, `Conflict` and their
  subclasses.
- **FR-002**: The English wording of every coded refusal MUST come from one catalog, whose
  entry holds the English template with named placeholders and the kind of each value: text
  (shown as given, such as a code or reference), term (an English product word that is itself
  translated, such as a field name), number, amount, quantity or date. The English sentence sent to clients MUST equal the
  template filled with the values.
- **FR-003**: The web API MUST send the code and values next to the unchanged English sentence
  for every coded refusal, for every refusal status it returns today (400, 404, 409, 422), and
  MUST keep the current shape for uncoded refusals.
- **FR-004**: The chat stream error event and the failed proposal receipt MUST carry the code
  and values next to the English sentence.
- **FR-005**: The web MUST show a coded refusal in the account language, with each value in its
  placeholder, terms translated, and numbers, amounts, quantities and dates formatted for that
  language without rounding, and MUST fall back to the English sentence when the code is unknown.
- **FR-006**: Every refusal raised by the services behind the in-scope forms MUST be coded, and
  every catalog entry MUST have German, Dutch and Spanish translations that contain all its
  placeholders.
- **FR-007**: A contract gate MUST fail when an in-scope service raises an uncoded refusal, when
  a raised code has no catalog entry, and when a catalog entry lacks a translation or a
  placeholder.
- **FR-008**: The chat model and MCP clients MUST keep receiving the English sentence; they MUST
  additionally receive the code (MCP: the refusal code where one exists, the class code
  otherwise) and the values.
- **FR-009**: Web code MUST NOT decide behaviour by comparing refusal text; it uses the code.

### Domain and Traceability Requirements

- **DR-001**: Refusal codes are identities, not wording: renaming a sentence keeps its code; a
  code is never reused for a different meaning.
- **DR-002**: No refusal changes when or why it happens. Codes and values are added to the
  existing refusal at the same place; services and adapters add no new rule.
- **DR-003**: No schema change. Failed proposal receipts keep their existing JSON output and
  gain the code and values inside it.
- **DR-004**: Values contain only what the English sentence already contained and stay within
  the tenant scope of the request.

### Key Entities

- **Refusal code**: the stable identity of a refusal's meaning (snake_case, like the existing
  analytics and guidance codes).
- **Refusal catalog entry**: the English template, its named placeholders and their kinds.

## Success Criteria *(mandatory)*

- **SC-001**: In the German, Dutch and Spanish editions, no in-scope form shows an English
  refusal sentence for any refusal its services can raise (proven by the gate and a browser
  test per language).
- **SC-002**: Out-of-scope surfaces, MCP and the chat model behave exactly as before, apart
  from the added code and values (existing suites stay green).
- **SC-003**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The account language (`AppUser.language`: en, de, nl, es) is already known to the web
  (`/api/auth/me`) and is the language refusals are shown in.
- The web's dictionaries keyed by English source text remain the translation store; the
  catalog's English templates become dictionary keys, as the spec 279 catalog does.
- About 800 tests match refusal text; they keep working because the English sentences do not
  change. New tests assert codes.
- The exact list of service entry points behind the in-scope forms, and the number of refusals
  they raise, is inventoried in the plan.

## Open Questions

None. Decided by the owner on 2026-09-27:
- codes with values, translated in the web (not English sentences as keys, not server-side
  translation);
- first increment: every refusal reachable from the web's decision and entry forms, plus the
  gate; other areas follow;
- chat stream errors are translated too; the model and MCP keep English plus the code.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 1 | service test: a coded refusal carries code and values |
| FR-002 | US2 1 | catalog test: English sentence equals the filled template |
| FR-003 | US1 1–4 | API test per status: code and values present; uncoded shape unchanged |
| FR-004 | US3 1 | chat stream and proposal receipt tests |
| FR-005 | US1 1–3, US2 1–3 | web contract and browser test in de/nl/es |
| FR-006 | US1 1 | gate over the in-scope services; localization contract |
| FR-007 | US4 1–3 | gate negative tests paired with a positive control |
| FR-008 | US3 2–3 | chat tool result and MCP error payload tests |
| FR-009 | Edge cases | web contract: no comparison with refusal text |
| DR-001 | — | catalog review; code uniqueness test |
| DR-002 | — | existing suites green; diff review |
| DR-003 | — | plan schema review: no migration |
| DR-004 | Edge cases | values test: only template placeholders, tenant scope unchanged |
