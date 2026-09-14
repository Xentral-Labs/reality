# Contributing to Reality

Thank you for considering a contribution. This document tells you how the project works so your
change lands smoothly.

## Before you start

- Read [AGENTS.md](AGENTS.md). It is the short version of the project's engineering contract:
  Source → Evidence → Reality, tenant scope everywhere, PostgreSQL only, shared services for every
  transport.
- Read [docs/SPEC_DRIVEN_WORKFLOW.md](docs/SPEC_DRIVEN_WORKFLOW.md). Every observable behaviour
  change starts with a specification under `specs/`; refactors and documentation declare
  `Spec impact: none` with a reason.
- Everything committed is written in English: code, comments, tests, specs, commit messages and
  pull requests. Conversations may happen in any language.

## Ways to contribute

- **Report a bug** with the issue template. Include the version from `GET /api/v1/system/status`
  and the shortest reproduction you have.
- **Propose a feature** with the feature template. Say what a person cannot do today and why it
  matters; a specification follows from that.
- **Fix documentation** directly; the product docs live in `apps/docs/content` (English) and
  `apps/docs/content/de` (German). Both editions change together.
- **Security issues** go through [SECURITY.md](SECURITY.md), never through public issues.

## Working on a change

1. Fork and branch from `main`. Name the branch after the spec when there is one
   (`NNN-short-name`).
2. For behaviour changes, create or update `specs/NNN-feature/spec.md` first. The number comes
   from `python3 scripts/next_feature_number.py`. Scope is agreed before implementation starts.
3. Write the test before the code where practical, then implement domain → service → tool →
   adapter. Business rules never live in a transport or in the browser.
4. Run the gates that apply to your change:

   ```bash
   make lint
   make test                # PostgreSQL required; see README "Local development"
   make spec-check
   cd apps/web && npm test && npm run i18n:audit && npm run build
   cd apps/docs && npm test && npm run build
   make docs-generate       # after changing commands, views, exceptions or MCP schemas
   ```

5. Open a pull request with the template. The `- Spec impact:` line is checked by CI; "small
   change" is not a reason.
6. Keep the branch rebased on `main` (`git rebase origin/main`). Merge commits in a feature branch
   block the rebase merge.

## What reviewers look for

- The change is the smallest coherent one for its specification.
- Every new query is tenant-scoped; every new public core function is classified in the tenant
  isolation catalog.
- No new schema without a proven, repeated core-logic need.
- New strings exist in every UI language the app ships (English, German, Dutch, Spanish).
- Tests fail before the change and pass after it.

## Licence

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE)
that covers the project.
