# Quickstart: Prominent Open-Source Entry

## Automated proof

```bash
make spec-check
cd provider-site && npm test
cd provider-site && npm run i18n:audit
make site-build
```

Expected: specification policy, Site contracts, all four language catalogs, and production build pass.

## Visual and interaction proof

1. Start the Site with `make site`.
2. Open `/`, `/why-reality`, and `/platform` at representative desktop and mobile widths.
3. In light and dark system appearance, confirm the labelled GitHub entry is visible in the applicable navigation state.
4. On `/`, confirm the section precedes the account CTA, remains visually distinct, and offers exactly repository and Docs actions.
5. Navigate the header, mobile disclosure, and both section actions with the keyboard.
6. Repeat the content check for `?lang=de`, `?lang=nl`, and `?lang=es`.

## Verification record — 2026-09-04

- `make spec-check`: PASS.
- `make site-build`: PASS, including 48/48 Site tests, formatting, complete EN/DE/NL/ES catalogs, and production build.
- `make web-build`: PASS, including 75/75 Product Web tests, complete EN/DE/NL/ES catalogs, formatting, and production build.
- `make docs-build`: PASS, including 37/37 Docs tests, formatting, and production build.
- `git diff --check`: PASS.
- Final diff review: PASS for FR-001–FR-006, FR-008–FR-010, and DR-001–DR-004; automated responsive and accessibility contracts for FR-007 pass.
- Browser visual review: PENDING because no in-app or extension browser was available in the execution environment. No substitute browser automation was used.
