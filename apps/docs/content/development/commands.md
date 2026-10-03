# Develop Commands

## What you will learn

Add a shared operation through its service, Application Tool and catalog entry. Distinguish reads
from mutations.

## When to use it

A Command describes an application operation with defined inputs/results. Add one when the operation
is missing; a new entrypoint to an existing operation does not need a second Command.

Follow `credit_exposure` in `config/command_catalog.yaml`, `_credit_exposure` and
`TOOLS["credit_exposure"]` in `tools/application.py`, and `credit_exposure` in its service module.
Unlike `reserve`, this entrypoint requires no mutation approval. It reads existing tenant-scoped
records; a read must not change business records while displaying them. Take inputs/results from the
actual schema rather than copying the reservation contract into a query.

## Before you start

Identify the affected Reality records and intended business outcome. Use PostgreSQL tests and
existing fixtures. Spec, plan and tests precede implementation; see the
[shared reference](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/reference.md).

## Worked example

1. `packages/reality-core/src/reality/services/core.py::reserve` owns the rules. It loads the
   `Commitment` with tenant scope, checks holds and inventory identity, calculates quantities with
   `Decimal`, creates the `Reservation`, and emits the Business Event.
2. `packages/reality-core/src/reality/tools/application.py::_reserve` translates application
   arguments into that service call and returns stable IDs plus `requested`, `applied`, `shortage`
   and `event_id`.
3. The same file registers `TOOLS["reserve"]` with `mutating=True`. Proposal and approval handling
   therefore recognizes the operation as a mutation.
4. `packages/reality-core/config/command_catalog.yaml` describes reads, writes, effect, parameters
   and adapters. `workspace_catalog.yaml` places it as the `reserve_stock` action.
5. HTTP, MCP, CLI and Chat call this application capability; they do not implement reservation
   rules.

Read the complete service and wrapper in the repository. Reservation uses the same path for Web, CLI
and agents; wrappers are not another rule authority.

## Step by step

1. Add a failing business test under `packages/reality-core/tests/`. State preconditions, records
   written, event emitted and authoritative verification read.
2. Implement the tenant-scoped service in `src/reality/services/`. Do not accept a document number
   or SKU where an opaque ID is required.
3. Add the wrapper and `Tool(...)` entry to `tools/application.py`. Mark every state-changing tool
   as mutating.
4. Add the command to `config/command_catalog.yaml`. If a human can trigger it, add an action to
   `config/workspace_catalog.yaml` with prerequisites, confirmation and result kind.
5. Add only the adapters needed. Agent mutations use `create_change_proposal`; the stored proposal
   contains the exact tool, arguments and server preview and runs only after separate approval.
6. Test the service, application tool, catalog and each adapter boundary.

Useful examples are `test_inventory_and_fulfillment.py`, `test_application_tools.py`,
`test_application_catalog.py` and `test_http_boundary.py`.

A read Command may expose a calculation or Projection. Keep the calculation in its shared service;
use an Exception derivation for a current risk condition and a connector for ERP transport. Never
add delivery or reservation status to a Document; derive it from Reality records.

## Check the result

Use the same business test story through service, tool and adapter: sufficient stock, shortage, held
Commitment and foreign tenant identity. Verify through Reservations and Movements rather than a new
Document status. Add resource membership and `labels.de` in `config/resource_catalog.yaml`, run
`make docs-generate` and inspect the reference.

Continue with concrete [Agent Tool](/development/agent-tools) and
[Web Action](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/web-actions.md)
templates. A new Command does not automatically require a new table; schema changes need a proven
use case in the spec and plan.

## Try it yourself

Trace the read `credit_exposure` Command and record its service, inputs/results. Compare it with
`reserve`: mutation marking and approval apply to the change. Expected result: explain which
existing parts an extra entrypoint reuses.

## Common mistakes

No business rules in adapters, document numbers as IDs or fulfillment status on Documents. A
shortened example does not replace the complete implementation's guards, idempotency and events.

## Continue

[Develop exceptions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/exceptions.md)
explains derived attention needs. Continue with [Agent Tools](/development/agent-tools) and
[Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/web-actions.md)
for entrypoints.
