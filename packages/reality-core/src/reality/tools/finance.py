"""Typed finance account tools shared by all adapters."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, TypeAdapter

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
        "bad_debt_expense",
        "dunning_fee_revenue",
        "payment_fee_expense",
        "carrier_claim_income",
        "opening_counterpart",
        "customer_down_payments",
        "exchange_difference",
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
    from reality.services.intake import _invoke

    return _invoke(
        f"finance_account_{name.rsplit('.', 1)[1]}",
        ACCOUNT_COMMANDS[name][1],
        session,
        tenant_id,
        **values,
        action_id=action_id,
        _commit=False,
    )


class AdjustmentRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    invoice_id: str = Field(min_length=1)
    amount: str
    reason_category: Literal[
        "early_payment_discount",
        "agreed_deduction",
        "accepted_small_remainder",
        "bad_debt",
        "payment_fee",
    ]
    reason: str = Field(min_length=1, max_length=4000)
    agreement: str = Field(default="", max_length=4000)
    source_record_id: str | None = Field(default=None, min_length=1)
    source_effect_id: str | None = Field(default=None, min_length=1, max_length=200)


ADJUSTMENT_COMMAND = "finance.adjustment.accept"
SETTLEMENT_COMMAND = "finance.settlement.apply"
OPENING_COMMAND = "finance.opening.import"
DUNNING_COMMAND = "finance.dunning.record"
DUNNING_REVERSE_COMMAND = "finance.dunning.reverse"
DUNNING_SCHEDULE_COMMAND = "finance.dunning.schedule.set"
DUNNING_RUN_COMMAND = "finance.dunning.run"
PAYMENT_RETURN_COMMAND = "finance.payment.return"
COLLECTION_HANDOVER_COMMAND = "finance.dunning.collection.handover"
DEPOSIT_RECORD_COMMAND = "finance.deposit.record"
DEPOSIT_CLEAR_COMMAND = "finance.deposit.clear"
PAYOUT_SETTLE_COMMAND = "finance.payout.settle"
AUTHORIZATION_RECORD_COMMAND = "finance.payment.authorization.record"
CAPTURE_RECORD_COMMAND = "finance.payment.capture.record"


class DunningRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    invoice_ids: list[str] = Field(min_length=1, max_length=100)
    level: Literal[1, 2, 3]
    notice_date: str
    fee_amount: str = "0"
    reason: str = Field(default="", max_length=4000)
    number: str = Field(default="", max_length=200)


class DunningReverseRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    notice_id: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=4000)


class DunningScheduleLevelRequest(BaseModel):
    # Strict, so `true` or `7.0` reach the service as stated and are refused
    # there with a code instead of being coerced into a schedule.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    level: StrictInt
    wait_days: StrictInt | StrictStr
    fee_amount: StrictStr | StrictInt = "0"


class DunningScheduleRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    levels: list[DunningScheduleLevelRequest] = Field(max_length=3)


class DunningRunItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    invoice_id: str = Field(min_length=1)
    level: StrictInt = Field(ge=1, le=3)


class DunningRunRequest(BaseModel):
    # No finance revision: every payment raises it, and a payment since the review
    # must skip its item, not refuse the run. The schedule is what the review pins.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    schedule_source_record_id: str = Field(min_length=1)
    run_date: str
    party_ids: list[str] = Field(default_factory=list, max_length=500)
    items: list[DunningRunItemRequest] = Field(min_length=1, max_length=500)


class PaymentReturnRequest(BaseModel):
    # No finance revision: every posting raises it; the return re-checks the
    # payment under the finance lock instead.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    payment_document_id: str = Field(min_length=1)
    kind: Literal["direct_debit_return", "chargeback"]
    returned_on: str
    reason: str = Field(max_length=4000)
    reference: str = Field(default="", max_length=200)
    fee_amount: StrictStr | StrictInt = "0"
    fee_bearer: Literal["customer", "company", "none"] | None = None


class PayoutReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    type: Literal[
        "invoice_number",
        "shop_id",
        "shop_order_number",
        "customer_reference",
        "customer_number",
        "tracking_number",
    ] = Field(
        description="What the stated value identifies; a tracking number names a shipment."
    )
    value: str = Field(
        min_length=1,
        max_length=200,
        description="The identifier exactly as the provider states it; looked up, never stored as a link.",
    )


class PayoutLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    line_id: str = Field(
        min_length=1,
        max_length=200,
        description="The provider's own identity of the line, unique within the statement.",
    )
    kind: Literal["charge", "refund", "chargeback", "fee"] = Field(
        description="A charge the provider collected, a refund or chargeback it paid back, or a fee it kept."
    )
    amount: StrictStr | StrictInt = Field(
        description="The positive amount the line states; its kind gives the sign."
    )
    references: list[PayoutReferenceRequest] = Field(
        default_factory=list,
        max_length=10,
        description="The order, invoice or shipment the line names; a fee may name none.",
    )
    reason: str = Field(
        default="",
        max_length=4000,
        description="The provider's stated reason, kept on a chargeback.",
    )


class PayoutSettleRequest(BaseModel):
    # No finance revision: a statement settles under the finance lock, and every
    # line is resolved again there (spec 336).
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    provider_party_id: str = Field(
        min_length=1,
        description="The marketplace, provider or carrier Party that paid.",
    )
    payout_reference: str = Field(
        min_length=1,
        max_length=200,
        description="The provider's payout identity; settling the same statement again books only unbooked lines.",
    )
    paid_on: str = Field(description="Calendar date the payout reached the bank.")
    currency: str = Field(
        pattern=r"^[A-Z]{3}$", description="Currency of the payout and its lines."
    )
    amount: StrictStr | StrictInt = Field(
        description="The net payout the provider states; the lines must add up to it."
    )
    clearing_account_id: str = Field(
        min_length=1,
        description="The active cash account that holds the provider's balance, apart from the bank.",
    )
    bank_account_id: str | None = Field(
        default=None,
        min_length=1,
        description="The cash account the payout reached; the cash default when omitted.",
    )
    lines: list[PayoutLineRequest] = Field(
        min_length=1,
        max_length=2000,
        description="Every line of the payout statement as the provider states it.",
    )


class AuthorizationRecordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    order_document_id: str = Field(
        min_length=1,
        description="Opaque same-tenant identity of the authorized sales order.",
    )
    amount: StrictStr | StrictInt = Field(
        description="The amount the provider authorized."
    )
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="The order's currency.")
    authorized_at: str = Field(
        description="When the provider authorized, as an ISO date-time."
    )
    valid_until: str = Field(
        description="When the authorization lapses as the provider states it, as an ISO date-time."
    )
    reference: str = Field(
        min_length=1,
        max_length=200,
        description="The provider's authorization identity, once per order.",
    )


class CaptureRecordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    authorization_id: str = Field(
        min_length=1,
        description="Opaque same-tenant identity of the recorded authorization.",
    )
    amount: StrictStr | StrictInt = Field(
        description="The amount captured; never more than is left of the authorization."
    )
    captured_at: str = Field(
        description="When the provider captured, as an ISO date-time."
    )
    reference: str = Field(
        default="",
        max_length=200,
        description="The provider's capture identity, as stated.",
    )


class CollectionHandoverRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    invoice_ids: list[str] = Field(min_length=1, max_length=100)
    handover_date: str
    reason: str = Field(max_length=4000)


class DepositRecordRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    side: Literal["customer", "supplier"]
    party_id: str = Field(min_length=1)
    amount: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    reference: str = Field(min_length=1, max_length=200)
    effective_at: str


class DepositClearRequest(AccountRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    deposit_document_id: str = Field(min_length=1)
    invoice_id: str = Field(min_length=1)
    amount: str


EDGE_COMMANDS = {
    DUNNING_COMMAND: DunningRequest,
    DUNNING_REVERSE_COMMAND: DunningReverseRequest,
    DUNNING_SCHEDULE_COMMAND: DunningScheduleRequest,
    DUNNING_RUN_COMMAND: DunningRunRequest,
    COLLECTION_HANDOVER_COMMAND: CollectionHandoverRequest,
    PAYMENT_RETURN_COMMAND: PaymentReturnRequest,
    DEPOSIT_RECORD_COMMAND: DepositRecordRequest,
    DEPOSIT_CLEAR_COMMAND: DepositClearRequest,
    PAYOUT_SETTLE_COMMAND: PayoutSettleRequest,
    AUTHORIZATION_RECORD_COMMAND: AuthorizationRecordRequest,
    CAPTURE_RECORD_COMMAND: CaptureRecordRequest,
}


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
    *EDGE_COMMANDS,
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
        "early_payment_discount",
        "agreed_deduction",
        "accepted_small_remainder",
        "bad_debt",
        "payment_fee",
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
        if name in EDGE_COMMANDS:
            return EDGE_COMMANDS[name].model_validate(arguments).model_dump()
        return AdjustmentRequest.model_validate(arguments).model_dump()
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error


def execute_finance_command(
    session, tenant_id, name, arguments, *, action_id, actor_id=None
):
    from reality.services.tenant_policy import require_finance_configuration

    require_finance_configuration(
        session, tenant_id, "execute_finance_command", locals()
    )
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
    if name == DUNNING_COMMAND:
        from reality.services.dunning import record_notice

        values = validate_finance_request(name, arguments)
        return record_notice(
            session,
            tenant_id,
            **values,
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == DUNNING_REVERSE_COMMAND:
        from reality.services.dunning import reverse_notice

        return reverse_notice(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == DUNNING_SCHEDULE_COMMAND:
        from reality.services.dunning_runs import set_schedule

        return set_schedule(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == DUNNING_RUN_COMMAND:
        from reality.services.dunning_runs import confirm_run

        return confirm_run(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == PAYMENT_RETURN_COMMAND:
        from reality.services.payment_returns import record_return

        return record_return(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == PAYOUT_SETTLE_COMMAND:
        from reality.services.payouts import settle_payout

        return settle_payout(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == AUTHORIZATION_RECORD_COMMAND:
        from reality.services.payment_authorizations import record_authorization

        return record_authorization(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == CAPTURE_RECORD_COMMAND:
        from reality.services.payment_authorizations import record_capture

        return record_capture(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == COLLECTION_HANDOVER_COMMAND:
        from reality.services.dunning_runs import record_handover

        return record_handover(
            session,
            tenant_id,
            **validate_finance_request(name, arguments),
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == DEPOSIT_RECORD_COMMAND:
        from reality.services.finance.deposits import record_deposit

        values = validate_finance_request(name, arguments)
        return record_deposit(
            session,
            tenant_id,
            **values,
            action_id=action_id,
            actor_id=actor_id,
        )
    if name == DEPOSIT_CLEAR_COMMAND:
        from reality.services.finance.deposits import clear_deposit

        values = validate_finance_request(name, arguments)
        return clear_deposit(session, tenant_id, **values, action_id=action_id)
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
