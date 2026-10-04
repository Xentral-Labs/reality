"""Non-authoritative, content-addressed interpretations (spec 356)."""

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PACKAGE_ROWS = 500
PACKAGE_BYTES = 2 * 1024 * 1024
MANIFEST_UNITS = 500
CONTINUATION_UNITS = 25


def canonical_json(value: Any) -> str:
    def encode(item: Any) -> str:
        if isinstance(item, Decimal):
            return format(item.normalize(), "f")
        if isinstance(item, date | datetime):
            return item.isoformat()
        raise TypeError(f"Unsupported intake value: {type(item).__name__}")

    return json.dumps(
        value,
        default=encode,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class IntakeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Effect(IntakeModel):
    """A closed operation vocabulary; never a caller-selected Python callable."""

    operation: Literal[
        "document",
        "commitment",
        "customer_payment",
        "payment_allocation",
        "source_document",
        "return_announcement",
        "credit_hold",
        "commitment_revision",
        "commitment_cancellation",
    ]
    arguments: dict[str, Any]


class ReferenceState(IntakeModel):
    record_type: Literal[
        "party", "item", "location", "document", "ledger_entry", "account"
    ]
    record_id: str
    digest: str


class CalendarState(IntakeModel):
    time_zone: str
    source_record_id: str | None = None


class ObservationState(IntakeModel):
    kind: Literal["credit_exposure", "shop_order_state"]
    arguments: dict[str, str]
    digest: str


class PreparedIntake(IntakeModel):
    schema_version: Literal[1] = 1
    tenant_id: str
    source_record_id: str
    source_hash: str
    source_version: int
    import_job_id: str
    profile: str
    finance_revision: int | None = None
    calendar: CalendarState | None = None
    interpreter_version: Literal["1"] = "1"
    mapping: dict[str, Any]
    references: tuple[ReferenceState, ...] = ()
    observations: tuple[ObservationState, ...] = ()
    effects: tuple[Effect, ...]
    issues: tuple[str, ...] = ()
    row_count: int = Field(ge=1, le=PACKAGE_ROWS)

    def review_digest(self) -> str:
        return content_digest(self.model_dump(mode="json"))


class ManifestEntry(IntakeModel):
    proposal_id: str = Field(min_length=1, max_length=128)
    digest: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class IntakeManifest(IntakeModel):
    """An aggregate selection, distinct from one atomic effect package."""

    mode: Literal["independent_units"] = "independent_units"
    revision: int = Field(ge=1)
    entries: tuple[ManifestEntry, ...] = Field(min_length=1, max_length=MANIFEST_UNITS)
