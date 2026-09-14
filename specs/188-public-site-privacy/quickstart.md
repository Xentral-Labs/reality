# Validation Guide: Public Site Privacy

The technical scripts are implemented. See `verification.md` for executed checks; real
legal review and publication remain pending. Preview commands use fictional inputs only.

## Prerequisites

Use the repository's Node/npm toolchains and Python environment. Full backend checks require
its PostgreSQL test setup. Browser tests follow the existing `PLAYWRIGHT_MODULE` and
`PLAYWRIGHT_EXECUTABLE` convention; use an installed module/browser rather than assuming
paths. Use only fictional operator inputs for automated tests. A deployed audit requires
real approved inputs and access to hosting/log settings; it never changes provider settings.

## Build and regression gates

From the repository root after implementation:

```sh
make spec-check
make lint
make test
make site-build
make web-build
make docs-build
make docs-catalog-check
```

`npm test` in provider-site must include planned legal-content and public-privacy tests.
It must prove missing/fixture/stale release inputs fail, all eight legal pages generate,
unsafe content is rejected, remote assets are absent and optional services cannot be enabled.
Existing shared-language and entry-routing tests must cover the new navigation-only contract.
Do not mark the feature verified from a source scan alone.

## Candidate browser proof

Build Site/Docs/App previews with their cross-surface origins configured consistently.
Serve built artifacts with their production routing; legal no-script checks must also
run against the built Site Nginx image. Existing browser harness inputs are:

```sh
export LANGUAGE_SITE_URL=http://127.0.0.1:4180
export LANGUAGE_APP_URL=http://127.0.0.1:4181
export LANGUAGE_DOCS_URL=http://127.0.0.1:4182
node provider-site/scripts/shared-language-browser.mjs
node provider-site/scripts/public-privacy-browser.mjs
```

The privacy harness will use LANGUAGE_SITE_URL and the existing Playwright module/browser
environment variables. Capture network destinations, cookie/localStorage operations and
screenshots in isolated contexts for all route/locale combinations, desktop/mobile, fresh,
returning, scripts-disabled legal pages and blocked storage. Observe initial load, scroll,
navigation and an explicit bounded idle window; a finite audit is evidence, not proof about
all future behavior. Fail on unknown destinations/operations. Redact personal data from logs.

Check legacy cleanup on host and production-like subdomains, preserving unrelated storage.
Verify Site → Docs → App → Site for en/de/nl/es, same-language selection, explicit English,
Docs topic/query/hash preservation, profile fallback and absence of account mutation. Docs
readiness must rely on rendered state rather than the removed localStorage key.

## Human review and public release

Review the operator facts, translations, inventory, provider/transfer evidence, retention,
asset rights, screen-reader behavior and deployment settings. Store reviewer/date and
references in the release dossier. Do not attach confidential contracts to public assets.
Public release mode rejects previews, missing reviews and mismatched digests. Use the
same candidate artifact for deployment after its pre-release approval.

Smoke-audit the canonical and www hosts after publication: direct legal pages with scripts
disabled, paths/locales, network/storage and host-added behavior. Hosting logs require
configuration review in addition to the browser audit. Record post-deploy status separately;
unknown processing or failure requires service disabling or rollback to a compliant artifact.
Reopen approval for changed inputs and assign the six-month review owner.

No deployment or legal approval is performed by preparing this plan.

## Isolated worktree evidence

Implementation is in `/private/tmp/reality-188` on `188-public-site-privacy`. Local Site,
Docs and App builds passed; the privacy and language harnesses use the documented existing
Playwright environment convention. The header harness uses `CHROMIUM_PATH` and
`DOCS_TEST_URL` rather than `PLAYWRIGHT_EXECUTABLE` and `LANGUAGE_DOCS_URL`.
Docker preview: `docker build --target preview --build-arg REALITY_SITE_MODE=preview -f provider-site/Dockerfile .`.
Public Docker release defaults to candidate mode and requires reviewed real input plus
a BuildKit secret `site_approval` binding the tested candidate digest. The checked-in real
input is deliberately blocked; never replace it with test data to bypass that gate.

## Hosting extension verification

Follow `infra/privacy-logging/README.md` for prerequisite provisioning, ALB enablement,
container rollout, collector retention and metadata-only live verification. Run
`python3 -m unittest discover -s infra/privacy-logging -p 'test_*.py' -v` locally first.
