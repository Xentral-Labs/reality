# Verification: First-Time Fact Rule Wizard

## Scope and review

Owner approved the five-stage scope on 2026-09-12. Planning reviewed the existing
Reality Gap lifecycle and rejected new schema, service semantics, wizard persistence
and implicit multi-write confirmation. Pre-implementation analysis found no critical,
high, ambiguity or missing-coverage issues: 13 FR/DR requirements mapped to 11 tasks.
Both specification-quality and UX-quality checklists passed before implementation.
No Spec Kit extension hooks were configured.

## Test-first evidence

`node --test apps/web/scripts/fact-rule-wizard.test.mjs` initially failed because
`ruleWizardState.ts` did not exist. The new browser journey and lifecycle checks were
written before the wizard. Existing guided-rule tests were adapted to enter through
the wizard and still exercise active version editing, advanced field preservation,
manual evidence, non-Fact outcomes, simulation failure, replay and access controls.

The manual-observation cancellation test caught lost inputs when the review replaced
the evidence component. Keeping the step mounted while hiding it during review and
navigation fixed the actual regression; the existing test then passed.

## Browser evidence

The fixture-backed wizard suite proves editable starters, inline goal validation,
read-only back navigation, retained source-search input, double-confirmation prevention, reviewed goal/evidence/
recommendation/interpretation/draft/activation calls, exact source identity and stated
value, saved-draft reopening, failed simulation retry, edit invalidation, no automatic
historical replay, uncertainty lock across dialog closure, read-only access and
ignored delayed simulation after company change. Zero matches are explicitly explained.

Desktop and 390px screenshots were inspected in en/de/nl/es. Configuration scrolling
retains the reachable footer; no horizontal overflow; Escape closes and restores focus
to the originating row action. Evidence is retained while review is visible, and
hidden fields do not enter keyboard navigation. Screenshot artifacts live under
`/private/tmp/fact-rule-wizard/` and `/private/tmp/guided-rules-screens/`.

Browser calls are intercepted fixtures; they do not mutate any real company. Existing
shared services are covered separately by the required complete PostgreSQL suite.

## Required gates

| Gate | Result |
|---|---|
| Spec policy | PASS |
| Ruff | PASS |
| Web contracts | PASS: 125 tests |
| Four-language audit | PASS: no missing or invalid translations |
| Site build | PASS |
| Web formatting and production build | PASS; existing bundle-size advisory only |
| New wizard browser journey | PASS |
| Legacy guided-rule browser | PASS, including manual-input retention and prepared handoff result |
| Full PostgreSQL suite including migrations | PASS: 2,288 passed, 9 skipped in 618.81 seconds |
| Generated catalog freshness | PASS; no generated diff |
| Diff whitespace | PASS |

The initial serial PostgreSQL run was stopped cleanly after confirming worker-safe
fixtures, then restarted with `PYTEST_ADDOPTS='-n 4 --dist loadfile' make test` to reduce
verification time. Sandbox restrictions required running local browser/server and
PostgreSQL checks with reviewed local execution permissions. No automatic approval
review rejection occurred.

## Final review

No database, domain, service, tool or executable catalog changes. Existing source
values and opaque links remain unchanged. Simulation is transient and tied to the
latest saved draft; any edit invalidates it. Every write is individually reviewed.
The legacy version workbench remains unchanged apart from optional editor guidance
and routing of new/never-activated setup. Rollback is a web code revert; saved questions
and immutable versions remain valid. No external deployment was performed.

All required gates passed on 2026-09-12. Final diff review found no outstanding requirement, schema or confirmation issue. All implementation tasks are complete.

## Local rollout — 2026-09-12

On owner request, rebuilt the web image with `docker compose build web` and replaced
only the web container with `docker compose up -d --no-deps web`. Port 8080 returns
HTTP 200 for the application and `UnifiedApp-ByKOmq7D.js`; the served bundle contains
`data-fact-rule-wizard`. The authentication proxy responds with the expected HTTP 401
for an unauthenticated request. No backend restart, migration or business write was
performed as part of this rollout.

## Caret spacing correction — 2026-09-12

The purpose textarea inherited the single-line control's horizontal-only padding.
Added local vertical padding and vertical resize, restoring FR-010 readability.
The browser assertion for at least 10px vertical inset and 60px height first failed,
then the complete wizard browser journey passed. Formatting, spec policy, whitespace
and the Docker production build passed. Rebuilt/recreated only web; port 8080 serves
`UnifiedApp-Bo471QfV.js` containing the corrected control classes. No backend changes;
the previously recorded complete backend suite remains applicable.
