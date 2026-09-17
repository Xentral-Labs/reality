"""The reporting graph as agent tools; caller identity never comes from arguments.

Two tools, matching the two things anybody needs: find out what can be asked, and
ask it. The catalog is generated from the declaration, so the tool and the
executor can never describe different things.

A refusal is returned as a refusal, with its stable code, because it is the most
useful answer this feature produces: it names the edge that fanned out, the unit
that cannot be added, or the property that does not exist, and a model can act on
that where it cannot act on a wrong number.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from reality.domain.analytics import StrictModel
from reality.domain.traversal import Traversal
from reality.services.analytics.cypher_surface import parse
from reality.services.analytics.graph_model import (
    ReportingGraphError,
    reporting_catalog,
)
from reality.services.analytics.traversal import TraversalRefused, run_traversal
from reality.services.core import get_tenant


class GraphCatalogRequest(StrictModel):
    node: str | None = Field(
        default=None,
        max_length=100,
        description=(
            "Optional exact node key; omit to discover every node, how they "
            "connect, and what each measure means."
        ),
    )


class GraphAskRequest(StrictModel):
    question: Traversal | None = Field(
        default=None,
        description=(
            "The question as a checked object: a path through declared edges, "
            "filters, declared measures and grouping."
        ),
    )
    path: str | None = Field(
        default=None,
        max_length=4000,
        description=(
            "The same question in the path syntax, for example "
            "MATCH (o:order) RETURN o.currency, sum(stated_order_amount). "
            "RETURN names declared measures; arithmetic on properties is refused, "
            "because summing one along a path that fans out multiplies the total."
        ),
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Values for $name placeholders used by the path syntax.",
    )

    @model_validator(mode="after")
    def check(self) -> GraphAskRequest:
        if bool(self.question) == bool(self.path):
            raise ValueError("ask with exactly one of question or path")
        return self


SCHEMAS = {
    "graph.catalog": GraphCatalogRequest,
    "graph.ask": GraphAskRequest,
}


def invoke(session, tenant_id: str, name: str, arguments: dict[str, Any]) -> Any:
    request = SCHEMAS[name].model_validate(arguments or {})
    get_tenant(session, tenant_id)
    if name == "graph.catalog":
        try:
            return reporting_catalog(request.node)
        except ReportingGraphError as error:
            raise TraversalRefused(str(error), "unknown_node") from error

    query = request.question or parse(request.path or "", request.parameters)
    result = run_traversal(session, tenant_id, query)
    return {
        "rows": list(result.rows),
        "path": list(result.path),
        "model_version": result.model_version,
        "statements": result.statements,
        "question": query.model_dump(mode="json", by_alias=True, exclude_defaults=True),
    }
