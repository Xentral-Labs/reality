# Contract: Public Site Localization

## Advertised languages

| Language | Code | `?lang=` value | Public routes |
|---|---|---|---|
| English | `en` | omitted | `/`, `/platform`, `/why-reality` |
| German | `de` | `?lang=de` | `/`, `/platform`, `/why-reality` |
| Dutch | `nl` | `?lang=nl` | `/`, `/platform`, `/why-reality` |
| Spanish | `es` | `?lang=es` | `/`, `/platform`, `/why-reality` |

All four render complete public-site copy. The header language control lists exactly
these four and no other.

## Resolution order

1. A supported `?lang=` value on the current route.
2. The stored `reality.language` preference when it is a supported value.
3. English.

An unsupported or malformed value is ignored at its level and resolution continues. No
error state, empty render, or redirect is produced.

## Selection effects

Selecting a language updates, without a page reload: rendered public-site copy,
`document.documentElement.lang`, the stored preference, and the route URL (`/` for
English, `?lang=<code>` otherwise). Sign-in and account-creation links keep pointing at
the configured product-web origin with the selected language preserved.

## Source of truth for text

- Components contain English source text only. No language conditional and no
  per-language copy branch is allowed in `provider-site/src`.
- `provider-site/src/localization.tsx` holds one catalog per non-English language, keyed by
  the English source string.
- A source string absent from a catalog renders its English text.
- Document titles and accessible labels are localized like page copy.

## Never translated

Product and domain terms (Reality, SourceRecord, Evidence, Fact, Commitment, Reservation,
Movement, Ledger Entry), brand and agent-system names, protocol acronyms, business
identifiers such as `R-2087` or `COM-C-2087-R2`, code samples and payload examples, and
the language names inside the language control.

## Coverage gate

`npm run i18n:audit` in `provider-site` reports per language: covered, invariant, missing,
invalid. It exits non-zero when any required translation is missing, empty, identical to
its English source without an invariant declaration, or drops a protected domain term the
source contains. The audit runs with only the public site's own dependencies installed
and must not import product-web tooling.
