# Verification: Public Site Privacy

**Date**: 2026-09-13
**Implementation location**: isolated worktree `/private/tmp/reality-188`, branch `188-public-site-privacy`.
**Baseline**: `feabb87`; no unrelated checkout was switched or overwritten.
**Status**: Technical implementation and verification complete; real operator/legal/publication review pending.

## Gates and scope

The owner approved spec scope on 2026-09-13 and requested implementation. The 16-item
requirements checklist was read without modification and passed. The plan's eight
Constitution rows passed; the preceding tasks analysis reported no critical/high issues
and covered 18 FR/DR plus six success criteria. No extension hooks are configured.
No schema, operational record, application tool or business service changes were made.

## Test-first evidence

- `/private/tmp/privacy-188-red.log`: new legal module unavailable, external asset/footer
  tests failing and language persistence regression failing before implementation.
- `/private/tmp/privacy-188-entry-red.log`: validated language lost by legacy entry aliases.
- `/private/tmp/privacy-188-date-red.log`: impossible calendar review date accepted before repair.
- Browser iteration found and repaired mobile Platform overflow and an absolute Nginx
  redirect that lost the mapped port. The mobile grid now wraps and redirects are relative.

## Verified technical checks

| Check                                                                                                                                                             | Result                                                                           | Evidence                                                                                                        |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Site formatting, Node tests, four-language audit and production build                                                                                             | PASS: 71 tests, zero failures                                                    | `/private/tmp/privacy-188-site-final.log`                                                                       |
| Web formatting, 151 Node tests, translations and build                                                                                                            | PASS                                                                             | `/private/tmp/privacy-188-web-final.log`                                                                        |
| Docs reference tests, Node tests, formatting and build                                                                                                            | PASS                                                                             | `/private/tmp/privacy-188-docs-final.log`                                                                       |
| Docs generated catalog freshness                                                                                                                                  | PASS                                                                             | `/private/tmp/privacy-188-catalog-final.log`                                                                    |
| Privacy browser: 3 marketing routes × 4 languages × 2 viewport sizes, eight no-script legal routes, reload, keyboard, missing route, storage restrictions/cleanup | PASS                                                                             | `/private/tmp/privacy-188-browser-final.log`; `/private/tmp/reality-188-privacy-evidence/results.json` and PNGs |
| Language browser: Site → Docs → App → Site, all four languages, internal Docs/reload, explicit English, profile conflict/save, no unintended account writes       | PASS                                                                             | `/private/tmp/privacy-188-language-final.log`                                                                   |
| Docs header: 24 layouts and 8 search-focus checks                                                                                                                 | PASS                                                                             | `/private/tmp/privacy-188-docs-header.log`                                                                      |
| Docker preview build                                                                                                                                              | PASS                                                                             | `/private/tmp/privacy-188-docker-final.log`                                                                     |
| Docker release rejects a preview despite supplied synthetic approval                                                                                              | PASS (expected build failure: Preview artifact cannot be promoted)               | `/private/tmp/privacy-188-docker-rejection.log`                                                                 |
| Candidate build with current real deployment inputs                                                                                                               | Correctly BLOCKED: facts, inventory and translations not supplied                | `/private/tmp/privacy-188-candidate-blocked.log`                                                                |
| Candidate approval checks actual bytes and origin; changed bytes, stale digest, missing evidence and impossible dates rejected                                    | PASS, seven focused tests, including current-input invalidation                  | `/private/tmp/privacy-188-legal-final.log`                                                                      |
| Vite development legal routes: complete German HTML, CSS, missing-page 404                                                                                        | PASS                                                                             | Local HTTP smoke on 127.0.0.1:4184                                                                              |
| TypeScript config and deployment shell syntax                                                                                                                     | PASS                                                                             | `tsc -b provider-site/tsconfig.node.json`; `bash -n scripts/deploy_railway_demo.sh`                                 |
| Ruff                                                                                                                                                              | PASS                                                                             | `/private/tmp/privacy-188-lint.log`                                                                             |
| Full backend PostgreSQL suite                                                                                                                                     | PASS: 2442 passed, 9 skipped, one SQLAlchemy transaction warning, 651.65 seconds | `/private/tmp/privacy-188-backend.log`                                                                          |
| Spec policy and whitespace diff                                                                                                                                   | PASS at last check                                                               | `make spec-check`; `git diff --check`                                                                           |

