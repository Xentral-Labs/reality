"""Decide what a path means before it is allowed to become a query.

Three decisions happen here, and each one prevents a number that would otherwise
be shipped with confidence:

    fan-out      a 1:n hop multiplies everything before it. A measure summed
                 along one is wrong by the number of rows the hop reached. Where
                 the fanned-out node is never referred to by the result, the hop
                 is narrowed to an existence test and the multiplication never
                 happens; where it is referred to, the question is unanswerable
                 and is refused, naming the edge and offering the measure that
                 lives at the grain the path reached.

    units        two currencies do not add up, and neither do pieces and
                 kilograms. A measure that carries a unit may only be aggregated
                 when that unit is one of the result's axes.

    additivity   a balance is a state, not a flow. Splitting one by month is not
                 a smaller version of a correct answer, it is a meaningless one.

Everything else about a question stays free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from reality.domain.reporting_graph import Edge, Measure, ReportingGraph
from reality.domain.traversal import Traversal
from reality.services.analytics.graph_model import reporting_graph
from reality.services.core import InvalidOperation


class TraversalRefused(InvalidOperation):
    """The question cannot be answered correctly, and why.

    A refusal carries a stable code beside its sentence, so a caller can branch on
    the kind of problem while a person reads the reason. It is an InvalidOperation
    because that is what it is: the question was understood and cannot be answered,
    which is different from the service being unavailable.
    """

    def __init__(self, message: str, code: str = "refused"):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ResolvedHop:
    alias: str
    origin: str
    edge_name: str
    edge: Edge
    node: str
    direction: str
    fans_out: bool
    depth: tuple[int, int] | None = None
    as_exists: bool = False


@dataclass(frozen=True)
class ResolvedExistence:
    """A sub-path proven to exist, never joined into the answer."""

    origin: str
    hops: tuple[ResolvedHop, ...]
    node_of: dict[str, str]
    negated: bool
    conditions: tuple[Any, ...] = ()


@dataclass(frozen=True)
class ResolvedPath:
    graph: ReportingGraph
    query: Traversal
    node_of: dict[str, str]
    hops: tuple[ResolvedHop, ...]
    measures: dict[str, Measure]
    measure_alias: dict[str, str]
    exists: tuple[ResolvedExistence, ...] = ()


@dataclass(frozen=True)
class TraversalResult:
    rows: tuple[dict[str, Any], ...]
    sql: str
    statements: int
    model_version: str
    path: tuple[str, ...]
    #: Equality filters whose value appears on no record at all. An empty answer
    #: means one of two very different things — nothing matched, or the question
    #: named something that does not exist — and only the second is the asker's
    #: mistake. Saying which is the difference between "there is no open
    #: delivery" and "there is no such status".
    matched_nothing: tuple[str, ...] = ()
    cost_basis: dict[str, Any] | None = None


def _fans_out(edge: Edge, direction: str, recursive: bool = False) -> bool:
    """Following `contains` forwards reaches many lines; `ordered_by` backwards
    reaches many orders. Both multiply whatever came before them.

    A variable-depth hop always reaches many rows, whichever way it is walked,
    so it fans out regardless of the edge's own multiplicity.
    """
    if recursive:
        return True
    return (edge.multiplicity == "1:n") == (direction == "out")


def resolve(graph: ReportingGraph, query: Traversal) -> ResolvedPath:
    if query.from_ not in graph.nodes:
        raise TraversalRefused(
            f"there is no node called {query.from_!r} in the model", "unknown_node"
        )
    node_of = {query.as_: query.from_}
    hops: list[ResolvedHop] = []
    previous = query.as_
    for hop in query.follow:
        origin = hop.from_ or previous
        edge = graph.edges.get(hop.edge)
        if edge is None:
            raise TraversalRefused(
                f"there is no edge called {hop.edge!r} in the model. Declare it with "
                "its multiplicity and it works everywhere.",
                "unknown_edge",
            )
        source, target = (
            (edge.from_, edge.to) if hop.direction == "out" else (edge.to, edge.from_)
        )
        if node_of[origin] != source:
            raise TraversalRefused(
                f"edge {hop.edge!r} runs from {source!r}, but the path is at "
                f"{node_of[origin]!r}. Follow it the other way round, or take another edge.",
                "edge_direction",
            )
        if hop.depth and not edge.recursive:
            raise TraversalRefused(
                f"edge {hop.edge!r} is not declared recursive, so it cannot be "
                "walked to a variable depth",
                "not_recursive",
            )
        if edge.recursive and not hop.depth:
            raise TraversalRefused(
                f"edge {hop.edge!r} is recursive, so a hop along it names the depth "
                f"it walks, at most {edge.recursive.max_depth}",
                "depth_required",
            )
        if hop.depth and edge.recursive and hop.depth[1] > edge.recursive.max_depth:
            raise TraversalRefused(
                f"edge {hop.edge!r} is declared to a depth of "
                f"{edge.recursive.max_depth}; {hop.depth[1]} is beyond it",
                "depth_exceeded",
            )
        hops.append(
            ResolvedHop(
                alias=hop.as_,
                origin=origin,
                edge_name=hop.edge,
                edge=edge,
                node=target,
                direction=hop.direction,
                fans_out=_fans_out(edge, hop.direction, bool(hop.depth)),
                depth=hop.depth,
            )
        )
        node_of[hop.as_] = target
        previous = hop.as_

    measures: dict[str, Measure] = {}
    measure_alias: dict[str, str] = {}
    for name in query.measures:
        measure = graph.measures.get(name)
        if measure is None:
            raise TraversalRefused(
                f"there is no measure called {name!r} in the model", "unknown_measure"
            )
        owners = [alias for alias, node in node_of.items() if node == measure.node]
        if not owners:
            raise TraversalRefused(
                f"measure {name!r} lives on {measure.node!r}, which this path never "
                "reaches. Follow an edge to it first.",
                "measure_unreachable",
            )
        measures[name] = measure
        measure_alias[name] = owners[0]
    tests: list[ResolvedExistence] = []
    for index, test in enumerate(query.exists):
        origin = test.follow[0].from_ or query.as_
        if origin not in node_of:
            raise TraversalRefused(
                f"an existence test starts at {origin!r}, which the path never reaches",
                "unknown_node",
            )
        inner: dict[str, str] = {origin: node_of[origin]}
        inner_hops: list[ResolvedHop] = []
        previous = origin
        for hop in test.follow:
            at = hop.from_ or previous
            edge = graph.edges.get(hop.edge)
            if edge is None:
                raise TraversalRefused(
                    f"there is no edge called {hop.edge!r} in the model", "unknown_edge"
                )
            source, target = (
                (edge.from_, edge.to)
                if hop.direction == "out"
                else (edge.to, edge.from_)
            )
            if inner.get(at) != source:
                raise TraversalRefused(
                    f"edge {hop.edge!r} runs from {source!r}, but the test is at "
                    f"{inner.get(at)!r}",
                    "edge_direction",
                )
            alias = f"e{index}_{hop.as_}"
            inner_hops.append(
                ResolvedHop(
                    alias=alias,
                    origin=at if at == origin else f"e{index}_{at}",
                    edge_name=hop.edge,
                    edge=edge,
                    node=target,
                    direction=hop.direction,
                    fans_out=_fans_out(edge, hop.direction, bool(hop.depth)),
                    depth=hop.depth,
                )
            )
            inner[alias] = target
            inner[hop.as_] = target
            previous = hop.as_
        for condition in test.filter:
            alias = condition.field.split(".")[0]
            if alias not in inner:
                raise TraversalRefused(
                    f"the existence test has no {alias!r} to filter on", "unknown_node"
                )
        tests.append(
            ResolvedExistence(
                origin,
                tuple(inner_hops),
                inner,
                test.negated,
                tuple(
                    condition.model_copy(
                        update={
                            "field": f"e{index}_{condition.field.split('.')[0]}"
                            f".{condition.field.split('.')[1]}"
                        }
                    )
                    for condition in test.filter
                ),
            )
        )

    return ResolvedPath(
        graph, query, node_of, tuple(hops), measures, measure_alias, tuple(tests)
    )


def _referenced(path: ResolvedPath) -> set[str]:
    """Aliases the answer actually mentions: a grouping key or a measure's home."""
    used = {grouping.field.split(".")[0] for grouping in path.query.group_by}
    used |= set(path.measure_alias.values())
    used |= {
        ordering.by.split(".")[0]
        for ordering in path.query.order_by
        if "." in ordering.by
    }
    return used


