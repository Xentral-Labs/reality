"""Load the reporting graph and hold it against the schema it claims to describe.

Validation lives here rather than only in a test, so anything reading the model
gets the same refusal — the rule every other catalog in this package follows. An
invalid declaration therefore stops the application at load instead of producing
a wrong number at query time.

The checks that need the database metadata live here; the ones that do not live
in `domain/reporting_graph.py`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml
from sqlalchemy import inspect as sa_inspect

from reality.config import config_text
from reality.db.core import Base
from reality.domain.reporting_graph import Edge, Node, ReportingGraph

REPORTING_GRAPH_FILE = "reporting_graph.yaml"


class ReportingGraphError(ValueError):
    """The declaration disagrees with the schema, or with itself."""


def _schema() -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    for mapper in Base.registry.mappers:
        entity = mapper.class_
        name = getattr(entity, "__tablename__", None)
        if isinstance(name, str):
            tables[name] = {column.name for column in sa_inspect(entity).columns}
    return tables


def _foreign_keys() -> dict[str, str]:
    """Where each foreign key actually points, as table.column -> target table."""
    targets: dict[str, str] = {}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            for key in column.foreign_keys:
                targets[f"{table.name}.{column.name}"] = key.column.table.name
    return targets


def _check_node(name: str, node: Node, schema: dict[str, set[str]]) -> None:
    if node.from_facts is not None:
        if "fact" not in schema:
            raise ReportingGraphError("node {name}: the fact table does not exist")
        return
    table = node.table or ""
    if table not in schema:
        raise ReportingGraphError(f"node {name}: table {table!r} does not exist")
    columns = schema[table]
    named = {
        "key": node.key,
        "tenant": node.tenant,
        **({"time": node.time} if node.time else {}),
        **({"evidence": node.evidence} if node.evidence else {}),
    }
    for role, column in named.items():
        if column not in columns:
            raise ReportingGraphError(
                f"node {name}: {role} column {table}.{column} does not exist"
            )
    for prop in node.properties:
        column = node.column_of(prop)
        if column not in columns:
            raise ReportingGraphError(
                f"node {name}: property {prop!r} reads {table}.{column}, which does not exist"
            )
    for column in node.where or {}:
        if column not in columns:
            raise ReportingGraphError(
                f"node {name}: discriminating column {table}.{column} does not exist"
            )
    for role, spec in (
        ("correction", node.correction_table),
        ("revision", node.revision_table),
    ):
        if spec is None:
            continue
        if spec.table not in schema:
            raise ReportingGraphError(
                f"node {name}: {role} table {spec.table!r} does not exist"
            )
        for field in ("original", "compensating", "replacement", "of", "order_by"):
            column = getattr(spec, field, None)
            if column and column not in schema[spec.table]:
                raise ReportingGraphError(
                    f"node {name}: {role} column {spec.table}.{column} does not exist"
                )
        # joins_on names a column on the node's own table, not on the correction
        # table, so it is held against the other one.
        joins_on = getattr(spec, "joins_on", None)
        if joins_on and joins_on not in columns:
            raise ReportingGraphError(
                f"node {name}: {role} join column {table}.{joins_on} does not exist"
            )


def _check_edge(
    name: str,
    edge: Edge,
    graph: ReportingGraph,
    schema: dict[str, set[str]],
    fks: dict[str, str],
) -> None:
    if edge.fact is not None:
        return
    via = edge.via or ""
    table, column = via.split(".", 1)
    if table not in schema:
        raise ReportingGraphError(f"edge {name}: table {table!r} does not exist")
    if column not in schema[table]:
        raise ReportingGraphError(f"edge {name}: column {via} does not exist")

    source = graph.nodes[edge.from_]
    target = graph.nodes[edge.to]
    # The direction check that catches a reversed declaration, which is otherwise
    # invisible until a total is silently multiplied: an n:1 edge is carried by a
    # column on the source's own table, a 1:n edge by a column on the target's.
    carrier = source.table if edge.multiplicity == "n:1" else target.table
    holder = "source" if edge.multiplicity == "n:1" else "target"
    if carrier and table != carrier:
        raise ReportingGraphError(
            f"edge {name} is declared {edge.multiplicity}, so {via} must sit on the "
            f"{holder} node's table {carrier!r}. Either the multiplicity or the "
            "direction is the wrong way round."
        )

    points_at = fks.get(via)
    expected = target.table if edge.multiplicity == "n:1" else source.table
    if points_at and expected and points_at != expected:
        raise ReportingGraphError(
            f"edge {name}: {via} is a foreign key to {points_at!r}, not to {expected!r}"
        )


def _check_measures(graph: ReportingGraph, schema: dict[str, set[str]]) -> None:
    for name, measure in graph.measures.items():
        node = graph.nodes[measure.node]
        table = node.table
        if not table:
            continue
        if isinstance(measure.source, str):
            if measure.source not in schema[table]:
                raise ReportingGraphError(
                    f"measure {name}: {table}.{measure.source} does not exist"
                )
        elif measure.source.distinct and measure.source.distinct not in schema[table]:
            raise ReportingGraphError(
                f"measure {name}: distinct key {table}.{measure.source.distinct} does not exist"
            )
        if measure.sign_from and measure.sign_from not in schema[table]:
            raise ReportingGraphError(
                f"measure {name}: sign column {table}.{measure.sign_from} does not exist"
            )
        unit = measure.unit
        if unit.column:
            unit_table = graph.nodes[unit.from_node].table if unit.from_node else table
            if unit_table and unit.column not in schema[unit_table]:
                raise ReportingGraphError(
                    f"measure {name}: unit column {unit_table}.{unit.column} does not exist"
                )


def validate_against_schema(graph: ReportingGraph) -> ReportingGraph:
    """Hold every declared name against the live schema.

    Drift therefore fails at load and in a test, not as a query error in front of
    somebody who asked a reasonable question.
    """
    schema = _schema()
    fks = _foreign_keys()
    for name, node in graph.nodes.items():
        _check_node(name, node, schema)
    for name, edge in graph.edges.items():
        _check_edge(name, edge, graph, schema, fks)
    _check_measures(graph, schema)
    return graph


def parse_reporting_graph(payload: dict[str, Any] | None = None) -> ReportingGraph:
    if payload is None:
        payload = yaml.safe_load(config_text(REPORTING_GRAPH_FILE))
    if not isinstance(payload, dict):
        raise ReportingGraphError("the reporting graph must be a mapping")
    known = {
        "version",
        "model_version",
        "language",
        "defaults",
        "nodes",
        "edges",
        "measures",
        "limits",
    }
    payload = {k: v for k, v in payload.items() if k in known}
    graph = ReportingGraph.model_validate(payload)
    return validate_against_schema(graph)


@lru_cache(maxsize=1)
def reporting_graph() -> ReportingGraph:
    return parse_reporting_graph()


def _kinds() -> dict[str, dict[str, str]]:
    """What sort of value each column holds, so a filter can offer the right editor.

    Guessing from the column name works until it does not; the schema already
    knows, and the catalog is the place that carries what the surfaces need.
    """
    from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric

    out: dict[str, dict[str, str]] = {}
    for table in Base.metadata.tables.values():
        columns: dict[str, str] = {}
        for column in table.columns:
            kind = column.type
            if isinstance(kind, (DateTime, Date)):
                columns[column.name] = "time"
            elif isinstance(kind, (Numeric, Integer)):
                columns[column.name] = "number"
            elif isinstance(kind, Boolean):
                columns[column.name] = "boolean"
            else:
                columns[column.name] = "text"
        out[table.name] = columns
    return out


def _label(carrier, fallback: str, language: str) -> str:
    """The word a person reads. Falls back to the key, which is never a lie."""
    label = getattr(carrier, "label", None)
    return label.pick(language) if label else fallback


def reporting_catalog(node: str | None = None, language: str = "en") -> dict[str, Any]:
    """What can be asked: the nodes, how they connect, and what each number means.

    Generated from the declaration rather than written beside it, so the catalog
    and the executor can never describe different things.
    """
    graph = reporting_graph()
    kinds = _kinds()
    if node is not None and node not in graph.nodes:
        raise ReportingGraphError(f"unknown node {node!r}")
    names = [node] if node else list(graph.nodes)
    return {
        "version": graph.version,
        "model_version": graph.model_version,
        "format": "traversal",
        "nodes": [
            {
                "key": name,
                "label": _label(graph.nodes[name], name, language),
                "grain": graph.nodes[name].grain,
                "backed_by": "facts"
                if graph.nodes[name].from_facts
                else graph.nodes[name].table,
                "corrections": graph.nodes[name].corrections,
                "coverage": list(graph.nodes[name].coverage),
                "properties": [
                    {
                        "key": prop,
                        "label": graph.nodes[name].label_of(prop, language),
                        "kind": kinds.get(graph.nodes[name].table or "", {}).get(
                            graph.nodes[name].column_of(prop), "text"
                        ),
                    }
                    for prop in sorted(graph.nodes[name].properties)
                ],
                "evidence": graph.nodes[name].evidence,
                "measures": [
                    {
                        "key": key,
                        "label": _label(measure, key, language),
                        "unit": measure.unit.kind,
                        "additive_over": list(measure.additive_over),
                        "never_across": list(measure.never_across),
                        "note": measure.note,
                    }
                    for key, measure in graph.measures_of(name).items()
                ],
                "edges": [
                    {
                        "key": key,
                        "label": _label(edge, key, language),
                        "to": edge.to,
                        "to_label": _label(graph.nodes[edge.to], edge.to, language),
                        "multiplicity": edge.multiplicity,
                        "recursive": bool(edge.recursive),
                        "stored": bool(edge.fact),
                    }
                    for key, edge in graph.edges_from(name).items()
                ],
                "edges_in": [
                    {
                        "key": key,
                        "label": _label(edge, key, language),
                        "from": edge.from_,
                        "from_label": _label(
                            graph.nodes[edge.from_], edge.from_, language
                        ),
                        "multiplicity": edge.multiplicity,
                    }
                    for key, edge in graph.edges_to(name).items()
                ],
            }
            for name in names
        ],
        "limits": graph.limits.model_dump(),
    }
