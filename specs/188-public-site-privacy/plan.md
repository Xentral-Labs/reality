# Implementation Plan: Public Site Privacy and Legal Information

**Branch**: `188-public-site-privacy` in isolated worktree `/private/tmp/reality-188`.
**Date**: 2026-09-13 | **Spec**: [spec.md](spec.md)
**Language**: English
**Status**: Implemented with fixture-based verification; real legal inputs and release approval remain pending.

## Summary

Implement an essential-only public site: static, localized imprint/privacy pages,
no remote fonts or imagery, no durable browser language preference, and explicit
language handoff across Site/Docs/App. Add a small release-input validator and an
observable network/storage audit. Do not add a consent library, backend or database.
Unknown operator/provider facts remain release blockers, not made-up configuration.
The approved spec remains authoritative; conditional optional-service requirements
are satisfied by proving no optional services are configured. Retaining one requires
an amended design and tasks before activating it.

## Technical Context

**Language/Version**: Existing TypeScript/React 19/Vite 7 site; Node 22 scripts; Vue/VitePress Docs.
**Dependencies**: Existing toolchain and browser-test convention; no production dependency added.
**Storage**: Versioned public legal content and deployment inventory; no database changes or new browser storage.
**Testing**: Node test runner, existing language/browser scripts, Playwright browser observations, build and repository gates.
**Project Type**: Independent static public site with a shared presentation-language helper.
**Constraints**: Four site languages; no-JavaScript legal access; no tenant requests from Site;
legal/operator reviews cannot be replaced by automated checks.
**Scale/Scope**: Three marketing routes plus eight legal documents; shared-language callers in Docs/App.
**Unknowns**: No unresolved technical decision. Operator identity, provider facts, legal copy,
asset rights and human reviews are publication dependencies tracked in the release contract.

## Constitution Check _(blocking gate)_

| Principle                          | Evidence in this plan                                                             | Result |
| ---------------------------------- | --------------------------------------------------------------------------------- | ------ |
| Source → Evidence → Reality        | Presentation/legal information only; no operational records                       | PASS   |
| Reality owns operational state     | No document status or business rule changes                                       | PASS   |
| Proven schema only                 | No schema, migration, consent table or business identity                          | PASS   |
| Tenant + shared service boundaries | Site stays independent; existing authenticated profile save path unchanged        | PASS   |
| Spec/test traceability             | Approved scope; test-first matrix below; tasks and analyze required before coding | PASS   |
| Explainable web behavior           | Legal disclosures trace to inventory and reviewed operator facts                  | PASS   |
| Received values not recomputed     | Operator/provider facts preserved, unknowns not inferred                          | PASS   |
| Smallest coherent design           | Static generator and URL handoff; no new framework or consent infrastructure      | PASS   |

Pre-design and post-design assessment: all rows PASS. This is an engineering design
assessment, not legal approval or completion evidence. No constitutional exceptions.

## Repository Structure and Layer Changes

Existing paths to change:

- `provider-site/src/components/PublicFooter.tsx`, `PublicHeader.tsx`, `src/site-routing.ts`:
  legal links and lossless language-aware internal navigation.
- `provider-site/src/LandingPage.tsx`, `PlatformPage.tsx`, `WhyRealityPage.tsx`,
  `localization.tsx`: remove automatic persistence and duplicate destructive URL updates.
- `provider-site/index.html`, `src/site.css`, `src/landing.css`, `src/platform.css`: remove Google Fonts,
  use the system font stack; remove remote Xentral logo request in LandingPage.
- `apps/shared/language.ts`: URL/in-memory presentation selection and narrow legacy cleanup.
- `apps/docs/.vitepress/theme/components/LanguageBridge.vue`, `ProductLink.vue`:
  preserve explicit handoff through internal Docs links and fallback languages.
- `apps/web/src/Auth.tsx`, `entryRouting.ts`: preserve lang through existing entry redirects,
  keep account language fallback and explicit profile saves; no automatic profile write.
- `provider-site/package.json`, `Dockerfile`, `nginx.conf`, `vite.config.ts`:
  legal generation in build/dev, direct static routes, release input validation.
- `.github/workflows/quality.yml`, `.github/workflows/deploy-testing.yml`:
  run tests/audits and ensure the public-site publication path cannot deploy fixture inputs.
