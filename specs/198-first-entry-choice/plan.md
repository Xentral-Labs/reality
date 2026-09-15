# Implementation Plan: Choose how the first company starts

## Technical Context
Service `free_playground.enter`, the account-scoped FastAPI adapter under
`/api/company-setup/playground`, and the React entry in `unified/FreePlayground.tsx`.
No schema, migration, job or profile change.

## Constitution Check
All principles PASS. Creation keeps running through `company_setup.create_company`,
so admission, ownership, request-key idempotency, the choice fingerprint and the
confirmation boundary are unchanged. The chosen content is a request input validated
against a closed set, never a client-supplied company configuration. No new table, no
alternative business path, no write outside the existing services.

## Design
`enter()` accepts `content` restricted to `international_demo` and `empty`, names the
company accordingly and enables live simulation only for the demo start. Both keep the
account's single `free-playground:v1` request key, so `entry_status().receipt` records
the start that was taken and the existing fingerprint check refuses a later retry that
states the other one. The adapter's `Confirmation` body gains the same closed literal
with the demo start as its default, which keeps existing clients working.

`TrialEntryRequest` renders a two-card start screen instead of firing the request on
mount; the request runs only after a card is chosen and carries that content. The
progress and failure states, the retry and the `open()` handover are unchanged. The
cards carry no form: the name, environment and options stay with the existing company
setup dialog.

## Verification / rollback
Service tests first: both contents create their company, the receipt reports the start,
replay returns the same company, the conflicting retry is refused, and Demo Data
connects after an empty start. Then API tests over the adapter body, web contract and
i18n tests, a browser run over both cards in four languages and a narrow viewport, and
the full PostgreSQL pytest run. Rollback is a code revert; companies already created
keep their receipts, and no migration exists to undo.
