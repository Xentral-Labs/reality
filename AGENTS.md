# Coding Agent Contract

## Mission
Build the smallest coherent Business Reality system that proves the domain model. Optimize for semantic clarity, traceability and testability—not feature count.

## Hard rules
1. **Source → Evidence → Reality**: SourceRecord → Document/DocumentLine → Fact/Commitment/Reservation/Movement/LedgerEntry.
2. Documents are not the operational center. Never add delivery/reservation/purchase fulfillment status fields to documents; derive them from Reality.
3. Store external payloads losslessly. Do not map fields just because upstream provides them.
4. A field becomes typed only when core logic repeatedly calculates, filters, joins, constrains, predicts or acts on it.
5. Prefer the shortest true relationship. Reservation → Commitment; do not duplicate Document/Line/Source FKs there.
6. Human numbers are never identity. Use opaque IDs/FKs.
7. Chat/agent calls the same application tools/services as CLI. No direct ORM writes.
8. Every business table is tenant-scoped; every repository query enforces tenant scope.
9. PostgreSQL is the only supported database; domain/services remain storage-disciplined through SQLAlchemy 2.
10. Mutating chat actions require confirmation; read-only queries do not.
11. Record values a source states; never recompute them. Derive observations from what is held, at read time, and never store a derivation as a new authority.

## Engineering
Python 3.12+, type hints, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, Typer, Rich, pytest. Decimal for money/quantities. UTC timestamps internally. SourceRecords are immutable; upstream changes create versions/events.

All repository content is English: code identifiers, comments, docstrings, tests,
migrations, specifications, plans, tasks, checklists, commits, pull requests, and
documentation. Conversation with the user may use another language; record decisions
in English. Preserve the original language only for lossless external payloads or
intentional business examples.

## Workflow
This repository uses GitHub Spec Kit. Read `.specify/memory/constitution.md` and
`docs/SPEC_DRIVEN_WORKFLOW.md` before changing behavior.

Mandatory path: specify → clarify/review → plan → tasks → analyze → implement →
verify → review. Do not start implementation while requirements contain unresolved
clarifications, the plan fails a Constitution Check, or critical analysis findings
remain. Tests must be planned before implementation and added first where practical.

Every observable behavior change must create or update `specs/NNN-feature/spec.md`.
A bug fix may reference an existing requirement plus a regression test when it only
restores already-specified behavior. Refactors/docs-only changes may declare
`Spec impact: none` with a concrete reason. Do not expand schema without a proven use
case in the spec and plan.

Implementation order remains domain → services → tools → adapters. Add unit, service,
business-story, and adapter tests in proportion to risk; run the complete required
suite. Never mark a task, acceptance criterion, or `docs/V0_CHECKLIST.md` item complete
while its required checks are red.

## Done
See `docs/V0_CHECKLIST.md`.

## Web UI invariant

The web product combines an Operations Cockpit and a Business Reality Inspector.

**Simple on the surface. Fully explainable underneath.**

Operational pages must use shared services/tools and must not implement alternative business rules. Every important number/action should be traceable through the shortest true links to its underlying reality records and, when applicable, to the original source payload. Read `docs/WEB_SPEC.md` before implementing web UI.

## Scheduled background work

Read [the shared scheduling contract](docs/features/scheduled-jobs.md) before adding
recurring or queued background work. It records implementation status and links executable examples and verification evidence. Use the shared job registry and
scheduling services, not per-subsystem timers or API-process loops. The selected
deployment roles are `apps/scheduler/` (materialize due jobs) and `apps/worker/`
(consume the PostgreSQL queue), both using `reality-core`. Handlers call application
services and preserve tenant scope, idempotency and confirmation. New scheduling
infrastructure or direct external-effect handlers require an explicit reviewed design.
Neither scheduler nor worker startup may run migrations. Existing invitation delivery
remains unchanged until separately migrated.

## Company setup and demo profiles

Read [the company setup/demo contract](docs/features/company-setup-demo.md) before
changing creation flows, Sandbox fixtures or continuous synthetic intake. It records
implemented service entrypoints, profile versions, source lifecycle and verification evidence.
Preserve existing admission and lesson boundaries. Reuse the canonical profile, normal
source interpretation and shared job registry; do not add browser timers or a second
demo queue. Review spec 146 before changing these contracts.

For explicit live-demo company creation, setup connects and starts Demo Data through
the shared services as part of the confirmed creation request (spec 146 FR-021).
Preserve its durable completion marker so request replay never overrides later source controls.

Home activity and scheduler/worker health: read `docs/features/home-live-status.md`
before extending readiness or activity polling (spec149).

## Documentation reference

The public docs page "Tool Usage" (`apps/docs/content/tool-usage/`) is generated from the
executable catalogs and the MCP registry by `apps/docs/scripts/generate-catalog-reference.py`.
After changing a command, agent tool, view, projection, exception or event, or an MCP input
schema, run `make docs-generate` and commit the generated pages and
`apps/docs/.vitepress/data/tool-usage.json`; CI fails on stale output (`make docs-catalog-check`).

`packages/reality-core/config/resource_catalog.yaml` groups that vocabulary by business object
(order, invoice, payment, business partner, ...) and lists the process steps. Membership is
derived from `match` patterns and `tables`; when the generator stops with "entries without a
business resource", give the new entry a home there rather than weakening the check. New
commands, views, projections and exceptions also take a German ERP label in the same file
(`labels.de`); without one the English label is shown in the German edition. Nested tool
arguments come from the MCP input schema itself, so declare their fields there instead of
describing them in prose.

