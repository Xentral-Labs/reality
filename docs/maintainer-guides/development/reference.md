# Shared Development Reference

Use this reference while implementing. Start learning from the [overview](./index.md).

The shared integration concept is explained in
[From source data to Reality](../integrations/connector-contract.md): first Source → Evidence →
Reality, then the rules for original records, identities, versions and errors.

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

Additional adapter locations: `packages/reality-core/src/reality/web/read_models.py` composes read
output, `apps/web/src/api.ts` is the typed client, and `apps/web/src/unified/` contains active
workspace flows. CLI lives in `packages/reality-core/src/reality/cli/app.py`.

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

Before adding anything, check the generated [Tool Usage reference](https://docs.runreality.ai/tool-usage/): it lists every
existing command, Business Event, Projection, Exception, MCP tool and workspace action.

## Shared workflow for every extension

Follow `docs/SPEC_DRIVEN_WORKFLOW.md`: specify → clarify/review → plan → tasks → analyze → implement
→ verify → review. Specify the business benefit, smallest necessary change and acceptance story
first. Implement only after clarifications and Constitution/analysis gates pass.

Choose the closest template in the relevant chapter. Read its actual service and tests rather than
copying a shortened excerpt as a complete module. Work domain → services → tools → adapters; a new
entrypoint leaves existing domain/service rules intact. Verify interfaces, permissions, tenant
boundaries, replay and provenance. New catalog entries need resource membership, German labels and
`make docs-generate`.
