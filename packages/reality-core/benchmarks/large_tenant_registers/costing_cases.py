"""Measured PostgreSQL observation strategies; no product API or stored authority."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import groupby

from sqlalchemy import text
from sqlalchemy.engine import Connection

from .costing_kernel import Event, money, replay


@dataclass(frozen=True, slots=True)
class Observation:
    issue_id: int
    order_id: int
    item: int
    economic_date: date
    cost: Decimal | None
    revenue: Decimal | None
    selling: Decimal | None


INPUT_SQL = """
WITH selected AS MATERIALIZED (
 SELECT m.* FROM costing_spike.movement m
 WHERE m.tenant=:tenant AND (CAST(:item AS integer) IS NULL OR m.item=:item)
 AND (CAST(:end_sequence AS integer) IS NULL OR m.sequence<=:end_sequence)
 AND (CAST(:pool_start AS integer) IS NULL OR m.item BETWEEN :pool_start AND :pool_end)
), deltas AS (
 SELECT component_id,sum(amount) amount FROM costing_spike.adjustment
 WHERE tenant=:tenant AND (CAST(:knowledge_revision AS integer) IS NULL OR id<=:knowledge_revision)
 GROUP BY component_id
), costs AS (
 SELECT a.receipt_id, CASE WHEN bool_and(c.known) THEN sum(c.amount+COALESCE(d.amount,0)) END amount
 FROM costing_spike.attribution a
 JOIN selected m ON m.tenant=a.tenant AND m.id=a.receipt_id
 JOIN costing_spike.component c ON c.tenant=a.tenant AND c.id=a.component_id
 LEFT JOIN deltas d ON d.component_id=c.id
 WHERE a.tenant=:tenant GROUP BY a.receipt_id
), matched AS (
 SELECT mt.issue_id,sum(mt.revenue) revenue,sum(mt.quantity) quantity
 FROM costing_spike.matching mt JOIN selected m ON m.tenant=mt.tenant AND m.id=mt.issue_id
 WHERE mt.tenant=:tenant GROUP BY mt.issue_id
), fees AS (
 SELECT a.order_id, CASE WHEN bool_and(c.known) THEN sum(c.amount+COALESCE(d.amount,0)) END amount
 FROM costing_spike.attribution a
 JOIN costing_spike.component c ON c.tenant=a.tenant AND c.id=a.component_id
 LEFT JOIN deltas d ON d.component_id=c.id
 WHERE a.tenant=:tenant AND a.order_id IS NOT NULL
 AND EXISTS (SELECT 1 FROM selected m WHERE m.tenant=a.tenant AND m.order_id=a.order_id)
 GROUP BY a.order_id
)
SELECT m.id,m.order_id,m.item,m.sequence,m.kind,m.quantity,m.original_issue,c.amount cost,
       o.economic_date,CASE WHEN mt.quantity=m.quantity THEN mt.revenue END revenue,f.amount selling
