# Add Web Actions

## What you will learn

Expose an existing operation as a confirmed human workflow and follow it to the result register.

## When to use it

A Web Action is a registered interaction: collect inputs, review effects, confirm changes and show
the result. It calls an existing Command. The catalog entry alone does not build a form.

## Before you start

The Command, service and suitable HTTP interface already exist. Identify inputs, permissions,
confirmation style and target register. Begin with [Commands](./commands.md) for missing business
logic.

## Worked example

This existing entry from `packages/reality-core/config/workspace_catalog.yaml` is formatted across
lines for readability:

```yaml
key: reserve_stock
label: Reserve stock
command: reserve
target_route: reservations
confirmation: summary
prerequisites: [commitment]
result_kind: reservation
```

`key` identifies the Web Action; `command` references the shared operation. `prerequisites`
describes required context without replacing service validation. `confirmation` specifies the review
style. `target_route` points to the result register. Reference the entry in the relevant
`workspaces[].actions` too.

## Step by step

1. Specify user role, starting context, inputs, confirmation and result. Plan tests before
   implementing the form.
2. Inspect the Command, service, existing HTTP route and permission. Add only missing parts. The
   service decides stock allocation and holds.
3. Add the action entry and workspace membership. Use stable keys and opaque identities rather than
   document numbers.
4. Follow `ActionLauncher.tsx`, `actionDiscovery.ts` and `CommitmentActionCard.tsx` in
   `apps/web/src/unified/`. Explicitly connect the new flow to supported form/action mappings;
   unknown keys do not automatically become executable.
5. Collect necessary inputs, call the existing typed API and show a concrete confirmation. Preserve
   server-preview and revision contracts; a button cannot bypass them.
6. Present success, partial effects and errors from the server result. Open the target register with
   the existing Inspector explanation path. Do not calculate stock availability in the browser.
7. Test permission, foreign IDs, cancellation without effect, confirmed execution, shortage, errors
   and replay. Templates: `test_unified_workspace_api.py`, `test_http_boundary.py` and
   Action/Workspace tests in `apps/web/scripts/`.
8. Add resource membership and German labels, run `make docs-generate`, and check that the Web
   Action and Command are discoverable with their relationship.

## Check the result

Open a Commitment with stock in a test company. Start the action and enter quantity 5. Cancellation
must not create a Reservation. After confirmation, inspect the Reservations register and its
Commitment link. Repeat with insufficient stock and a foreign tenant identity: the form must show
the service outcome correctly without disclosing another tenant's record.

API and CLI use the same operation. [Add entrypoints](./application-surfaces.md) explains these
adapters; [Add Agent Tools](./agent-tools.md) covers proposal and approval.

## Try it yourself

Trace `reserve_stock` from workspace membership to form and target register. Change only placement
in a local exercise, not the Command. Expect the same operation/confirmation in the chosen
workspace.

## Common mistakes

A YAML entry does not create a form. Do not make arbitrary Commands executable, bypass confirmation
or calculate shortages in the browser.

## Continue

[Agent Tools](./agent-tools.md) covers proposal/approval; [API and CLI](./api-cli.md) covers additional
adapters.
