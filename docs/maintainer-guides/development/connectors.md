# Connect ERP and Data Sources

Start with [Connect an example ERP step by step](../integrations/example-erp.md): promises first, then
actual deliveries and the additional data your question requires. That chapter shows the business
output before this guide explains implementation.

## What you will learn

Separate transport from interpretation and trace an ERP order losslessly to its operational promise.

## When to use it

An integration has two independent parts: the connector transports and stores the external payload;
the interpreter derives Evidence and Reality records. Keeping them separate means an unknown object
can be retained losslessly without pretending that its business meaning is known.

## Before you start

Have an original payload, source identity and version contract. Use a test company and keep
credentials out of fixtures. Read the
[From source data to Reality](../integrations/connector-contract.md) first.

| Kind                      | Extend here                                  | Example                             |
| ------------------------- | -------------------------------------------- | ----------------------------------- |
| Named ERP object          | `services/core.py` and `SOURCE_INTERPRETERS` | `("shopify", "order")`              |
| CSV, JSON or JSONL upload | `services/file_interpreters.py`              | `sales_order`, `inventory_snapshot` |
| Available connector shell | `config/connector_catalog.yaml`              | Odoo, Xentral, weclapp              |
| Source capability         | `SourceCapability` through the service/API   | source type → target type           |

`connector_catalog.yaml` only advertises a credential-free shell and its possible capabilities. It
does not contain authentication, transport or field mapping, and an installed shell does not imply
that an interpreter exists.

## Worked example

`services/core.py::_shopify_interpretation` reads the immutable `SourceRecord.payload`, resolves or
creates Evidence and Reality records for first versions, preserves provenance through Evidence and
shortest Reality links, and emits events. Supported reductions/cancellations use the shared change
service; other changes require review. Existing Evidence is not replaced. Registration is explicit:

```python
SOURCE_INTERPRETERS = {
    ("shopify", "order"): _shopify_interpretation,
}
```

`process_import_job` selects the interpreter by `(source_system, source_type)`. With no registered
interpreter, the job becomes `unmapped` and records an `interpreter_unavailable` outcome. Ambiguous
business meaning should raise `InterpretationNeedsReview`; it must not be guessed.

## Step by step

1. Capture the vendor payload unchanged as a versioned `SourceRecord`. Keep authentication and
   polling in the adapter; call the shared ingest service.
2. Add the source type and intended target to the connector shell when it should be selectable.
3. Implement a tenant-scoped interpreter. Use application services such as `create_document`,
   `create_item` or `record_movement`; do not write ORM rows from the transport adapter.
4. Preserve the shortest true provenance links: Evidence references its SourceRecord; Reality refers
   to its Evidence or existing authoritative record. Do not duplicate a SourceRecord foreign key on
   every derived record. Emit normal business events.
5. Register the exact `(source_system, source_type)` key in `SOURCE_INTERPRETERS`.
6. Test first import, retry, upstream correction/supersession, ambiguous input, malformed input and
   tenant isolation. Assert the trace back to the original payload.

For file imports, add a target to `FILE_INTERPRETER_TARGETS`, define required and optional columns
in `FILE_MAPPING_PROFILES`, and implement the branch in `interpret_artifact`. Do not silently match
a human number when it is not unique.

Read the [From source data to Reality](../integrations/connector-contract.md) before implementing
transport.

## Check the result

Work through the [ERP order example](../integrations/order-example.md) alongside the
[From source data to Reality](../integrations/connector-contract.md). Begin with an original payload
fixture. Import must preserve SourceRecord → Document/DocumentLine → Commitment traceability; replay
must not create a second operational promise. A corrected version remains a new SourceRecord and
must not silently overwrite an interpreted business operation. Test unknown object types separately:
payloads remain available even without interpretation.

Recurring intake follows `docs/features/scheduled-jobs.md`: reuse the shared job registry and
services instead of browser timers or API-process loops. Another integration does not need another
scheduler.

## Try it yourself

Deliver the same fixture payload twice: expect no second operational promise. Add an unknown
external field in a new version: retain the original without automatically creating a typed field or
silently overwriting business records.

## Common mistakes

Transport does not write domain ORM rows. Human numbers are not identities. Do not guess unknown
meaning or duplicate Source foreign keys along existing Evidence/Reality links.

## Continue

For complete source cases: [Connect Xentral](../integrations/xentral.md),
[Connect Shopify](../integrations/shopify.md) and [Connect Odoo](../integrations/odoo.md). The
[coverage matrix](../integrations/connector-contract.md#completeness-and-acceptance) defines completion
for your agreed scope.

The [technical order-import example](../integrations/order-example.md) shows the implementation path;
[From source data to Reality](../integrations/connector-contract.md) explains the shared concept and
its rules. [Shared rules](./reference.md) includes scheduling/spec guidance.
