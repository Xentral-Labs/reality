"""What deriving a reservation's open quantity costs on the hot read paths (spec 317).

Builds a disposable database migrated to head, fills one large company with a
year of reservation history in today's shape (stored status, split rows) and in
the proposed shape (unchanging reservation plus appended resolutions), and runs
the same five reads against both. Reports the median time of several runs and
the shared buffers each plan touched, which, unlike time, does not move with
host load.

    TEST_POSTGRES_ADMIN_URL=... PYTHONPATH=src python \
        ../../specs/317-reservation-resolutions/research/measure_open_reservations.py \
        --reservations 200000 --output out.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine, make_url, text

ADMIN = os.getenv(
    "TEST_POSTGRES_ADMIN_URL",
    "postgresql+psycopg://reality:local-only@localhost:54329/postgres",
)
TENANT = "ten_big"

SETUP = """
INSERT INTO tenant (id, name, purpose, created_at)
  SELECT 'ten_big', 'Big', 'business', now()
  UNION ALL SELECT 'ten_n' || g, 'Noise ' || g, 'business', now() FROM generate_series(1, 3) g;

-- Today's shape. Per reservation: 2 % still open, 3 % released, the rest
-- consumed; one in ten consumed reservations was shipped in two parts, which
-- today is a consumed row plus a remainder row.
CREATE TEMP TABLE plan AS
  SELECT g AS n,
         'itm_' || (g % 150) AS item_id,
         'loc_' || (g % 3) AS location_id,
         now() - ((200000 - g) * interval '1 day' / 550) AS reserved_at,
         CASE WHEN g > :reservations * 0.98 THEN 'active'
              WHEN g % 33 = 0 THEN 'released'
              ELSE 'consumed' END AS fate,
         (g % 10 = 0) AS split,
         (1 + g % 9)::numeric AS quantity
  FROM generate_series(1, :reservations) g;

INSERT INTO reservation (id, tenant_id, commitment_id, item_id, location_id, quantity, status, reserved_at)
  SELECT 'res_' || n, :tenant, 'com_' || n, item_id, location_id,
         quantity, fate, reserved_at FROM plan;
INSERT INTO reservation (id, tenant_id, commitment_id, item_id, location_id, quantity, status, reserved_at)
  SELECT 'res_' || n || '_r', :tenant, 'com_' || n, item_id, location_id,
         quantity, fate, reserved_at + interval '1 day' FROM plan
  WHERE split AND fate = 'consumed';
INSERT INTO reservation (id, tenant_id, commitment_id, item_id, location_id, quantity, status, reserved_at)
  SELECT 'res_n' || g, 'ten_n' || (1 + g % 3), 'com_n' || g, 'itm_' || (g % 150),
         'loc_' || (g % 3), 1, CASE WHEN g % 50 = 0 THEN 'active' ELSE 'consumed' END, now()
  FROM generate_series(1, :reservations / 4) g;

-- The proposed shape: the reservation as made, and what happened to it.
CREATE TABLE reservation_new (
  tenant_id text NOT NULL, id text NOT NULL, commitment_id text NOT NULL,
  item_id text NOT NULL, location_id text NOT NULL, quantity numeric(18,4) NOT NULL,
  reserved_at timestamptz NOT NULL, handling_unit_id text, lot_id text, serial_unit_id text,
  PRIMARY KEY (tenant_id, id));
CREATE INDEX ix_rn_item ON reservation_new (tenant_id, item_id, location_id);
CREATE INDEX ix_rn_commitment ON reservation_new (tenant_id, commitment_id);
CREATE INDEX ix_rn_reserved ON reservation_new (tenant_id, reserved_at, id);
CREATE TABLE reservation_resolution (
  tenant_id text NOT NULL, id text NOT NULL, reservation_id text NOT NULL,
  kind text NOT NULL, quantity numeric(18,4) NOT NULL, resolved_at timestamptz NOT NULL,
  movement_id text, PRIMARY KEY (tenant_id, id));
CREATE INDEX ix_rr_reservation ON reservation_resolution (tenant_id, reservation_id);

INSERT INTO reservation_new (tenant_id, id, commitment_id, item_id, location_id, quantity, reserved_at)
  SELECT :tenant, 'res_' || n, 'com_' || n, item_id, location_id,
         quantity * CASE WHEN split AND fate = 'consumed' THEN 2 ELSE 1 END, reserved_at
  FROM plan;
INSERT INTO reservation_new (tenant_id, id, commitment_id, item_id, location_id, quantity, reserved_at)
  SELECT 'ten_n' || (1 + g % 3), 'res_n' || g, 'com_n' || g, 'itm_' || (g % 150),
         'loc_' || (g % 3), 1, now()
  FROM generate_series(1, :reservations / 4) g;
INSERT INTO reservation_resolution (tenant_id, id, reservation_id, kind, quantity, resolved_at)
  SELECT :tenant, 'rr_' || n, 'res_' || n,
         CASE fate WHEN 'released' THEN 'release' ELSE 'consume' END, quantity, reserved_at
  FROM plan WHERE fate <> 'active';
INSERT INTO reservation_resolution (tenant_id, id, reservation_id, kind, quantity, resolved_at)
  SELECT :tenant, 'rr_' || n || '_r', 'res_' || n, 'consume', quantity, reserved_at + interval '1 day'
  FROM plan WHERE split AND fate = 'consumed';
INSERT INTO reservation_resolution (tenant_id, id, reservation_id, kind, quantity, resolved_at)
  SELECT 'ten_n' || (1 + g % 3), 'rr_n' || g, 'res_n' || g, 'consume', 1, now()
  FROM generate_series(1, :reservations / 4) g WHERE g % 50 <> 0;
