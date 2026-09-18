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
    Date,
    DateTime,
    Integer,
    Numeric,
    Select,
    all_,
    and_,
    distinct,
    exists,
    func,
    literal,
    select,
    text,
)
from sqlalchemy import Table as SaTable
from sqlalchemy.dialects.postgresql import array
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
        column = node.column_of(prop) or (node.key if prop == node.key else "")
        if not column:
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


def _closure(hop: ResolvedHop, node: Node, tenant_id: str):
    """Walk a recursive edge to a bounded depth, once, for the whole tenant.

    The anchor and the recursive term both carry the tenant predicate. Forgetting
    it in the recursive term is the classic way a closure leaks, and it is why
    this is written here rather than left to whoever asks the question.

    A visited list terminates a cycle. Real data is not supposed to contain one,
    and a run that meets one has found a defect to report rather than a reason to
    exhaust the connection.

    The carrying column travels with each row so the walk works in both
    directions: downwards a child names its parent, upwards a row's own carrier
    names the parent to step onto next.
    """
    table_name, column = (hop.edge.via or "").split(".", 1)
    table = _table(table_name)
    key = node.key
    low, high = hop.depth or (1, 1)

    anchor = (
        select(
            table.c[key].label("ancestor"),
            table.c[key].label("descendant"),
            table.c[column].label("carrier"),
            literal(0).label("depth"),
            array([table.c[key]]).label("visited"),
        )
        .where(table.c[node.tenant] == tenant_id)
        .cte(name=f"{hop.alias}_closure", recursive=True)
    )
    step = table.alias(f"{hop.alias}_step")
    stepping = (
        step.c[column] == anchor.c.descendant
        if hop.direction == "in"
        else step.c[key] == anchor.c.carrier
    )
    recursive_term = select(
        anchor.c.ancestor,
        step.c[key],
        step.c[column],
        anchor.c.depth + 1,
        anchor.c.visited.op("||")(step.c[key]),
    ).where(
        and_(
            stepping,
            step.c[node.tenant] == tenant_id,
            anchor.c.depth < high,
            step.c[key] != all_(anchor.c.visited),
        )
    )
    return anchor.union_all(recursive_term), low, high


def _bucket(column, bucket: str, field: str):
    """Fold a timestamp into the period somebody asked for.

    Only a column that actually holds a time can be folded. A date kept as text
    reaches PostgreSQL as `date_trunc(varchar, varchar)`, whose error names two
    types and no question, so the refusal is made here instead.
    """
    if not isinstance(column.type, (DateTime, Date)):
        raise TraversalRefused(
            f"{field} is not kept as a date, so it cannot be grouped by {bucket}",
            code="not_temporal",
        )
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


def _compare(expression, op: str, value: Any) -> ColumnElement[bool]:
    return {
        "eq": expression == value,
        "ne": expression != value,
        "lt": expression < value,
        "lte": expression <= value,
        "gt": expression > value,
        "gte": expression >= value,
    }[op]


def _deducted(path: ResolvedPath, name: str, row, tenant_id: str):
    """What is still open on this row: the base value, less what was counted
    against it along a declared path.

    It is a correlated subquery and not a join, and that is the whole point. A
    join to the far side would repeat this row once per movement and multiply
    the promise it is supposed to be reducing — the exact mistake the graph
    exists to prevent, arriving through the back door of a difference.

    The subquery carries the tenant predicate on every table it touches, for
    the same reason the outer statement does.
    """
    measure = path.measures[name]
    less = measure.less
    assert less is not None  # only called for a measure that declares one
    far = path.graph.measures[less.measure]

    at = path.graph.nodes[measure.node]
    carried = row
    conditions: list[ColumnElement[bool]] = []
    tables: list[Any] = []
    for depth, step in enumerate(less.over):
        edge = path.graph.edges[step.edge]
        target_name = edge.to if step.direction == "out" else edge.from_
        target = path.graph.nodes[target_name]
        table = _table(target.table or "").alias(f"__less{depth}__{name}")
        tables.append(table)
        via_table, column = (edge.via or "").split(".", 1)
        # The link column sits on one of the two tables; which one is what the
        # declared multiplicity and direction already settled.
        if at.table == via_table:
            conditions.append(carried.c[column] == table.c[target.key])
        else:
            conditions.append(table.c[column] == carried.c[at.key])
        if edge.target_where:
            for selector_name, selector in edge.target_where.items():
                values = selector if isinstance(selector, list) else [selector]
                conditions.append(table.c[selector_name].in_(values))
        conditions += _scope(target, table, tenant_id)
        at, carried = target, table

    counted = (
        func.count(distinct(carried.c[far.source.distinct]))
        if not isinstance(far.source, str)
        else func.sum(carried.c[far.source])
    )
    statement = select(counted).where(and_(*conditions))
    for table in tables[:-1]:
        statement = statement.select_from(table)
    # A promise nothing has moved against is open in full, not unknown.
    return func.coalesce(statement.scalar_subquery(), 0)