- `scripts/deploy_railway_demo.sh` and site build documentation: apply the same public
  artifact gate to alternate publication paths, without redesigning deployment infrastructure.
- `specs/176-shared-language/spec.md`, `docs/WEB_SPEC.md` and new
  `docs/features/public-site-privacy.md`: document changed persistence and verified evidence.

Planned new files:

- `provider-site/legal/deployment.json`, `provider-site/legal/content/{en,de,nl,es}.json`:
  public deployment facts, structured legal paragraphs and review references.
- `provider-site/scripts/legal-content.mjs`: pure validation/rendering helpers with escaped text.
- `provider-site/scripts/generate-legal-pages.mjs`: generate static HTML and local CSS into
  `dist/`; integrate the same rendering in development, without shipping preview fixtures.
- `provider-site/scripts/legal-content.test.mjs`, `public-privacy.test.mjs`,
  `public-privacy-browser.mjs`: legal-input, route/asset and behavioral proofs.
- `provider-site/scripts/fixtures/legal/`: unmistakably fictional test-only records.
- `docs/privacy/releases/`: release dossiers keyed by deployment and candidate digest,
  with links to restricted evidence when provider agreements contain non-public data.

Domain → services → tools: no change is justified. Work starts with pure presentation
helpers/tests, then Site/Docs/App adapters and deployment checks. No application command,
view, event or catalog changes are planned; docs generation must remain clean.

## Design

### Reality flow

Not applicable to website legal preferences. Public identity facts are rendered as
approved and are not translated into Business Reality entities. No tenant/API access
is added. A release dossier is engineering evidence, not a SourceRecord.

### Service and adapter flow

1. Validate deployment metadata and legal documents at build time. Use structured text
   with explicit links and HTML escaping, not arbitrary raw HTML, scripts or remote embeds.
2. Generate `/imprint/`, `/privacy/` and `/de/`, `/nl/`, `/es/` equivalents. Each is a
   complete UTF-8 HTML document with lang, title, headings, local CSS, navigation and footer.
   English has no locale prefix. No JavaScript is required for legal pages or locale links.
3. Add direct legal links to the shared React footer. Use native links to equivalent
   legal translations; static legal return links carry `?lang=` including explicit English.
4. Nginx serves the eight generated documents before SPA fallback. Normalize slashless
   legal URLs to their canonical paths; missing legal assets must return an error, never
   silently serve the marketing shell. Verify `www` path preservation at the host edge.
5. Remove font preconnect/stylesheets; use installed system fonts. Replace the remote
   Xentral logo with the existing plain-text brand presentation unless a separately
   verified licensed local asset is supplied. No new image-generation step is needed.
6. Shared language resolves validated URL selection, then in-memory selection for the
   current page; App may use its existing authenticated profile fallback. Explicit choices
   surgically update lang while preserving path, other query parameters and fragment.
   Do not turn inferred defaults into explicit choices or save them automatically.
7. Carry lang through internal Site/Docs navigation, external handoff and App entry aliases.
   Docs renders English for nl/es while preserving the original explicit choice through
   navigation and outgoing links. New direct anonymous visits without lang use the surface
   default; cross-session anonymous preference retention is deliberately removed.
8. Perform best-effort cleanup of only the legacy language key and cookie, without reading
   their values. Do not clear all storage. Authenticated profile data and session cookies
   remain untouched. Details are in the data model and UI contract.

### Release input and review flow

Keep build validation separate from legal judgement. The validator can require complete
facts, content versions, classifications, review identity/date and evidence references;
it cannot establish that a reviewer is qualified or that a legal conclusion is correct.
Human review of the dossier remains mandatory.

Ordinary CI may generate clearly marked non-publishable preview artifacts from explicit
fixtures. A public release build must reject fixtures, missing translations, unresolved
inventory rows, absent reviews and stale content/inventory digests. Do not fall back to
example operator information. Production Docker and publication workflows must explicitly
select release validation, including the workflow named `Deploy (testing)`, whose URLs
point at runreality.ai. Generic self-hosted images require their operator's inputs rather
than inheriting production identity. No live environment is changed during this plan.

Use two distinct checks: before candidate generation validate reviewed operator/content/
inventory inputs; after generation validate browser-test evidence and approval for the
actual artifact digest before public promotion. Candidate approval/digest is an external
dossier, never embedded into the artifact being hashed. Fixture-only builds cannot be
promoted. This is one candidate build followed by approval, not a rebuild after approval.

