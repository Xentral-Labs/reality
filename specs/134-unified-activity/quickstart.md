# Unified activity drawer acceptance

Open http://localhost:5177/app and choose Activity in the header (history icon on mobile).
The local UI uses the existing shared users and companies. This increment needs no API
restart, schema change or deployment.

## Manual walkthrough
1. Start from Facts or Your work with unfinished input. Open Activity and confirm the
   selected company appears. Search by party, item, reference or event.
2. Select 24 hours, 7 days, 30 days or all time. Windows use event time; order uses
   recording sequence. Attention is historical classification, not current case status.
3. Load older events. Open an event Inspector or a supported related record; Escape
   closes the Inspector first. Technical details preserve IDs, times and escaped payload.
4. Close the drawer; the original route and input remain. Changing company discards the
   old drawer, including in-flight results. Refresh explicitly to see newly recorded events.

## Automated proof
The new browser script intercepts every API request and rejects writes. It proves
cursor paging across shared correlations, duplicate suppression, all windows, attention,
unknown subjects/titles, event and related Inspector, original content, failure and retry,
obsolete search responses, company changes, native modal focus/dismissal and 16 EN/DE/NL/ES
light/dark mobile/desktop layouts. No shared business records are changed.

```sh
cd apps/web
PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs PLAYWRIGHT_EXECUTABLE=/path/to/chrome npm run test:activity-browser
npm run test:unified-browser
npm run test:contracts
npm run test:i18n
npm run i18n:audit
npm run format:check
npm run build
```

Existing PostgreSQL event-history tests cover the reused service's tenant, cursor and
business-context semantics. The complete backend suite remains a completion gate.

## Review and limits
No domain, service, tool, database or API source changes. Flat event rows avoid claiming
complete correlated processes or filtered totals. Unknown event titles retain the
server's language; original business values are preserved. Technical Explorer and
full legacy/practice retirement remain open. The old activity navigation contract is
explicitly scoped to the legacy app in WEB_SPEC; unified navigation uses this drawer.

Test-first: the new browser test first failed on the missing Activity header button.
After implementation, it passed paging, errors, stale results, tenant isolation,
inspection and responsive layout checks. Native dialog keyboard verification permits
browser chrome focus and confirms underlying workspace controls remain inert.


## Verified result — 2026-09-08
- Complete PostgreSQL suite: 1750 passed, 7 existing skips in 311.75 seconds; `/private/tmp/reality-134-backend.log`.
- New activity browser: all interaction scenarios and 16 layouts passed; `/private/tmp/reality-134-browser.log`; screenshots in `/private/tmp/reality-134-browser/`.
- Existing unified application and delivery browser suites passed; `/private/tmp/reality-134-existing-browser.log`.
- 131 frontend contracts and 100 localization tests passed. All 1869 audited keys per language covered; zero missing/invalid. Build, full frontend format check, lint, spec policy and diff whitespace checks passed.
- Final review: FR-001..006 covered; no schema, domain, service, tool or API changes; no shared business data mutations; no critical findings. Existing local Vite serves the change. No API restart or deployment needed.
