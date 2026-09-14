# Codex: Start Here

Read `AGENTS.md`, `.specify/memory/constitution.md`,
`docs/SPEC_DRIVEN_WORKFLOW.md`, and then `docs/V0_CHECKLIST.md`.

For new behavior use the installed Spec Kit skills in this order:

1. `$speckit-specify`
2. `$speckit-clarify` when requirements are ambiguous
3. specification review and approval
4. `$speckit-plan`
5. `$speckit-checklist` and `$speckit-tasks`
6. `$speckit-analyze`
7. implementation only after the gates pass
8. tests, final spec-conformance review, and status update

Do not treat the recommended implementation order below as permission to skip a
feature specification.

Recommended implementation order:
1. DB/session/config + migrations.
2. Tenant context and isolation tests.
3. Party/Item/Location.
4. Movement + stock query.
5. SourceRecord + Shopify interpreter + Evidence.
6. Commitment + Reservation.
7. Guided demo and `--auto` golden test.
8. Explain + timeline.
9. Normal-month scenario.
10. Chat provider/tool registry + confirmation flow.
11. Minimal Ledger.

At each step, approve the feature spec and its acceptance tests before implementation
or schema expansion. If tempted to add a field, write the business scenario that
proves it is core first.

## Web phase

After the core domain, tenancy, persistence, CLI and shared services are working, read `docs/WEB_SPEC.md` and implement `reality web`.

Do not create a second business-logic path for web. Use the same services/tools as CLI and chat. Start with FastAPI + server-rendered HTML/HTMX unless a testable requirement proves a SPA is necessary.

Web V0 order:
1. tenant shell + empty-tenant demo entry
2. Home
3. Commitments
4. Inventory
5. Documents + raw source payload
6. Timeline
7. persistent tenant-scoped Chat sessions
8. Issues
9. Explorer / Inspect
