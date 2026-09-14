# Spec-Driven Development Workflow

Business Reality uses GitHub Spec Kit 1.0.0 with the Codex skills integration. The
project Constitution is `.specify/memory/constitution.md`; `AGENTS.md` is its concise
runtime contract.

All repository artifacts and recorded decisions are written in English. Conversation
with the owner may use another language, but approved answers are translated into
English before they are committed.

## When a specification is required

Create or update `specs/NNN-feature-name/spec.md` whenever a change alters observable
business, API, CLI, Web, MCP, Chat, persistence, or integration behavior. Also update
the applicable long-lived contract under `docs/` when its behavior changes.

A defect may point to an existing `FR-*`/`DR-*` requirement and add a regression test
instead of creating a new feature directory only when the intended behavior is already
unambiguous. Documentation, build maintenance, and behavior-preserving refactors may
use `Spec impact: none`, followed by a concrete reason in the pull request.

## Required sequence

Every `spec.md` MUST carry a `Non-Goals` heading and a
`## Assumptions and Dependencies` section; `make spec-check` fails without them.
Non-Goals is conventionally a third-level heading inside `## Context and Intent`,
beside `### Problem` and `### Scope`.

1. **Specify** — Derive the feature number with
   `python3 scripts/next_feature_number.py` and pass it to Spec Kit as `--number`.
   Spec Kit itself only reads the `specs/` directory of the current checkout, so two
   branches started from the same base otherwise claim the same number. Then run
   `$speckit-specify`; capture what and why, scope, non-goals, prioritized stories,
   requirements, acceptance scenarios, edge cases, and success.
2. **Clarify and review** — Run `$speckit-clarify` when needed. A human accepts product
   scope before technical planning. No `[NEEDS CLARIFICATION]` marker may remain.
3. **Plan** — Run `$speckit-plan`; document the smallest implementation, exact layers,
   Source → Evidence → Reality flow, tenant boundary, schema proof, rollback, and tests.
4. **Constitution gate** — Every plan row must be PASS. An exception needs explicit
   justification and human approval in Complexity Tracking.
5. **Checklist and tasks** — Run `$speckit-checklist` and `$speckit-tasks`. Map each
   `FR-*` and `DR-*` to tests and implementation tasks with exact paths.
6. **Analyze** — Run `$speckit-analyze`. Resolve all CRITICAL consistency or coverage
   findings before implementation.
7. **Implement test-first** — Observe a meaningful failing proof where practical, then
   implement domain → service → tool → adapter. Keep business rules out of transports.
8. **Verify and review** — Run every required gate, review the diff against the spec and
   Constitution, then update task/checklist status. Red checks mean not done.

## Review gates

| Gate | Required evidence | Approval |
|---|---|---|
| Specification | Scope, stories, FR/DR, scenarios, non-goals, no ambiguity | Product/domain owner |
| Architecture/domain | Constitution PASS; schema and shortest-link proof | Domain/technical when applicable |
| Pre-implementation | Tasks trace every requirement; Analyze has no CRITICAL result | Implementer + reviewer |
| Completion | Acceptance proof, full CI, migration/rollback review, final diff review | Pull-request reviewer |

The author may prepare all artifacts, but self-review does not replace human approval
for product scope, schema expansion, constitutional exceptions, or merge.

## Artifact ownership

- Feature branches are updated with `git rebase origin/main`, never
  `git merge main`. A merge commit in the branch makes GitHub refuse a rebase merge
  ("This branch can't be rebased"), which costs the repository its linear history for
  that change.
- `specs/`: change-oriented executable intent and plans. One feature number
  identifies exactly one specification; `make spec-check` fails on a collision.
  `022-auditable-document-line-corrections` and `022-public-site` are an accepted
  historical exception because both are already merged.
- `docs/features/`: durable business feature contracts.
- `docs/ARCHITECTURE.md`, `DATA_MODEL.md`, `WEB_SPEC.md`: cross-feature authorities.
- `docs/V0_CHECKLIST.md`: verified release status only, never aspirational progress.
- ADRs: durable architectural choices and their consequences.

Avoid migrating all historical documents into Spec Kit at once. When an existing
feature next changes materially, create its numbered feature directory and link the
existing contract. This preserves history without manufacturing retroactive approval.

## Local commands

```bash
specify --version
python3 scripts/next_feature_number.py --explain
make spec-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

The absolute `specify` path is shown because the uv tool directory is not currently on
the shell `PATH`. Running `uv tool update-shell` is optional and changes user shell
configuration, so it is not performed by repository automation.

## Current adoption status

Spec Kit was introduced on 2026-08-31. Existing feature documents predate the workflow
and are baseline references, not retrospectively approved Spec Kit artifacts. The
adoption audit initially found 13 Ruff findings and 21 failing tests. The same adoption
work repaired the test-environment boundary and lint findings; the verified baseline is
recorded in `docs/V0_CHECKLIST.md` and CI preserves it.
