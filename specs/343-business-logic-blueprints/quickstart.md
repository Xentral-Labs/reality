# Validation Guide: Live Business Blueprints

The implementation reads the loaded application source and reviewed raw tests on demand. See [verification.md](verification.md) for executed checks and remaining review gates.

## Prerequisites

Use the normal repository PostgreSQL test/development environment, matching API/MCP source releases, approved test evidence in both images, and a docs live-target configuration. Use synthetic company records only. Technical source analysis needs no AI provider. The new ERP-readable live interpretation uses the deployment Anthropic configuration; it does not use a company API key or company records. A company AI provider remains needed for natural-language Chat.

## Focused executable checks

```bash
cd packages/reality-core
../../.venv/bin/pytest tests/test_business_blueprint_inventory.py tests/test_business_blueprint_analysis.py tests/test_business_blueprint_tests.py tests/test_business_blueprint_adapters.py tests/test_business_blueprint_cases.py tests/test_business_blueprint_release.py tests/scenarios/test_credit_blueprint_journey.py
```

## Business review

1. Open credit exposure in the Web technical catalog. Identify the three exposure components, currency exclusions, zero-limit meaning and strict comparison. Follow every decision to actual running source.
2. Open associated actual tests; inspect their setup and assertions. Identify what they do not prove. Test results must be unknown unless a matching run is supplied.
3. Follow hold creation, blocked readiness and owner-confirmed credit-hold release. Confirm that unrelated delivery blockers remain distinct.
4. Ask Chat and MCP for the same logic/tests. Compare rule identities, expression operators, assertions, evidence limits and source revision with Web and docs.
5. Compare a matching synthetic situation, a differing currency and a situation with missing fixture assumptions. Observe explicit differences/unknowns without a mutation.
6. Use a controlled test module/release with an altered comparison operator and test assertion. Reload its running version, without any explanation generation or docs build; the next request must show the changed operator/assertion and revision.
7. Alter disk source without reload. The explanation must report inconsistency rather than show disk changes as running behavior.
8. Remove release test evidence or disconnect the docs target. Observe explicit unavailable evidence; no saved blueprint replaces it.
9. Attempt arbitrary source paths and another tenant's record. Expect rejection/not-found without disclosure.
10. In a documented ERP-professional review, identify inputs, refusal condition and closest existing test in five minutes without reading Python.

## Required final gates

```bash
make spec-check
make lint
make test
make web-build
make docs-generate
make docs-catalog-check
make docs-build
```

Also run the repository-required frontend localization audit, registered browser suite and API/MCP release-image evidence smoke checks. Confirm `make docs-build` is available in the environment; otherwise use the docs package's existing build command. Do not mark acceptance complete while any required check is red. Preserve unrelated worktree changes.

## Release and live-target configuration

API and MCP images use the same `REALITY_COMMIT` build argument and contain approved raw evidence under `/opt/blueprint-evidence`; `REALITY_BLUEPRINT_EVIDENCE` points there. The packager stores source test files and their SHA-256 manifest, never rendered business explanations. A missing or mismatched manifest is reported explicitly. Discovered tests have unknown execution status unless a trusted matching run includes the release, timestamp and exact source/test digests.

Set `BUSINESS_LOGIC_API_URL` when building docs to select the responding API target (otherwise the existing `API_URL` is used). Tool Usage requests `/api/business-logic/entries` only on demand, with credentials omitted and no response caching. Tenant record comparison is available only through the authenticated application/MCP boundary.

Traversal is bounded to 128 functions, eight helper levels, ten seconds, 200 scenarios and one MiB of captured function source. Omitted dependencies and unsupported semantics are visible limitations. Public responses have a two MiB cap, two concurrent analyses and 30 requests per minute per direct client address. These limits do not certify complete business semantics.

The source snapshot, release and evidence digest are displayed with each response. Refreshing clears the prior response before reading again; unavailable or inconsistent source is never substituted with an old explanation. Test candidates and assertion-linked relationships remain distinct; predicate gaps are explicit and are not branch execution coverage.

The five-minute ERP-professional exercise is a separate human review gate. Automated success does not complete it.

Configure `DOCS_URL` on the API for the exact docs origin when they use different origins. Unsupported default factories are not executed; their source limitations are propagated. Imported scalar defaults and raw positional/keyword default layouts are checked, and a mismatch is outdated evidence that cannot be used for comparison.

## Generic live interpretation checks

Configure a valid deployment ANTHROPIC_API_KEY. The business view is generated only
when the reader requests live logic, from verified source and approved test evidence.
It is not generated during builds or stored alongside source. Existing and future
registered entries use the same provider/prompt; unavailable source/test evidence
remains explicit. No per-operation explanation file is needed.

Use English or German on both live detail adapters. Check the primary business
overview, cited rules, contracted source graph and Given/When/Then test descriptions;
expand technical evidence to inspect original expressions, versions and raw tests.
Set REALITY_BLUEPRINT_LLM_ENABLED=false for source-only deployments. Missing/rejected
provider access gives an unavailable interpretation without substituting cached prose.
The provider interprets at most 12 selected actual test cases; every discovered case
remains in the technical response. Source/compare reads do not invoke the model.
