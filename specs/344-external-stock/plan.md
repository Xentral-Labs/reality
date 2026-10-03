# Implementation Plan: External Stock Statements

**Branch**: `344-external-stock` | **Spec**: [spec.md](spec.md)

## Summary

A new append-only table `external_stock_statement` (migration 0133 on 0132) holds stated stock
per item, location and time with its source record and optional reporter. `services/external_stock.py`
records statements (reviewed tool `external_stock_state`), reads the latest per item and location
with Reality's stock at the stated time (set-based, two aggregate queries), and derives the finding
`external_stock_differs`. The file interpreter gains the target `external_stock`.

## Constitution Check

- Source → Evidence → Reality: every statement keeps its source record (the file, or the reviewed
  statement as an internal source); the statement is evidence and never becomes a movement.
- III: the table is typed because core logic repeatedly compares, filters (latest per item and
  location) and derives a finding from it. A Fact predicate was considered; facts are per
  subject without a location and time pair to compare on, so the shortest true relationship is
  a row naming item and location.
- VIII: the stated quantity and time are kept as stated; the difference is derived at read time.
- Tenant scope on every query; mutations are reviewed (the tool) or come from a file import the
  person started.
- No document status.

## Design

- `ExternalStockStatement`: id, tenant_id, item_id, location_id, quantity (Numeric(18,4), ≥ 0),
  stated_at, reporter_party_id (nullable), source_record_id, created_at. Index on
  (tenant_id, item_id, location_id, stated_at).
- Comparison: for the latest statement per pair, sum movements to and from the location with
  `occurred_at <= stated_at`, leaving out corrected and compensating movements (as
  `stock_counts.book_as_of`), grouped by statement in two queries.
- Finding: record_type `external_stock_statement`, record_id the latest statement; sort time the
  stated time.

## Tests

Service tests, adapter tests (MCP strict schema, CLI, API), the J07 story, the migration test, and
all new-class and new-table gates.
