# Verification: Copilot Decision Queue and Chat Archiving

Verified on 2026-09-02:

- 26 Web API tests pass, including archive retention, restore, decision tenancy, and Home activity.
- 11 migration/PostgreSQL integration tests pass; Alembic has one head at revision 0031.
- Six decision/archive Web contract tests pass and the production Web build succeeds.
- English, German, Dutch, and Spanish localization audits pass with zero missing strings.
- Spec policy, Ruff, formatting, and diff checks pass.
- The final full backend suite passes with 320 passed and seven skipped.
- Docker Compose rebuilt successfully and applied the migration. Visual browser inspection was not
  available in this environment; automated build and UI contract evidence is green.
