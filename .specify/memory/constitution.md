# Business Reality Constitution

## Core Principles

### I. Source → Evidence → Reality

Every business flow MUST preserve the chain SourceRecord → Document/DocumentLine →
Fact/Commitment/Reservation/Movement/LedgerEntry wherever those stages apply. Source
payloads are immutable and lossless; upstream changes create versions or events.
Important results MUST remain traceable through opaque IDs and the shortest true links
to their evidence and original payload.

### II. Reality Is the Operational Authority

Documents MUST NOT own delivery, reservation, purchase-fulfilment, inventory, or
payment state. Those states are derived from Reality records. Human-readable numbers
MUST NOT serve as identity. New relationships MUST use opaque IDs/FKs and MUST NOT
duplicate Document, Line, or Source links when a shorter authoritative relationship
already exists.

### III. Proven Schema Only

A field becomes typed only after an explicit business scenario proves that core logic
repeatedly calculates, filters, joins, constrains, predicts, or acts on it. Schema
expansion MUST be justified in the feature specification and data model. Unknown
external fields remain in lossless source payloads. The smallest coherent model wins.

### IV. Tenant and Service Boundaries Are Non-Negotiable

Every business table and every repository/service query MUST be tenant-scoped.
Cross-tenant reads behave as not found; cross-tenant writes and links fail without
disclosure. CLI, API, Web, MCP, and Chat MUST call the same application services/tools;
transport layers and agents MUST NOT write through the ORM or implement alternative
business rules. Mutating Chat actions require preview and explicit confirmation.

### V. Specification and Test Evidence Before Completion

Observable behavior changes MUST start with an approved feature specification. Plans
MUST pass the Constitution Check before implementation tasks are accepted. Each
functional requirement MUST map to acceptance scenarios, implementation tasks, and an
executable test or an explicit, reviewed reason why automation is not appropriate.
Tests are written or updated before implementation and observed failing when practical.
A feature or checklist item MUST NOT be called complete while required CI is red.

### VI. Explainable Web Product

The web product combines an Operations Cockpit with a Business Reality Inspector:
simple on the surface and fully explainable underneath. Operational pages MUST use
shared services and every important number or action MUST expose a path to its
derivation, Reality records, evidence, and source payload where applicable. Business
rules MUST NOT live in the browser.

### VII. Simplicity and Storage Discipline

PostgreSQL is the only supported business database. Domain and service code use
SQLAlchemy 2 with disciplined persistence boundaries. Python 3.12+, type hints,
Pydantic v2, Decimal for money and quantity, and UTC timestamps are mandatory. New
infrastructure, abstractions, fields, and dependencies require a proven use case and a
documented rejection of the simpler alternative.

### VIII. Received Values Are Recorded, Never Recomputed

A value a source states — a total, a tax amount, an agreed price — MUST be recorded as
received and MUST NOT be recalculated. Where a source states nothing, Reality MAY derive an
observation from the facts it holds, at read time, and MUST NOT store that observation as a
new authority. Deriving stock from Movements, an outstanding amount from postings and
allocations, or an operational exception from any of them is the product's purpose;
producing the figure a source is responsible for is not.

The distinction is authority, and the cost of blurring it is concrete. Recomputing an
amount means owning a rounding rule, that rule will differ from the source's, and Reality
then holds a second number for the same thing and inherits the reconciliation. A comparison
between two received values is not a recomputation and remains encouraged: it is how a
disagreement becomes visible instead of being averaged away.

## Required Specification Artifacts

All repository artifacts MUST be written in English: source code identifiers, comments,
docstrings, tests, migrations, commit and pull-request text, specifications, plans,
tasks, checklists, ADRs, and technical/product documentation. User conversations may
use another language, but their approved decisions MUST be recorded in English in the
repository. External source payloads and business data retain their original language
when lossless preservation or a business example requires it.

Material features and behavior changes live in `specs/NNN-feature-name/` and contain:

- `spec.md`: what and why, prioritized independently testable stories, `FR-*`
  requirements, edge cases, non-goals, assumptions, and measurable outcomes.
- `plan.md`: technical approach, Constitution Check, repository paths, migration and
  rollback considerations, and review risks.
- `tasks.md`: ordered tasks referencing user stories and `FR-*` requirements, with
  tests before the implementation they prove.
- Supporting `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and
  `checklists/` artifacts when the change needs them.

Existing contracts in `docs/`, especially `ARCHITECTURE.md`, `DATA_MODEL.md`,
`TEST_STRATEGY.md`, `WEB_SPEC.md`, and `features/`, remain authoritative references.
Specifications link to them and update them when behavior changes; they do not silently
fork their rules.

A small defect that only restores already-specified behavior MAY use the existing
requirement plus a regression test instead of a new feature directory. The pull request
MUST identify that requirement. Refactors and documentation-only work MAY declare
`Spec impact: none` with a concrete reason. Any observable behavior change requires a
specification update.

## Development and Review Workflow

The mandatory sequence is:

1. Read the Constitution and applicable domain/feature contracts.
2. Create or update `spec.md`; resolve `[NEEDS CLARIFICATION]` markers.
3. Review requirements and acceptance scenarios before planning.
4. Create `plan.md`; pass the Constitution Check before design work continues.
5. Create tasks with requirement/test traceability.
6. Run Spec Kit analysis; resolve CRITICAL findings before implementation.
7. Implement through domain → service → tool → adapter layers, with tests first.
8. Run backend, frontend, migration, spec, and documentation gates.
9. Review the diff against the spec, Constitution, and shortest true links.
10. Mark tasks/checklists complete only after their evidence is green.

Required review gates are specification review, architecture/domain review where the
model or service boundary changes, and final code review. Self-review does not replace
human approval for product-scope decisions, schema expansion, exceptions to this
Constitution, or merge authorization.

## Governance

This Constitution is the highest project-local engineering authority. `AGENTS.md`
provides the concise runtime contract and MUST remain consistent with it. Conflicts are
resolved in favor of this Constitution, followed by explicit feature specifications,
ADRs, domain documentation, and implementation details in that order.

Amendments require a documented rationale, impact review, migration plan for affected
specifications/templates, and semantic version change: MAJOR for principle removal or
incompatible governance, MINOR for a new principle or materially stronger requirement,
PATCH for clarification. Every plan and pull request MUST verify compliance. Exceptions
MUST be explicit, narrow, approved, and recorded in the plan's Complexity Tracking.

**Version**: 1.2.0 | **Ratified**: 2026-08-31 | **Last Amended**: 2026-09-05
