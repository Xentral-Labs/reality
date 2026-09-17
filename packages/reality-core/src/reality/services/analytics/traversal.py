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


class TraversalRefused(ValueError):
    """The question cannot be answered correctly, and why."""


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
class ResolvedPath:
    graph: ReportingGraph
    query: Traversal
    node_of: dict[str, str]
    hops: tuple[ResolvedHop, ...]
    measures: dict[str, Measure]
    measure_alias: dict[str, str]


@dataclass(frozen=True)
class TraversalResult:
    rows: tuple[dict[str, Any], ...]
    sql: str
    statements: int
    model_version: str
    path: tuple[str, ...]


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
        raise TraversalRefused(f"there is no node called {query.from_!r} in the model")
    node_of = {query.as_: query.from_}
    hops: list[ResolvedHop] = []
    previous = query.as_
    for hop in query.follow:
        origin = hop.from_ or previous
        edge = graph.edges.get(hop.edge)
        if edge is None:
            raise TraversalRefused(
                f"there is no edge called {hop.edge!r} in the model. Declare it with "
                "its multiplicity and it works everywhere."
            )
        source, target = (
            (edge.from_, edge.to) if hop.direction == "out" else (edge.to, edge.from_)
        )
        if node_of[origin] != source:
            raise TraversalRefused(
                f"edge {hop.edge!r} runs from {source!r}, but the path is at "
                f"{node_of[origin]!r}. Follow it the other way round, or take another edge."
            )
        if hop.depth and not edge.recursive:
            raise TraversalRefused(
                f"edge {hop.edge!r} is not declared recursive, so it cannot be "
                "walked to a variable depth"
            )
        if edge.recursive and not hop.depth:
            raise TraversalRefused(
                f"edge {hop.edge!r} is recursive, so a hop along it names the depth "
                f"it walks, at most {edge.recursive.max_depth}"
            )
        if hop.depth and edge.recursive and hop.depth[1] > edge.recursive.max_depth:
            raise TraversalRefused(
                f"edge {hop.edge!r} is declared to a depth of "
                f"{edge.recursive.max_depth}; {hop.depth[1]} is beyond it"
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
            raise TraversalRefused(f"there is no measure called {name!r} in the model")
        owners = [alias for alias, node in node_of.items() if node == measure.node]
        if not owners:
            raise TraversalRefused(
                f"measure {name!r} lives on {measure.node!r}, which this path never "
                "reaches. Follow an edge to it first."
            )
        measures[name] = measure
        measure_alias[name] = owners[0]
    return ResolvedPath(graph, query, node_of, tuple(hops), measures, measure_alias)


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
            f"summing it here would multiply the total.{offer}"
        )


def check_units(path: ResolvedPath) -> None:
    grouped = {
        grouping.field for grouping in path.query.group_by if grouping.bucket is None
    }
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
                    "which this path never reaches"
                )
            home = owners[0]
        field = f"{home}.{unit.column}"
        if field not in grouped:
            axis = ", ".join(measure.never_across) or unit.column
            raise TraversalRefused(
                f"measure {name!r} may not be summed across {axis}. Group by "
                f"{field!r}, or filter the question down to one."
            )


def check_additivity(path: ResolvedPath) -> None:
    has_time_axis = any(grouping.bucket for grouping in path.query.group_by)
    for name, measure in path.measures.items():
        if has_time_axis and "time" in measure.never_across:
            raise TraversalRefused(
                f"measure {name!r} is a state, not a flow, so it is not additive "
                "over time. Ask for it as it stands, without a time axis."
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
                f"It has: {available}."
            )


def plan(query: Traversal, graph: ReportingGraph | None = None) -> ResolvedPath:
    """Resolve and check a question. Nothing touches the database until this passes."""
    graph = graph or reporting_graph()
    if len(query.follow) > graph.limits.max_path_length:
        raise TraversalRefused(
            f"a path may take at most {graph.limits.max_path_length} steps"
        )
    path = resolve(graph, query)
    check_properties(path)
    path = narrow_unreferenced_hops(path)
    check_fan_out(path)
    check_units(path)
    check_additivity(path)
    return path


def run_traversal(
    session: Session, tenant_id: str, query: Traversal
) -> TraversalResult:
    from reality.services.analytics.compile_sql import execute

    path = plan(query)
    return execute(session, tenant_id, path)
