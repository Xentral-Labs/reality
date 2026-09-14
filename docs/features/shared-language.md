# Language continuity through navigation

Specs [176](../../specs/176-shared-language/spec.md) and
[188](../../specs/188-public-site-privacy/spec.md) define the shared presentation contract.
The public marketing site referenced by 188 is provider-operated and lives outside this repository.
Site, Docs and App links carry validated `lang=en|de|nl|es`, including explicit English.
URL language overrides the authenticated account fallback. Navigation never updates an
account or its number format/timezone.

No anonymous language preference is read from or persisted to cookies, localStorage or
sessionStorage. Each updated surface removes only obsolete `reality.language` localStorage
and host-scoped `reality_language`; known runreality.ai hosts also expire its parent-domain
cookie. Other hosts never receive a guessed parent domain. Blocked cleanup does not
prevent navigation. Old deployments can recreate legacy cookies until all surfaces update.

Docs supports en/de. Explicit nl/es choices render English Docs while retaining that
language in internal and outgoing links. Explicit en/de selection replaces the URL choice.
Topic paths, unrelated query parameters and fragments survive language changes.

A bare anonymous URL uses the surface default; cross-session anonymous recall is no longer
promised. An authenticated App visit can use its saved account language. Explicit profile
saves still use the existing service and update the current URL; merely loading an account
or following a link performs no profile write. Verification belongs to spec 188.
