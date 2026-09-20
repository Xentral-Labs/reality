"""Disposable staged generations; immutable fixture inputs, never business authority."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    Date,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    case,
    func,
    select,
    text,
)
from sqlalchemy.engine import Connection

from .costing_cases import derive

VERSION = "costing-generation-v1"


def initialize(connection: Connection) -> None:
    for statement in (
        """CREATE TABLE costing_spike.generation (
          tenant text REFERENCES costing_spike.tenant(id), id text, revision int NOT NULL,
          algorithm text NOT NULL, state text NOT NULL CHECK(state IN ('building','ready')),
          cursor int NOT NULL DEFAULT 0, range_count int NOT NULL, item_count int NOT NULL,
          observation_count int NOT NULL, PRIMARY KEY(tenant,id))""",
        """CREATE UNIQUE INDEX ON costing_spike.generation(tenant) WHERE state='building'""",
        """CREATE TABLE costing_spike.generation_range (
          tenant text, generation_id text, ordinal int, first_item int, last_item int,
          movements int CHECK(movements>0 AND movements<=50000),
          PRIMARY KEY(tenant,generation_id,ordinal),
          FOREIGN KEY(tenant,generation_id) REFERENCES costing_spike.generation(tenant,id))""",
        """CREATE TABLE costing_spike.generation_observation (
          tenant text, generation_id text, issue_id int, order_id int, item int,
          economic_date date, cost numeric(18,4), revenue numeric(18,4), selling numeric(18,4),
          PRIMARY KEY(tenant,generation_id,issue_id),
          FOREIGN KEY(tenant,generation_id) REFERENCES costing_spike.generation(tenant,id))""",
        """CREATE INDEX ON costing_spike.generation_observation(tenant,generation_id,order_id)""",
        """CREATE INDEX ON costing_spike.generation_observation(tenant,generation_id,economic_date,item)""",
        """CREATE TABLE costing_spike.generation_inventory (
          tenant text, generation_id text, item int, quantity numeric(18,4), cost numeric(18,4),
          unknown_quantity numeric(18,4), PRIMARY KEY(tenant,generation_id,item),
          FOREIGN KEY(tenant,generation_id) REFERENCES costing_spike.generation(tenant,id))""",
        """CREATE TABLE costing_spike.published_generation (
          tenant text PRIMARY KEY, generation_id text,
          FOREIGN KEY(tenant,generation_id) REFERENCES costing_spike.generation(tenant,id))""",
    ):
        connection.execute(text(statement))


def start_generation(
    connection: Connection,
    tenant: str,
    *,
    movement_budget: int = 50000,
    force: bool = False,
) -> str:
    if not 1 <= movement_budget <= 50000:
        raise ValueError("Invalid pool work budget.")
    params = {"tenant": tenant}
    if (
        connection.scalar(
            text("SELECT id FROM costing_spike.tenant WHERE id=:tenant FOR UPDATE"),
            params,
        )
        is None
    ):
        raise ValueError("Tenant not found.")
    existing = connection.scalar(
        text(
            "SELECT id FROM costing_spike.generation WHERE tenant=:tenant AND state='building'"
        ),
        params,
    )
    if existing:
        return existing
    revision = connection.scalar(
        text(
            "SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant=:tenant"
        ),
        params,
    )
    published = connection.execute(
        text("""SELECT g.id,g.revision FROM costing_spike.published_generation p
      JOIN costing_spike.generation g ON g.tenant=p.tenant AND g.id=p.generation_id
      WHERE p.tenant=:tenant"""),
        params,
    ).first()
    if published and published.revision == revision and not force:
        return published.id
    pools = connection.execute(
        text("""SELECT item,count(*) count,
      count(*) FILTER(WHERE kind IN ('issue','return')) observations
      FROM costing_spike.movement WHERE tenant=:tenant GROUP BY item ORDER BY item"""),
        params,
    ).all()
    ranges = []
    first = last = None
    count = 0
    for item, amount, _ in pools:
        if amount > movement_budget:
            raise ValueError("Indivisible pool exceeds bounded work budget.")
        if count and count + amount > movement_budget:
            ranges.append((first, last, count))
            first, count = None, 0
        first = item if first is None else first
        last, count = item, count + amount
    if count:
        ranges.append((first, last, count))
    if not ranges:
        raise ValueError("Empty generation scope.")
    identity = uuid4().hex
    params.update(
        id=identity,
        revision=revision,
        algorithm=VERSION,
        ranges=len(ranges),
        items=len(pools),
        observations=sum(p.observations for p in pools),
    )
    connection.execute(
        text("""INSERT INTO costing_spike.generation
      (tenant,id,revision,algorithm,state,range_count,item_count,observation_count)
      VALUES (:tenant,:id,:revision,:algorithm,'building',:ranges,:items,:observations)"""),
        params,
    )
    connection.execute(
        text("""INSERT INTO costing_spike.generation_range
      VALUES (:tenant,:id,:ordinal,:first,:last,:count)"""),
        [
            {
                "tenant": tenant,
                "id": identity,
                "ordinal": i,
                "first": r[0],
                "last": r[1],
                "count": r[2],
            }
            for i, r in enumerate(ranges)
        ],
    )
    return identity


def work_generation(
    connection: Connection,
    tenant: str,
    generation: str,
    *,
    max_ranges: int = 3,
    deadline: datetime | None = None,
) -> dict:
    if not 1 <= max_ranges <= 3:
        raise ValueError("Invalid child work budget.")
    params = {"tenant": tenant, "id": generation}
    row = (
        connection.execute(
            text(
                "SELECT * FROM costing_spike.generation WHERE tenant=:tenant AND id=:id FOR UPDATE"
            ),
            params,
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ValueError("Generation not found.")
    if row["algorithm"] != VERSION:
        raise ValueError("Unsupported generation version.")
    if row["state"] == "ready":
        return {"ranges": 0, "rows": 0, "movements": 0, "published": True}
    ranges = connection.execute(
        text("""SELECT ordinal,first_item,last_item,movements
      FROM costing_spike.generation_range WHERE tenant=:tenant AND generation_id=:id
      AND ordinal>=:cursor ORDER BY ordinal LIMIT :limit"""),
        {**params, "cursor": row["cursor"], "limit": max_ranges},
    ).all()
    completed = total_rows = movements = 0
    for ordinal, first, last, amount in ranges:
        if (
            completed
            and deadline
            and (deadline - datetime.now(UTC)).total_seconds() < 10
        ):
            break
        observations, inventory = derive(
            connection,
            tenant,
            pool_range=(first, last),
            knowledge_revision=row["revision"],
        )
        raw = connection.connection.driver_connection
        with (
            raw.cursor() as cursor,
            cursor.copy("COPY costing_spike.generation_observation FROM STDIN") as copy,
        ):
            for r in observations:
                copy.write_row(
                    (
                        tenant,
                        generation,
                        r.issue_id,
                        r.order_id,
                        r.item,
                        r.economic_date,
                        r.cost,
                        r.revenue,
                        r.selling,
                    )
                )
        with (
            raw.cursor() as cursor,
            cursor.copy("COPY costing_spike.generation_inventory FROM STDIN") as copy,
        ):
            for r in inventory:
                copy.write_row((tenant, generation, *r))
        completed += 1
        total_rows += len(observations)
        movements += amount
    next_cursor = row["cursor"] + completed
    ready = next_cursor == row["range_count"]
    if ready:
        counts = connection.execute(
            text("""SELECT
          (SELECT count(*) FROM costing_spike.generation_observation WHERE tenant=:tenant AND generation_id=:id),
          (SELECT count(*) FROM costing_spike.generation_inventory WHERE tenant=:tenant AND generation_id=:id)"""),
            params,
        ).one()
        if tuple(counts) != (row["observation_count"], row["item_count"]):
            raise ValueError("Incomplete staged generation.")
        connection.execute(
            text("SELECT id FROM costing_spike.tenant WHERE id=:tenant FOR UPDATE"),
            params,
        )
        connection.execute(
            text("""INSERT INTO costing_spike.published_generation VALUES (:tenant,:id)
          ON CONFLICT(tenant) DO UPDATE SET generation_id=excluded.generation_id"""),
            params,
        )
    connection.execute(
        text("""UPDATE costing_spike.generation SET cursor=:cursor,state=:state
      WHERE tenant=:tenant AND id=:id"""),
        {**params, "cursor": next_cursor, "state": "ready" if ready else "building"},
    )
    return {
        "ranges": completed,
        "rows": total_rows,
        "movements": movements,
        "published": ready,
    }


_METADATA = MetaData()
_OBSERVATION = Table(
    "generation_observation",
    _METADATA,
    Column("tenant", String),
    Column("generation_id", String),
    Column("issue_id", Integer),
    Column("order_id", Integer),
    Column("item", Integer),
    Column("economic_date", Date),
    Column("cost", Numeric(18, 4)),
    Column("revenue", Numeric(18, 4)),
    Column("selling", Numeric(18, 4)),
    schema="costing_spike",
)
_POINTER = Table(
    "published_generation",
    _METADATA,
    Column("tenant", String),
    Column("generation_id", String),
    schema="costing_spike",
)


def published_relation(tenant: str):
    """One indexed SQL relation at issue/return grain for tools and reporting proofs."""
    return (
        select(*_OBSERVATION.c)
        .join(
            _POINTER,
            (_POINTER.c.tenant == _OBSERVATION.c.tenant)
            & (_POINTER.c.generation_id == _OBSERVATION.c.generation_id),
        )
        .where(_OBSERVATION.c.tenant == tenant, _POINTER.c.tenant == tenant)
        .subquery()
    )


def _totals(relation):
    c = relation.c
    complete_cost = func.count(c.cost) == func.count()
    complete_revenue = func.count(c.revenue) == func.count()
    complete_selling = func.count(c.selling) == func.count()
    return [
        func.count().label("count"),
        case((complete_cost, func.sum(c.cost))).label("cost"),
        case((complete_revenue, func.sum(c.revenue))).label("revenue"),
        case((complete_cost & complete_revenue, func.sum(c.revenue - c.cost))).label(
            "db1"
        ),
        case(
            (
                complete_cost & complete_revenue & complete_selling,
                func.sum(c.revenue - c.cost - c.selling),
            )
        ).label("db2"),
    ]


def snapshot(connection: Connection, tenant: str, order: int) -> dict:
    """Caller uses REPEATABLE READ for metadata and value from one generation."""
    meta = (
        connection.execute(
            text("""SELECT g.id,g.revision,
      (SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant=:tenant) latest
      FROM costing_spike.published_generation p JOIN costing_spike.generation g
      ON g.tenant=p.tenant AND g.id=p.generation_id WHERE p.tenant=:tenant AND g.state='ready'"""),
            {"tenant": tenant},
        )
        .mappings()
        .one_or_none()
    )
    if meta is None:
        return {"state": "not_ready", "value": None}
    relation = published_relation(tenant)
    result = (
        connection.execute(
            select(*_totals(relation)).where(relation.c.order_id == order)
        )
        .mappings()
        .one()
    )
    return {
        "state": "ready" if meta["revision"] == meta["latest"] else "pending",
        "generation": meta["id"],
        "published_revision": meta["revision"],
        "input_revision": meta["latest"],
        "value": dict(result) if result["count"] else None,
    }


def report_month(connection: Connection, tenant: str, month):
    relation = published_relation(tenant)
    end = (
        month.replace(year=month.year + 1, month=1)
        if month.month == 12
        else month.replace(month=month.month + 1)
    )
    return [
        dict(r)
        for r in connection.execute(
            select(relation.c.item, *_totals(relation))
            .where(relation.c.economic_date >= month, relation.c.economic_date < end)
            .group_by(relation.c.item)
            .order_by(relation.c.item)
        ).mappings()
    ]
