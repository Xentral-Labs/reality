# Data Model: Large-Tenant Register Benchmark

This feature adds no persistent business schema. These are benchmark artifact concepts
and their relationships to existing business records.

## Benchmark Dataset Definition

Fields: definition version, profile (`reduced` or `full`), seed, UTC business date,
order count, deterministic line/flow distributions, expected record cardinalities and
control-tenant sentinel definition.

Validation:

- Identical definition, profile and seed produce identical external identities, dates,
  distributions and expected counts. Database-generated opaque IDs may differ after an
  explicit rebuild; they remain stable across repeated reads of one completed dataset.
- Full profile has at least 10,000 distinct orders on one business date.
- Every order has SourceRecord, Document and DocumentLine evidence and applicable
  shortest links to Reality records.
- A profile is incomplete until all cardinality and sampled trace checks pass.

## Benchmark Tenant

An existing Tenant containing the generated records. It gains no benchmark-only fields
or behavior and is never identified by human-readable order/document numbers.

## Control Tenant

An existing Tenant populated with overlapping human numbers and unique sentinel strings.
Every case checks rows, counts, aggregates, searches and options for its absence.

## Benchmark Case

Fields: stable case ID, register family, operation, product read parameters, expected
total/page/aggregate, SQL expectations and covered requirement IDs.

Validation:

- IDs are unique and deterministically ordered.
- All nine families have representative count, filter and paging coverage.
- Expected values derive from the dataset definition, not the returned page.

## Case Observation

Fields: case ID, start time, duration, outcome, observed row/count/page/aggregate values,
bounded statement summaries and safe failure context. Credentials and full source
payloads are excluded.

## Benchmark Result

Validated by the canonical Pydantic v2 result model in the benchmark harness. Its
exported contract is retained as `contracts/benchmark-result.schema.json`. It binds
revision and schema to environment, dataset identity/cardinalities, ordered observations,
outcome and limitations.

State transitions:

```text
started -> setup_validated -> cases_complete -> report_validated -> accepted
    |             |                 |                 |
    +-----------> failed <----------+-----------------+
```

Only a passing, schema-valid, complete full-profile result may become accepted. Product
owner final review records acceptance; generation alone does not.
