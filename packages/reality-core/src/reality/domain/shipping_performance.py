"""Source-stated dispatch inputs and read-time completion-slot-v1 observations."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from itertools import pairwise
from typing import Any, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError


class ClosedInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("An explicit time zone is required.")
    return value.astimezone(UTC)


class RequirementInput(ClosedInput):
    commitment_id: str = Field(min_length=1)
    quantity: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    dispatch_due_at: datetime
    planned_handover_at: datetime | None = None

    @field_validator("quantity", mode="before")
    @classmethod
    def exact_quantity(cls, value: Any) -> Any:
        if isinstance(value, (float, bool)):
            raise PydanticCustomError(
                "decimal_quantity",
                "Quantity must be a decimal string or Decimal, never binary float.",
            )
        return value

    @field_validator("dispatch_due_at", "planned_handover_at")
    @classmethod
    def zoned_time(cls, value: datetime | None) -> datetime | None:
        return aware(value) if value is not None else None

    @model_validator(mode="after")
    def planned_before_deadline(self) -> Self:
        if self.planned_handover_at and self.planned_handover_at > self.dispatch_due_at:
            raise ValueError(
                "Planned handover cannot follow its stated dispatch deadline."
            )
        return self


class CapacityInput(ClosedInput):
    starts_at: datetime
    ends_at: datetime
    collection_cutoff_at: datetime
    completion_slots: StrictInt = Field(ge=0)
    confirmation_state: Literal["confirmed", "requested"]
    confirmation_source_record_id: str | None = Field(default=None, min_length=1)

    @field_validator("starts_at", "ends_at", "collection_cutoff_at")
    @classmethod
    def zoned_time(cls, value: datetime) -> datetime:
        return aware(value)

    @model_validator(mode="after")
    def interval_and_confirmation(self) -> Self:
        if not self.starts_at < self.collection_cutoff_at <= self.ends_at:
            raise ValueError(
                "Collection cutoff must fall inside a positive capacity interval."
            )
        if (
            self.confirmation_state == "confirmed"
            and not self.confirmation_source_record_id
        ):
            raise ValueError(
                "Confirmed capacity requires its exact original confirmation Source."
            )
        return self


class PlanInput(ClosedInput):
    statement_kind: Literal["plan", "withdrawal"] = "plan"
    dispatch_location_id: str = Field(min_length=1)
    business_day: date
    business_time_zone: str
    site_time_zone: str
    requirements: tuple[RequirementInput, ...] = ()
    capacity_windows: tuple[CapacityInput, ...] = ()

    @field_validator("business_time_zone", "site_time_zone")
    @classmethod
    def existing_zone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("A valid IANA time zone is required.") from error
        return value

    @model_validator(mode="after")
    def exact_scope(self) -> Self:
        if self.statement_kind == "withdrawal":
            if self.requirements or self.capacity_windows:
                raise ValueError(
                    "Withdrawal retains a header without work or capacity children."
                )
            return self
        if not self.requirements:
            raise ValueError("A plan requires explicitly stated dispatch work.")
        identities = [row.commitment_id for row in self.requirements]
        if len(identities) != len(set(identities)):
            raise ValueError(
                "A commitment may have only one requirement in a statement."
            )
        zone = ZoneInfo(self.business_time_zone)
        if any(
            row.dispatch_due_at.astimezone(zone).date() != self.business_day
            for row in self.requirements
        ):
            raise ValueError(
                "Dispatch deadlines must fall in the stated company business day."
            )
        windows = sorted(self.capacity_windows, key=lambda row: row.starts_at)
        if any(left.ends_at > right.starts_at for left, right in pairwise(windows)):
            raise ValueError(
                "Capacity windows cannot overlap, including requested windows."
            )
        return self


@dataclass(frozen=True)
class PhysicalContent:
    movement_id: str
    quantity: Decimal
    dispatched_at: datetime
    handover_times: tuple[datetime | None, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "dispatched_at", aware(self.dispatched_at))
        object.__setattr__(
            self,
            "handover_times",
            tuple(
                aware(value) if value is not None else None
                for value in self.handover_times
            ),
        )


def covered_at(
    quantity: Decimal, contents: list[PhysicalContent], *, observed_at: datetime
) -> tuple[datetime | None, tuple[str, ...]]:
    """Cover a quantity once per effective movement, using actual handover time."""
    observed_at = aware(observed_at)
    unique: dict[str, PhysicalContent] = {}
    gaps: set[str] = set()
    for content in contents:
        if content.movement_id in unique and unique[content.movement_id] != content:
            gaps.add("conflicting_physical_content")
        unique[content.movement_id] = content
    completed: list[tuple[datetime, Decimal]] = []
    for content in unique.values():
        if not content.handover_times:
            continue
        times = set(content.handover_times)
        if None in times or len(times) != 1:
            gaps.add("missing_or_conflicting_handover_time")
            continue
        instant = aware(next(iter(times)))
        if instant > observed_at or instant < aware(content.dispatched_at):
            gaps.add("unresolved_handover_chronology")
            continue
        completed.append((instant, content.quantity))
    if gaps:
        return None, tuple(sorted(gaps))
    covered = Decimal(0)
    for instant, amount in sorted(completed):
        covered += amount
        if covered >= quantity:
            return instant, ()
    return None, ()


@dataclass(frozen=True)
class DispatchWork:
    commitment_id: str
    order_id: str
    location_id: str
    quantity: Decimal
    due_at: datetime
    planned_at: datetime | None
    handed_over_at: datetime | None
    ready: bool
    coverage_gaps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("due_at", "planned_at", "handed_over_at"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, aware(value))


# Physical/execution uncertainty does not withdraw an independently valid plan.
OBSERVATION_ONLY_GAPS = frozenset(
    {
        "conflicting_physical_content",
        "missing_or_conflicting_handover_time",
        "unresolved_handover_chronology",
        "unresolved_future_handover",
        "unresolved_future_physical_content",
        "incompatible_dispatch_contents",
        "unresolved_shipment_linkage",
        "unresolved_execution_outcome",
    }
)


@dataclass(frozen=True)
class Capacity:
    location_id: str
    starts_at: datetime
    ends_at: datetime
    cutoff_at: datetime
    slots: int
    confirmation_state: str

    def __post_init__(self) -> None:
        for field in ("starts_at", "ends_at", "cutoff_at"):
            object.__setattr__(self, field, aware(getattr(self, field)))


def _microseconds(value: timedelta) -> int:
    return (value.days * 86400 + value.seconds) * 1_000_000 + value.microseconds


def evaluate(
    work: list[DispatchWork], capacities: list[Capacity], *, observed_at: datetime
) -> dict[str, Any]:
    """Observe complete order/site units; never mutate inputs or forecast authority."""
    observed_at = aware(observed_at)
    units: dict[tuple[str, str], list[DispatchWork]] = defaultdict(list)
    for row in work:
        units[(row.location_id, row.order_id)].append(row)
    orders: dict[str, list[tuple[str, str]]] = defaultdict(list)
    site_keys: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in units:
        orders[key[1]].append(key)
        site_keys[key[0]].append(key)
    actual: dict[tuple[str, str], datetime] = {}
    planned: dict[tuple[str, str], datetime] = {}
    predicted: dict[tuple[str, str], datetime] = {}
    unknown_sites: set[str] = set()
    unknown_plan: set[str] = set()
    unit_gaps: dict[tuple[str, str], tuple[str, ...]] = {}
    for key, rows in units.items():
        gaps = tuple(
            sorted(
                {gap for row in rows for gap in row.coverage_gaps}
                | (
                    {"unresolved_future_handover"}
                    if any(
                        row.handed_over_at and row.handed_over_at > observed_at
                        for row in rows
                    )
                    else set()
                )
            )
        )
        unit_gaps[key] = gaps
        if gaps:
            unknown_sites.add(key[0])
        if all(row.planned_at is not None for row in rows) and not (
            set(gaps) - OBSERVATION_ONLY_GAPS
        ):
            planned[key] = max(row.planned_at for row in rows)
        else:
            unknown_plan.add(key[0])
        if (
            all(
                row.handed_over_at is not None and row.handed_over_at <= observed_at
                for row in rows
            )
            and not gaps
        ):
            actual[key] = max(row.handed_over_at for row in rows)
    predicted.update(actual)
    exceeded_windows: list[str] = []
    for site in sorted(site_keys):
        windows = sorted(
            [row for row in capacities if row.location_id == site],
            key=lambda row: row.starts_at,
        )
        if not windows or any(a.ends_at > b.starts_at for a, b in pairwise(windows)):
            unknown_sites.add(site)
        candidates = sorted(
            [
                key
                for key in site_keys[site]
                if key not in actual
                and not unit_gaps[key]
                and all(
                    row.handed_over_at is not None or row.ready for row in units[key]
                )
            ],
            key=lambda key: (
                min(row.due_at for row in units[key] if row.handed_over_at is None),
                key[1],
            ),
        )
        candidates.reverse()
        consumed_actual: set[tuple[str, str]] = set()
        for window in windows:
            if window.confirmation_state != "confirmed" or site in unknown_sites:
                continue
            used_keys = {
                key
                for key in site_keys[site]
                if key in actual
                and key not in consumed_actual
                and window.starts_at
                <= actual[key]
                <= min(observed_at, window.cutoff_at)
            }
            consumed_actual |= used_keys
            used = len(used_keys)
            if used > window.slots:
                exceeded_windows.append(site)
            remaining = max(0, window.slots - used)
            if not remaining or not window.slots:
                continue
            start = max(observed_at, window.starts_at)
            period = _microseconds(window.ends_at - window.starts_at)
            if period <= 0 or not window.starts_at < window.cutoff_at <= window.ends_at:
                raise ValueError(
                    "Capacity must retain its original positive interval/cutoff."
                )
            for slot in range(1, remaining + 1):
                offset = Fraction(period * slot, window.slots)
                micros = (
                    offset.numerator + offset.denominator - 1
                ) // offset.denominator
                instant = start + timedelta(microseconds=micros)
                if instant > window.cutoff_at or not candidates:
                    break
                predicted[candidates.pop()] = instant

    def company_times(times: dict[tuple[str, str], datetime]) -> dict[str, datetime]:
        result = {}
        for order, keys in orders.items():
            if all(key in times for key in keys):
                result[order] = max(times[key] for key in keys)
        return result

    risk: set[str] = set()
    risk_requirements = []
    sites = {}
    for site in sorted(site_keys):
        keys = site_keys[site]
        site_risk = set()
        for key in keys:
            for row in units[key]:
                if row.handed_over_at is not None and row.handed_over_at <= observed_at:
                    continue
                if not row.ready or (
                    site not in unknown_sites
                    and (key not in predicted or predicted[key] > row.due_at)
                ):
                    site_risk.add(key[1])
                    risk_requirements.append(
                        {
                            "commitment_id": row.commitment_id,
                            "order_id": row.order_id,
                            "location_id": site,
                            "due_at": row.due_at,
                            "code": "blocked"
                            if not row.ready
                            else "no_confirmed_slot"
                            if key not in predicted
                            else "after_deadline",
                        }
                    )
        risk |= site_risk
        sites[site] = {
            "due": len(keys),
            "handed_over": sum(key in actual for key in keys),
            "forecast": None
            if site in unknown_sites
            else sum(key in predicted for key in keys),
            "risk": None if site in unknown_sites else len(site_risk),
            "risk_order_ids": sorted(site_risk),
            "coverage_complete": site not in unknown_sites,
        }
    return {
        "actual_times": company_times(actual),
        "planned_times": company_times(planned),
        "forecast_times": company_times(predicted),
        "site_actual_times": actual,
        "site_planned_times": planned,
        "site_forecast_times": predicted,
        "sites": sites,
        "risk_order_ids": sorted(risk),
        "risk_requirements": risk_requirements,
        "forecast_complete": not unknown_sites,
        "plan_complete": not unknown_plan,
        "unknown_sites": sorted(unknown_sites),
        "capacity_exceeded_sites": sorted(set(exceeded_windows)),
        "policy_version": "completion-slot-v1",
    }
