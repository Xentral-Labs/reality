# Quickstart: Verify Inline Row Previews

## Static and build gates

```sh
make spec-check
cd apps/web
npm run test:contracts
npm run i18n:audit
npm run build
```

Expected: all commands pass and no migration is generated.

## Browser journey

Against an isolated frontend test server, verify desktop and mobile:

1. Commitments, Exceptions, and Decisions open below their list item.
2. Sales, Purchasing, Warehouse, Finance, and each Master Data family open below their table row.
3. A second preview replaces the first; context changes clear stale previews.
4. Preview, navigation, filter, edit, and operational controls have distinct semantics.
5. Failures stay inline with retry and close.
6. Edit and operational actions retain explicit workflows and confirmation.
7. Deeper inspection still reaches Reality, Evidence, and Source.

## Diff review

Confirm changes are limited to frontend presentation/tests and Web UI documentation, with no service, database, migration, or calculation changes.

## Verification evidence — 2026-09-10

- `make spec-check`: PASS.
- Frontend contracts: 88/88 PASS, including four new inline-preview contracts.
- Production TypeScript/Vite build: PASS.
- Localization audit: PASS for English, German, Dutch, and Spanish (1225/1225 each).
- Prettier check: PASS.
- Daily-work browser matrix: PASS for Commitments, Exceptions, and Decisions in English/German, light/dark, desktop/mobile (24 opened-preview journeys); zero write requests.
- Finance browser matrix: PASS for Open items, Payments, and Journal including paging, filters, inline preview reload, company reset, retry, four languages, light/dark, desktop/mobile (48 screenshots); zero write requests.
- Visual review: an opened Commitment preview remains attached to its row at 1440 px and 390 px without page-level horizontal overflow.
- Follow-up review requires the preview chevron in a fixed trailing action slot and uses a two-column desktop information hierarchy with one-column mobile reflow.
- Diff review: frontend presentation/tests plus Web UI and Spec Kit artifacts only; no backend, service, domain, database, or migration changes.
