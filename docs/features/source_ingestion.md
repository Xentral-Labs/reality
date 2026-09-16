# Feature: Generic source ingestion

`enqueue_source` is the shared CLI/API entry point for any external JSON object.
The tenant-scoped identity is `(source_system, source_type, external_id)`; canonical
payload hashing makes identical delivery idempotent and changed payloads immutable
versions in one SourceStream.

Storage and interpretation are separate. Every accepted version receives one
ImportJob. `SOURCE_INTERPRETERS` maps known `(system, type)` pairs to application
interpreters. Unknown pairs are stored with status `unmapped`, never guessed or
discarded. Registering an interpreter later allows an unmapped job to be retried.

The transactional outbox emits `source_record.received` once for a new version,
`source_record.unmapped` for unknown formats, and `source_record.interpreted` after
a successful interpretation. An interpreter creates Evidence and Reality in its
job transaction and emits their normal business events.

The initial registry contains `("shopify", "order")`. Stripe, CRM, PIM, and custom
formats use the same ingestion service and add only their explicit interpreter.

## Interpretation coverage

`ImportJob.status` is current queue state, not history. Every terminal attempt appends
one tenant-scoped `InterpretationOutcome`. A successful outcome commits atomically with
the Evidence and Reality it produced and references controlled types and opaque IDs.
On failure, attempted business changes roll back before a safe `failed` outcome is
stored.

Non-executed sources receive attempt-zero outcomes: `unsupported`, `stale`, or
`conflict`. `pending` and `processing` are non-terminal job states. `not_recorded` is a
computed label for historical sources without outcome evidence, never a fabricated
outcome. Agents use the read-only `interpretation_coverage` capability through Chat or
MCP; it excludes payloads, job inputs, credentials, and stack traces.

## Tenant integration registry

Tenants may define external systems before a connector exists. `SourceSystem` is
the opaque identity of one configured origin (for example `shopify_de` or
`shopify_b2b`). `SourceCapability` declares which upstream `source_type` that
origin may provide and its intended operational `target_type`. Multiple systems
may declare the same source or target type.

The registry is descriptive in V0: ingestion remains open and lossless so an
unregistered or not-yet-interpretable payload is still retained as immutable
SourceRecord evidence. Interpreter availability is derived from the application
registry, not edited by users. Credentials, endpoints, schedules, mappings, and
connector state are intentionally out of scope until an actual adapter exists.

A `SourceSystem` additionally records the connector shell it was installed from
(`connector_code`) and an optional `base_url` (spec 211). The connector code is the only
association between an instance and a catalog connector; the description-prefix test it
replaced claimed one instance for several connectors whenever two catalog display names
shared a prefix. The base address is where this system's own interface answers, for
example `https://acme-de.myshopify.com/admin`. It stays inside the descriptive boundary
above: it holds no credential, Reality never calls it, and it drives nothing but a link a
person can follow. Vendor address templates live in `connector_catalog.yaml` under
`deep_links`, keyed by source type, and may interpolate only `{external_id}`. A connector
without a template, or a system without a base address, simply offers no link.

`docs/connector_catalog.yaml` is the machine-readable catalog of mock connector
shells. A user selects the exact capabilities needed and chooses a tenant-local
instance code; installing `order` from `xentral_shop_de` must not implicitly
enable products, contacts, or payments. Multiple instances of one vendor are
valid. Installation creates only a SourceSystem and the selected
SourceCapabilities. It never stores credentials, calls a vendor API, schedules
sync, or claims to be connected.

SourceRecord keeps its textual source-system snapshot because evidence is
immutable. New configuration relationships use opaque SourceSystem IDs.

## Large-file intake

Orders, Items, Parties, Inventory, Payments, Documents, and Integrations all
open one contextual intake flow. The entry point supplies only an
`expected_target`; it does not create a second set of import rules.

Files are streamed in bounded chunks into tenant-scoped, content-addressed
artifact storage. They are never base64-encoded into a Change Proposal or loaded into
memory in full. `SourceArtifact` retains the immutable original bytes plus its
SHA-256, byte size, media type, filename, and lifecycle state. A confirmed
`source_ingest` application-tool proposal creates a SourceRecord with a stable
artifact envelope and queues its ImportJob.

Preview is bounded. Full parsing and operational interpretation belong to a
worker reading the stored artifact. Unknown formats remain `unmapped`. An
inventory snapshot must eventually produce append-only adjustment Movements
from a calculated delta; a bank statement must eventually produce payment
Evidence and balanced journal entries. Neither upload directly overwrites a
balance.

## Explicit file mapping profiles

CSV, TSV, and JSONL are streamed row by row. JSON accepts one object or an array
up to 64 MiB; larger JSON remains safely stored and must be supplied as CSV or
JSONL for mapping. Arbitrary files are always retained, but only these explicit
profiles create typed operational records:

| Target | Required columns | Optional typed columns | Existing references |
| --- | --- | --- | --- |
| `item` | `sku`, `name` | `unit`, `item_type`, `tracking_type`, `purchase_unit`, `conversion_factor`, `lead_time_days` | none |
| `party` | `name` | `party_type`/`type`, `roles`, `accounting_code`, `payment_term_code`, `default_currency`, `credit_limit`, `tax_identifier` | payment term by code |
| `location` | `name` | `location_type`, `allows_stock` | none |
| `sales_order` | `order_id` or `order_number`, `sku`, `quantity`, `location`, and `party_accounting_code` or `party_name` | `line_id`, `name`, `unit_price`/`price`, `currency`, `ordered_at`, `requested_delivery_at`, `customer_reference` | company party, customer party, item by SKU, location by exact name |
| `inventory_snapshot` | `sku`, `location`, `quantity` | none | item by SKU, location by exact name |
| `bank_statement` | `amount`, and `party_accounting_code` or `party_name` | `direction`, `currency`, `effective_at`, `payment_number`/`external_id` | party by accounting code or exact name |

Stable aliases are intentionally small: `article_number`/`item_number` for
`sku`, `title`/`description` for `name`, `qty`/`stock` for `quantity`,
`location_name`/`warehouse` for `location`, `value`/`total` for `amount`,
`currency_code` for `currency`, and `date`/`booking_date` for `effective_at`.
Unknown columns are not promoted to schema fields; they remain losslessly
available in the immutable artifact (and order-line payload where applicable).
No fuzzy column guessing is performed.

`fixtures/imports/` contains a coherent, ordered demo set covering every file
profile plus one raw-only JSON payload. The same files are exercised by the
business-story test suite.

After upload, typed profiles show the detected source columns, bounded sample
values, and one manual target-field selector per source column. The suggested
mapping uses only the documented deterministic aliases. Users may change it for
this import before a Change Proposal is prepared. Required target fields are validated
before confirmation, and the confirmed mapping is stored in ImportJob context
so worker execution is reproducible. Mapping never changes the immutable file.

An external Copilot may later suggest this same mapping, but it is optional. If
the tenant has no external provider and API key configured, the screen states
that AI suggestions are unavailable and continues to offer full manual mapping.