Avoid a circular gate: pre-publication approval binds legal content/inventory and the
candidate artifact digest; candidate browser tests run in an isolated preview. The same
artifact is then smoke-audited on the actual deployment. The dossier remains pending
post-deploy verification until that audit succeeds. Unexpected processing requires removal,
disabling or rollback to a previously approved compliant artifact, not the old known gap.
A fixture artifact must never pass the public deploy gate, even if all its unit tests pass.

### Data and migration impact

No Alembic migration or backend table. Delete legacy language preferences on the host
where they are accessible. A production parent-domain cookie can be expired only on
known runreality.ai hosts; unrelated hosts do not receive an inferred parent domain.
Removal does not need a new versioned browser record. Legal approvals/digests live in
release evidence and must not contain confidential provider contracts in public assets.

### Failure, security, and tenant behavior

Invalid/blocked storage does not break navigation. Unknown provider/retention/identity
blocks release, not source editing or local tests. The default optional-service list is
empty; adding an item fails the current release validator with an actionable error.
There is no optional runtime that could fail open. Preserve authenticated profile service
calls and confirmation boundaries; do not write account language on login or URL handoff.
There are no new schedulers: six-month review is an assigned operational responsibility.

## Test Strategy and Traceability

Write meaningful failing proofs before implementation where practical. Browser observations
are required; source-string assertions alone cannot prove absence of tracking.

| Requirements          | Level and planned evidence                                                                                                                                      | Expected initial failure                                                           |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| FR-001                | legal-content.test.mjs plus public-privacy-browser.mjs: eight routes, direct loads, scripts disabled, redirects                                                 | Legal routes currently render SPA fallback                                         |
| FR-002–FR-003, FR-013 | legal-content.test.mjs invalid-input/digest tests; manual operator/legal/provider dossier review                                                                | No legal input validation or approved content                                      |
| FR-004                | Generator locale tests; browser keyboard/mobile checks; manual screen-reader and translation review                                                             | No legal translations/pages                                                        |
| FR-005–FR-006         | public-privacy.test.mjs and browser request/storage instrumentation; provider/logging inventory and license review                                              | Google Fonts and Graphassets requests present                                      |
| FR-007                | provider-site/scripts/shared-language.test.mjs and shared-language-browser.mjs; apps/web/scripts/entry-routing.test.mjs; apps/docs/scripts/header-browser-check.mjs | Default mount persists language; current handlers drop URL state                   |
| FR-008–FR-012         | Empty-optional-inventory, no-banner, and rejection of configured optional-service tests                                                                         | No inventory enforcement; runtime consent tests inapplicable while services absent |
| FR-014–FR-015         | Candidate/deployment audit evidence; gate rejects missing/stale evidence; human review ownership/change-trigger exercise                                        | No dossier or deployment gate                                                      |
| DR-001–DR-003         | Diff/no-schema review, Site no-API proof and cross-surface browser mocks asserting no account mutation                                                          | Existing language helper performs unnecessary persistence                          |

FR-009–FR-012 are conditional, not declared implemented consent controls. If retaining a
service becomes necessary, revise this plan, data model, tasks and analyze first; include
pre-consent, reject, subset, withdrawal, multi-tab, expiry, changed-provider and failure tests.

Implementation verification: `make spec-check`, `make lint`, full required `make test`
with PostgreSQL, `make site-build`, `make web-build`, `make docs-build`, and
`make docs-catalog-check`; run browser language/privacy proofs and production image smoke.
Also update `apps/docs/scripts/header-browser-check.mjs` to stop waiting for the removed
localStorage key, and review `apps/web/scripts/company-danger-zone-browser.mjs`, which
seeds that key: intended language setup must use an explicit URL.
No new backend test is justified solely to mirror an unchanged backend. Preserve required
CI checks; record actual results, not assumed passes. Manual legal/screen-reader/host checks
must have dated evidence. These checks have not been run for unbuilt behavior in this phase.

## Rollout and Rollback

1. Complete tasks/analyze before coding. Implement and verify using fixture-only local previews.
2. Obtain reviewed real inputs, confirm actual deployment inventory, and build candidate.
3. Test complete candidate and language changes across the three surfaces. Coordinate releases
   so an old Docs/App helper cannot recreate the removed parent-domain cookie unnoticed.
