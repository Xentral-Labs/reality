# Develop Projections

## What you will learn

Derive a reusable read model and prove it can be reproduced from Reality.

## When to use it

Several consumers repeatedly need the same calculated answer. Presentation belongs to
[Views](./views). First inspect the [Projection catalog](../tool-usage/views) for an existing
answer.

## Before you start

You need a defined question, authoritative records and a PostgreSQL service test. Choose explicitly
between read-time calculation and a materialized cache; this example is materialized.

## Worked example

Use a Projection when several consumers repeatedly need the same derived answer, such as physical,
reserved and available inventory. Define the question first, then the authoritative Reality records
and formula that answer it. A Projection is rebuildable and never becomes another source of truth.

Register its producer, consumers and invalidating Business Events. Keep tenant scope in every query,
define deterministic ordering and pagination for registers, and provide an explanation path back to
the underlying records.

### Code example: inventory position

Follow `_inventory_rows` in `packages/reality-core/src/reality/services/projections.py`:

- `OPERATIONAL_PROJECTIONS` declares the supported name.
- `_build_operational_rows` calls tenant-scoped `inventory_rows` and emits one stable `record_key`
  per item with physical, reserved, available, incoming and projected quantities.
- `refresh_operational_projections` rebuilds stale rows; `projection_rows` is the shared,
  deterministically ordered read entry point.
- `config/projection_catalog.yaml` documents records, calculation, outputs and consumers.

The complete row builder from the existing module (its imports and helpers remain in that module):

```python
def _inventory_rows(
    session: Session, tenant_id: str, item_ids: frozenset[str] | set[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Stock, for the whole company or for named articles alone."""
    from reality.services.core import inventory_rows

    return {
        row["item"].id: {
            "item_id": row["item"].id,
            "item": row["item"].name,
            "sku": row["item"].sku,
            **quantity_unit(row["item"]),
            "aggregation": "item_all_locations",
            "physical": row["physical"],
            "reserved": row["reserved"],
            "blocked": row["blocked"],
            "available": row["available"],
            "incoming": row["incoming"],
            "projected": row["projected"],
            "receipt_ids": [movement.id for movement in row["receipts"]],
            "issue_ids": [movement.id for movement in row["issues"]],
        }
        for row in inventory_rows(
            session, tenant_id, item_ids=set(item_ids) if item_ids is not None else None
        )
    }
```

### Before and after

A test item has 10 units of physical stock, no holds and no reservation. Expect physical 10,
reserved 0, available 10. After reserving 3: physical 10, reserved 3, available 7. After release: 10
/ 0 / 10 again. Values come from existing records; rebuilding creates no new movement.

## Step by step

1. Specify records, formula, explanation and freshness contract in the spec and service test. Use
   the before/after case above as an expectation.
2. Implement the row builder in the shared Projection service, using existing readers and stable
   `record_key` identities.
3. For a materialized Projection, connect it to `_build_operational_rows`, `OPERATIONAL_PROJECTIONS`
   and `projection_catalog.yaml`.
4. Connect consumers and refresh. Add event invalidation when the global sequence is insufficient. A
   read-time derivation needs no additional cache.
5. Adapt tenant, rebuild and stale cases from `test_materialized_projections.py`. Add catalog and
   HTTP tests for the surfaces actually exposed.
6. Add resource membership, label and `make docs-generate`.

## Check the result

Create an item, Commitment, Reservation and Movement in a test tenant through existing fixtures and
services. Verify that reservation leaves physical stock unchanged while reserved/available
quantities change correctly. Rebuilding again must produce the same answer; a second tenant must see
none of its rows. Test new events, stale results, deterministic sorting and pagination. Follow each
result's explanation back to Reality records. Register new entries in the resource catalog and
regenerate the reference.

## Try it yourself

Extend the test with a second reservation and its release. Predict physical, reserved and available
quantities before comparing rebuilt results. Change a formula only after specifying a new business
need.

## Common mistakes

Persisting a derivation as new authority; treating every Projection as a cache; displaying stale
results without indicating freshness; omitting tenant scope or stable ordering.

## Continue

[Views](./views) presents the result. [Exceptions](./exceptions) derives attention needed.
