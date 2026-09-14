# Operational Exception Contract

## Taxonomy

The initial taxonomy has this stable visible order:

1. `outgoing_commitment_at_risk`
2. `overdue_incoming_supplier_commitment`
3. `source_interpretation_failure`
4. `unexplained_movement`
5. `unmatched_financial_event`

`insufficient_reservation` is a required cause of
`outgoing_commitment_at_risk`, not a sixth visible row.

The taxonomy validator rejects unknown, missing, stale, duplicate, unproven, unordered,
or registry-incompatible classes and causes. Every evidence reference resolves to a
focused test symbol.

## List Row

Every interface receives the same logical fields:

| Field | Contract |
|---|---|
| `id` | Stable derived identity using class ID and authoritative opaque record ID |
| `class_id` | One visible taxonomy class |
| `cause_ids` | Ordered approved causes; empty where none apply |
| `severity` | Default class severity |
| `title` | Stable operator label |
| `impact` | Concise current impact |
| `record_type` | Authoritative record kind |
| `record_id` | Authoritative opaque ID |
| `causal_values` | Reproducible class-specific values |
| `trace` | Compact existing Source/Evidence/Reality identities and explicit absence |

The legacy `severity`, `title`, `id`, and `impact` fields remain available to current
presentation consumers.

## Explanation

Explanation accepts only the derived exception identity and tenant context. The service
re-derives current exceptions and returns the matching row with hydrated authoritative
details. Unknown, resolved, stale, malformed, and foreign identities all return the same
not-found outcome.

Explanation MUST NOT infer authorization from the class ID, embedded record ID, human
number, or Source external ID supplied by the caller.

## Ordering and Pagination

Canonical order is deterministic: severity priority, taxonomy order, causal due/effective
time where applicable, then opaque record ID. Web pagination slices this canonical result
and reports counts from the same result. Projections preserve the same row identities.

## Clearing

- outgoing risk: reserve, fulfill shipment, or cancel through existing services;
- overdue incoming: fulfill receipt or cancel through existing services;
- source failure: successful existing retry/process path;
- unmatched finance: allocate the payment through the existing settlement service;
- unexplained movement: no retroactive clearing in this scope; history remains visible.

No interface directly edits an exception or projection row.

## Shared Consumers

- materialized `exceptions` projection;
- application tools `exceptions` and `exception_explain`;
- Web Home, Exceptions list, and Exception Inspector;
- MCP `exceptions_list` and `exception_explain`;
- fallback Chat risk rendering.

All consumers use the shared service contract and contain no class derivation rule.
