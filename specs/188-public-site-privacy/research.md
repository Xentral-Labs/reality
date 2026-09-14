# Research: Public Site Privacy

**Date**: 2026-09-13
**Status**: Technical decisions resolved; deployment/legal facts remain release dependencies.

## Static legal pages

**Decision**: Generate complete localized HTML using the existing Node build, with native
links and local CSS. Keep the marketing React application otherwise intact.
**Rationale**: Current `main.tsx` routes unknown paths to LandingPage and Nginx falls back
to index.html. React-only routes cannot meet FR-001 when scripts are unavailable.
**Alternatives considered**: A new SSR framework is unnecessary for eight documents;
duplicated handwritten translations/templates invite drift. A generator shares layout
while keeping each language's approved content explicit. No external CMS is required.

## Language storage

**Decision**: Remove durable language reads/writes; retain explicit URL/in-memory handoff
and existing authenticated profile fallback. Clean only legacy language storage.
**Rationale**: No reviewed necessity/retention decision exists. Inventing a one-year or
six-month cookie duration would create an unsupported processing claim. Source evidence:
Site LocalizationProvider, Docs LanguageBridge and App Auth currently remember on mount
or account load. Site handlers also discard other query parameters/fragments. Docs needs
explicit nl/es handoff through its English pages; App entry aliases need lang preserved.
**Alternatives considered**: Provenance-aware expiring cookies are possible after necessity
review but add state without current evidence. Merely removing Site's mount write is
insufficient because Docs/App can recreate the shared cookie. Cookie consent for language
alone creates avoidable UI and evidence complexity.
**Compatibility decision**: Anonymous direct reopen no longer remembers a prior language;
this is the approved spec's navigation-only fallback, and spec 176 must be updated.

## External assets

**Decision**: System font stack, no Google font request, and text presentation for the
remote Xentral logo unless licensed local bytes are supplied.
**Rationale**: `provider-site/index.html` contains font preconnects/stylesheets;
LandingPage's `xentralLogoUrl` points to Graphassets. A cookie banner does not eliminate
those requests. No unverified copying or provider assumption is needed.
**Alternatives considered**: Local font/image files are acceptable with verified rights,
but are not prerequisites when system fonts and existing text brand presentation suffice.

## Optional services

**Decision**: Empty optional-service inventory is the initial supported deployment.
Reject configurations adding optional services until the conditional design is reviewed.
**Rationale**: No tracker has been requested or identified in inspected source. Do not
build a generic consent subsystem for speculative services.
**Alternatives considered**: Always-on decorative banner creates a false choice; third-party
consent managers introduce a new provider and procurement without a demonstrated need.

## Evidence and publication

**Decision**: Validate input completeness and version binding automatically; require
separate human approval and actual deployment audit. Keep fixture builds non-publishable.
**Rationale**: `.github/workflows/deploy-testing.yml` targets runreality.ai, not merely a
private test host. Hosting logs and injected services cannot be inferred from the bundle.
**Alternatives considered**: A checklist without deployment enforcement permits accidental
publication; automatically declaring legal compliance from a passing scan is unsound.

## Sources and boundaries

Repository evidence: files named above, `apps/shared/language.ts`, `apps/web/src/Auth.tsx`,
`apps/web/src/entryRouting.ts`, `apps/docs/.vitepress/theme/components/LanguageBridge.vue`,
`docs/TEST_STRATEGY.md` and existing browser-test scripts. Bounded read-only language
research was delegated under the plan skill; no implementation was delegated or performed.

The [spec's legal reference baseline](spec.md#legal-reference-baseline) contains the
consulted primary legal sources. No new legal conclusion is asserted in this technical
plan. Real hosts, log retention, contracts, legal identity, translations and transfer
assessments must be supplied/reviewed before release; they are not technical ambiguities
that justify inventing defaults. No live-site audit has been performed.

## Hosting extension decisions

Choose a dedicated unversioned S3 bucket. Versioned current-object expiration adds a
delete marker rather than deleting old data; combining current/noncurrent 30-day rules
would exceed the requested retention. S3 lifecycle is asynchronous. Use SSE-S3, matching
ALB delivery support, with scoped service delivery and named administrator roles.
A CloudFormation prerequisite and opt-in Helm overlay fit the existing external AWS
resource ownership without adding another Terraform state or cluster operator.
Official references are recorded in `infra/privacy-logging/README.md`.

## Xentral source reconciliation (2026-09-14)

Official privacy source: https://xentral.com/de/legal/datenschutz (stated date 2026-02-09).
Section 13 names a US AWS entity;
section 14.16 names AWS EMEA SARL in Luxembourg. Neither establishes the contract for
Reality's AWS account. User questions covered privacy contact, contracting entity/DPA
and the final reviewer. No marketing plugin inventory or old legal boilerplate is copied.
Use independently drafted Reality-specific text and explicit unresolved sections.

The user subsequently selected internal review and removed the external privacy-provider
designation. The current draft lists only the confirmed controller contact.
