"""Strict, storage-independent analytical definitions and local calendar windows."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Predicate(StrictModel):
    relationship: Literal["purchases", "order_lines", "outbound"] | None = Field(
        default=None,
        description="Cataloged related-record scope for exists/not_exists.",
    )
    where: Predicate | None = Field(
        default=None, description="Filter evaluated inside the selected relationship."
    )
    time: TimeSelection | None = Field(
        default=None, description="Optional related-record time window."
    )
    field: str | None = Field(
        default=None, description="Cataloged field key for a leaf condition."
    )
    op: (
        Literal[
            "eq",
            "ne",
            "in",
            "not_in",
            "contains",
            "gte",
            "gt",
            "lte",
            "lt",
            "is_missing",
            "is_present",
            "exists",
            "not_exists",
        ]
        | None
    ) = Field(
        default=None,
        description="Operator valid for the selected field or relationship.",
    )
    value: str | int | bool | None = Field(
        default=None, description="Typed scalar for a comparison operator."
    )
    values: list[str | int | bool] | None = Field(
        default=None, max_length=100, description="Typed values for in/not_in."
    )
    all: list[Predicate] | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        description="Conditions that must all match.",
    )
    any: list[Predicate] | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        description="Conditions where at least one must match.",
    )

    @model_validator(mode="after")
    def shape(self):
        if self.relationship:
            if (
                self.op not in {"exists", "not_exists"}
                or self.field
                or self.value is not None
                or self.values is not None
                or self.all is not None
                or self.any is not None
            ):
                raise ValueError(
                    "A relationship requires exists or not_exists and its scoped filter only."
                )
            if self.time and self.time.field != (
                "occurred_at" if self.relationship == "outbound" else "ordered_at"
            ):
                raise ValueError("Purchase relationships use order date.")
            return self
        if self.where or self.time or self.op in {"exists", "not_exists"}:
            raise ValueError("Scoped conditions require a cataloged relationship.")
        if self.all is not None or self.any is not None:
            if (
                (self.all is not None and self.any is not None)
                or self.field
                or self.op
                or self.value is not None
                or self.values is not None
            ):
                raise ValueError("A filter is one group or one condition.")
        elif not self.field or not self.op:
            raise ValueError("A condition requires a field and operator.")
        elif self.op in {"in", "not_in"}:
            if not self.values or self.value is not None:
                raise ValueError("Membership filters require values only.")
        elif self.op in {"is_missing", "is_present"}:
            if self.value is not None or self.values is not None:
                raise ValueError("Missing-value filters take no value.")
        elif self.value is None or self.values is not None:
            raise ValueError("A comparison requires exactly one value.")
        if self.op == "contains" and (
            not isinstance(self.value, str) or len(self.value) > 200
        ):
            raise ValueError("Text filters require at most 200 characters.")
        return self


class Window(StrictModel):
    kind: Literal[
        "absolute",
        "iso_week",
        "last_complete_weeks",
        "last_complete_months",
        "current_month",
        "current_quarter",
        "current_year",
        "last_days",
    ] = "last_complete_weeks"
    start: date | None = None
    end: date | None = None
    year: int | None = Field(default=None, ge=1900, le=9998)
    week: int | None = Field(default=None, ge=1, le=53)
    count: int = Field(default=12, ge=1, le=3660)

    @model_validator(mode="after")
    def valid_window(self):
        if self.kind != "absolute" and (self.start is not None or self.end is not None):
            raise ValueError("Explicit dates require an absolute time window.")
        if self.kind != "iso_week" and (self.year is not None or self.week is not None):
            raise ValueError("ISO year and week require an ISO week window.")
        if self.kind == "absolute" and (
            not self.start
            or not self.end
            or not self.start < self.end
            or (self.end - self.start).days > 3660
        ):
            raise ValueError(
                "Absolute dates need an increasing range of at most ten years."
            )
        if self.kind == "iso_week":
            if self.year is None or self.week is None:
                raise ValueError("An ISO week requires its year and week.")
            date.fromisocalendar(self.year, self.week, 1)
        if self.kind == "last_complete_weeks" and self.count > 520:
            raise ValueError("At most 520 weeks are supported.")
        if self.kind == "last_complete_months" and self.count > 120:
            raise ValueError("At most 120 months are supported.")
        return self


class TimeSelection(StrictModel):
    field: str = Field(
        default="ordered_at", description="Cataloged datetime field to constrain."
    )
    timezone: str = Field(
        default="UTC", description="IANA timezone used for local calendar boundaries."
    )
    window: Window = Field(
        default_factory=Window, description="Bounded local calendar window."
    )

    @model_validator(mode="after")
    def known_zone(self):
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Choose a valid IANA timezone.") from error
        return self


class Sort(StrictModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"


class Presentation(StrictModel):
    kind: Literal["table", "bar", "line", "pivot"] = "table"
    rows: list[str] = Field(default_factory=list, max_length=2)
    column: str | None = None
    measures: list[str] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def kind_fields(self):
        if self.kind != "pivot" and (self.rows or self.column or self.measures):
            raise ValueError("Pivot fields require pivot presentation.")
        return self


class AnalyticsDefinition(StrictModel):
    version: Literal[1] = 1
    dataset: str = Field(description="Exact dataset key returned by analytics_catalog.")
    dimensions: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Zero to four groupable field keys from this dataset.",
    )
    measures: list[str] = Field(
        min_length=1,
        max_length=4,
        description="One to four measure keys from this dataset.",
    )
    where: Predicate | None = Field(
        default=None, description="Optional strict leaf/group/relationship filter tree."
    )
    time: TimeSelection | None = Field(
        default=None, description="Optional explicit observation period."
    )
    cancellation: Literal["all_recorded", "exclude_fully_cancelled"] = Field(
        default="all_recorded",
        description="Whether fully operationally cancelled orders remain in descriptive evidence.",
    )
    sort: list[Sort] = Field(
        default_factory=list,
        max_length=4,
        description="Selected dimension/measure or comparison-change sort fields.",
    )
    compare: Literal["previous_period"] | TimeSelection | None = Field(
        default=None,
        description="Previous equal period or an explicit comparison period using the same date field.",
    )
    presentation: Presentation = Field(
        default_factory=Presentation,
        description="Saved display preference; pivot totals are always calculated by the service.",
    )

    @model_validator(mode="after")
    def bounded(self):
        def size(node, depth=1):
            if node is None:
                return 0
            if depth > 3:
                raise ValueError("Filter groups support at most three levels.")
            if node.relationship:
                return max(1, size(node.where, depth + 1))
            return (
                sum(size(child, depth + 1) for child in (node.all or node.any or []))
                if node.all or node.any
                else 1
            )

        if size(self.where) > 32:
            raise ValueError("At most 32 filter conditions are supported.")
        if len(set(self.dimensions)) != len(self.dimensions) or len(
            set(self.measures)
        ) != len(self.measures):
            raise ValueError("Select each dimension and measure once.")
        if self.compare and not self.time:
            raise ValueError("A comparison requires a time window.")
        if len(json.dumps(self.model_dump(mode="json")).encode()) > 16384:
            raise ValueError("A report definition is limited to 16 KiB.")
        return self


class AnalyticsQuery(StrictModel):
    definition: AnalyticsDefinition = Field(
        description="Versioned allowlisted analysis; SQL and caller identity are never accepted."
    )
    page_size: int = Field(
        default=50, ge=1, le=200, description="Maximum result groups on this page."
    )
    cursor: str | None = Field(
        default=None,
        max_length=2048,
        description="Opaque continuation bound to company and exact definition.",
    )


class ContributorQuery(AnalyticsQuery):
    group: dict[str, Any] = Field(
        default_factory=dict,
        description="Exact dimension and implicit currency/unit values from one result row.",
    )
    measure: str = Field(
        description="Selected measure whose supporting records are requested."
    )
    page_size: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def bounded_group(self):
        if len(self.group) > 6 or any(
            not isinstance(value, (str, int, bool, type(None)))
            or isinstance(value, str)
            and len(value) > 512
            for value in self.group.values()
        ):
            raise ValueError(
                "Contributor groups require at most six bounded scalar values."
            )
        return self


def resolve_window(
    selection: TimeSelection, observed_at: datetime
) -> tuple[datetime, datetime]:
    zone = ZoneInfo(selection.timezone)
    today = observed_at.astimezone(zone).date()
    window = selection.window
    if window.kind == "absolute":
        start, end = window.start, window.end
    elif window.kind == "iso_week":
        start = date.fromisocalendar(window.year, window.week, 1)
        end = start + timedelta(days=7)
    elif window.kind == "last_complete_weeks":
        end = today - timedelta(days=today.weekday())
        start = end - timedelta(weeks=window.count)
    elif window.kind == "last_complete_months":
        end = today.replace(day=1)
        ordinal = end.year * 12 + end.month - 1 - window.count
        start = date(ordinal // 12, ordinal % 12 + 1, 1)
    elif window.kind == "current_month":
        start, end = today.replace(day=1), today + timedelta(days=1)
    elif window.kind == "current_quarter":
        start, end = (
            date(today.year, ((today.month - 1) // 3) * 3 + 1, 1),
            today + timedelta(days=1),
        )
    elif window.kind == "current_year":
        start, end = date(today.year, 1, 1), today + timedelta(days=1)
    else:
        start, end = today - timedelta(days=window.count - 1), today + timedelta(days=1)
    return tuple(
        datetime.combine(day, datetime.min.time(), zone).astimezone(UTC)
        for day in (start, end)
    )


class ReportChange(StrictModel):
    operation: Literal["create", "update", "rename", "duplicate", "delete"] = Field(
        description="The private report change to prepare for confirmation."
    )
    request_id: UUID = Field(
        description="New client retry UUID; reuse it only for the identical change."
    )
    report_id: str | None = Field(
        default=None,
        max_length=128,
        description="Opaque owned report ID; omitted only when creating.",
    )
    expected_revision: int | None = Field(
        default=None,
        ge=1,
        description="Revision shown to the caller; required for every existing report change.",
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        description="Private report name for create, rename or duplicate.",
    )
    definition: AnalyticsDefinition | None = Field(
        default=None,
        description="Complete replacement definition for create or update.",
    )

    @model_validator(mode="after")
    def operation_fields(self):
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("Enter a report name.")
        if self.operation == "create":
            if (
                not self.name
                or not self.definition
                or self.report_id
                or self.expected_revision
            ):
                raise ValueError(
                    "Creating a report requires only a name and definition."
                )
        elif not self.report_id or not self.expected_revision:
            raise ValueError(
                "A report change requires its identity and expected revision."
            )
        if self.operation in {"rename", "duplicate"} and not self.name:
            raise ValueError("Enter a report name.")
        if self.operation == "update" and not self.definition:
            raise ValueError("An update requires the complete definition.")
        if self.operation in {"rename", "duplicate", "delete"} and self.definition:
            raise ValueError("This operation does not accept a replacement definition.")
        return self