4. Approve publication only with the pre-release dossier; perform deployed smoke immediately.
5. On failure, disable offending processing or restore the last compliant artifact. Never
   restore optional processing or invalid legal copy simply to recover an old visual design.

Rollback may remove the new preference behavior but must not reintroduce automatic durable
storage. No database rollback exists. Keep content/inventory/evidence versions together.

## Review Risks

- Actual operator/provider facts remain unknown; an engineering plan is not a legal sign-off.
- Changing shared language removes anonymous cross-session recall from spec 176; explicit
  handoff and authenticated profile preferences remain and need regression proof.
- A React-only legal page cannot satisfy the no-script requirement; test actual HTML response.
- Deployment called testing uses public production domains; it must not bypass release gates.
- Preview and release artifacts must not be confusable; fail closed for public publication.
- Other simultaneous work uses the shared checkout; this plan changes only spec 188 artifacts.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| ---------------------- | ---------- | ---------------------------- | -------- |
| None                   | —          | —                            | —        |

## Implementation notes

See [verification.md](verification.md) for actual evidence and open manual checks.
The known shared-language feature contract and coverage matrix also required updates.
Real translated content is resolved from four locale JSON files; fixtures may inline it.
A document-lifetime choice and account fallback preserve SPA navigation without durable storage.
Promotion validates the current reviewed input as well as the candidate artifact, so a
changed provider/retention fact invalidates an old candidate even before rebuilding.

## Hosting extension plan (2026-09-14)

Use a standalone CloudFormation S3 prerequisite in `infra/privacy-logging/`, matching
the chart's existing external AWS prerequisite boundary. No controller, new scheduler
or runtime dependency is needed. Require real administrator role ARNs as parameters;
never infer administrators from arbitrary local credentials. Use a deterministic bucket
name containing the AWS account and region and prefix `alb`. Leave versioning absent
and explicitly prevent administrators from enabling it or replication/Object Lock
through the bucket's policy without a reviewed policy change.

Apply an explicit Helm overlay only after the bucket exists; do not turn on an ALB
bucket reference in the default GitOps values before provisioning. Preserve the existing
300-second ALB idle timeout. Disable request access logs in all three Nginx configs and
the API/MCP Uvicorn entrypoints. Nginx errors remain on stderr at warn level. Existing
application/error collectors require exact group names and a 30-day retention setting;
unknown collectors block live completion rather than creating an unused log group.

Tests first: Python standard-library tests exercise a read-only AWS evidence validator
with adversarial region/encryption/public-policy/lifecycle/versioning/delivery/retention
fixtures; validate template and overlay constraints; run effective Nginx configuration
and request smoke checks where Docker is available. Use CloudFormation lint plus Helm
rendering when tooling is available. Add a metadata-only AWS CLI verifier and an ordered
runbook. It must not read visitor log contents or grant publication approval.

Constitution Check: PASS for all principles. No business data, schema, tenant queries,
chat mutations or scheduling changes. User approved infrastructure mutations; no live
credentials are currently configured. Order: spec review (explicit user request), this
plan, tasks, analysis, tests, implementation, checks, review. Live operations remain
pending until credentials and administrator roles are supplied.

## Real-operator draft preview design

Extend the existing build validator with a third explicit mode, `draft`, using
`legal/draft/deployment.json` (`fixture: false`, `draft: true`). Only this mode may
render unresolved blockers. It still validates identity, content, links and inventory
shape. Candidate mode rejects draft input before review checks; promotion already
requires candidate metadata. Render localized draft banners and noindex; generate
robots disallow for drafts. Existing fixture preview defaults stay unchanged.
Add adversarial tests before implementation and rebuild only the local Site preview.
Constitution Check: PASS; presentation/build-only extension, no domain/schema changes.

## Final Railway demo legal-page design

Add an explicit `demo` mode that starts from the reviewed real-operator content, applies
a small Railway-specific hosting inventory and localized replacements for delivery,
retention and international-processing sections, and binds the output origin to the
required Railway `SITE_URL`. Demo output has no draft banner but remains non-indexable
and cannot pass candidate promotion. The canonical AWS content and approval path do not
change. Tests generate all four locales and reject AWS/draft wording. Constitution
Check: PASS; this changes static presentation/build inputs only, with no schema, domain,
tenant or operational-service behavior.
