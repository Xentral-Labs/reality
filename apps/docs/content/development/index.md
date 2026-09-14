# Reality Core Development

This section is for contributors who change Reality's shared business behaviour. ERP consultants
should normally begin with [What can be adapted?](../integrations/customization) and enter this
section only when the required Command, Projection or Exception does not exist yet.

## What Core developers can add

| You want to…                                            | Extend…                              | Continue with…                                                               |
| ------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------- |
| import another ERP object losslessly and interpret it   | connector capability and interpreter | [Connect another ERP](./connectors)                                          |
| perform an operation such as allocating stock           | service and application command      | [Add business commands](./commands)                                          |
| calculate a reusable position such as available stock   | Projection                           | [Develop metrics and operational warnings](./derived-views)                  |
| bring a current risk into the operational queue         | Exception derivation                 | [Develop metrics and operational warnings](./derived-views#add-an-exception) |
| make an existing capability available to another client | adapter only                         | [Expose capabilities safely](./application-surfaces)                         |

Do not begin with a page or API endpoint. First decide which business question is missing. The
implementation order is always:

```text
domain records → application service → application tool → adapters
```

## Repository map

| Concern               | Main location                                            | Existing example                                  |
| --------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| Domain records        | `packages/reality-core/src/reality/db/core.py`           | `Commitment`, `Reservation`, `Movement`           |
| Business behaviour    | `packages/reality-core/src/reality/services/`            | `core.py::reserve`                                |
| Application tools     | `packages/reality-core/src/reality/tools/application.py` | `_reserve` and `TOOLS["reserve"]`                 |
| Executable vocabulary | `packages/reality-core/config/*.yaml`                    | `command_catalog.yaml`, `projection_catalog.yaml` |
| HTTP adapter          | `packages/reality-core/src/reality/web/api.py`           | tenant-scoped routes calling services             |
| Agent adapter         | `packages/reality-core/src/reality/mcp/catalog.py`       | tool input schemas and proposal tools             |
| Web client            | `apps/web/src/`                                          | API client and operational pages                  |
| Verification          | `packages/reality-core/tests/`                           | service, catalog, HTTP and business-story tests   |

## Before changing code

1. Find the closest existing business story and follow it end to end.
2. Update the feature specification when observable behaviour changes. A documentation-only
   clarification has `Spec impact: none`.
3. Add the service test first where practical.
4. Keep Source → Evidence → Reality traceable and every query tenant-scoped.
5. Use opaque IDs. A document number, SKU or ERP number is a reference, never identity.

An upstream field stays in the lossless `SourceRecord.payload` unless core logic repeatedly needs to
calculate, filter, join, constrain, predict or act on it. Adapters never write through the ORM and
never reproduce business rules.

## A useful reading exercise

Trace stock reservation through the repository: `reserve` in `services/core.py`, `_reserve` and the
`TOOLS` entry in `tools/application.py`, `reserve` in `command_catalog.yaml`, `reserve_stock` in
`workspace_catalog.yaml`, and the assertions in `test_inventory_and_fulfillment.py` and
`test_application_tools.py`. That is the complete shape a new governed operation should resemble.

Before adding anything, check the generated [Tool Usage reference](../tool-usage/): it lists every
existing command, Business Event, Projection, Exception, MCP tool and workspace action.
