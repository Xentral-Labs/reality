"""Compile checked paths with tenant predicates and bound values.

Ordinary paths execute one SQL aggregate. Registered service paths first perform
one bounded canonical bulk derivation, then aggregate its ephemeral relation;
the returned statement count measures those reads instead of claiming one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
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
    case,
    cast,
    distinct,
    event,
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
from reality.domain.reporting_graph import Node, Property, ReportingGraph
from reality.services.analytics import derivations
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
        value = self.tables[alias].c[column]
        prop_def = node.properties.get(prop)
        if (
            isinstance(prop_def, Property)
            and prop_def.temporal == "date"
            and not isinstance(value.type, Date)
        ):
            return _calendar_date(value)
        return value


def _table(name: str) -> SaTable:
    table = Base.metadata.tables.get(name)
    if table is None:  # pragma: no cover - the declaration is validated at load
        raise TraversalRefused(f"table {name!r} is not mapped")
    return table


def _scope(
    node: Node, table, tenant_id: str, graph: ReportingGraph
) -> list[ColumnElement[bool]]:
    """The tenant predicate, plus whatever makes this table mean this node."""
    conditions = [table.c[node.tenant] == tenant_id]
    for column, selector in (node.where or {}).items():
        values = selector if isinstance(selector, list) else [selector]
        conditions.append(table.c[column].in_(values))
    if node.of:
        parent = graph.nodes[node.of]
        parent_table = _table(parent.table or "").alias()
        # The company is the scope, not the relationship. Since spec 181 FR-005 a
        # reference between two company-scoped tables carries the company as its
        # first column, so `tenant_id` also holds a foreign key to the parent —
        # counting it would make every ordinary parent look like two and refuse
        # the traversal. Both sides are held to the same company by `_scope`
        # below, so the composite is honoured without being counted.
        links = [
            column.name
            for column in _table(node.table or "").columns
            if column.name != node.tenant
            and any(
                key.column.table.name == parent.table for key in column.foreign_keys
            )
        ]
        if len(links) != 1:
            raise TraversalRefused(
                "a child node requires one unambiguous parent reference"
            )
        conditions.append(
            exists(
                select(1)
                .select_from(parent_table)
                .where(
                    table.c[links[0]] == parent_table.c[parent.key],
                    *_scope(parent, parent_table, tenant_id, graph),
                )
            )
        )
    return conditions


def _join_condition(hop: ResolvedHop, frame: Frame, origin: str) -> ColumnElement[bool]:
    if (
        hop.edge.via is None
    ):  # pragma: no cover - fact edges arrive with their own slice
        raise TraversalRefused(
            f"edge {hop.edge_name!r} is stored as Facts, which this slice does not traverse yet"
        )
    _, column = hop.edge.via.split(".", 1)
    origin_carries = (hop.edge.multiplicity == "n:1") == (hop.direction == "out")
    carrier_alias = origin if origin_carries else hop.alias
    other_alias = hop.alias if carrier_alias == origin else origin
    carrier = frame.tables[carrier_alias].c[column]
    other = frame.tables[other_alias].c[frame.nodes[other_alias].key]
    condition = carrier == other
    if hop.edge.target_where:
        target = frame.tables[hop.alias if hop.direction == "out" else origin]
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


def _calendar_date(column):
    """Validate ISO calendar evidence without ever casting an invalid date."""
    year = cast(func.substr(column, 1, 4), Integer)
    month = cast(func.substr(column, 6, 2), Integer)
    day = cast(func.substr(column, 9, 2), Integer)
    last_day = func.extract(
        "day", func.make_date(year, month, 1) + text("INTERVAL '1 month - 1 day'")
    )
    valid_day = case(
        (day.between(1, last_day), func.make_date(year, month, day)), else_=None
    )
    valid_parts = case(
        (and_(year.between(1, 9999), month.between(1, 12)), valid_day), else_=None
    )
    return cast(
        case(
            (column.op("~")(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"), valid_parts), else_=None
        ),
        Date,
    )


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
        if isinstance(kind, Date):
            return date.fromisoformat(value)
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
        _, column = (edge.via or "").split(".", 1)
        # The link column sits on one of the two tables; which one is what the
        # declared multiplicity and direction already settled.
        if (edge.multiplicity == "n:1") == (step.direction == "out"):
            conditions.append(carried.c[column] == table.c[target.key])
        else:
            conditions.append(table.c[column] == carried.c[at.key])
        if edge.target_where:
            for selector_name, selector in edge.target_where.items():
                values = selector if isinstance(selector, list) else [selector]
                selector_table = table if step.direction == "out" else carried
                conditions.append(selector_table.c[selector_name].in_(values))
        conditions += _scope(target, table, tenant_id, path.graph)
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
        value = row.c[source]
        if measure.sign_from:
            value = case(
                (row.c[measure.sign_from] == "debit", value),
                (row.c[measure.sign_from] == "credit", -value),
                else_=None,
            )
        return func.sum(value)
    if source.contribution:
        from reality.services.analytics.contribution_aggregates import (
            contribution_aggregate_columns,
        )

        return next(
            column
            for column in contribution_aggregate_columns(
                frame.tables[alias],
                reviewed=path.query.captured_cost_context is None,
            )
            if column.name == source.contribution
        )
    if source.distinct:
        return func.count(distinct(frame.tables[alias].c[source.distinct]))
    # Binding to the canonical service is the point of this measure: a receivable
    # balance covers opening items, several document types and reversal groups,
    # and a second derivation beside it would agree most of the time, which is
    # the more dangerous kind of wrong. Executing it here is separate work.
    raise TraversalRefused(
        f"measure {name!r} comes from {source.service!r}, which works out the "
        "number in one authoritative place. This page cannot run it yet, and "
        "deriving a second answer beside it would be worse than saying so.",
        "service_measure",
    )


def build(path: ResolvedPath, tenant_id: str, derived_relations=None) -> Select:
    def node_table(node, alias):
        table = _table(node.table or "")
        if node.derivation:
            from reality.services.analytics.derivations import REGISTRY

            source = (derived_relations or {}).get(node.derivation)
            if source is None:
                raise TraversalRefused(
                    "This position requires canonical service execution",
                    "service_measure",
                )
            if REGISTRY[node.derivation].canonical:
                return source.alias(alias)
            identity = REGISTRY[node.derivation].identity
            return (
                select(*table.c, *[col for col in source.c if col.name != identity])
                .select_from(
                    table.join(
                        source,
                        table.c[REGISTRY[node.derivation].anchor_key]
                        == source.c[identity],
                    )
                )
                .where(table.c.tenant_id == tenant_id)
                .subquery(alias)
            )
        return table.alias(alias)

    query = path.query
    frame = Frame(tables={}, nodes={}, conditions=[])

    root_alias = query.as_
    root_node = path.graph.nodes[path.node_of[root_alias]]
    root_table = node_table(root_node, root_alias)
    frame.tables[root_alias] = root_table
    frame.nodes[root_alias] = root_node
    frame.conditions += _scope(root_node, root_table, tenant_id, path.graph)

    statement = select().select_from(root_table)
    for hop in path.hops:
        node = path.graph.nodes[hop.node]
        table = node_table(node, hop.alias)
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
                    *_scope(node, table, tenant_id, path.graph),
                ),
            )
            continue
        statement = statement.join(
            table,
            and_(
                _join_condition(hop, frame, hop.origin),
                *_scope(node, table, tenant_id, path.graph),
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
            *_scope(node, table, tenant_id, path.graph),
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
            table = node_table(node, hop.alias)
            inner_tables[hop.alias] = table
            inner_nodes[hop.alias] = node
            inner = Frame(tables=inner_tables, nodes=inner_nodes, conditions=[])
            conditions.append(_join_condition(hop, inner, hop.origin))
            conditions += _scope(node, table, tenant_id, path.graph)
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


MAX_PUSHED_IDENTITIES = 20_000


def reachable_identities(
    session: Session, path: ResolvedPath, tenant_id: str, derivation: str
) -> set[str] | None:
    """Push a direct anchor filter into a canonical derivation when it is safe."""
    from reality.services.analytics.derivations import REGISTRY

    aliases = [
        alias
        for alias, name in path.node_of.items()
        if path.graph.nodes[name].derivation == derivation
    ]
    if len(aliases) != 1:
        return None
    alias = aliases[0]
    node = path.graph.nodes[path.node_of[alias]]
    table = _table(node.table or "")
    derived_columns = set(derivations.columns_for(derivation))
    conditions = []
    for condition in path.query.filter:
        field_alias, prop = condition.field.split(".", 1)
        if field_alias != alias or prop in derived_columns:
            continue
        column = node.column_of(prop) or (node.key if prop == node.key else "")
        if column and column in table.c:
            conditions.append(
                _condition(
                    Frame(
                        tables={alias: table}, nodes={alias: node}, conditions=[]
                    ),
                    condition.field,
                    condition.op,
                    condition.value,
                )
            )
    if not conditions:
        return None
    anchor_key = REGISTRY[derivation].anchor_key
    statement = (
        select(distinct(table.c[anchor_key]))
        .where(and_(*_scope(node, table, tenant_id, path.graph), *conditions))
        .limit(MAX_PUSHED_IDENTITIES + 1)
    )
    found = set(session.scalars(statement))
    return None if len(found) > MAX_PUSHED_IDENTITIES else found


def _plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)  # exact, and never a float on the way out
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _unknown_values(
    session: Session, tenant_id: str, path: ResolvedPath
) -> tuple[str, ...]:
    """Which equality filters name a value no record carries.

    Asked only when the answer is empty, because that is the only time the
    difference matters and the only time the extra look is worth taking. A model
    that filtered `type = "sale"` where the records say `customer_delivery` got
    nothing back and reported it as a fact about the business; this is what it
    needed to know instead.
    """
    unknown: list[str] = []
    for condition in path.query.filter:
        if condition.op != "eq" or not isinstance(condition.value, str):
            continue
        alias, prop = condition.field.split(".", 1)
        node = path.graph.nodes[path.node_of[alias]]
        table = _table(node.table or "")
        column = node.column_of(prop)
        if not column or column not in table.c:
            continue
        found = session.scalar(
            select(literal(1))
            .select_from(table)
            .where(
                and_(
                    table.c[column] == condition.value,
                    *_scope(node, table, tenant_id, path.graph),
                )
            )
            .limit(1)
        )
        if found is None:
            unknown.append(f"{condition.field} = {condition.value!r}")
    return tuple(unknown)


def execute(session: Session, tenant_id: str, path: ResolvedPath) -> TraversalResult:
    """Run a checked query and any canonical derivation under statement deadlines.

    The budget is set on the transaction rather than the connection, so it falls
    away with the query and never leaks into whatever the session does next.
    """
    budget_ms = int(path.graph.limits.statement_timeout_seconds) * 1000
    session.execute(text(f"SET LOCAL statement_timeout = {budget_ms:d}"))
    used = {path.graph.nodes[name].derivation for name in path.node_of.values()} | {
        path.graph.nodes[hop.node].derivation
        for test in path.exists
        for hop in test.hops
    }
    used.discard(None)
    derived = bool(used)
    reads = 0
    connection = session.connection()

    def count_read(conn, cursor, statement, parameters, context, executemany):
        nonlocal reads
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            reads += 1

    if derived:
        event.listen(connection, "before_cursor_execute", count_read)
    try:
        from reality.services.analytics.derivations import REGISTRY
        from reality.services.analytics.position_relations import snapshot_date

        snapshot = snapshot_date(path)
        cost_basis = None
        shared: dict[Any, Any] = {"moment": datetime.now(UTC)}
        relations = {
            name: REGISTRY[name].read(
                session,
                tenant_id,
                identities=reachable_identities(session, path, tenant_id, name),
                cache=shared,
                **({"snapshot": snapshot} if name.endswith(".history") else {}),
            )
            for name in sorted(used - {"costing.inventory", "costing.contribution"})
        }
        if "costing.inventory" in used:
            from reality.services.analytics.costing_relation import report_relation

            relations["costing.inventory"], cost_basis = report_relation(
                session,
                tenant_id,
                path.query.inventory_cost_context,
                path.query.captured_cost_context,
                path.query.company_cost_context,
            )
        if "costing.contribution" in used:
            from reality.services.analytics.contribution_relation import report_relation

            relations["costing.contribution"], cost_basis = report_relation(
                session,
                tenant_id,
                path.query.contribution_cost_context,
                path.query.captured_cost_context,
                path.query.company_cost_context,
            )
        statement = build(path, tenant_id, relations)
        rendered = str(statement.compile(compile_kwargs={"literal_binds": False}))
        rows = session.execute(statement).mappings().all()
        if (
            "costing.contribution" in used
            and path.query.contribution_cost_context is not None
        ):
            from reality.services.analytics.contribution_relation import (
                _finalize_report,
            )

            _finalize_report(
                session,
                tenant_id,
                cost_basis,
                path.query.contribution_cost_context.mode,
            )
        unknown = (
            _unknown_values(session, tenant_id, path)
            if not rows and cost_basis is None
            else ()
        )
    finally:
        if derived:
            event.remove(connection, "before_cursor_execute", count_read)
    return TraversalResult(
        cost_basis=cost_basis,
        matched_nothing=unknown,
        rows=tuple({key: _plain(value) for key, value in row.items()} for row in rows),
        sql=rendered,
        statements=reads if derived else 1,
        model_version=path.graph.model_version,
        path=tuple(
            f"{hop.origin}-[{hop.edge_name}]->{hop.alias}"
            + (" (exists)" if hop.as_exists else "")
            for hop in path.hops
        ),
    )
