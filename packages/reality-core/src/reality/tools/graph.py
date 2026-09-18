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
    reporting_templates,
)
from reality.services.analytics.reports import CALLER, get_report, list_reports
from reality.services.analytics.traversal import TraversalRefused, run_traversal
from reality.services.core import get_tenant


class GraphCatalogRequest(StrictModel):
    language: str = Field(
        default="en",
        max_length=5,
        description="Language for the business words in the catalog.",
    )
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
            "filters, declared measures and grouping. Every field is "
            "alias.property, where the alias is `as` on the start node "
            "(default 'root') or on a hop — 'ordered_at' alone is refused "
            "because the path may reach more than one record that has it. A "
            "period is two half-open bounds on the same field: gte the first "
            "instant, lt the first instant after it. Example: "
            '{"from": "order", "as": "o", '
            '"filter": [{"field": "o.ordered_at", "op": "gte", "value": "2026-09-10T00:00:00Z"}, '
            '{"field": "o.ordered_at", "op": "lt", "value": "2026-09-17T00:00:00Z"}], '
            '"measures": ["stated_order_amount"], '
            '"group_by": [{"field": "o.currency"}]}'
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


class GraphTemplatesRequest(StrictModel):
    language: str = Field(
        default="en",
        max_length=5,
        description="Language for the template names and explanations.",
    )


class GraphReportsRequest(StrictModel):
    query: str = Field(
        default="", max_length=200, description="Optional report-name search."
    )
    limit: int = Field(
        default=50, ge=1, le=200, description="Maximum private reports to return."
    )
    cursor: str | None = Field(
        default=None,
        max_length=2048,
        description="Opaque continuation from the same owner-scoped search.",
    )


class GraphReportRequest(StrictModel):
    report_id: str = Field(
        max_length=128,
        description="Opaque ID of a private graph report owned by the caller.",
    )


SCHEMAS = {
    "graph.catalog": GraphCatalogRequest,
    "graph.templates": GraphTemplatesRequest,
    "graph.ask": GraphAskRequest,
    "graph.reports.list": GraphReportsRequest,
    "graph.reports.get": GraphReportRequest,
}


def invoke(session, tenant_id: str, name: str, arguments: dict[str, Any]) -> Any:
    request = SCHEMAS[name].model_validate(arguments or {})
    get_tenant(session, tenant_id)
    if name == "graph.catalog":
        try:
            # The session comes with the call, so a short-vocabulary column can
            # list the words this company's records actually use rather than
            # leaving the caller to guess them.
            return reporting_catalog(
                request.node, request.language, session=session, tenant_id=tenant_id
            )
        except ReportingGraphError as error:
            raise TraversalRefused(str(error), "unknown_node") from error

    if name == "graph.templates":
        return {"templates": reporting_templates(request.language)}

    if name == "graph.reports.list":
        return list_reports(
            session,
            tenant_id,
            CALLER.get(),
            **request.model_dump(mode="json"),
            report_kind="graph",
        )
    if name == "graph.reports.get":
        return get_report(
            session,
            tenant_id,
            CALLER.get(),
            request.report_id,
            report_kind="graph",
        )

    query = request.question or parse(request.path or "", request.parameters)
    result = run_traversal(session, tenant_id, query)
    return {
        "rows": list(result.rows),
        # An empty answer means one of two different things; only one of them is
        # about the business, and the caller cannot tell them apart alone.
        **(
            {"matched_nothing": list(result.matched_nothing)}
            if result.matched_nothing
            else {}
        ),
        "path": list(result.path),
        "model_version": result.model_version,
        "statements": result.statements,
        "sql": result.sql,
        "question": query.model_dump(mode="json", by_alias=True, exclude_defaults=True),
    }
