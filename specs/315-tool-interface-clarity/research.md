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

## Self-service tutorial review

Reviewed both development overviews, customization guides, connector guides, ERP order example/contract, Command, View/Projection, exception and entrypoint pages against actual source registries. Retain the ERP example's explicit abbreviated-code warning and full-interpreter reference; its ORM example belongs inside the service interpreter, never transport. Existing connector contract covers immutable source versions and chain preservation.

Findings addressed: Commands were incorrectly limited to mutations; source provenance instructions encouraged redundant Reality SourceRecord links; inventory tutorial referred to a nonexistent inventory_position function; Agent Tools/Web Actions lacked visible dedicated templates and end-to-end confirmation examples. Added source-matched MCP registration, full Web Action metadata plus workspace/form wiring, read Command example, shared spec-first workflow, resource labels/docs generation, and business/test verification stories for each extension type. Detailed registry schema remains authoritative; templates illustrate existing operations rather than invent new ones or promise that catalog registration generates forms.

No new runtime capability or service rule. Snippets are disclosed as excerpts in an existing module, not standalone executable projects. Documentation contract tests compare the Agent Tool excerpt to the actual registry.


## Systematic handbook review (2026-10-03)

Approved scope is a documentation learning-path rewrite, not a business-runtime extension. Before implementation, FR-017–FR-021, the appended plan and T024–T028 were reviewed for coverage, Constitution constraints and unresolved questions. All requirements have tasks; no critical finding or unanswered design dependency. The new bilingual overview/outline test failed against the old table before edits.

Content placement: the overview now explains relationships and lists Building block first. Shared repository/workflow material moved to reference.md. Separate views.md and projections.md retain the warehouse_queue and _inventory_rows examples; the full row builder is checked verbatim against the implementation. derived-views.md preserves all previous section headings and onward links. application-surfaces.md is the entrypoint decision page; api-cli.md holds HTTP/CLI implementation guidance. The former generic Web App.tsx pointer is replaced by active apps/web/src/unified/ flows in the reference. Connector/example/contract stay together; existing ERP payload narrative and technical contract remain intact. Customization now explicitly distinguishes supported configuration from missing executable code.

Each implementation chapter follows outcome → use → prerequisites → worked example → ordered changes → verification → exercise → mistakes → next steps. Stock/reservation examples connect shared readers, service, Command, proposal access and workspace interaction. Projections distinguish read-time calculation from materialized caches and include a 10/0/10 → 10/3/7 → 10/0/10 expectation. Training inventory access copies the actual schema and read handler, adds no production registration and is removed after the exercise.

This review establishes source correctness and a consistent teaching structure. It does not claim that a new reader independently completed every extension tutorial, or that every hypothetical extension was implemented. Desktop/mobile visual review remains unavailable in the enabled browser environment.


## Vendor coverage research and review (2026-10-03)

SOURCE_INTERPRETERS currently registers Shopify order and refund plus demo types; Xentral/Odoo have shells only. The shells advertise more objects than the executable registry implements. The earlier generic Shopify update paragraph was stale: shop_order_changes.apply_order_version applies supported reductions/cancellations through core services and holds unsupported changes. shop_refunds records supported refund Evidence and return announcements/reductions; that does not imply general payment/ledger transport or physical return receipt.

Official references checked: Xentral product/versioned API guide, sales-order lifecycle, stock reads and stock-movement reference; Shopify GraphQL bulk retrieval, HTTPS webhook verification and order/fulfillment guide; Odoo 19 JSON-2 reference (search-returned official content after direct fetch timeout). Guides use version-qualified prerequisites and explicitly require inspection of installed Odoo models/fields and Xentral resource/authentication contracts. No guessed vendor endpoint mappings or runnable fake live adapters are introduced.

Coverage distinguishes source identity and authority, original stated monetary values, physical stock versus allocation, actual shipment versus fulfillment request, snapshot opening versus later movements, legal financial Evidence versus shop order/payment status, return announcement versus physical receipt, and overlapping shop/ERP/provider events. Relevant production/BOM, lots/serials, conditions and service/custom modules are explicit additional scope, not implied support. The shared seven-step numeric scenario and purchasing partial-receipt case are proposed acceptance targets requiring real source fixtures; they are not newly executed vendor integrations.

The Connector Contract is allowlisted input to Product Advisor knowledge. Its prose update invalidated the generated knowledge checksum during Python verification. Regeneration updates only derived knowledge/capability payloads and shared generated references; no new command, schema, transport, interpreter or capability was registered. New vendor pages are documentation destinations, not new advisor capability registrations.