Browser tests use isolated localhost Nginx containers with read-only built artifacts.
Playwright is installed in `/private/tmp/privacy-188-browser`, not added to runtime dependencies.
The existing installed Chromium executes the tests; synthetic account responses ensure
no real profile or tenant record is changed. PostgreSQL tests use the repository's
random temporary test database on the local PostgreSQL service.

Visual inspection of the German mobile privacy PNG confirms readable static content,
visible focus and accessible native navigation. Content is explicitly fictional and
non-publishable. This is not a human screen-reader or legal-translation sign-off.

## Implementation decisions and reviewed adjustments

- Legal content may be inline in fixture input; real input resolves the four reviewed
  `provider-site/legal/content/{en,de,nl,es}.json` files. They are deliberately absent until supplied.
- `ProductLink.vue` needs no duplicate state: the shared Docs bridge rewrites its links
  using the explicit choice; browser handoff tests verify the result.
- A document-lifetime in-memory choice preserves language through SPA navigation; Auth
  supplies the account fallback without modifying the URL. Reload/origin changes reset
  this memory. A failing regression is in `/private/tmp/privacy-188-memory-red.log`.
- The existing `docs/features/shared-language.md` and coverage matrix were updated along
  with spec 176 so durable contracts do not retain contradictory persistence promises.
- Fonts use installed system fonts; the remote Xentral image is replaced with text.
  Existing bundled Simple Icons are retained. No external image was copied and no new
  asset license is asserted; remaining asset-rights review belongs to the release dossier.
- The release gate uses input reviews before candidate generation and a separate approval
  secret afterward. Cached candidate bytes are checked by digest; no approval is embedded
  in the hashed artifact. The public workflow cannot use its "testing" name to bypass it.
- Railway now checks local candidate eligibility before any deployment. Its builder must
  also support the required BuildKit secret; unsupported publication remains blocked.

## Pending external checks and limitations

- T011: actual human screen-reader review remains pending, though semantic HTML, keyboard,
  viewport and visual checks passed.
- T031–T032: verified operator identity, provider/logging inventory, jurisdiction and legal
  review, complete reviewed translations and manual operator approval are not supplied.
- T036: no public promotion approval exists; fixture results cannot authorize it.
- T037: no publication or live canonical/www/hosting audit was performed.
- T038 cannot certify feature/release completion until required manual/deployment evidence exists.

The initial optional inventory is empty. T022–T024 prove this boundary and reject attempts
to enable optional processing; FR-009–FR-012 consent controls are conditionally inapplicable,
not implemented or claimed tested. Any retained service needs reviewed design and tests first.
See `docs/privacy/releases/runreality-pending.md` for roles responsible for missing inputs.
No claim of legal immunity or comprehensive compliance is made.

Release cache review: Docker documents that changing a BuildKit secret does not invalidate
a cached RUN. The public workflow now disables caching for `approved`, revalidates even
when an image tag exists, and transports multiline approval JSON using `secret-envs`.
A failing-before-fix workflow contract regression is in `/private/tmp/privacy-188-cache-red.log`.

Final self-review found no business-schema, tenant-service or confirmation-boundary change.
All 32 technical tasks have evidence; six manual/release tasks remain pending. Browser
parent-domain cleanup was tested by intercepting requests and serving only local responses;
no production Site was contacted. Runtime and deployment code must still undergo normal
PR/human review before merge; no commit, push, merge or public deployment was performed.

The three isolated preview containers and worktree development server were stopped
after verification. Screenshots, logs, build artifacts and the worktree remain available.

## Hosting extension verification (2026-09-14)

Scope: FR-016–FR-018, T039–T046. Observed initial unittest failure because the verifier
did not exist. After implementation, five tests pass, including wrong-region, public
bucket, weak encryption, versioned/suspended storage, wrong expiry/prefix, unauthorized
policy additions, disabled logging, stale/test-only/unrelated-ALB delivery and missing
collector-retention negatives. Added these tests to CI's spec-policy job.

CloudFormation cfn-lint passes. Helm 3.17.3 (download checksum verified) lint and render
pass, including exact ALB bucket/prefix/idle timeout/connection-log attributes and all
four host routes. Local disposable nginx:1.27-alpine containers for Site, Docs and Web
pass syntax validation and serve a request without an access-log line; Uvicorn config
confirms access handlers disabled while error logging remains enabled.