FROM selected m JOIN costing_spike.trade_order o ON o.tenant=m.tenant AND o.id=m.order_id
LEFT JOIN costs c ON c.receipt_id=m.id
LEFT JOIN matched mt ON mt.issue_id=m.id
LEFT JOIN fees f ON f.order_id=m.order_id
ORDER BY m.item,m.sequence
"""


def derive(
    connection: Connection,
    tenant: str,
    order_id: int | None = None,
    *,
    pool: int | None = None,
    knowledge_revision: int | None = None,
    pool_range: tuple[int, int] | None = None,
) -> tuple[list[Observation], list[tuple]]:
    item = pool
    end_sequence = None
    if order_id is not None:
        item = connection.scalar(
            text(
                "SELECT item FROM costing_spike.trade_order WHERE tenant=:tenant AND id=:id"
            ),
            {"tenant": tenant, "id": order_id},
        )
        if item is None:
            return [], []
        end_sequence = order_id * 10
    params = {
        "tenant": tenant,
        "item": item,
        "end_sequence": end_sequence,
        "knowledge_revision": knowledge_revision,
        "pool_start": pool_range[0] if pool_range else None,
        "pool_end": pool_range[1] if pool_range else None,
    }
    rows = connection.execute(text(INPUT_SQL), params).mappings()
    output = []
    inventory = []
    for item_id, group in groupby(rows, key=lambda r: r["item"]):
        batch = list(group)
        result = replay(
            Event(
                str(r["id"]),
                r["kind"],
                r["quantity"],
                r["cost"],
                None if r["original_issue"] is None else str(r["original_issue"]),
            )
            for r in batch
        )
        metadata = {r["id"]: r for r in batch if r["kind"] in ("issue", "return")}
        for issue in (*result.issues, *result.returns):
            identity = int(issue.identity)
            row = metadata[identity]
            if order_id is not None and row["order_id"] != order_id:
                continue
            # Six evidenced fulfilment slices per order; allocate original fee totals
            # cumulatively before report filtering, never six rounded unit prices.
            position = (identity - 1) % 10 - 2
            fee = row["selling"]
            selling = (
                None
                if fee is None
                else money(fee * position / 6) - money(fee * (position - 1) / 6)
            )
            if row["kind"] == "return":
                selling = Decimal(
                    0
                )  # Fixture explicitly states no incremental return fee.
            output.append(
                Observation(
                    identity,
                    row["order_id"],
                    item_id,
                    row["economic_date"],
                    issue.cost,
                    row["revenue"],
                    selling,
                )
            )
        inventory.append(
            (
                item_id,
                result.remaining_quantity,
                result.remaining_cost,
                result.unvalued_quantity,
            )
        )
    return output, inventory


def observe(
    connection: Connection, tenant: str, order_id: int | None = None
) -> list[Observation]:
    return derive(connection, tenant, order_id)[0]


def publish(
    connection: Connection,
    tenant: str,
    rows: list[Observation],
    inventory: list[tuple] | None = None,
    *,
    pool: int | None = None,
    input_revision: int | None = None,
) -> None:
    """Caller transaction publishes replacement and checkpoint together."""
    if (
        connection.scalar(
            text("SELECT id FROM costing_spike.tenant WHERE id=:tenant FOR UPDATE"),
            {"tenant": tenant},
        )
        is None
    ):
        raise ValueError("Unknown tenant.")
    connection.execute(
        text(
            "DELETE FROM costing_spike.observation WHERE tenant=:tenant AND (CAST(:pool AS integer) IS NULL OR item=:pool)"
        ),
        {"tenant": tenant, "pool": pool},
    )
    raw = connection.connection.driver_connection
    with (
        raw.cursor() as cursor,
        cursor.copy(
            "COPY costing_spike.observation (tenant,issue_id,order_id,item,economic_date,cost,revenue,selling) FROM STDIN"
        ) as copy,
    ):
        for r in rows:
            copy.write_row(
                (
                    tenant,
                    r.issue_id,
                    r.order_id,
                    r.item,
                    r.economic_date,
                    r.cost,
                    r.revenue,
                    r.selling,
                )
            )
    if inventory is not None:
        connection.execute(
            text(
                "DELETE FROM costing_spike.inventory_observation WHERE tenant=:tenant AND (CAST(:pool AS integer) IS NULL OR item=:pool)"
            ),
            {"tenant": tenant, "pool": pool},
        )
        with (
            raw.cursor() as cursor,
            cursor.copy(
                "COPY costing_spike.inventory_observation (tenant,item,quantity,cost,unknown_quantity) FROM STDIN"
            ) as copy,
        ):
            for r in inventory:
                copy.write_row((tenant, *r))
    prior = connection.scalar(
        text(
            "SELECT input_revision FROM costing_spike.checkpoint WHERE tenant=:tenant"
        ),
        {"tenant": tenant},
    )
    revision = (
        input_revision
        if input_revision is not None
        else connection.scalar(
            text(
                "SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant=:tenant"
            ),
            {"tenant": tenant},
        )
    )
    if prior is not None and prior > revision:
        raise ValueError("Superseded generation cannot replace newer publication.")
    if pool is not None:
        outside = connection.scalar(
            text("""SELECT count(*) FROM costing_spike.adjustment d
          LEFT JOIN costing_spike.attribution a ON a.tenant=d.tenant AND a.component_id=d.component_id
          LEFT JOIN costing_spike.movement m ON m.tenant=a.tenant AND m.id=a.receipt_id
          WHERE d.tenant=:tenant AND d.id>:prior AND d.id<=:revision AND (m.item IS DISTINCT FROM :pool)"""),
            {"tenant": tenant, "prior": prior or 0, "pool": pool, "revision": revision},
        )
        if prior is None:
            raise ValueError("Scoped publication requires complete initial generation.")
        if outside:
            revision = (
                prior  # Conservative: only full replay can certify several dirty pools.
            )
    connection.execute(
        text("""INSERT INTO costing_spike.checkpoint VALUES (:tenant,1,:revision,clock_timestamp())
       ON CONFLICT (tenant) DO UPDATE SET generation=checkpoint.generation+1,input_revision=excluded.input_revision,updated_at=clock_timestamp()"""),
        {"tenant": tenant, "revision": revision},
    )


def order_read(connection: Connection, tenant: str, order_id: int) -> dict | None:
    row = (
        connection.execute(
            text("""SELECT count(*) count,CASE WHEN count(revenue)=count(*) THEN sum(revenue) END revenue,
       CASE WHEN count(cost)=count(*) THEN sum(cost) END cost,
       CASE WHEN count(cost)=count(*) AND count(revenue)=count(*) THEN sum(revenue-cost) END db1,
       CASE WHEN count(cost)=count(*) AND count(revenue)=count(*) AND count(selling)=count(*) THEN sum(revenue-cost-selling) END db2
       FROM costing_spike.observation WHERE tenant=:tenant AND order_id=:id"""),
            {"tenant": tenant, "id": order_id},
        )
        .mappings()
        .one()
    )
    return dict(row) if row["count"] else None


def inventory_read(connection: Connection, tenant: str) -> dict:
    params = {"tenant": tenant}
    rows = (
        connection.execute(
            text(
                "SELECT * FROM costing_spike.inventory_observation WHERE tenant=:tenant ORDER BY item LIMIT 100"
            ),
            params,
        )
        .mappings()
        .all()
    )
    totals = (
        connection.execute(
            text("""SELECT sum(quantity) quantity,sum(unknown_quantity) unknown_quantity,
       CASE WHEN bool_and(cost IS NOT NULL) THEN sum(cost) END cost
       FROM costing_spike.inventory_observation WHERE tenant=:tenant"""),
            params,
        )
        .mappings()
        .one()
    )
    return {"rows": [dict(r) for r in rows], "totals": dict(totals)}


def monthly_read(connection: Connection, tenant: str, month: date) -> list[dict]:
    return [
        dict(r)
        for r in connection.execute(
            text("""SELECT item,CASE WHEN count(revenue)=count(*) THEN sum(revenue) END revenue,
       CASE WHEN count(cost)=count(*) AND count(revenue)=count(*) THEN sum(revenue-cost) END db1,
       CASE WHEN count(cost)=count(*) AND count(revenue)=count(*) AND count(selling)=count(*) THEN sum(revenue-cost-selling) END db2
       FROM costing_spike.observation WHERE tenant=:tenant AND economic_date>=:month
       AND economic_date<CAST(:month AS date)+INTERVAL '1 month' GROUP BY item ORDER BY item"""),
            {"tenant": tenant, "month": month},
        ).mappings()
    ]


def attention_read(connection: Connection, tenant: str) -> dict:
    params = {"tenant": tenant}
    counts = (
        connection.execute(
            text("""SELECT count(*) FILTER(WHERE cost IS NULL) missing_cost,
       count(*) FILTER(WHERE revenue IS NULL) missing_revenue,
       count(*) FILTER(WHERE cost IS NOT NULL AND revenue-cost<0) negative_db1,
       count(*) FILTER(WHERE selling IS NULL) missing_selling
       FROM costing_spike.observation WHERE tenant=:tenant"""),
            params,
        )
        .mappings()
        .one()
    )
    rows = (
        connection.execute(
            text("""SELECT issue_id,order_id,cost FROM costing_spike.observation
       WHERE tenant=:tenant AND (cost IS NULL OR revenue IS NULL OR selling IS NULL OR revenue-cost<0)
       ORDER BY issue_id LIMIT 100"""),
            params,
        )
        .mappings()
        .all()
    )
    return {"counts": dict(counts), "rows": [dict(r) for r in rows]}


def refresh_pool(connection: Connection, tenant: str, item: int) -> int:
    """Replay immutable input at a frozen revision; lock only for publication."""
    revision = connection.scalar(
        text(
            "SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant=:tenant"
        ),
        {"tenant": tenant},
    )
    rows, inventory = derive(connection, tenant, pool=item, knowledge_revision=revision)
    publish(connection, tenant, rows, inventory, pool=item, input_revision=revision)
    return len(rows)


def snapshot_read(
    connection: Connection, tenant: str, read, *, live: bool = False
) -> dict:
    """Caller uses one repeatable-read snapshot; stale values never claim live readiness."""
    row = (
        connection.execute(
            text("""SELECT c.generation,c.input_revision,
      (SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant=:tenant) latest
      FROM costing_spike.checkpoint c WHERE c.tenant=:tenant"""),
            {"tenant": tenant},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return {"state": "not_ready", "value": None}
    current = row["input_revision"] == row["latest"]
    return {
        "state": "current" if current else ("not_ready" if live else "stale"),
        "generation": row["generation"],
        "published_revision": row["input_revision"],
        "input_revision": row["latest"],
        "value": read() if current or not live else None,
    }


def live_order_read(
    connection: Connection,
    tenant: str,
    order_id: int,
    *,
    max_movements: int = 5000,
    max_parts: int = 20000,
) -> dict:
    """Read one order at the caller's repeatable-read snapshot, without publication.

    Scope dependencies are specific to immutable v3 inputs plus append-only adjustments.
    This is not a production source-version or arbitrary cross-pool return resolver.
    """
    absent = {"state": "not_ready", "value": None}
    scope = (
        connection.execute(
            text("""SELECT o.item,c.generation,c.input_revision,
      (SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant=:tenant) latest
      FROM costing_spike.trade_order o JOIN costing_spike.checkpoint c ON c.tenant=o.tenant
      WHERE o.tenant=:tenant AND o.id=:order_id"""),
            {"tenant": tenant, "order_id": order_id},
        )
        .mappings()
        .one_or_none()
    )
    if scope is None:
        return absent
    params = {
        "tenant": tenant,
        "order_id": order_id,
        "item": scope["item"],
        "end": order_id * 10,
        "published": scope["input_revision"],
        "latest": scope["latest"],
    }
    dirty = connection.scalar(
        text("""SELECT COALESCE(max(CASE WHEN a.id IS NULL OR (a.receipt_id IS NOT NULL AND m.id IS NULL) THEN 2 ELSE 1 END),0)
      FROM costing_spike.adjustment d
      LEFT JOIN costing_spike.attribution a ON a.tenant=d.tenant AND a.component_id=d.component_id
      LEFT JOIN costing_spike.movement m ON m.tenant=a.tenant AND m.id=a.receipt_id
      WHERE d.tenant=:tenant AND d.id>:published AND d.id<=:latest
      AND (a.id IS NULL OR (a.receipt_id IS NOT NULL AND m.id IS NULL)
           OR (m.item=:item AND m.sequence<=:end) OR a.order_id=:order_id)"""),
        params,
    )
    envelope = {
        "state": "current",
        "scope": "order",
        "generation": scope["generation"],
        "published_revision": scope["input_revision"],
        "input_revision": scope["latest"],
        "assessed_revision": scope["latest"],
    }
    if dirty == 2:
        return {
            **envelope,
            "state": "not_ready",
            "basis": "unresolved_dependency",
            "value": None,
        }
    if not dirty:
        return {
            **envelope,
            "basis": "projection",
            "value": order_read(connection, tenant, order_id),
        }
    if max_movements < 1 or max_parts < 1:
        raise ValueError("Positive replay bounds required.")
    params.update(movement_limit=max_movements + 1, part_limit=max_parts + 1)
    count = connection.scalar(
        text("""SELECT count(*) FROM (
      SELECT 1 FROM costing_spike.movement WHERE tenant=:tenant AND item=:item
      AND sequence<=:end LIMIT :movement_limit) bounded"""),
        params,
    )
    if count > max_movements:
        return {
            **envelope,
            "state": "not_ready",
            "basis": "bounded_refusal",
            "value": None,
        }
    parts = connection.scalar(
        text("""WITH selected AS MATERIALIZED (
      SELECT id,order_id FROM costing_spike.movement WHERE tenant=:tenant AND item=:item AND sequence<=:end
    ) SELECT count(*) FROM (
      SELECT 1 FROM costing_spike.attribution a WHERE a.tenant=:tenant AND
      (a.receipt_id IN (SELECT id FROM selected) OR a.order_id IN (SELECT order_id FROM selected))
      UNION ALL
      SELECT 1 FROM costing_spike.matching m WHERE m.tenant=:tenant AND m.issue_id IN (SELECT id FROM selected)
      UNION ALL
      SELECT 1 FROM costing_spike.adjustment WHERE tenant=:tenant AND id<=:latest
      LIMIT :part_limit) bounded"""),
        params,
    )
    if parts > max_parts:
        return {
            **envelope,
            "state": "not_ready",
            "basis": "bounded_refusal",
            "value": None,
        }
    rows, _ = derive(connection, tenant, order_id, knowledge_revision=scope["latest"])

    def complete(field):
        values = [getattr(r, field) for r in rows]
        return None if any(v is None for v in values) else sum(values, Decimal(0))

    cost, revenue, selling = complete("cost"), complete("revenue"), complete("selling")
    db1 = None if cost is None or revenue is None else revenue - cost
    value = {
        "count": len(rows),
        "cost": cost,
        "revenue": revenue,
        "db1": db1,
        "db2": None if db1 is None or selling is None else db1 - selling,
    }
    return {**envelope, "basis": "direct", "replayed_movements": count, "value": value}
