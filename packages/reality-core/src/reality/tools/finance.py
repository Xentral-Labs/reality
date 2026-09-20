"""Typed finance account tools shared by all adapters."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from reality.domain.target_mappings import COMMANDS as TARGET_COMMANDS
from reality.services.finance import accounts


class AccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int


class CreateAccount(AccountRequest):
    code: str
    name: str
    role: Literal[
        "accounts_receivable",
        "accounts_payable",
        "cash",
        "sales_revenue",
        "inventory",
        "customer_reduction",
        "supplier_reduction",
        "opening_counterpart",
    ]


class UpdateAccount(AccountRequest):
    account_id: str
    code: str | None = None
    name: str | None = None
    state: Literal["active", "blocked"] | None = None


class DefaultAccount(AccountRequest):
    role: str
    account_id: str


ACCOUNT_COMMANDS = {
    "finance.account.initialize": (AccountRequest, accounts.initialize_accounts),
    "finance.account.create": (CreateAccount, accounts.create_account),
    "finance.account.update": (UpdateAccount, accounts.update_account),
    "finance.account.set_default": (DefaultAccount, accounts.set_default_account),
}


def validate_request(name, arguments):
    from pydantic import ValidationError

    from reality.services.core import InvalidOperation

    try:
        return ACCOUNT_COMMANDS[name][0].model_validate(arguments).model_dump()
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error


def execute_account_command(session, tenant_id, name, arguments, *, action_id):
    values = validate_request(name, arguments)
    return ACCOUNT_COMMANDS[name][1](
        session, tenant_id, **values, action_id=action_id, _commit=False
    )


class AdjustmentRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    invoice_id: str = Field(min_length=1)
    amount: str
    reason_category: Literal[
        "early_payment_discount", "agreed_deduction", "accepted_small_remainder"
    ]
    reason: str = Field(min_length=1, max_length=4000)
    agreement: str = Field(default="", max_length=4000)
    source_record_id: str | None = Field(default=None, min_length=1)
    source_effect_id: str | None = Field(default=None, min_length=1, max_length=200)


ADJUSTMENT_COMMAND = "finance.adjustment.accept"
SETTLEMENT_COMMAND = "finance.settlement.apply"
OPENING_COMMAND = "finance.opening.import"


class CreateReference(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    kind: Literal["cost_center", "case_code", "coding_group"]
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=4000)


class UpdateReference(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reference_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    state: Literal["active", "blocked"]
    reason: str = Field(min_length=1, max_length=4000)


REFERENCE_COMMANDS = {
    "finance.reference.create": CreateReference,
    "finance.reference.update": UpdateReference,
}


class ComponentPart(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    cost_center_reference_id: str = Field(min_length=1)
    amount: str


class AssignmentRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    document_id: str = Field(min_length=1)
    document_line_id: str | None = None
    basis: Literal["net", "gross", "base"]
    expected_evidence_hash: str = Field(min_length=64, max_length=64)
    case_reference_id: str | None = None
    group_reference_id: str | None = None
    parts: list[ComponentPart] = Field(default_factory=list, max_length=100)
    reason: str = Field(min_length=1, max_length=4000)


ASSIGNMENT_COMMAND = "finance.component.assign"


class SourceMappingRequest(AccountRequest):
    source_system_id: str = Field(min_length=1)
    namespace: str = Field(min_length=1, max_length=200)
    field_kind: Literal["case_code", "coding_group"]
    source_code: str = Field(min_length=1, max_length=200)
    reference_id: str = Field(min_length=1)
    state: Literal["active", "blocked"] = "active"
    reason: str = Field(min_length=1, max_length=4000)


SOURCE_MAPPING_COMMAND = "finance.source_mapping.set"
FINANCE_COMMANDS = {
    "cost.change",
    *TARGET_COMMANDS,
    SOURCE_MAPPING_COMMAND,
    ASSIGNMENT_COMMAND,
    *REFERENCE_COMMANDS,
    *ACCOUNT_COMMANDS,
    ADJUSTMENT_COMMAND,
    SETTLEMENT_COMMAND,
    OPENING_COMMAND,
}


class OpeningRow(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    party_id: str = Field(min_length=1)
    direction: Literal[
        "customer_debt", "customer_credit", "supplier_debt", "supplier_credit"
    ]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: str
    external_item_key: str = Field(min_length=1, max_length=200)
    reference: str = Field(default="", max_length=200)
    original_document_date: str | None = None
    due_date: str | None = None
    original_total: str | None = None
    source_record_id: str | None = Field(default=None, min_length=1)


class OpeningRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_namespace: str = Field(min_length=1, max_length=200)
    snapshot_key: str = Field(min_length=1, max_length=200)
    cutover_date: str
    coverage_kind: Literal["individual", "summary"]
    reason: str = Field(min_length=1, max_length=4000)
    items: list[OpeningRow] = Field(min_length=1, max_length=100)


class StatedReduction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    amount: str
    reason_category: Literal[
        "early_payment_discount", "agreed_deduction", "accepted_small_remainder"
    ]
    reason: str = Field(min_length=1, max_length=4000)
    agreement: str = Field(default="", max_length=4000)
    source_record_id: str | None = Field(default=None, min_length=1)
    source_effect_id: str | None = Field(default=None, min_length=1, max_length=200)


class SettlementBase(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    document_id: str = Field(min_length=1)
    amount: str


class CashSettlement(SettlementBase):
    reference: str = Field(min_length=1, max_length=200)
    effective_at: str = Field(min_length=1)
    source_record_id: str | None = Field(default=None, min_length=1)
    source_effect_id: str | None = Field(default=None, min_length=1, max_length=200)


class PaymentSettlement(CashSettlement):
    mode: Literal["payment"]
    allocation_amount: str
    reduction: StatedReduction | None = None


class CreditAllocation(SettlementBase):
    mode: Literal["allocate_credit"]
    invoice_id: str = Field(min_length=1)


class CreditRefund(CashSettlement):
    mode: Literal["refund_credit"]


SETTLEMENT_REQUEST = TypeAdapter(
    Annotated[
        PaymentSettlement | CreditAllocation | CreditRefund, Field(discriminator="mode")
    ]
)


def validate_finance_request(name, arguments):
    if name in TARGET_COMMANDS:
        from reality.services.finance.target_mappings import validate

        return validate(name, arguments)
    if name in ACCOUNT_COMMANDS:
        return validate_request(name, arguments)
    from pydantic import ValidationError

    from reality.services.core import InvalidOperation

    try:
        if name == "cost.change":
            from reality.domain.costing import CHANGE

            return CHANGE.validate_python(arguments).model_dump(mode="json")
        if name == SOURCE_MAPPING_COMMAND:
            return SourceMappingRequest.model_validate(arguments).model_dump()
        if name == ASSIGNMENT_COMMAND:
            return AssignmentRequest.model_validate(arguments).model_dump()
        if name in REFERENCE_COMMANDS:
            return REFERENCE_COMMANDS[name].model_validate(arguments).model_dump()
        if name == OPENING_COMMAND:
            return OpeningRequest.model_validate(arguments).model_dump()
        if name == SETTLEMENT_COMMAND:
            return SETTLEMENT_REQUEST.validate_python(arguments).model_dump()
        return AdjustmentRequest.model_validate(arguments).model_dump()
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error


def execute_finance_command(
    session, tenant_id, name, arguments, *, action_id, actor_id=None
):
    if name == "cost.change":
        from reality.services.costing import execute_cost_change

        return execute_cost_change(
            session,
            tenant_id,
            arguments=arguments,
            action_id=action_id,
            actor_id=actor_id,
            confirmed=True,
        )
    if name in TARGET_COMMANDS:
        from reality.services.finance.target_mappings import (
            maintain_target_configuration,
        )

        return maintain_target_configuration(
            session,
            tenant_id,
            command=name,
            arguments=arguments,
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == SOURCE_MAPPING_COMMAND:
        from reality.services.finance.source_mappings import set_source_mapping

        return set_source_mapping(
            session,
            tenant_id,
            arguments=validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == ASSIGNMENT_COMMAND:
        from reality.services.finance.components import assign_component

        return assign_component(
            session,
            tenant_id,
            arguments=validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name in REFERENCE_COMMANDS:
        from reality.services.finance.references import maintain_reference

        return maintain_reference(
            session,
            tenant_id,
            arguments=validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == OPENING_COMMAND:
        from reality.services.finance.opening import import_opening

        return import_opening(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == SETTLEMENT_COMMAND:
        from reality.services.finance.settlement_flows import apply_settlement

        return apply_settlement(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name in ACCOUNT_COMMANDS:
        return execute_account_command(
            session, tenant_id, name, arguments, action_id=action_id
        )
    from reality.services.finance.settlement import accept_adjustment

    return accept_adjustment(
        session,
        tenant_id,
        **validate_finance_request(name, arguments),
        action_id=action_id,
        actor_id=actor_id,
    )


def settlement_input_schema() -> dict:
    """Expose an object tool envelope; mode-specific requirements are enforced at execution."""
    schemas = [
        model.model_json_schema()
        for model in (PaymentSettlement, CreditAllocation, CreditRefund)
    ]
    properties = {
        key: value for schema in schemas for key, value in schema["properties"].items()
    }
    properties["mode"] = {
        "type": "string",
        "enum": ["payment", "allocate_credit", "refund_credit"],
        "description": "Payment requires allocation_amount, reference and effective_at; allocate_credit requires invoice_id; refund_credit requires reference and effective_at. Only payment accepts reduction. Cash evidence fields are only for payment/refund.",
    }
    return {
        "type": "object",
        "properties": properties,
        "required": ["mode", "document_id", "expected_revision", "amount"],
        "additionalProperties": False,
        "$defs": {
            key: value
            for schema in schemas
            for key, value in schema.get("$defs", {}).items()
        },
    }
