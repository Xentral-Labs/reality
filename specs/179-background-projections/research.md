# Research decisions

## Catalog
Measured three unconnected `load_application_catalog()` calls at 1.246s, 1.365s and 0.972s; serialized payload 357,630 bytes. cProfile attributes 1.554/2.287s to YAML parsing and 0.483s to source AST validation. This is local CPU evidence, not production HTTP latency. Keep the raw validation entrypoint; cache a successful runtime snapshot only. Failed results are not cached. Collapsed Inspector entries currently mount 30 full detail components; lazy mount without changing metadata search.

## Outbox as trigger
`emit_business_event` already serializes tenant sequence allocation under the tenant row lock and writes in the business transaction. Scheduler can detect committed dirtiness without adding an enqueue failure to business writes. Queue cap is deferral, never loss. Event invalidation catalog needs a correctness audit before selective refresh; its existing human documentation was not an executable dependency guarantee.

## Internal authorization
Shared queued runs currently require AppUser actor FK. Selecting an arbitrary owner or inventing a user is false attribution. Propose nullable actor strictly constrained to a registered internal cache job; all user-triggered jobs retain current rules. This is the specific schema-review item, not a general system-actor bypass.

## Consistency
Current READ COMMITTED builders issue many queries; merely reading max sequence once is insufficient to publish a consistent generation during concurrent writes. Select repeatable-read before all queries in the projection child and retain claim fencing/atomic success; retry serialization conflicts. New events committed after the snapshot remain dirty. Never hold the business tenant sequence lock across the expensive builder.

## Time and parameterization
Commitment risk/exceptions depend on time, and usage includes activity that may not emit business events. Give these existing materializations minute eligibility through scheduler. Price queries have arbitrary party/item/quantity/time arguments and cannot be universally precomputed: call canonical resolve_price live, without unrelated rebuild. Explicit v2 MCP contracts currently promise live keyset reads and no cache writes; preserve that contract and explain calculation modes.

## Layer and tenant findings
The monolithic builder calls tenant_usage_summaries across all tenants; worker must use a scoped equivalent. Web payments uses live rows plus cached totals and needs a consistent response strategy. Existing jobs prohibit handler commits, so the current committing refresh service must be split into a transaction-bound implementation and explicit maintenance boundary before registration.