ANALYZE;
"""

OPEN_NEW = """
  (SELECT r.*, r.quantity - coalesce(x.q, 0) AS open
     FROM reservation_new r
     LEFT JOIN (SELECT reservation_id, sum(quantity) AS q FROM reservation_resolution
                 WHERE tenant_id = :tenant GROUP BY reservation_id) x
       ON x.reservation_id = r.id
    WHERE r.tenant_id = :tenant {extra}) o
"""

# Per row: a correlated sum, which lets the planner visit only the candidates.
OPEN_LATERAL = """
  (SELECT r.*, r.quantity - coalesce(x.q, 0) AS open
     FROM reservation_new r
     CROSS JOIN LATERAL (SELECT sum(quantity) AS q FROM reservation_resolution s
                          WHERE s.tenant_id = r.tenant_id AND s.reservation_id = r.id) x
    WHERE r.tenant_id = :tenant {extra}) o
"""

COMMITMENTS = ", ".join(f"'com_{n}'" for n in range(199000, 199500))

READS = {
    "active_reserved(item, location)": (
        "SELECT coalesce(sum(quantity), 0) FROM reservation WHERE tenant_id = :tenant "
        "AND item_id = 'itm_7' AND location_id = 'loc_1' AND status = 'active'",
        "SELECT coalesce(sum(open), 0) FROM {open} WHERE open > 0",
        "AND r.item_id = 'itm_7' AND r.location_id = 'loc_1'",
    ),
    "reserved for 500 promises": (
        "SELECT commitment_id, sum(quantity) FROM reservation WHERE tenant_id = :tenant "
        f"AND status = 'active' AND commitment_id IN ({COMMITMENTS}) GROUP BY commitment_id",
        "SELECT commitment_id, sum(open) FROM {open} WHERE open > 0 GROUP BY commitment_id",
        f"AND r.commitment_id IN ({COMMITMENTS})",
    ),
    "reserved per item, whole company": (
        "SELECT item_id, sum(quantity) FROM reservation WHERE tenant_id = :tenant "
        "AND status = 'active' GROUP BY item_id",
        "SELECT item_id, sum(open) FROM {open} WHERE open > 0 GROUP BY item_id",
        "",
    ),
    "reserved per item and location, whole company": (
        "SELECT item_id, location_id, sum(quantity) FROM reservation "
        "WHERE tenant_id = :tenant AND status = 'active' GROUP BY item_id, location_id",
        "SELECT item_id, location_id, sum(open) FROM {open} WHERE open > 0 "
        "GROUP BY item_id, location_id",
        "",
    ),
    "register: newest 50 active": (
        "SELECT id FROM reservation WHERE tenant_id = :tenant AND status = 'active' "
        "ORDER BY reserved_at DESC, id DESC LIMIT 50",
        "SELECT id FROM {open} WHERE open > 0 ORDER BY reserved_at DESC, id DESC LIMIT 50",
        "",
    ),
}


def _measure(connection, sql: str, params: dict, runs: int) -> dict:
    timings = []
    buffers = None
    for _ in range(runs):
        plan = connection.execute(
            text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql), params
        ).scalar()
        top = plan[0]
        timings.append(top["Execution Time"])
        node = top["Plan"]
        buffers = node.get("Shared Hit Blocks", 0) + node.get("Shared Read Blocks", 0)
    return {"median_ms": round(statistics.median(timings), 2), "buffers": buffers}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reservations", type=int, default=200000)
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    name = f"reality_benchmark_317_{uuid.uuid4().hex[:8]}"
    admin = create_engine(make_url(ADMIN), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(ADMIN).set(database=name).render_as_string(hide_password=False)
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=True,
            env={**os.environ, "REALITY_DATABASE_URL": url},
            stdout=subprocess.DEVNULL,
        )
        engine = create_engine(url)
        params = {"tenant": TENANT, "reservations": args.reservations}
        with engine.begin() as connection:
            # Reads do not touch foreign keys; the fixture has no promises or items.
            for (constraint,) in connection.execute(
                text(
                    "SELECT conname FROM pg_constraint WHERE contype = 'f' "
                    "AND conrelid = 'reservation'::regclass"
                )
            ).all():
                connection.execute(
                    text(f'ALTER TABLE reservation DROP CONSTRAINT "{constraint}"')
                )
            for statement in SETUP.split(";\n"):
                if statement.strip():
                    connection.execute(text(statement), params)
        results = {"reservations": args.reservations, "reads": {}}
        with engine.connect() as connection:
            counts = connection.execute(
                text(
                    "SELECT (SELECT count(*) FROM reservation WHERE tenant_id = :tenant),"
                    " (SELECT count(*) FROM reservation_new WHERE tenant_id = :tenant),"
                    " (SELECT count(*) FROM reservation_resolution WHERE tenant_id = :tenant)"
                ),
                params,
            ).one()
            results["rows"] = dict(zip(("today", "proposed", "resolutions"), counts))
            for label, (today, proposed, extra) in READS.items():
                same = [
                    connection.execute(text(today), params).all(),
                    connection.execute(
                        text(proposed.format(open=OPEN_NEW.format(extra=extra))), params
                    ).all(),
                ]
                results["reads"][label] = {
                    "today": _measure(connection, today, params, args.runs),
                    "grouped": _measure(
                        connection,
                        proposed.format(open=OPEN_NEW.format(extra=extra)),
                        params,
                        args.runs,
                    ),
                    "lateral": _measure(
                        connection,
                        proposed.format(open=OPEN_LATERAL.format(extra=extra)),
                        params,
                        args.runs,
                    ),
                    "same_answer": sorted(map(tuple, same[0])) == sorted(map(tuple, same[1])),
                }
        engine.dispose()
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    args.output.write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps(results, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
