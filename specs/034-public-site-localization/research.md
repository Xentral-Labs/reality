# Research: Public Site Localization

**Language**: English. Date: 2026-09-02.

## R1 — Why Dutch and Spanish do not change the page

Observed in `provider-site/src`:

- `LandingPage.tsx` selects copy with `copy[language === "de" ? "de" : "en"]`, and `copy`
  contains only `en` and `de`. Dutch and Spanish therefore resolve to English by
  construction.
- `PlatformPage.tsx`, `WhyRealityPage.tsx`, and `components/PublicHeader.tsx` decide copy
  with `const de = language === "de"` and inline `de ? … : …` expressions, which behave
  identically for `nl` and `es`.
- `localization.tsx` is a seven-line stub whose `LocalizationProvider` renders children
  and ignores `preferences`; there is no catalog and no lookup.
- What does change on selection: the header language code, `localStorage`
  (`reality.language`), the `?lang=` query, `document.documentElement.lang`, and the
  `locale` passed to the stub provider. This is why the control appears to work.
- `components/PublicHeader.tsx` offers all four languages, and
  `localization-core.ts` accepts all four in `resolvePublicLanguage`.

Conclusion: the defect is a missing translation layer on the site, not a broken switch.

## R2 — Contract status before the change

- `specs/022-public-site/spec.md` FR-015 and FR-025 specify English and German only, so
  today's behavior is not a violation of an existing requirement; four-language support
  is a product-scope decision. The product owner took that decision on 2026-09-02.
- `docs/WEB_SPEC.md` "Public product page" states English default plus `/?lang=de` for
  the complete German version.
- `specs/017-complete-web-localization/spec.md` already proves four-language coverage for
  the product web with catalogs, invariant declarations, and an auditing gate. It is the
  pattern to follow, not a contract the site currently satisfies.

## R3 — Size and shape of the text inventory

A throwaway AST transform paired every German alternative with its English counterpart
across the four public-site component files:

- 330 unique English source strings.
- 0 conflicting German values, so one English key never needs two German translations.
- 2 nodes needed manual handling, both in `PlatformPage.tsx`: template literals embedding
  `earlyAccessLimit`.
- Copy shapes covered: `copy.en`/`copy.de` objects including nested tuple arrays,
  conditional string literals in JSX text, conditional string literals in JSX attributes,
  conditional arrays (`features`, `chain`), and `document.title` assignments.

This confirms the German catalog can be produced mechanically and reviewed as a diff,
and it fixes the translation volume for Dutch and Spanish at 330 strings each.

## R4 — Provider shape: DOM translation versus per-call-site `t()`

`apps/web/src/localization.tsx` translates the rendered document with a TreeWalker and a
MutationObserver, protecting `code`, `pre`, and `data-localization="original"` subtrees,
and also translates `placeholder`, `aria-label`, and `title` attributes.

Chosen for the site because public copy sits in SVG `<text>` labels, inline `<b>`/`<small>`
fragments, and long nested sections where per-call-site `t()` would be invasive; because
it keeps components as readable English source; and because it is already proven in the
product web. `t()` remains exported for values outside the document body, specifically
`document.title`.

Rejected alternative: keeping per-page `copy` objects with four language branches. It
duplicates 330 strings four times inside components, keeps language conditionals in the
markup, and diverges from the product web.

## R5 — Runtime values inside translated sentences

`/platform` embeds `earlyAccessLimit` in two sentences and `cloudPrice` in a price line.
Options considered:

1. Split the sentence into text fragments around the value. Rejected: it hard-codes
   English word order, and German already places the number differently.
2. Per-language format functions in the catalog. Rejected: it makes the catalog
   heterogeneous and untestable by a simple string audit.
3. Numeric placeholder keys: normalize digit runs to `{0}`, `{1}`, … for the catalog key
   and substitute the captured values back into the translated value. Chosen: one
   grammatical sentence per language, free number placement, and the catalog stays a
   plain string map that the audit can verify.

## R6 — Why the site cannot reuse the product web's audit library

CI's `site-quality` job runs `cd provider-site && npm ci && npm test && build` and never
installs `apps/web`. `apps/web/scripts/i18n-audit-lib.mjs` imports `typescript`, which
Node resolves from `apps/web/node_modules`; that directory does not exist in the site job,
so a cross-app import fails the gate. Beyond CI, `022-public-site` established the site as
an independently deployed application. The site therefore gets its own smaller audit over
the same concepts (inventory, catalogs, invariants, missing/invalid classification), and
`typescript` is already a site dependency used by the existing `site-contract.test.mjs`.
