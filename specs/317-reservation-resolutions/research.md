# Research: What Deriving Open Reservations Costs

**Date**: 2026-10-02 · **Raw output**: [research/results-2026-10-02.json](research/results-2026-10-02.json)

## Method

`research/measure_open_reservations.py` creates a disposable `reality_benchmark_317_*` database, migrates it to head and fills it:

- **Large company**: 200,000 reservations across 150 items and 3 locations, reserved over about a year.
  - 2 % still open, 3 % released, the rest consumed.
  - One in ten consumed reservations was shipped in two parts.
- **Today's shape** (`reservation`): 219,007 rows, because a split is a consumed row plus a remainder row.
- **Proposed shape**:
  - `reservation_new`: 200,000 rows, one per reservation as made.
  - `reservation_resolution`: 215,007 appended releases and consumptions.
- **Three noise companies**: 50,000 reservations in each shape.
- Foreign keys on `reservation` are dropped in the fixture. Reads do not use them, and the fixture has no promises or items.

Each read runs 7 times under `EXPLAIN (ANALYZE, BUFFERS)`. Reported are the median execution time and the shared buffers (hit + read) of the top plan node. In both shapes every read returned the same answer.

Two ways to derive the open quantity were tried:

- **grouped**: one grouped sum of the company's resolutions, joined to its reservations.
- **lateral**: a correlated sum per candidate reservation.

## Results

The host was loaded (load average 12–19 from other test runs), so the times are indicative. The buffers do not depend on load.

| Read | Today | Grouped | Lateral |
|---|---|---|---|
| active reserved, one item at one location | 1,338 buf · 2.7 ms | 77,793 buf · 197 ms | 6,647 buf · 11 ms |
| reserved for 500 promises | 16 buf · 0.7 ms | 41,828 buf · 102 ms | 1,515 buf · 2.4 ms |
| reserved per item, whole company | 105 buf · 1.7 ms | 155,832 buf · 359 ms | 1,015,309 buf · 2,273 ms |
| reserved per item and location, whole company | 105 buf · 1.8 ms | 155,832 buf · 312 ms | 1,015,309 buf · 1,839 ms |
| register: newest 50 active | 6 buf · 0.06 ms | 155,852 buf · 325 ms | 156 buf · 0.2 ms |

## Reading

- Today the company-wide reads are served from the `status` index (`ix_reservation_tenant_status_reserved`) and touch only the open rows.
- In the proposed shape, whether a reservation is open follows from a sum over another table. No index can hold that. Every company-wide read therefore visits the whole history: about 1,500× the buffers at one year, growing with every order.
- Targeted reads survive with the lateral form. Company-wide reads do not, and they feed:
  - `core.inventory_rows`
  - `inventory_detail_rows`
  - the operational projections
  - the exception derivations
- `stock_block` (spec 316) does not have this problem, because blocks are few. The same shape is cheap there for the same reason it is expensive here.

## Rerun

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python \
  ../../specs/317-reservation-resolutions/research/measure_open_reservations.py \
  --reservations 200000 --output /tmp/res317.json
```

`TEST_POSTGRES_ADMIN_URL` selects the server; the default is the local test container. The run takes a few minutes and drops its database at the end.
