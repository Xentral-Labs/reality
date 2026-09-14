# CLI Specification

Executable: `reality`. CLI commands call application services; they never write ORM
models directly.

## Implemented surface

- `status`
- `tenant create NAME`, `tenant list`, `tenant use NAME_OR_ID`, `tenant current`
- `party|item|location create ...`, `update ...`, `deactivate ID`, `activate ID`
- `demo [--tenant ID] [--auto]` (compact onboarding seed)
- `scenario run normal-month --tenant ID`
- `stock [--tenant ID]`
- `finance open INVOICE_ID`, `finance pay-customer INVOICE_ID AMOUNT`,
  `finance pay-supplier INVOICE_ID AMOUNT` (all accept `--tenant`; payments accept
  optional evidence label `--number`)
- `web [--host HOST] [--port PORT]`

## Required V0 surface

The CLI does not start an MCP server. Remote MCP is an independently deployed,
authenticated Streamable HTTP runtime configured through `MCP_URL`; local development
uses the same HTTP boundary. Tenant authority comes only from the MCP bearer token, not
from a CLI option or transport-local tenant selection.

- Source/Evidence: `source ingest FILE SYSTEM TYPE EXTERNAL_ID`, `source list`,
  `source show ID [--raw]`, `source retry JOB_ID`, and `imports work`. Ingestion
  accepts any JSON object; registered `(system, type)` interpreters may create
  Evidence and Reality, while unknown combinations remain losslessly `unmapped`.
- Reality: `commitment list/create`, `reserve COMMITMENT_ID`, `reservation release`,
  `movement receive/ship/adjust`, `purchase create`, `stock`, `timeline`,
  `explain commitment ID`.
- Movement correction: `movement correct MOVEMENT_ID --reason TEXT` prints the exact
  server-derived compensation and optional `--replacement-json` before confirmation.
  Abort has no effect; `--yes` is explicit automation and still prints preview/result.
- Finance: invoice posting and credits remain required; payment and open-balance
  commands are implemented. `finance reverse POSTING_GROUP_ID --reason TEXT`
  prints the server-derived complete inverse and affected allocations before explicit
  confirmation; abort has no effect and `--yes` is explicit automation.
- Demo: guided step-by-step mode and explicit scenario reset remain V0 work.
- Chat: reads execute directly; mutations show proposed tool calls and require confirmation.

Use Rich tables/panels. Mutations print opaque IDs, semantic result, provenance, and a
useful next command. Cross-tenant/not-found and invalid-state errors are business-readable.

Party, Item, and Location lifecycle commands are adapters over the same application
services used by the JSON API. Their Rich output is not domain state; parity is measured
from authoritative tenant-scoped records after create, update, deactivate, and activate.

The canonical command catalog declares Chat/MCP parity for tenant business commands.
CLI, API, Web, Chat, and MCP reach the same application services. Agent reads execute
directly; agent mutations follow Proposal → Approval → Execution. Ordinary CLI commands
and explicit human Web/API submissions retain their existing confirmation semantics.
