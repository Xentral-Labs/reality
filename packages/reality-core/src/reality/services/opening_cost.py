"""Opening stock's stated acquisition cost as source evidence (spec 282 US3).

The person states the total acquisition value their evidence shows (an inventory list,
an import document) together with a reference to it. It is recorded as received, in a
SourceRecord the opening Movement points to; nothing here derives a unit cost or any
other figure (Constitution VIII).
"""

from decimal import Decimal
from decimal import InvalidOperation as DecimalError
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import SourceRecord
from reality.services.core import InvalidOperation, store_source_record

SOURCE_SYSTEM = "reality"
SOURCE_TYPE = "opening_cost_statement"
FIELDS = {"amount", "currency", "evidence_reference"}


def normalize_opening_cost(value: Any) -> dict[str, str]:
    """Accept exactly the stated amount, its currency and the evidence reference."""
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise InvalidOperation(
            "Opening cost needs the stated amount, currency and evidence reference."
        )
    try:
        amount = Decimal(str(value["amount"]))
    except (DecimalError, TypeError, ValueError) as error:
        raise InvalidOperation("Enter the acquisition value as a number.") from error
    if not amount.is_finite() or amount < 0 or amount >= Decimal(10) ** 14:
        raise InvalidOperation("Enter a non-negative acquisition value.")
    if amount != amount.quantize(Decimal("0.0001")):
        raise InvalidOperation(
            "The acquisition value supports at most 4 decimal places."
        )
    currency = str(value["currency"]).strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise InvalidOperation("Enter a three-letter currency code.")
    reference = str(value["evidence_reference"]).strip()
    if not reference or len(reference) > 500:
        raise InvalidOperation("Name the evidence the acquisition value comes from.")
    # The amount is kept exactly as written, so the statement reads as received.
    return {
        "amount": str(value["amount"]).strip(),
        "currency": currency,
        "evidence_reference": reference,
    }


def record_opening_cost_statement(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    item_id: str,
    quantity: str,
    opening_cost: dict[str, str],
) -> SourceRecord:
    """Store the statement once per confirmed opening proposal."""
    record, _, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        action_id,
        {
            **normalize_opening_cost(opening_cost),
            "item_id": item_id,
            "quantity": quantity,
        },
    )
    return record


def is_statement_of(
    session: Session, tenant_id: str, source_record_id: str | None, action_id: str
) -> bool:
    """Whether a movement's source is the statement this opening proposal recorded."""
    if source_record_id is None:
        return False
    return (
        session.scalar(
            select(SourceRecord.id).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == source_record_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.source_type == SOURCE_TYPE,
                SourceRecord.external_id == action_id,
            )
        )
        is not None
    )
