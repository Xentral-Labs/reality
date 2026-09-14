"""Shared analytics tools; caller identity never comes from model arguments."""

from contextlib import contextmanager
from contextvars import ContextVar

from pydantic import Field

from reality.domain.analytics import (
    AnalyticsDefinition,
    AnalyticsQuery,
    ContributorQuery,
    StrictModel,
)
from reality.services.analytics.budget import CANCELLED
from reality.services.analytics.catalog import catalog
from reality.services.analytics.execution import execute
from reality.services.analytics.reports import get_report, list_reports
from reality.services.core import get_tenant
from reality.services.memberships import Principal

CALLER: ContextVar[Principal | None] = ContextVar("analytics_caller", default=None)


@contextmanager
def caller(principal):
    token = CALLER.set(principal)
    try:
        yield
    finally:
        CALLER.reset(token)


class CatalogRequest(StrictModel):
    dataset: str | None = Field(
        default=None,
        max_length=100,
        description="Optional exact dataset key; omit to discover the whole analytics catalog.",
    )


class ExportRequest(StrictModel):
    definition: AnalyticsDefinition = Field(
        description="The same strict analytical definition accepted by analytics_query."
    )
    expected_fingerprint: str | None = Field(
        default=None,
        description="Optional fingerprint of the reviewed executed definition.",
    )


class ReportsRequest(StrictModel):
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


class ReportRequest(StrictModel):
    report_id: str = Field(
        max_length=128, description="Opaque ID of a private report owned by the caller."
    )


SCHEMAS = {
    "analytics.catalog": CatalogRequest,
    "analytics.query": AnalyticsQuery,
    "analytics.contributors": ContributorQuery,
    "analytics.export": ExportRequest,
    "analytics.reports.list": ReportsRequest,
    "analytics.reports.get": ReportRequest,
}


def invoke(session, tenant_id, name, arguments):
    request = SCHEMAS[name].model_validate(arguments)
    values = request.model_dump(mode="json")
    get_tenant(session, tenant_id)
    if name == "analytics.catalog":
        return catalog(**values)
    if name == "analytics.reports.list":
        return list_reports(session, tenant_id, CALLER.get(), **values)
    if name == "analytics.reports.get":
        return get_report(session, tenant_id, CALLER.get(), **values)
    return execute(
        tenant_id, values, operation=name.split(".")[1], cancellation=CANCELLED.get()
    )