Ten legal/privacy regression tests, spec policy, core/new-code Ruff and diff whitespace
checks pass. Previous full backend/frontend/browser baseline is recorded above; no
business code changed in this extension, so those suites were not rerun solely for
Docker logging flags. No UI rendering or legal generation behavior changed.

Review: the overlay is opt-in to avoid enabling a nonexistent bucket; it preserves the
shared ALB idle timeout. The prerequisite requires real administrator/execution roles
and protects unversioned expiry. No retention fact, role ARN, contract or deployment
approval was fabricated. No cloud credentials or Kubernetes context are available.
T044–T046 remain incomplete: provision, apply/roll out, inventory/configure all error
collectors and node copies, verify real delivery and effective deployed settings.
The exact live bucket/prefix must be recorded from outputs and AWS verification.

## Real-operator draft preview (2026-09-14)

FR-019 implemented after recording scope, design, tasks and analysis. Initial new
test failed on unknown draft mode. Final Site suite: 73 passed; format check, TypeScript
and Vite draft build, spec policy and diff check passed. Tests ensure real operator
identity matches canonical input, all eight draft pages are static and noindex, blockers
remain, and candidate validation/promotion reject drafts even with approval-shaped data.

Rebuilt and restarted only local `reality-site-1` via the temporary Compose override
`/private/tmp/privacy188-preview.override.yml` with `REALITY_SITE_MODE=draft`. Base local
Compose project remains reality, originating in /private/tmp/reality-186; Docker build
context is /private/tmp/reality-188. All eight HTTP legal URLs on localhost:8082 return
200 with Xentral identity, localized draft labels, no fictional content and no scripts.
robots.txt disallows indexing. No public deployment or IAM changes were performed.

At this stage, questions covered privacy contact, AWS contracting entity/DPA and
final reviewer; subsequent user decisions are recorded in the release dossier. The Xentral privacy page
has conflicting AWS entity names; it does not verify Reality's provider contract or
actual logging. Existing legal/publication and live infrastructure tasks remain open.

## Operator-approved local finalization (2026-09-14)

The user confirmed internal text review and AWS verification and authorized removal
of the draft marking. Candidate inputs now contain the four final locale documents
and a digest-bound reference to operator-confirmation-2026-09-14.md. AWS verification
is attributed to the operator, not to an unperformed implementer inspection.

Site tests: 73 passed. Candidate TypeScript/Vite/legal build, spec policy and diff
checks passed. Local Site Docker build and restart passed using candidate input and
the local preview image target. All eight local legal URLs returned 200 with Xentral
identity and without draft banners, fictional content or draft noindex metadata.
Public artifact approval, public deployment and its post-deployment audit were not
performed. No AWS or IAM settings were changed in this step.

## PR #260 installer readiness repair

The first PR CI run failed only in the installer e2e: `/healthz` received an empty
response immediately after the API became healthy but before Nginx was ready. The
repair restores spec 187 FR-013 by checking the proxied Web health route and waiting
for that container in the shared install/start/restore/upgrade path. The readiness
budget and e2e assertion are unchanged.

Regression tests failed first; all 18 installer tests now pass. Shellcheck, 5 publish
workflow tests, 6 Docs install-option tests, Ruff/spec policy and the complete isolated
Docker e2e install/sign-in/backup/restore/upgrade story passed. All other checks on the
initial PR head passed in GitHub; the fix will trigger a new CI run.

## Final Railway demo legal pages (2026-09-14)

Deployment `<redacted-id>` published merged main commit
`170ba06e5e2df7fa9ae8ab6bdb9ca2cb2477e749` to the Railway `site` service with
status `SUCCESS`. The provider build used the configured Railway Site, App and Docs
origins and generated legal pages in explicit `demo` mode.

All 75 Site tests, Site and Docs formatting, spec policy and the real Railway Docker
build passed. Live no-script HTTP requests to imprint and privacy in English, German,
Dutch and Spanish all returned successfully. No page contained a draft label or AWS
hosting claim; every privacy locale named Railway Corporation. The deployed
`robots.txt` returned `User-agent: *` and `Disallow: /`. This evidence applies only to
the non-canonical Railway demo and does not approve or replace the AWS release path.
