# Implementation plan

## Technical Context
Python3.12+, Pydantic2, SQLAlchemy2 and PostgreSQL. No new dependency/schema.
Existing390 canonical _basis/_reference_check and391 _item_digest are authority.

## Constitution Check
| Principle | Gate | Reason |
|---|---|---|
| Source evidence chain | PASS | Frozen original/source binding, no writes |
| Reality authority | PASS | Existing master data only, no document status |
| Proven schema | PASS | No schema expansion |
| Tenant/service boundary | PASS | Explicit tenant predicates, same service via MCP |
| Tests/specification | PASS | Root-approved FR001-008 and test-first tasks |
| Explainable product | PASS | Canonical reference digests and source links |
| Storage simplicity | PASS | Bounded normal reads, no locks across network |
| Received values | PASS | No recomputed amount, inferred unit or mapping |

## Implementation
Domain DTO in domain/shopify_reference_lookup.py. Service uses canonical source
basis and projects selected received line SKU context. Bounded family queries use
active records, tenant scope and canonical qualification;21st row only establishes
hasMore. Read fingerprints twice with populate_existing to refuse changed master
evidence. Re-read source basis last. No session.flush/commit/add/ORM mutation.
Tool adapter delegates to service; add normal read dispatch, catalogue metadata,
MCP definition and generated tool-usage docs. Freeze input/output schemas and
synthetic response plus actual SDK advertisement.

## Tests and Risks
Disposable PostgreSQL fixtures reused from390/389; no existing database. Verify
business/source/job counts and original payload/input unchanged. Test foreign and
stale source, roles/shipping, duplicate SKU, explicit ID and bounded results.
Mutation-between-reads regression proves no mixed-current output. No broad
snapshot/latest/upstream or whole-record revision claims.

## Rollback
Remove additive read registration and consumer opt-in; no data rollback/migration.
