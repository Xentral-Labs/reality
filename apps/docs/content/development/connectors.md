# Connect an ERP System

An integration has two independent parts: the connector transports and stores the external payload;
the interpreter derives Evidence and Reality records. Keeping them separate means an unknown object
can be retained losslessly without pretending that its business meaning is known.

## Existing paths

| Kind                      | Extend here                                  | Example                             |
| ------------------------- | -------------------------------------------- | ----------------------------------- |
| Named ERP object          | `services/core.py` and `SOURCE_INTERPRETERS` | `("shopify", "order")`              |
| CSV, JSON or JSONL upload | `services/file_interpreters.py`              | `sales_order`, `inventory_snapshot` |
| Available connector shell | `config/connector_catalog.yaml`              | Odoo, Xentral, weclapp              |
| Source capability         | `SourceCapability` through the service/API   | source type → target type           |

`connector_catalog.yaml` only advertises a credential-free shell and its possible capabilities. It
does not contain authentication, transport or field mapping, and an installed shell does not imply
that an interpreter exists.

## Example: Shopify order

`services/core.py::_shopify_interpretation` reads the immutable `SourceRecord.payload`, resolves or
creates Evidence and Reality records for first versions, links them to `source_record_id`, and emits
events. Changed versions require review without replacing existing business records. Registration is
explicit:

```python
SOURCE_INTERPRETERS = {
    ("shopify", "order"): _shopify_interpretation,
}
```

`process_import_job` selects the interpreter by `(source_system, source_type)`. With no registered
interpreter, the job becomes `unmapped` and records an `interpreter_unavailable` outcome. Ambiguous
business meaning should raise `InterpretationNeedsReview`; it must not be guessed.

## Add an ERP object

1. Capture the vendor payload unchanged as a versioned `SourceRecord`. Keep authentication and
   polling in the adapter; call the shared ingest service.
2. Add the source type and intended target to the connector shell when it should be selectable.
3. Implement a tenant-scoped interpreter. Use application services such as `create_document`,
   `create_item` or `record_movement`; do not write ORM rows from the transport adapter.
4. Preserve `source_record_id` on Evidence/Reality records and emit the normal business events.
5. Register the exact `(source_system, source_type)` key in `SOURCE_INTERPRETERS`.
6. Test first import, retry, upstream correction/supersession, ambiguous input, malformed input and
   tenant isolation. Assert the trace back to the original payload.

For file imports, add a target to `FILE_INTERPRETER_TARGETS`, define required and optional columns
in `FILE_MAPPING_PROFILES`, and implement the branch in `interpret_artifact`. Do not silently match
a human number when it is not unique.

Read the [Connector contract](../integrations/connector-contract) before implementing transport.