def narrow_unreferenced_hops(path: ResolvedPath) -> ResolvedPath:
    """Turn the trailing hops the answer never mentions into an existence test.

    A hop that only filters does not need to be joined, and joining it is exactly
    what multiplies the total. This is the same rewrite a careful person makes by
    hand and routinely forgets.
    """
    used = _referenced(path)
    hops = list(path.hops)
    cut = len(hops)
    while cut > 0 and hops[cut - 1].alias not in used and not hops[cut - 1].depth:
        cut -= 1
    if cut == len(hops):
        return path
    narrowed = [
        hop if index < cut else ResolvedHop(**{**hop.__dict__, "as_exists": True})
        for index, hop in enumerate(hops)
    ]
    return ResolvedPath(
        path.graph,
        path.query,
        path.node_of,
        tuple(narrowed),
        path.measures,
        path.measure_alias,
    )


def check_fan_out(path: ResolvedPath) -> None:
    joined = [hop for hop in path.hops if not hop.as_exists]
    order = [path.query.as_, *(hop.alias for hop in joined)]
    for name, measure in path.measures.items():
        if not isinstance(measure.source, str):
            continue  # a distinct count is immune, and a service measure is not a column
        home = path.measure_alias[name]
        after = joined[order.index(home) :]
        fanning = [hop for hop in after if hop.fans_out]
        if not fanning:
            continue
        edge = fanning[0]
        reached = path.node_of[edge.alias]
        alternatives = [
            key
            for key, other in path.graph.measures.items()
            if other.node == reached and isinstance(other.source, str)
        ]
        offer = (
            f" Use {alternatives[0]!r}, which lives at that grain."
            if alternatives
            else " No measure is declared at that grain."
        )
        raise TraversalRefused(
            f"measure {name!r} is counted once per {measure.node!r}, but the edge "
            f"{edge.edge_name!r} reaches many {reached!r} rows for each one, so "
            f"summing it here would multiply the total.{offer}",
            "fan_out",
        )


