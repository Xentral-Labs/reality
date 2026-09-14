"""Bounded Playground inputs; real business behavior stays in shared services."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    field_validator,
)

MASTER_TOOLS = frozenset(
    f"{family}_{action}"
    for family in ("party", "item", "location")
    for action in ("create", "update")
)


class PlaygroundMasterRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: StrictStr | None = Field(default=None, min_length=1, max_length=128)
    expected_revision: StrictStr | None = Field(
        default=None, min_length=1, max_length=128
    )
    name: StrictStr = Field(min_length=1, max_length=200)


class PlaygroundPartyRecord(PlaygroundMasterRecord):
    type: Literal["company", "customer", "supplier"]
    roles: list[Literal["company", "customer", "supplier"]] = Field(
        min_length=1, max_length=3
    )


class PlaygroundItemRecord(PlaygroundMasterRecord):
    sku: StrictStr = Field(min_length=1, max_length=128)
    unit: StrictStr = Field(min_length=1, max_length=32)


class PlaygroundLocationRecord(PlaygroundMasterRecord):
    type: StrictStr = Field(min_length=1, max_length=64)


class PlaygroundMasterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[dict] = Field(min_length=1, max_length=1)


def validate_master_input(tool: str, arguments: dict) -> dict:
    """Allow one basic record, never source configuration or unrelated fields."""
    parsed = PlaygroundMasterInput.model_validate(arguments)
    family, mode = tool.split("_")
    model = {
        "party": PlaygroundPartyRecord,
        "item": PlaygroundItemRecord,
        "location": PlaygroundLocationRecord,
    }[family]
    record = model.model_validate(parsed.records[0]).model_dump(exclude_none=True)
    if (mode == "update") != ("id" in record):
        raise ValueError("Only updates require an existing record ID.")
    if mode == "create" and "expected_revision" in record:
        raise ValueError("Creation has no previous revision.")
    return {"records": [record]}


class PlaygroundInvoiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_line_id: StrictStr = Field(min_length=1, max_length=128)
    number: StrictStr = Field(min_length=1, max_length=128)
    quantity: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    gross_amount: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    effective_at: AwareDatetime | None = None


class PlaygroundPaymentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invoice_id: StrictStr = Field(min_length=1, max_length=128)
    payment_number: StrictStr = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False)
    effective_at: AwareDatetime | None = None


class PlaygroundReleaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reservation_id: StrictStr = Field(min_length=1, max_length=128)


class PlaygroundRefundInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credit_note_id: StrictStr = Field(min_length=1, max_length=128)
    refund_number: StrictStr = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False)
    effective_at: AwareDatetime | None = None


class OpeningStockInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    movement_type: Literal["opening_stock"]
    item_id: StrictStr = Field(min_length=1, max_length=128)
    to_location_id: StrictStr = Field(min_length=1, max_length=128)
    quantity: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    occurred_at: AwareDatetime | None = None

    @field_validator("occurred_at")
    @classmethod
    def normalize_time(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value is not None else None


class PlaygroundReceiptInput(OpeningStockInput):
    movement_type: Literal["receipt"]
    commitment_id: StrictStr = Field(min_length=1, max_length=128)
    from_location_id: None = None


class PlaygroundReturnInput(PlaygroundReceiptInput):
    movement_type: Literal["return"]


class PlaygroundOrderInput(BaseModel):
    """Small sales or purchase order used by the guided lessons."""

    model_config = ConfigDict(extra="forbid")

    direction: Literal["sales", "purchase"]
    number: StrictStr = Field(min_length=1, max_length=128)
    company_party_id: StrictStr = Field(min_length=1, max_length=128)
    counterparty_id: StrictStr = Field(min_length=1, max_length=128)
    location_id: StrictStr = Field(min_length=1, max_length=128)
    item_id: StrictStr = Field(min_length=1, max_length=128)
    quantity: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    unit_price: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    currency: StrictStr = Field(default="EUR", min_length=3, max_length=3)


class PlaygroundOrderProposalInput(BaseModel):
    """Normalized order arguments persisted in a ChangeProposal."""

    model_config = ConfigDict(extra="forbid")

    direction: Literal["sales", "purchase"]
    number: StrictStr = Field(min_length=1, max_length=128)
    company_party_id: StrictStr = Field(min_length=1, max_length=128)
    counterparty_id: StrictStr = Field(min_length=1, max_length=128)
    location_id: StrictStr = Field(min_length=1, max_length=128)
    lines: list[dict]
    gross_amount: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    currency: StrictStr = Field(default="EUR", min_length=3, max_length=3)


class PlaygroundReservationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commitment_id: StrictStr = Field(min_length=1, max_length=128)
    quantity: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )


class PlaygroundShipmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    movement_type: Literal["shipment"]
    item_id: StrictStr = Field(min_length=1, max_length=128)
    from_location_id: StrictStr = Field(min_length=1, max_length=128)
    commitment_id: StrictStr = Field(min_length=1, max_length=128)
    to_location_id: None = None
    quantity: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False
    )
    occurred_at: AwareDatetime | None = None

    @field_validator("occurred_at")
    @classmethod
    def normalize_time(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value is not None else None
