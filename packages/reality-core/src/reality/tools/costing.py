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
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate receipt cost evidence to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.receipt.result:
    Return receipt cost from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    try:
        request = ReceiptRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.receipt.result
    return costing.receipt_cost(session, tenant_id, **request.model_dump())


def evidence(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate cost evidence to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.evidence.result:
    Return cost evidence from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    try:
        request = EvidenceRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.evidence.result
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
            return {key: inline(item) for key, item in value.items() if key != "$defs"}
        if isinstance(value, list):
            return [inline(item) for item in value]
        return value

    result = inline(schema)
    result["type"] = "object"
    result["additionalProperties"] = False
    return result


def inventory(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate inventory cost evidence to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.inventory.result:
    Return inventory cost from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    try:
        request = InventoryRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.inventory.result
    return costing.inventory_cost(session, tenant_id, **request.model_dump())


def contribution(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate contribution preview to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.contribution.result:
    Return contribution preview from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    try:
        request = ContributionRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.contribution.result
    return costing.contribution_preview(session, tenant_id, **request.model_dump())


def reviewed_contribution(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate reviewed contribution evidence to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.reviewed_contribution.result:
    Return reviewed contribution from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    try:
        request = ReviewedContributionRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.reviewed_contribution.result
    return costing.reviewed_contribution(session, tenant_id, **request.model_dump())


def commercial_match(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate commercial matches to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.commercial_match.result:
    Return commercial match from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    try:
        request = CommercialMatchRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.commercial_match.result
    return costing.commercial_match(session, tenant_id, **request.model_dump())


def record(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate a selected cost record to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.record.result:
    Return cost record from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    from reality.domain.cost_records import CostRecordRead

    try:
        request = CostRecordRead.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.record.result
    return costing.cost_record(session, tenant_id, **request.model_dump())


def review_draft(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate a cost review draft to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.review_draft.result:
    Return cost review draft from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    from reality.domain.cost_review_draft import CostReviewDraftRequest

    try:
        request = CostReviewDraftRequest.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.review_draft.result
    return costing.cost_review_draft(
        session,
        tenant_id,
        kind=request.kind,
        scope_id=request.scope_id,
        answers=request.answers.model_dump(exclude_none=True)
        if request.answers
        else None,
    )


def query(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Validate the typed request and delegate a typed cost query to the shared costing service; keep calculation and refusal rules in that service.

    BUSINESS RULE tools.costing.query.result:
    Return cost query from the common costing service after typed request validation. The adapter does not calculate a second value or write a derived value as authority.
    """
    from reality.domain.cost_query import CostQueryRequest

    try:
        request = CostQueryRequest.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    # reality-rule: tools.costing.query.result
    return costing.cost_query(session, tenant_id, **request.model_dump())
