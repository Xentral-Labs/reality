# Benchmark Case Catalog Contract

## Required families

The catalog contains Orders, Commitments, Inventory, Reservations, Movements, Open
items, Payments, Journal and Documents. Every case calls the existing Product Web read
model rather than a benchmark-owned query.

## Common cases

Every applicable family provides:

1. a default first page with at most 50 rows and the complete total;
2. an oversized request returning no more than 100 rows;
3. a selective query/filter matching beyond the unfiltered first page;
4. a zero-match filter;
5. stable, non-overlapping adjacent pages;
6. control-tenant sentinel exclusion;
7. query evidence for tenant scope, filter-before-limit, count-before-limit, stable order
   and bounded result materialization.

Documented categorical, date and Decimal filters are represented where applicable.
Complete-result totals or aggregates use a filtered population larger than one page.

## Case result and repeatability

Each case emits stable ID, family, inputs, expected/observed values, duration, safe query
evidence, requirements and outcome. Missing cases or skipped assertions fail the run.
Two runs on the same dataset must match in ordered cases, expected/observed semantic
values and outcomes; timestamps and durations are excluded from equality.