def _pinned(path: ResolvedPath) -> set[str]:
    """Fields the question has narrowed to exactly one value.

    A sum across two currencies is meaningless, but a sum inside one is not, and
    a question filtered to `currency = "EUR"` has already done that. The refusal
    told the reader to "filter the question down to one" while the check looked
    only at the axes — so following its own advice changed nothing.
    """
    return {
        condition.field
        for condition in path.query.filter
        if condition.op == "eq"
        or (
            condition.op == "in"
            and isinstance(condition.value, (list, tuple))
            and len(condition.value) == 1
        )
    }


def check_units(path: ResolvedPath) -> None:
    grouped = {
        grouping.field for grouping in path.query.group_by if grouping.bucket is None
    } | _pinned(path)
    for name, measure in path.measures.items():
        unit = measure.unit
        if unit.kind == "count" or not unit.column:
            continue
        home = path.measure_alias[name]
        if unit.from_node:
            owners = [
                alias for alias, node in path.node_of.items() if node == unit.from_node
            ]
            if not owners:
                raise TraversalRefused(
                    f"measure {name!r} is measured in the unit of {unit.from_node!r}, "
                    "which this path never reaches",
                    "unit_unreachable",
                )
            home = owners[0]
        field = f"{home}.{unit.column}"
        if field not in grouped:
            axis = ", ".join(measure.never_across) or unit.column
            raise TraversalRefused(
                f"measure {name!r} may not be summed across {axis}. Group by "
                f"{field!r}, or filter the question down to one.",
                "unit_mismatch",
            )


def check_additivity(path: ResolvedPath) -> None:
    has_time_axis = any(grouping.bucket for grouping in path.query.group_by)
    for name, measure in path.measures.items():
        if has_time_axis and "time" in measure.never_across:
            raise TraversalRefused(
                f"measure {name!r} is a state, not a flow, so it is not additive "
                "over time. Ask for it as it stands, without a time axis.",
                "not_additive",
            )


