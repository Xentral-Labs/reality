"""Where the bytes are, and whether the schema would let them be split up.

Spec 181 FR-005 asks for three things: operational tables that can be partitioned
by tenant and time, source payloads that can move to a tiered store behind the
reference the record already carries, and queries that resolve their cluster from
the tenant scope. None of the three can be argued about without knowing where the
bytes actually sit, and the first cannot even be attempted while a key forbids it.

So this records two things at every checkpoint, and they answer different questions.

**Size** says what is expensive to keep. It separates the heap from the indexes and
from the out-of-line payload storage, because the three grow for different reasons
and only one of them is the data somebody entered. A table whose indexes outweigh
its rows is not a storage problem to be tiered, it is an indexing decision.

**Readiness** says what the schema permits. PostgreSQL requires every unique
constraint of a partitioned table — the primary key included — to contain the
partition key. A table whose primary key is `id` alone therefore cannot be
partitioned by tenant at all, however large it grows, and no measurement of its
size changes that. This names the constraints that stand in the way, so the work
FR-005 implies is a list rather than a guess.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from .report import StorageShape, TableBlocker, TableSize

#: Below this a table is noise: the measurement is about where a company's bytes
#: go as it grows, and a fixed 8 kB catalog table never answers that.
FLOOR_BYTES = 128 * 1024

#: The column that scopes a row to a company. A table without it is not a
#: candidate for tenant partitioning in the first place — it is shared.
TENANT_COLUMN = "tenant_id"

_SIZES = text("""
    SELECT c.relname AS table_name,
           GREATEST(c.reltuples, 0)::bigint AS estimated_rows,
           pg_relation_size(c.oid) AS heap_bytes,
           pg_indexes_size(c.oid) AS index_bytes,
           pg_total_relation_size(c.oid)
             - pg_relation_size(c.oid)
             - pg_indexes_size(c.oid) AS out_of_line_bytes
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relkind = 'r'
       AND pg_total_relation_size(c.oid) >= :floor
     ORDER BY pg_total_relation_size(c.oid) DESC
""")

#: Every uniqueness promise a table makes, with the columns it makes it over.
#: Both the primary key and the unique constraints count: PostgreSQL treats them
#: alike when it refuses to partition.
_KEYS = text("""
    SELECT c.relname AS table_name,
           con.conname AS constraint_name,
           con.contype AS kind,
           EXISTS (
             SELECT 1 FROM pg_attribute a
              WHERE a.attrelid = c.oid
                AND a.attname = :tenant_column
                AND NOT a.attisdropped
                AND a.attnum > 0
           ) AS has_tenant_column,
           (SELECT bool_or(a.attname = :tenant_column)
              FROM unnest(con.conkey) k(attnum)
              JOIN pg_attribute a
                ON a.attrelid = con.conrelid AND a.attnum = k.attnum
           ) AS covers_tenant
      FROM pg_constraint con
      JOIN pg_class c ON c.oid = con.conrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND con.contype IN ('p', 'u')
     ORDER BY c.relname, con.conname
""")


def _sizes(session: Session) -> list[TableSize]:
    """Every table big enough to matter, largest first.

    The row count is PostgreSQL's own estimate rather than a count. The runner
    analyzes before it samples, so the estimate is fresh, and counting forty
    tables exactly at a hundred thousand orders would cost more than the
    measurement it belongs to.
    """
    rows = session.execute(_SIZES, {"floor": FLOOR_BYTES}).mappings().all()
    return [TableSize.model_validate(dict(row)) for row in rows]


def _blockers(session: Session) -> list[TableBlocker]:
    """The constraints that forbid partitioning a tenant-scoped table by tenant.

    A table that carries no tenant column is left out rather than reported as
    blocked: it is shared by every company, so tenant partitioning is not a thing
    that was refused, it is a thing that was never asked for.
    """
    blocked: dict[str, list[str]] = {}
    for row in session.execute(_KEYS, {"tenant_column": TENANT_COLUMN}).mappings():
        if row["has_tenant_column"] and not row["covers_tenant"]:
            blocked.setdefault(row["table_name"], []).append(row["constraint_name"])
    return [
        TableBlocker(table_name=table, constraints=sorted(constraints))
        for table, constraints in sorted(blocked.items())
    ]


def storage_shape(session: Session, *, orders: int) -> StorageShape:
    """What this company costs to keep, and what its keys would allow.

    `orders` divides the total, because the figure FR-005 is about is not how
    large the database is — that is a property of the fixture's size — but how
    much one order to cash leaves behind.
    """
    tables = _sizes(session)
    return StorageShape(
        orders=orders,
        tables=tables,
        blocked_from_tenant_partitioning=_blockers(session),
    )
