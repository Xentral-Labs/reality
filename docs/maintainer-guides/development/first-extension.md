# Your First Extension

## Goal and expected result

In a **local exercise branch**, add a read Agent Tool named `training_inventory_read`. It returns
the same inventory rows as `inventory_read`. Learn registration, schemas, service reuse and result
verification without new tables or business rules. This alias is a training aid rather than a new
product capability.

## Prerequisites

Work from the repository root with the Python environment and dependencies from
[installation](../operations/installation.md). The result test needs the repository’s PostgreSQL test
environment. Do not use a production database. Read the [shared development reference](./reference.md);
product changes still follow specification, review, planning, tasks and tests.

## 1. Understand the template

Open `packages/reality-core/src/reality/mcp/catalog.py` and find `inventory_read` in
`MCP_TOOL_CATALOG`. Its name and label make it discoverable, `read` identifies access, the schema
describes inputs, and `_read("inventory")` reuses the existing Application Tool. The `view` option
selects aggregate or location inventory.

## 2. Test the contract first

Create `packages/reality-core/tests/test_training_inventory_tool.py` with this content. The first
test checks the contract; the second compares actual inventory rows. `session` and `business` use
existing PostgreSQL fixtures, not production data.

```python
from decimal import Decimal

from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services.core import record_movement


def test_training_inventory_schema():
    original = MCP_TOOL_REGISTRY["inventory_read"]
    training = MCP_TOOL_REGISTRY["training_inventory_read"]
    assert training.access == "read"
    assert training.input_schema == original.input_schema


def test_training_inventory_result(session, business):
    record_movement(
        session, business.tenant.id, "opening_stock", business.item.id, "10",
        to_location_id=business.location.id,
    )
    arguments = {"view": "aggregate", "item_id": business.item.id}
    original = dispatch_tool(session, business.tenant.id, "inventory_read", arguments)
    training = dispatch_tool(
        session, business.tenant.id, "training_inventory_read", arguments
    )
    assert len(original["records"]) == 1
    assert Decimal(original["records"][0]["available"]) == Decimal("10")
    assert training["records"] == original["records"]
```

```bash
.venv/bin/python -m pytest packages/reality-core/tests/test_training_inventory_tool.py -q
```

Before registration, the tests fail because the registry key is missing. This is expected.

## 3. Add the entrypoint

Insert this definition **inside `MCP_TOOL_CATALOG`, immediately after `inventory_read`**. Keep the
complete schema rather than inventing simplified inputs. The registry and tool-name set are built
from the catalog.

```python
    MCPToolDefinition(
        "training_inventory_read",
        "Training: read inventory",
        "Read inventory as cursor pages: labelled item totals or item/location rows with units. Page mode does not write projection caches.",
        "read",
        "Operations",
        _object_schema(
            {
                **PAGE_PROPERTIES,
                "view": {
                    "type": "string",
                    "enum": ["aggregate", "location"],
                    "default": "aggregate",
                },
                "item_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
            }
        ),
        _read("inventory"),
    ),
```

## 4. Check the result

Run the test command again. Expected: **2 tests pass**. The first confirms read access and identical
schemas; the second confirms the same nonempty inventory rows through the canonical dispatcher. This
goes beyond a syntax check; the result test requires PostgreSQL.

Then run `make docs-generate` and `make docs-catalog-check`. Existing `inventory` matching provides
the business-resource home. If generation reports an entry without a resource, extend
`resource_catalog.yaml` rather than weakening the check. Inspect the new entry under Item in the
generated catalog. Add separate discovery and production permission tests if you turn the exercise
into a product change.

## 5. Try it yourself

Extend the result test with `view="location"`. Its rows must still match `inventory_read`. Follow
the handler to the shared inventory reader and explain where the calculation happens.

## Clean up and continue

Remove the training alias and test after the exercise and regenerate the reference. Define a
business need before adding a real capability. [Agent Tools](./agent-tools.md) explains read and
mutation access, [Views](./views.md) covers presentation, [Projections](./projections.md) covers
derivation, and [Commands](./commands.md) covers operations.
