"""Typed cost tools delegate all accounting semantics to the shared service."""

from pydantic import ValidationError

from reality.domain.costing import (
    CHANGE,
    CommercialMatchRead,
    ContributionRead,
    EvidenceRead,
    InventoryRead,
    ReceiptRead,
    ReviewedContributionRead,
)
from reality.services import costing
from reality.services.core import InvalidOperation


def receipt(session, tenant_id, arguments):
    try:
        request = ReceiptRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.receipt_cost(session, tenant_id, **request.model_dump())


def evidence(session, tenant_id, arguments):
    try:
        request = EvidenceRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.cost_evidence(session, tenant_id, **request.model_dump())


def change_input_schema() -> dict:
    """Expose the exact discriminated domain union without cross-variant defaults."""
    schema = CHANGE.json_schema()
    definitions = schema.get("$defs", {})

    def inline(value):
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                return inline(definitions[reference.rsplit("/", 1)[-1]])
            return {
                key: inline(item)
                for key, item in value.items()
                if key != "$defs"
            }
        if isinstance(value, list):
            return [inline(item) for item in value]
        return value

    result = inline(schema)
    result["type"] = "object"
    return result


def inventory(session, tenant_id, arguments):
    try:
        request = InventoryRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.inventory_cost(session, tenant_id, **request.model_dump())


def contribution(session, tenant_id, arguments):
    try:
        request = ContributionRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.contribution_preview(session, tenant_id, **request.model_dump())


def reviewed_contribution(session, tenant_id, arguments):
    try:
        request = ReviewedContributionRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.reviewed_contribution(session, tenant_id, **request.model_dump())


def commercial_match(session, tenant_id, arguments):
    try:
        request = CommercialMatchRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.commercial_match(session, tenant_id, **request.model_dump())


def record(session, tenant_id, arguments):
    from reality.domain.cost_records import CostRecordRead

    try:
        request = CostRecordRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.cost_record(session, tenant_id, **request.model_dump())


def query(session, tenant_id, arguments):
    from reality.domain.cost_query import CostQueryRequest

    try:
        request = CostQueryRequest.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    return costing.cost_query(session, tenant_id, **request.model_dump())
