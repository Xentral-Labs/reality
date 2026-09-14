# Quickstart: Validate Public Site Localization

## Prerequisites

- Node 22 with the public site's own dependencies installed (`cd provider-site && npm ci`).
  No product-web installation and no backend service is required.

## Gates

```bash
cd provider-site
npm run format:check
npm test            # site contract, site localization, and audit behavior proofs
npm run i18n:audit  # four-language coverage report, non-zero exit when incomplete
APP_URL=https://app.runreality.ai npm run build
```

`make site-build` runs the same four steps in order.

## Recorded results (2026-09-02)

```text
en: PASS — 419/419 covered, 0 invariant, 0 missing, 0 invalid
de: PASS — 419/419 covered, 82 invariant, 0 missing, 0 invalid
nl: PASS — 419/419 covered, 89 invariant, 0 missing, 0 invalid
es: PASS — 419/419 covered, 76 invariant, 0 missing, 0 invalid
```

- `npm test`: 36 tests, 36 pass, 0 fail.
- `npm run format:check`: all matched files use Prettier code style.
- `npm run build`: `tsc -b` clean; Vite built the client bundle.
- Inventory: 419 discovered English strings across the landing, `/platform`,
  `/why-reality`, and the shared public header. 331 of them were paired mechanically with
  their existing German wording; the remaining German gaps were places where the
  bilingual site had silently rendered English inside the German page.

## Four-language browser verification

Served with `npm run dev` and driven through headless Chrome (`--dump-dom` plus a
DevTools `Runtime.evaluate` session for the in-page switch):

| Check | Result |
|---|---|
| `/` in en/de/nl/es | Headline, intro, navigation, SVG diagram labels, and the `aria-label` on the core map all render in the selected language; `<html lang>` matches. |
| `/platform` in en/de/nl/es | Title, hero, prices, and both capacity sentences render in the selected language, with the runtime capacity value in place (`250 early-access spots`, `250 Early-Access-Plätze`, `250 early-access-plekken`, `250 plazas de acceso anticipado`). |
| `/why-reality` in en/de/nl/es | Title, hero, graph labels, and vocabulary render in the selected language; the JSON payload sample stays byte-identical; `Evidence`, `Fact`, `Commitment`, `Reservation`, `Movement`, and `Ledger Entry` stay unchanged. |
| In-page switch en → nl → es → de → en → nl | Every switch re-renders all copy without a reload; switching back and forth never leaves a stale translation. |
| Language control | `English`, `Deutsch`, `Nederlands`, `Español` stay in their own language in every selection. |
| Documentation link | `Docs` / `Dokumentation` / `Documentatie` / `Documentación`. |
| Monetary amounts | en `€1 / €0 / €49.00`, de `1 € / 0 € / 49,00 €`, nl `€ 1 / € 0 / € 49,00`, es `1 € / 0 € / 49,00 €`; they follow an in-page switch, and the German rendering matches what the bilingual site showed. |
| Stored preference | Loading `/` without `?lang=` after a previous Dutch selection renders Dutch, as the documented query → stored → English order requires. |
| German regression | Pre-existing German wording is unchanged (`Damit deine Agenten dein Business wirklich verstehen.`, `Agentic Core`, `Pakete`, `Verifizierte Accounts können innerhalb der ersten 250 Plätze sofort starten. …`). |

## Injected-regression check

Each of these must fail `npm run i18n:audit` (and the audit test covers the same four
cases against fixtures):

1. Add new English copy to a public component without catalog entries → `missing`.
2. Blank one catalog value → `invalid`.
3. Copy an English value verbatim into a catalog without declaring it invariant → `invalid`.
4. Remove `Reality` from a translation whose English source contains it → `invalid`.

## Notes for review

- `provider-site/src/localization.tsx` is the only place holding non-English public-site text.
- Invariant strings are declared with reasons in `provider-site/scripts/i18n-invariants.mjs`.
- Copy that rendered nowhere was removed from `LandingPage.tsx`: the dead `integrations`
  constant and twelve `copy` keys whose sections no longer exist, including a duplicate of
  the header navigation labels. They are recoverable from git history if a section returns.
- Standalone monetary amounts are formatted by `formatMoney(locale, value, digits)` in
  `localization-core.ts` and rendered inside `data-localization="original"`. The locale is
  passed explicitly because a page renders before the provider it returns publishes its
  preferences. Amounts inside sentences remain catalog copy.
- German wording is unchanged and needs no re-approval. For Dutch and Spanish, automated
  coverage is the evidence; editorial native-speaker certification remains outside this
  feature's claim.
