# Research: Complete Chat and MCP Command Coverage

## Coverage universe

**Decision**: Every `command_catalog.yaml` entry declares agent eligibility and maps to
an application tool, or has an explicit exclusion/block reason.

**Rationale**: It already documents shared services across CLI, Web, and API and avoids
the accidental gaps the owner encountered.

**Alternatives considered**: Typer-route comparison includes demo/maintenance commands;
a second MCP-only list perpetuates drift.

## One application registry

**Decision**: Keep `reality.tools.application.TOOLS` executable and bind MCP schemas to
it; managed Chat consumes the same model schemas.

**Rationale**: This preserves the existing dependency boundary.

**Alternatives considered**: Separate Chat handlers and CLI subprocesses duplicate
contracts or weaken transaction and error semantics.

## Approval boundary

**Decision**: All eligible agent mutations use propose → approve → execute; reads are direct.

**Rationale**: The Constitution requires confirmation and existing ChangeProposal
storage is sufficient.

**Alternatives considered**: Risk-based automatic mutation and approval for ordinary
human API/Web form submits are outside the approved safety model and scope.

## Discovery and identity

**Decision**: Provide bounded list/search/detail reads; relationship mutations require opaque IDs.

**Rationale**: Agents can discover required fields safely without treating names as identity.

**Alternatives considered**: Silent name resolution is ambiguous; generic unbounded
query tools are unsafe and consume excessive context.

## Order orchestration

**Decision**: Add one manual order service that records lossless Source evidence,
creates Document/DocumentLine evidence, and derives Commitments using existing interpretation.

**Rationale**: Lower-level building blocks exist, but no complete order command exists.

**Alternatives considered**: Direct Commitment creation breaks provenance; document
status breaks Reality authority; agent composition of low-level writes risks partial effects.

## Schema and exclusions

**Decision**: Add no database fields. Explicitly exclude global/destructive tenant
administration, credentials, projection rebuilds, demo/scenario mutations, raw event
emission, and generic persistence operations.

**Rationale**: Configuration/code can enforce parity, and complete tenant business
capability does not mean arbitrary remote administration.

**Alternatives considered**: A database tool registry and advertising every callable
function add infrastructure and risk without a proven business use case.
