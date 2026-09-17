"""Turn a checked path into exactly one PostgreSQL statement.

Two properties matter more than anything else here.

One statement. An eleven-thousand-query builder is what a per-row implementation
produces, and it is the failure mode this compiler could most easily reproduce,
so the count is asserted rather than assumed.

The tenant predicate on every node. It comes from the authenticated caller and is
emitted by this module, never written by whoever asked the question — which is why
the model needs no barrier view and no role per tenant. Every identifier below is
resolved through the declaration, and every value is bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import (
    DateTime,
    Integer,
    Numeric,
    Select,
    and_,
    distinct,
    exists,
    func,
    select,
)
from sqlalchemy import Table as SaTable
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from reality.db.core import Base
from reality.domain.reporting_graph import Node
from reality.services.analytics.traversal import (
    ResolvedHop,
    ResolvedPath,
    TraversalRefused,
    TraversalResult,
)

BUCKETS = {
    "day": ("day", "YYYY-MM-DD"),
    "week": ("week", 'IYYY-"W"IW'),
    "month": ("month", "YYYY-MM"),
    "quarter": ("quarter", 'YYYY-"Q"Q'),
    "year": ("year", "YYYY"),
}


@dataclass
class Frame:
    """The aliased tables a path reaches, and the conditions that scope them."""

    tables: dict[str, Any]
    nodes: dict[str, Node]
    conditions: list[ColumnElement[bool]]

    def column(self, alias: str, prop: str):
        node = self.nodes[alias]
        column = node.properties.get(prop, node.key if prop == node.key else None)
        if column is None:
            raise TraversalRefused(f"{alias}.{prop} is not a declared property")
        return self.tables[alias].c[column]


def _table(name: str) -> SaTable:
    table = Base.metadata.tables.get(name)
    if table is None:  # pragma: no cover - the declaration is validated at load
        raise TraversalRefused(f"table {name!r} is not mapped")
    return table


def _scope(node: Node, table, tenant_id: str) -> list[ColumnElement[bool]]:
    """The tenant predicate, plus whatever makes this table mean this node."""
    conditions = [table.c[node.tenant] == tenant_id]
    for column, selector in (node.where or {}).items():
        values = selector if isinstance(selector, list) else [selector]
        conditions.append(table.c[column].in_(values))
    return conditions


def _join_condition(hop: ResolvedHop, frame: Frame, origin: str) -> ColumnElement[bool]:
    if (
        hop.edge.via is None
    ):  # pragma: no cover - fact edges arrive with their own slice
        raise TraversalRefused(
            f"edge {hop.edge_name!r} is stored as Facts, which this slice does not traverse yet"
        )
    table_name, column = hop.edge.via.split(".", 1)
    carrier_alias = origin if frame.nodes[origin].table == table_name else hop.alias
    other_alias = hop.alias if carrier_alias == origin else origin
    carrier = frame.tables[carrier_alias].c[column]
    other = frame.tables[other_alias].c[frame.nodes[other_alias].key]
    condition = carrier == other
    if hop.edge.target_where:
        target = frame.tables[hop.alias]
        for name, selector in hop.edge.target_where.items():
            values = selector if isinstance(selector, list) else [selector]
            condition = and_(condition, target.c[name].in_(values))
    return condition


def _bucket(column, bucket: str):
    unit, pattern = BUCKETS[bucket]
    return func.to_char(func.date_trunc(unit, column), pattern)


def _coerce(column, value: Any, field: str) -> Any:
    """Bring a supplied value to the column's own type, or say why it cannot be.

    A period bound arrives as ISO text. Handing that straight to PostgreSQL asks
    it to compare a timestamp with a string, and the error it returns describes
    types rather than the question somebody asked.
    """
    if value is None or not isinstance(value, str):
        return value
    kind = column.type
    try:
        if isinstance(kind, DateTime):
            return datetime.fromisoformat(value)
        if isinstance(kind, Numeric):
            return Decimal(value)
        if isinstance(kind, Integer):
            return int(value)
    except (ValueError, InvalidOperation) as error:
        raise TraversalRefused(
            f"{field} expects a {kind.__class__.__name__.lower()}, and {value!r} is not one"
        ) from error
    return value


def _condition(frame: Frame, field: str, op: str, value: Any) -> ColumnElement[bool]:
    alias, prop = field.split(".", 1)
    column = frame.column(alias, prop)
    if op in ("in", "not_in"):
        value = [_coerce(column, item, field) for item in value]
    else:
        value = _coerce(column, value, field)
    if op == "eq":
        return column == value
    if op == "ne":
        return column != value
    if op == "in":
        return column.in_(list(value))
    if op == "not_in":
        return column.notin_(list(value))
    if op == "lt":
        return column < value
    if op == "lte":
        return column <= value
    if op == "gt":
        return column > value
    if op == "gte":
        return column >= value
    if op == "is_null":
        return column.is_(None)
    return column.is_not(None)


def _measure_expression(path: ResolvedPath, frame: Frame, name: str):
    measure = path.measures[name]
    alias = path.measure_alias[name]
    source = measure.source
    if isinstance(source, str):
        return func.sum(frame.tables[alias].c[source])
    if source.distinct:
        return func.count(distinct(frame.tables[alias].c[source.distinct]))
    raise TraversalRefused(
        f"measure {name!r} is produced by the canonical service {source.service!r}, "
        "which this slice does not execute yet"
    )


def build(path: ResolvedPath, tenant_id: str) -> Select:
    query = path.query
    frame = Frame(tables={}, nodes={}, conditions=[])

    root_alias = query.as_
    root_node = path.graph.nodes[path.node_of[root_alias]]
    root_table = _table(root_node.table or "").alias(root_alias)
    frame.tables[root_alias] = root_table
    frame.nodes[root_alias] = root_node
    frame.conditions += _scope(root_node, root_table, tenant_id)

    statement = select().select_from(root_table)
    for hop in path.hops:
        node = path.graph.nodes[hop.node]
        table = _table(node.table or "").alias(hop.alias)
        frame.tables[hop.alias] = table
        frame.nodes[hop.alias] = node
        if hop.as_exists:
            continue
        statement = statement.join(
            table,
            and_(
                _join_condition(hop, frame, hop.origin), *_scope(node, table, tenant_id)
            ),
            isouter=hop.edge.nullable and not hop.fans_out,
        )

    # Hops the answer never mentions filter through an existence test, so they
    # narrow the result without multiplying it.
    for hop in path.hops:
        if not hop.as_exists:
            continue
        node = frame.nodes[hop.alias]
        table = frame.tables[hop.alias]
        inner = [
            _join_condition(hop, frame, hop.origin),
            *_scope(node, table, tenant_id),
        ]
        inner += [
            _condition(frame, c.field, c.op, c.value)
            for c in query.filter
            if c.field.split(".")[0] == hop.alias
        ]
        frame.conditions.append(
            exists(select(1).select_from(table).where(and_(*inner)))
        )

    narrowed = {hop.alias for hop in path.hops if hop.as_exists}
    frame.conditions += [
        _condition(frame, c.field, c.op, c.value)
        for c in query.filter
        if c.field.split(".")[0] not in narrowed
    ]

    labels: list[Any] = []
    group_keys: list[Any] = []
    for grouping in query.group_by:
        alias, prop = grouping.field.split(".", 1)
        column = frame.column(alias, prop)
        expression = _bucket(column, grouping.bucket) if grouping.bucket else column
        name = grouping.as_ or grouping.field
        labels.append(expression.label(name))
        group_keys.append(expression)

    for name in query.measures:
        labels.append(_measure_expression(path, frame, name).label(name))

    statement = statement.with_only_columns(*labels).where(and_(*frame.conditions))
    if group_keys:
        statement = statement.group_by(*group_keys)
    for ordering in query.order_by:
        column = next((label for label in labels if label.name == ordering.by), None)
        if column is None:
            raise TraversalRefused(f"nothing in the answer is called {ordering.by!r}")
        statement = statement.order_by(column.desc() if ordering.descending else column)
    return statement.limit(min(query.limit, path.graph.limits.result_rows))


def _plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)  # exact, and never a float on the way out
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def execute(session: Session, tenant_id: str, path: ResolvedPath) -> TraversalResult:
    statement = build(path, tenant_id)
    rendered = str(statement.compile(compile_kwargs={"literal_binds": False}))
    rows = session.execute(statement).mappings().all()
    return TraversalResult(
        rows=tuple({key: _plain(value) for key, value in row.items()} for row in rows),
        sql=rendered,
        statements=1,
        model_version=path.graph.model_version,
        path=tuple(
            f"{hop.origin}-[{hop.edge_name}]->{hop.alias}"
            + (" (exists)" if hop.as_exists else "")
            for hop in path.hops
        ),
    )
