# Research: Tool interface clarity

## Three-operation audit

| Operation | Agent interface | Shared execution | Workspace action | Finding |
|---|---|---|---|---|
| Reservation | `reservation_propose`; registry schema requires `commitment_id`, accepts optional quantity and physical identities; `_propose("reserve")` creates a governed proposal | `tools.application._reserve` calls `services.core.reserve`; preview/service owns allocation and tenant checks | `reserve_stock` maps to `reserve` with confirmation and reservation target | No second reservation implementation. Quantity is optional, so a generic required-positive-field example would misdescribe this interface. |
| Manual order | `order_create_propose`; schema includes direction, parties, location, lines and stated amounts; `_propose("order_create")` | `tools.application._manual_order` calls `services.core.create_manual_order` | `create_manual_order` maps to that service | Transport application-tool name differs from service key. Explicit catalog coverage resolves the relationship; blindly deriving it from names would be incorrect. |
| Customer payment | `customer_payment_post_propose`; requires invoice and amount, accepts payment/source/time metadata; `_propose("customer_payment_post")` | `tools.application._payment("customer")` calls `services.core.post_customer_payment` | `post_customer_payment` maps to that service | Shared customer/supplier adapter already removes execution duplication. Proposal schema and service contract have different responsibilities. |

Sources: `packages/reality-core/src/reality/mcp/catalog.py`, `tools/application.py`, `services/core.py`, `config/command_catalog.yaml`, `config/workspace_catalog.yaml`.

The Web forms were also inspected: `apps/web/src/unified/ActionCard.tsx` sends commitment, explicit quantity and optional tracking identities through `deliveryActions.prepare`, then presents a separate confirmation. Its quantity input is required, whereas the MCP reservation quantity is optional. This is a deliberate interaction difference: a generic required-field definition would change the agent contract. `OrderCard.tsx` sends its draft through `orderActions.prepare` and collects source-stated order/line amounts; it does not make these amounts from line calculations. `PaymentCard.tsx` uses the payment prepare/review/confirmation interface and server-scoped outstanding-invoice reads. Browser choice labels and review layout therefore remain adapter concerns.

## Decision: consolidate presentation terminology first

The generator's `COPY` and `ToolUsage.vue` separately define category names. Both presentations also need the same new explanation and example. Define category labels, singular labels, descriptions and guide text once in the generator; publish them in generated JSON and render manuals from that same metadata. Resolve example IDs through the existing workspace-action command and command-to-tool mapping, validating the proposal access mode.

Rationale: a demonstrated duplicate definition can be removed without changing runtime business semantics. The runtime already shares execution services and generic proposal handlers. The audit does not establish a safe universal equivalence between MCP schemas, service arguments and Web forms.

Alternatives: a universal schema/form generator would add an unproven abstraction and risk changing optional/default/confirmation behavior. Copying a new guide into Vue and both Markdown locales would perpetuate known drift. Replacing explicit catalog mappings with handler-name inference would lose reviewed relationships.

## Compatibility

Keep `action`, `command`, and `tool` IDs, anchors, paths, filters and schemas stable. Rename presentation labels only. General resource/process actions remain business operations. Existing unmapped tool descriptions remain authoritative; mapping absence is explained without guessing a new execution relationship.
