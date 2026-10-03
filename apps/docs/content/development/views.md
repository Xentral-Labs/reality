# Develop Views

## What you will learn

Build a business read surface on an existing reader without copying business rules.

## When to use it

A View is the business surface where users read data. Reuse an existing register or Projection; a
new View does not automatically need a new Projection. Define the user's question, filters and
explanation path first.

Register the View in `packages/reality-core/config/workspace_catalog.yaml` with a stable key, route
and data basis. The Web surface reads existing tenant-scoped services without its own calculations.
Test tenant boundaries, filters, empty results and links to underlying Reality records.
[Add entrypoints](./application-surfaces) explains the shared service boundary.

## Before you start

Write the user question and inspect the [View catalog](../tool-usage/views). You need a
tenant-scoped reader and TypeScript/React for a Web page. If the read model is missing, start with
[Projections](./projections).

## Worked example

Follow `warehouse_queue` in the workspace catalog. Its entry uses `kind: materialized_projection`,
`route: warehouse-queue` and `projection: fulfillment_queue`. `orders` uses the same Projection for
a different business purpose. This is the template for a View backed by an existing read model. A
new route/catalog entry alone is insufficient: connect the reader and page through existing API/Web
mappings.

```yaml
- {
    key: warehouse_queue,
    label: Warehouse Queue,
    route: warehouse-queue,
    kind: materialized_projection,
    projection: fulfillment_queue,
    description: Orders prioritized for warehouse execution and shipment readiness,
  }
```

## Step by step

1. Write a test for the question, filters and expected rows.
2. Reuse the existing `fulfillment_queue` reader; preserve reservation rules.
3. Add the View in `workspace_catalog.yaml` and its resource in `resource_catalog.yaml`.
4. Connect the API reader, route and page through existing Web mappings, following
   `warehouse_queue`.
5. Add labels, empty/error states and links to the underlying Commitment.
6. Run `make docs-generate`.

## Check the result

Compare the reader and page: identical rows and quantities, correct filters, empty state and no
other tenant’s data. Follow a row’s explanation to its Reality records. A catalog entry alone does
not pass this check.

## Try it yourself

Sketch a second surface over the same `fulfillment_queue` for another role. List its question,
filters and columns. Decide whether it needs a new reader using the existing fields.

## Common mistakes

Confusing a View with its Projection; recalculating quantities in the browser; expecting YAML alone
to create a page; replacing opaque IDs with document numbers.

## Continue

Use [Projections](./projections) for a new read model or [Web Actions](./web-actions) for an
interaction.
