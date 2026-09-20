"""Typed cost tools delegate all accounting semantics to the shared service."""

from pydantic import ValidationError

from reality.domain.costing import (
    Assign,
    CommercialMatchRead,
    CommercialMatchReview,
    ContributionBatchReview,
    ContributionRead,
    ContributionReview,
    EvidenceRead,
    InventoryBatchReview,
    InventoryRead,
    InventoryReview,
    ReceiptRead,
    Replace,
    Review,
    ReviewedContributionRead,
    SellingAssign,
    Withdraw,
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
    """Expose a tool object; the discriminated domain model validates each operation."""
    schemas = [
        model.model_json_schema()
        for model in (
            Assign,
            Replace,
            Review,
            Withdraw,
            InventoryReview,
            InventoryBatchReview,
            ContributionReview,
            ContributionBatchReview,
            CommercialMatchReview,
            SellingAssign,
        )
    ]
    properties = {
        key: value for schema in schemas for key, value in schema["properties"].items()
    }
    properties["document_line_id"] = Assign.model_json_schema()["properties"][
        "document_line_id"
    ]
    properties["tax_treatment"] = Assign.model_json_schema()["properties"][
        "tax_treatment"
    ]
    properties["parts"] = {
        "type": "array",
        "minItems": 1,
        "maxItems": 100,
        "items": {
            "anyOf": [{"$ref": "#/$defs/CostPart"}, {"$ref": "#/$defs/SellingPart"}]
        },
    }
    properties["operation"] = {
        "type": "string",
        "enum": [
            "assign",
            "replace",
            "review",
            "withdraw",
            "inventory_review",
            "inventory_batch_review",
            "contribution_review",
            "contribution_batch_review",
            "commercial_match_review",
            "selling_assign",
        ],
        "description": "Assign received shares; replace requires fresh evidence and predecessor ID; review requires movement and all six categories; withdraw requires component basis ID. Inventory review requires an explicit FIFO policy, full history and ownership evidence, exact receipt reviews and economic issue identities. Inventory batch review requires 2–10 distinct scopes with the same cutoff, economic owner and currency, within 100 movements and 20 receipts in total; it confirms all scopes atomically. Contribution review requires the exact candidate hash, explicit commercial_v1/profile and revenue completeness confirmation, and the exact shipment economic time. Contribution batch review requires 2–10 distinct positions on one common confirmed inventory action, cutoff, economic owner and currency; all positions are confirmed atomically with independent selling coverage. Selling assign requires received supplier net evidence, recoverable/no-tax treatment, explicit selling-expense confirmation excluding acquisition/inventory/overhead, and exact sold-line shares. Contribution selling_categories optionally reviews all seven categories to finalize DB2. Every operation requires the current event sequence and a reason.",
    }
    return {
        "type": "object",
        "properties": properties,
        "required": ["operation", "expected_event_sequence", "reason"],
        "additionalProperties": False,
        "$defs": {
            key: value
            for schema in schemas
            for key, value in schema.get("$defs", {}).items()
        },
    }


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