def check_properties(path: ResolvedPath) -> None:
    def known(alias: str) -> set[str]:
        node = path.graph.nodes[path.node_of[alias]]
        return set(node.properties) | {node.key}

    fields = [c.field for c in path.query.filter] + [
        g.field for g in path.query.group_by
    ]
    for field in fields:
        alias, prop = field.split(".", 1)
        if prop not in known(alias):
            available = ", ".join(sorted(known(alias))[:8])
            raise TraversalRefused(
                f"{path.node_of[alias]!r} has no property called {prop!r}. "
                f"It has: {available}.",
                "unknown_property",
            )


def check_having(path: ResolvedPath) -> None:
    """A filter on an aggregate may only name a number the question asked for."""
    for condition in path.query.having:
        if condition.measure not in path.measures:
            raise TraversalRefused(
                f"there is no measure called {condition.measure!r} in this question",
                "unknown_measure",
            )


def plan(query: Traversal, graph: ReportingGraph | None = None) -> ResolvedPath:
    """Resolve and check a question. Nothing touches the database until this passes."""
    graph = graph or reporting_graph()
    if len(query.follow) > graph.limits.max_path_length:
        raise TraversalRefused(
            f"a path may take at most {graph.limits.max_path_length} steps",
            "path_too_long",
        )
    costing = graph.nodes.get(query.from_)
    is_inventory = costing is not None and costing.derivation == "costing.inventory"
    if is_inventory and not (
        query.inventory_cost_context
        or query.captured_cost_context
        or query.company_cost_context
    ):
        raise TraversalRefused(
            "An inventory cost context is required", "cost_context_required"
        )
    if query.inventory_cost_context is not None and (
        not is_inventory
        or query.follow
        or query.exists
        or query.captured_cost_context is not None
        or query.company_cost_context is not None
    ):
        raise TraversalRefused(
            "Inventory cost context requires a standalone inventory question",
            "cost_context_invalid",
        )
    if is_inventory and any(group.bucket for group in query.group_by):
        raise TraversalRefused(
            "A confirmed inventory state cannot be bucketed across time", "not_additive"
        )
    is_contribution = (
        costing is not None and costing.derivation == "costing.contribution"
    )
    if is_contribution and not (
        query.contribution_cost_context
        or query.captured_cost_context
        or query.company_cost_context
    ):
        raise TraversalRefused(
            "A contribution cost context is required", "cost_context_required"
        )
    if query.contribution_cost_context is not None and (
        not is_contribution
        or query.follow
        or query.exists
        or query.inventory_cost_context is not None
        or query.captured_cost_context is not None
        or query.company_cost_context is not None
    ):
        raise TraversalRefused(
            "Contribution cost context requires a standalone contribution question",
            "cost_context_invalid",
        )
    if query.captured_cost_context is not None and (
        not (is_inventory or is_contribution)
        or query.follow
        or query.exists
        or query.inventory_cost_context is not None
        or query.contribution_cost_context is not None
        or query.company_cost_context is not None
    ):
        raise TraversalRefused(
            "Captured cost context requires a standalone inventory or contribution question",
            "cost_context_invalid",
        )
    if query.company_cost_context is not None and (
        not (is_inventory or is_contribution)
        or query.follow
        or query.exists
        or query.inventory_cost_context is not None
        or query.contribution_cost_context is not None
        or query.captured_cost_context is not None
    ):
        raise TraversalRefused(
            "Company cost context requires a standalone inventory or contribution question",
            "cost_context_invalid",
        )
    if is_contribution:
        if any(
            group.bucket and group.field != f"{query.as_}.economic_at"
            for group in query.group_by
        ):
            raise TraversalRefused(
                "Only contribution economic dates may be bucketed", "not_additive"
            )
        axes = {group.field for group in query.group_by if not group.bucket}
        axes.update(
            condition.field for condition in query.filter if condition.op == "eq"
        )
        if (
            query.measures
            and not {f"{query.as_}.currency", f"{query.as_}.base_unit"} <= axes
        ):
            raise TraversalRefused(
                "Contribution measures require currency and base unit grouping or equality filters",
                "unit_mismatch",
            )
    path = resolve(graph, query)
    check_properties(path)
    path = narrow_unreferenced_hops(path)
    check_fan_out(path)
    check_units(path)
    check_additivity(path)
    check_having(path)
    return path


def run_traversal(
    session: Session, tenant_id: str, query: Traversal
) -> TraversalResult:
    from reality.services.analytics.compile_sql import execute

    path = plan(query)
    with session.no_autoflush:
        return execute(session, tenant_id, path)