def _measure_expression(path: ResolvedPath, frame: Frame, name: str, tenant_id: str):
    measure = path.measures[name]
    alias = path.measure_alias[name]
    source = measure.source
    if isinstance(source, str):
        row = frame.tables[alias]
        if measure.less is not None:
            return func.sum(row.c[source] - _deducted(path, name, row, tenant_id))
        return func.sum(row.c[source])
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
        if hop.depth:
            closure, low, high = _closure(hop, node, tenant_id)
            origin_key = frame.tables[hop.origin].c[frame.nodes[hop.origin].key]
            statement = statement.join(
                closure,
                and_(
                    closure.c.ancestor == origin_key,
                    closure.c.depth >= low,
                    closure.c.depth <= high,
                ),
            ).join(
                table,
                and_(
                    table.c[node.key] == closure.c.descendant,
                    *_scope(node, table, tenant_id),
                ),
            )
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

    # An existence test narrows without joining, so it cannot multiply a total.
    # Joining the same sub-path would, which is the whole reason it is a clause.
    for test in path.exists:
        inner_tables: dict[str, Any] = {test.origin: frame.tables[test.origin]}
        inner_nodes: dict[str, Node] = {test.origin: frame.nodes[test.origin]}
        conditions: list[ColumnElement[bool]] = []
        for hop in test.hops:
            node = path.graph.nodes[hop.node]
            table = _table(node.table or "").alias(hop.alias)
            inner_tables[hop.alias] = table
            inner_nodes[hop.alias] = node
            inner = Frame(tables=inner_tables, nodes=inner_nodes, conditions=[])
            conditions.append(_join_condition(hop, inner, hop.origin))
            conditions += _scope(node, table, tenant_id)
        inner = Frame(tables=inner_tables, nodes=inner_nodes, conditions=[])
        for condition in test.conditions:
            conditions.append(
                _condition(inner, condition.field, condition.op, condition.value)
            )
        subquery = exists(
            select(1)
            .select_from(inner_tables[test.hops[0].alias])
            .where(and_(*conditions))
        )
        frame.conditions.append(~subquery if test.negated else subquery)

    labels: list[Any] = []
    group_keys: list[Any] = []
    for grouping in query.group_by:
        alias, prop = grouping.field.split(".", 1)
        column = frame.column(alias, prop)
        expression = column
        if grouping.bucket:
            expression = _bucket(column, grouping.bucket, grouping.field)
        name = grouping.as_ or grouping.field
        labels.append(expression.label(name))
        group_keys.append(expression)

    for name in query.measures:
        labels.append(_measure_expression(path, frame, name, tenant_id).label(name))

    statement = statement.with_only_columns(*labels).where(and_(*frame.conditions))
    if group_keys:
        statement = statement.group_by(*group_keys)
    for condition in query.having:
        measured = next(
            label
            for label in labels
            if getattr(label, "name", None) == condition.measure
        )
        statement = statement.having(_compare(measured, condition.op, condition.value))
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
    """Run the one statement under a deadline the caller cannot raise.

    The budget is set on the transaction rather than the connection, so it falls
    away with the query and never leaks into whatever the session does next.
    """
    statement = build(path, tenant_id)
    rendered = str(statement.compile(compile_kwargs={"literal_binds": False}))
    # SET takes no bind parameter. The value is an integer field of the validated
    # declaration, never anything a caller supplied, and it is coerced again here
    # so this line cannot become an injection point if that ever changes.
    budget_ms = int(path.graph.limits.statement_timeout_seconds) * 1000
    session.execute(text(f"SET LOCAL statement_timeout = {budget_ms:d}"))
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
