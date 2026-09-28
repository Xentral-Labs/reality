# Contract: Business Journey Guide

## Public catalog

`GET /api/journey-guide` returns public catalog data, locales and status definitions. Static Docs ships the same payload. No internal evidence is present.

## Public question

`POST /api/journey-guide/questions` accepts bounded `question`, locale and result limit. It returns a structured conclusion, status, matched journeys, citations and fallback outcome. It is anonymous, rate-limited and non-persisting.

## Internal question

`POST /api/accounts/me/journey-guide/questions` uses the same query service with authorized internal evidence. Unauthorized calls disclose no internal reference.

## Proposals

- `GET /api/journey-proposals`: moderated list/filter and derived counts.
- `POST /api/accounts/me/journey-proposals/prepare`: validation plus matching journeys/proposals and confirmation token.
- `POST /api/accounts/me/journey-proposals`: confirmed idempotent creation.
- `POST /api/accounts/me/journey-proposals/{id}/vote`: confirmed/retry-safe vote.
- `DELETE /api/accounts/me/journey-proposals/{id}/vote`: confirmed/retry-safe withdrawal.
- Reviewer lifecycle changes use platform authorization and required rationale.

Chat calls matching prepare/confirm application tools; it never writes through an adapter.

## Docs UI

Routes are `/getting-started/business-journeys` and `/de/getting-started/business-journeys`. They provide filters, search, expandable evidence/limitations and Ask Reality. API failure falls back to local catalog matching. Proposal CTAs point to Product Web and preserve locale/context. “Atlas” never appears in product copy.

All other public Docs routes expose the shared public capability widget as a closed launcher. The Docs theme uses the configured Product Web `APP_URL` as the public question origin, chooses the locale-specific Guide route, and does not render a second launcher on either Business Journey Guide or standalone Journey Chat route. Widget or question-service failure does not block Docs navigation or content.

## Public marketing-site chatbot

The repository publishes a versioned, framework-neutral chatbot asset with configured public API and Docs origins. A marketing page embeds it as a closed-by-default launcher that opens an accessible panel, accepts anonymous capability questions, shows cited Guide links and stores no durable conversation history. Load/API failure cannot block or obscure the host page. The private operations repository owns the `runreality.ai` embed and must record a production smoke check against this contract.

## Normal Reality Chat

The existing authenticated Chat recognizes capability questions in ordinary sessions and calls the same guide query service through a registered read tool. It does not create a separate session type or capability-chat mode. Public capability status and citations remain identical to Website and Docs; authorized internal evidence is additive and tenant-specific questions continue through the existing tenant-scoped tool boundary.
