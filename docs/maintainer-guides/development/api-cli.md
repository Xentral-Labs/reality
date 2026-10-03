# Add API and CLI Entrypoints

## What you will learn

Expose an existing operation through HTTP or CLI and verify its boundaries.

## When to use it

A supported client needs HTTP, or development and administration need terminal access. Use
[Agent Tools](./agent-tools.md) for agents and [Web Actions](./web-actions.md) for human interactions.

## Before you start

The shared service must already exist and be tested. Read [Commands](./commands.md) and the
[development reference](./reference.md). Use PostgreSQL test fixtures and the authenticated tenant
boundary.

## Worked example

Follow `tenant_inventory_control` in `packages/reality-core/src/reality/web/api.py`:
`/inventory-control` calls the shared read model with tenant and pagination arguments. For
mutations, `commitment_reserve` in `packages/reality-core/src/reality/cli/app.py` shows
`selected_tenant` → `reserve` → result presentation. Its `@commitment_app.command("reserve")`
decorator registers the CLI subcommand. Neither adapter owns an inventory formula.

## Step by step

1. Write adapter tests for success, invalid input and another tenant first.
2. Define Pydantic HTTP request/response models or typed Typer arguments.
3. Resolve the tenant through the existing entrypoint and call the shared service.
4. Translate domain errors using existing error conventions.
5. Inspect `/openapi.json` or CLI help. Add a typed Web client only when needed.

## Check the result

With the same fixture, compare the adapter response with the direct service read. Check
authentication, tenant isolation, validation and safe errors. Verify mutations through a subsequent
authoritative read. Agent approval remains part of the agent flow; an HTTP entrypoint does not
replace it.

## Try it yourself

Trace an additional inventory filter through HTTP/CLI → shared reader → result. First check whether
the reader already supports it; do not introduce another calculation.

## Common mistakes

Writing ORM records in an adapter; trusting an unchecked tenant input; copying domain rules;
reporting success without verifying the result.

## Continue

[Agent Tools](./agent-tools.md), [Web Actions](./web-actions.md) and the [shared reference](./reference.md).
