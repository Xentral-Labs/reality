# Implementation Plan: Merging Duplicate Business Partners

**Branch**: `339-party-merge` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

## Summary

- A reviewed command, `party_merge`, records that one business partner is a duplicate of another, the survivor. It writes one `party_merge` row and the statement as an internal source record, and makes the duplicate inactive through the existing lifecycle event.
- The partner detail and inspector, the customer and supplier balances and the credit exposure resolve merged partners to their survivor at read time. Nothing stated is rewritten.
- Shop orders and file import rows that name a merged partner land on its survivor.

## Technical Context

**Language/Version**: Python 3.12, SQLAlchemy 2, Alembic, PostgreSQL

**Storage**: migration `0131_party_merges` with one table, `party_merge`. No new column.

**Testing**:
- service tests with positive controls and a statement-count bound;
- adapter tests (MCP schema, CLI, web API);
- stories L10 and O02;
- the party balance, credit exposure and Shopify suites as regression.

**Constraints**: tenant-scoped; one merge row per duplicate; merged reads add one bounded query.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The merge statement is an internal source record; the merge row carries it. |
| II. Reality is the operational authority | PASS | No document status; nothing on documents changes. |
| III. Proven schema only | PASS | One table, justified below. |
| IV. Tenant and service boundaries | PASS | Reviewed command through the shared proposal flow; every read is tenant-scoped. |
| V. Specification and test evidence | PASS | Tests first per phase. |
| VI. Explainable Web product | PASS | The survivor's detail names each merged partner; the duplicate's detail names its survivor and the merge's statement. |
| VII. Simplicity and storage discipline | PASS | Existing reads widen their party filter; no parallel ledger. |
| VIII. Received values are recorded, never recomputed | PASS | Every document, promise and ledger entry keeps the party it states. |

### DR-001: `party_merge`

- Every survivor read (detail, balances, credit exposure) filters by it to find the duplicates to add.
- Every balance row and exposure joins a stated party to its survivor through it.
- Intake resolves a named party through it before recording an order.
- The merge itself checks it for chains (a unique duplicate per company) and refuses on it.

A flag or column on `party` would duplicate the survivor link and lose the reason and statement.

## Design

### 1. Merge (`services/party_merges.py`)

- `validate_party_merge`: both partners found in the company, distinct; neither already merged; the survivor not a duplicate and active; the duplicate not the company's partner; every role of the duplicate held by the survivor; no open delivery hold on the duplicate. Refusals are coded.
- `review_party_merge`: normalized arguments and the review: both partners, their roles, how many documents, promises and ledger entries the duplicate brings.
- `merge_party`: under the company's business lock; writes the source record (`internal_party_merge`), the `party_merge` row, the lifecycle change of the duplicate and the event `party.merged`.
- Reads: `party_merges` (the list), `merged_into` (one party's survivor), `merged_members` (survivor → duplicates for a set of parties, one query).

### 2. Merged reads

- `core.party_detail`: widens documents, promises and ledger entries to the survivor and its duplicates; adds `merged_parties` and `merged_into`.
- `finance/balances.party_balance_rows`: maps every row's party to its survivor before bucketing; a `party_ids` filter is widened by the duplicates.
- `credit_exposure.credit_exposures`: reads the survivor and its duplicates and counts them under the survivor.

### 3. Intake

- Shopify interpretation: the context's customer partner resolves to its survivor before the order is recorded.
- File interpretation: a party row match resolves to its survivor; several matches that are one survivor count as one.

### 4. Surfaces and gates

- Tool `party_merge` (mutation) and read `party_merges`; MCP `party_merge_propose` and `party_merges`; CLI `party merge-propose`, `party merges`; web API `POST /parties/merge-proposals`, `GET /party-merges`; the partner page's merge action and merged section.
- Catalogs: commands, events, isolation, action discovery, tool catalog, resource catalog with German labels, refusals, data model, reporting-graph deferral, i18n, `make docs-generate`.

## Rollback

The migration's downgrade drops `party_merge` and is refused while a merge exists. Duplicates made inactive stay inactive.
