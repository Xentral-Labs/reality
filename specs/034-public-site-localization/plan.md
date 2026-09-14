# Implementation Plan: Public Site Localization

**Branch**: `034-public-site-localization` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)
**Language**: English for all repository artifacts and review evidence.
**Status**: Specification and plan approved by the product owner on 2026-09-02.

## Summary

Turn the public site into a genuine four-language surface by adopting the product web's
localization pattern inside `provider-site`: English source text in the components, one
catalog per non-English language, and a translating provider that rewrites rendered text
and accessible labels when the language changes. The existing German wording is
extracted mechanically from today's bilingual conditionals so it survives verbatim;
Dutch and Spanish are written against the resulting English inventory. A site-owned
audit gate then fails whenever an advertised language is incomplete. No backend, schema,
API, or product-web change.

## Technical Context

**Language/Version**: TypeScript 5.8 with React 19 for the site; Node 22 for gates
**Primary Dependencies**: React, Vite, lucide-react, simple-icons, `typescript` (already a site dependency, used by the site's existing AST-based contract test)
**Storage**: None. Language preference stays in browser `localStorage`
**Testing**: `node --test` site contract, localization and audit tests plus Prettier `format:check`, `tsc -b` and the Vite build via `make site-build`
**Project Type**: Independent static browser deployment (`provider-site`)
**Constraints**: No API/tenant/auth dependency; no product-web import; no new runtime dependency; German wording preserved verbatim
**Scale/Scope**: 3 public routes plus 1 shared header; 419 discovered English strings (330 already paired with German); 3 non-English catalogs

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Presentation-only change. No source payload is received, no Evidence or Reality record is created or read, and no business rule is restated on the site. | PASS |
| Reality owns operational state | No status, inventory, or financial state is introduced. The site keeps describing Reality; it never computes it. | PASS |
| Proven schema only | No table, column, migration, or typed field. The only stored value remains the existing browser-local language preference. | PASS |
| Tenant + shared service boundaries | The site gains no API, auth, tenant, or service dependency; the independence contract test is extended, not relaxed. | PASS |
| Spec/test traceability | Every FR maps to a named test in the strategy table below; catalog completeness is enforced by an executable audit inside the site gate. | PASS |
| Explainable web behavior | Domain vocabulary stays identical across languages, so public copy keeps matching the product's own terms; no business logic moves into the browser. | PASS |
| Simplicity and storage discipline | Reuses the proven catalog pattern with no i18n framework, no SSR, no per-language route, and no new dependency. Cross-app reuse of the product web's audit library is rejected below with a concrete reason. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
provider-site/src/localization-core.ts             # translation lookup, money formatting, original-content rule (pure)
provider-site/src/localization.tsx                 # real provider: de/nl/es catalogs, t(), DOM translation
provider-site/src/LandingPage.tsx                  # English source only; drop the copy.de branch
provider-site/src/PlatformPage.tsx                 # English source only; runtime-value sentences keyed by placeholder
provider-site/src/WhyRealityPage.tsx               # English source only
provider-site/src/components/PublicHeader.tsx      # English source only; language control stays invariant
provider-site/scripts/i18n-invariants.mjs          # invariant declarations with reasons; non-copy rule
provider-site/scripts/i18n-audit-lib.mjs           # site-owned inventory/catalog audit
provider-site/scripts/i18n-audit.mjs               # gate entrypoint, non-zero exit on failure
provider-site/scripts/i18n-audit.test.mjs          # audit behavior incl. injected regressions
provider-site/scripts/site-localization.test.mjs   # structure, German parity, invariants, resolution
provider-site/scripts/site-contract.test.mjs       # existing claims re-pointed at English source + catalog
provider-site/package.json                         # test script covers the new proofs; i18n:audit script
provider-site/src/localization.tsx                 # generated catalog file, Prettier-formatted like the rest of the site
docs/WEB_SPEC.md                               # four-language public-site contract
docs/SPEC_COVERAGE_MATRIX.md                   # Public Site row evidence
specs/022-public-site/spec.md                  # FR-015/FR-025 language scope
Makefile                                       # site-build runs the audit
.github/workflows/quality.yml                  # site job runs the audit
```

Dependency direction stays one-way: page components → provider/catalog → pure
localization core. Gate scripts read source files; they are not shipped to the browser
bundle and add no runtime dependency.

## Design

### Source and catalog structure

`provider-site/src/localization.tsx` follows `apps/web/src/localization.tsx`: a `dictionaries`
object with `de`, `nl`, and `es` maps from English source string to translation, a `t()`
lookup with English fallback, and a `LocalizationProvider` that sets
`document.documentElement.lang`, translates the rendered document, and observes further
DOM changes so text rendered later is translated too. Reasons for reusing this shape
rather than a `t()` call at every call site: the site is static marketing copy with copy
inside SVG labels and deeply nested inline elements, the pattern is already proven in the
product web, and it keeps components readable as plain English source.

`provider-site/src/localization-core.ts` keeps the pure, directly testable parts:
`resolvePublicLanguage` as today, plus `resolveTranslation` and the original-content rule
that exempts `code`, `pre`, and anything marked `data-localization="original"`.

### Restructuring the bilingual components

Today's German wording is the approved reference and must survive verbatim, so it is
extracted mechanically rather than retyped: a one-time AST transform pairs every
`language === "de" ? german : english` conditional and every `copy.de`/`copy.en` key,
emits `english → german` catalog entries, and replaces the expression with its English
branch. Research already ran this transform against a copy of the site: 330 unique
English strings, zero conflicting German values, and only the two template-literal
sentences in `PlatformPage.tsx` need manual handling. The transform is throwaway
tooling and is not committed; the committed result is reviewed as a normal diff, and the
German parity test proves nothing was lost.

### Runtime values inside sentences

Two `/platform` sentences embed the configured early-access capacity, and one embeds the
cloud price. Splitting them into fragments would fix English word order, so instead the
catalog key keeps a numeric placeholder: before lookup, digit runs in the source text are
replaced by `{0}`, `{1}`, … and the captured values are substituted back into the
translated value. This keeps one grammatical sentence per language, lets each language
place the number where it belongs, and needs no per-language format function. The zero
capacity case keeps its separate waitlist wording and is catalogued as an ordinary
string.

### Monetary amounts and dead copy

Standalone amounts (the cloud price, the €0 self-hosted price, the finance example's
credit-note amount) are not copy: their currency position and decimal separator are a
locale property. They move to a pure `formatMoney(locale, value, fractionDigits)` in
`localization-core.ts` and render inside `data-localization="original"`, which keeps the
text translator away from an already formatted value. The locale is passed explicitly
because a page renders before the provider it returns publishes its preferences, so an
ambient locale would always be one render behind. Amounts inside sentences stay catalog
copy, where each language already writes them naturally.

Copy that no route renders is removed instead of translated: a dead `integrations`
constant, a duplicate of the header's navigation labels, and eleven `copy` keys whose
sections no longer exist. Translating them would inflate the inventory with text no
visitor can read and would hide what the site actually says.

### Invariants

The site declares its invariant strings with reasons, in the same spirit as the product
web's invariant list: product and domain terms (Reality, SourceRecord, Evidence, Fact,
Commitment, Reservation, Movement, Ledger Entry), brand and agent-system names, protocol
acronyms, business identifiers such as `R-2087`, diagram labels that are domain record
types, and accepted loanwords per language. Declared invariants are reported as invariant,
never as missing coverage. The language control keeps `data-localization="original"` so
`English`, `Deutsch`, `Nederlands`, and `Español` are never translated.

### Audit gate

`provider-site/scripts/i18n-audit-lib.mjs` walks `provider-site/src` with the TypeScript AST and
collects user-facing English text: JSX text, translatable JSX attributes, `t()` arguments,
copy-object and array string literals. It compares the inventory against the catalogs and
reports per language: covered, invariant, missing, invalid. Missing means no entry;
invalid means empty, whitespace-only, identical to the English source without an
invariant declaration, or missing a protected domain term the source contains.
`npm run i18n:audit` exits non-zero on any failure and `npm test` runs the audit tests, so
`make site-build` gates both.

The product web's `apps/web/scripts/i18n-audit-lib.mjs` is deliberately not imported.
The site is installed, tested, built, and deployed independently — CI installs only
`provider-site` — so importing that file would break the site gate through a missing
`typescript` resolution in the web workspace and would couple two independent
deployments. The site's audit is therefore its own smaller implementation over the same
concepts.

### Failure and fallback behavior

A missing catalog entry renders the English source; the visitor never sees an empty
string or an error. An unsupported or malformed `?lang=` value falls back to the stored
preference and then to English, exactly as today. Language switching mutates only
presentation state, so no request, storage write beyond the existing preference, or
navigation side effect is added.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-003, FR-004 | site unit/contract + browser | Catalog lookup, placeholder, and fallback behavior asserted directly against `localization-core.ts`; provider wiring asserted structurally in `provider-site/scripts/site-localization.test.mjs`; the rendered four-language result and the in-page switch recorded from a headless-browser session in `quickstart.md` | No catalog or provider behavior exists. |
| FR-002, SC-004 | source contract | Zero language conditionals and zero per-language copy branches in `provider-site/src` | Roughly 330 conditionals plus `copy.de` exist today. |
| FR-005 | site unit | Document titles and accessible labels resolve through `t()`/attribute translation | Titles are German-conditional today. |
| FR-006, SC-003 | parity regression | Pre-existing German sentences are asserted verbatim against the German catalog | German copy lives in components, not a catalog. |
| FR-007 | audit/provider unit | Unknown source string falls back to English | No lookup exists. |
| FR-008 | site unit | Price and capacity sentences render one sentence per language, including zero capacity | Template literals are English/German only. |
| FR-009 | audit + source contract | Protected term, identifier, and code-sample preservation | No protection rule exists. |
| FR-010 | source contract | Language control stays marked original and lists the four language names | Passes today; guarded against regression. |
| FR-011, FR-012, FR-013 | audit unit | Inventory/report shape plus injected missing, empty, English-duplicate, and dropped-term regressions in `provider-site/scripts/i18n-audit.test.mjs` | No audit exists. |
| FR-014, FR-017, SC-007 | gate + contract | `npm test` and `npm run i18n:audit` pass with only site dependencies; independence assertions extended to reject product-web imports | Audit script is absent. |
| FR-015, FR-016 | pure unit | `resolvePublicLanguage` and `accountHref` cases for all four languages plus malformed values | Partially covered; extended to four languages. |
| FR-018 | doc review | `022-public-site`, `docs/WEB_SPEC.md`, coverage matrix updated | Contracts still say English and German. |
| DR-001–DR-004 | diff/policy gate | No schema, service, API, or tenant change in the diff | Pass unless implementation oversteps. |
| SC-001, SC-002 | audit + review | Zero missing/invalid for de/nl/es; recorded four-language review per route in `quickstart.md` | Dutch and Spanish are absent. |

Tests are added before the behavior they prove: the audit and structure proofs are
written first and observed failing against today's bilingual sources, then the
restructuring, catalogs, and translations make them pass.

## Rollout and Rollback

The change is presentation-only and ships with the static site image. No migration, no
feature flag, no data backfill. Rollback is a revert of the site sources, catalogs, and
gate scripts; visitors return to the bilingual site with the same URLs, the same stored
preference key, and the same account links. Because English remains the fallback, a
partially reverted catalog degrades to English rather than breaking a route.

## Review Risks

- Dutch or Spanish copy that silently reinterprets a domain term. The protected-term
  audit rule and the invariant declarations bound this risk; reading fluency is not
  certified by this feature and is not claimed anywhere in its evidence.
- Losing or rewording a German sentence during the mechanical restructuring; the parity
  test exists specifically to catch this.
- An audit that passes because its inventory is too narrow. The inventory must cover JSX
  text, translatable attributes, copy objects, arrays, and `t()` arguments, and the
  discovered count is recorded in `quickstart.md`.
- Over-broad invariant declarations used to make the gate green instead of translating.
- A DOM-translating provider that also rewrites code samples, payload examples, or
  business identifiers.
- Reaching into `apps/web` for tooling and breaking the site's independent gate.
- Disturbing concurrent work in the shared worktree; this feature touches only
  `provider-site`, its own spec directory, and the three named contract documents.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | Importing the product web's audit library was rejected because the public site installs and gates independently; a site-owned audit keeps the deployment boundary intact. | Product owner, 2026-09-02 |

## Post-Design Constitution Re-check

All rows remain PASS. The design stays inside the presentation layer, adds no dependency
to the runtime bundle, keeps domain vocabulary identical across languages, and introduces
no schema, service, or tenant surface.
