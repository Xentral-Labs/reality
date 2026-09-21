"""Server-side tenant-purpose restrictions, independent of role and transport.

The business-only boundary has no administrator, feature-flag or auth-disabled
override. The internal opening-stock decision scope permits one exact confirmed
action; it never grants business credentials, outbound delivery or other tools.
"""

import json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import event, select
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from reality.db.core import (
    AppUser,
    BusinessEvent,
    ChangeProposal,
    PlaygroundRun,
    PlaygroundStep,
    Tenant,
    TenantMembership,
)
from reality.playground.actions import (
    MASTER_TOOLS,
    OpeningStockInput,
    PlaygroundInvoiceInput,
    PlaygroundOrderProposalInput,
    PlaygroundPaymentInput,
    PlaygroundReceiptInput,
    PlaygroundRefundInput,
    PlaygroundReleaseInput,
    PlaygroundReservationInput,
    PlaygroundReturnInput,
    PlaygroundShipmentInput,
    validate_master_input,
)
from reality.services.account_policy import account_eligible, account_eligible_clause
from reality.services.core import InvalidOperation, NotFound


@dataclass(frozen=True)
class _SeedAuthority:
    session: Session
    transaction: object
    run_id: str
    user_id: str
    tenant_id: str


_seed_authority: ContextVar[_SeedAuthority | None] = ContextVar(
    "playground_seed", default=None
)
_chat_authority: ContextVar[tuple[Session, object, str] | None] = ContextVar(
    "playground_chat", default=None
)


def playground_chat_active(session: Session, tenant_id: str) -> bool:
    authority = _chat_authority.get()
    return authority == (session, session.get_transaction(), tenant_id)


@contextmanager
def playground_chat_scope(session: Session, user_id: str, run_id: str):
    """Allow one owner-scoped explanation, never a mutation or proposal."""
    run = require_playground_run(session, run_id, user_id)
    if run.status not in {"active", "archived"}:
        raise PlaygroundOperationDenied("Sandbox is not ready for questions.")
    token = _chat_authority.set((session, session.get_transaction(), run.tenant_id))
    try:
        yield run
    finally:
        _chat_authority.reset(token)


_SEED_OPERATIONS = frozenset(
    {
        "create_party",
        "create_item",
        "create_location",
        "create_master_source_record",
        "emit_business_event",
    }
)


@dataclass(frozen=True)
class _ProposalAuthority:
    session: Session
    transaction: object
    run_id: str
    user_id: str
    tenant_id: str
    tool_name: str
    intent: str


_proposal_authority: ContextVar[_ProposalAuthority | None] = ContextVar(
    "playground_proposal", default=None
)


@dataclass(frozen=True)
class _DecisionAuthority:
    session: Session
    connection: Connection
    run_id: str
    user_id: str
    tenant_id: str
    proposal_id: str
    operation: str
    intent: str


_decision_authority: ContextVar[_DecisionAuthority | None] = ContextVar(
    "playground_decision", default=None
)


@contextmanager
def _decision_scope(
    session: Session, run_id: str, user_id: str, proposal_id: str, operation: str
):
    """Internal decision permission on the already pinned operation connection."""
    run = require_playground_run(session, run_id, user_id, for_write=True)
    connection = session.connection()
    proposal = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == run.tenant_id, ChangeProposal.id == proposal_id
        )
    )
    step = session.scalar(
        select(PlaygroundStep).where(
            PlaygroundStep.tenant_id == run.tenant_id,
            PlaygroundStep.run_id == run.id,
            PlaygroundStep.proposal_id == proposal_id,
        )
    )
    if (
        not isinstance(connection, Connection)
        or operation not in {"proposal_execute", "proposal_reject"}
        or proposal is None
        or step is None
        or (operation == "proposal_execute" and step.before_observation is None)
        or proposal.type
        not in {f"tool:{tool}" for tool in MASTER_TOOLS}
        | {
            "tool:movement_create",
            "tool:order_create",
            "tool:reserve",
            "tool:reservation_release",
            "tool:sales_invoice_record",
            "tool:customer_payment_post",
            "tool:supplier_invoice_record",
            "tool:supplier_payment_post",
            "tool:sales_credit_record",
            "tool:customer_refund_post",
        }
    ):
        raise PlaygroundOperationDenied("Unsupported Playground decision scope.")
    if proposal.type.removeprefix("tool:") in MASTER_TOOLS:
        validate_master_input(
            proposal.type.removeprefix("tool:"), json.loads(proposal.input)
        )
    elif proposal.type == "tool:movement_create":
        movement_type = json.loads(proposal.input).get("movement_type")
        if movement_type not in {"opening_stock", "shipment", "receipt", "return"}:
            raise PlaygroundOperationDenied("Unsupported Playground decision scope.")
        if movement_type == "return":
            PlaygroundReturnInput.model_validate_json(proposal.input)
        elif movement_type == "receipt":
            PlaygroundReceiptInput.model_validate_json(proposal.input)
        elif movement_type == "shipment":
            PlaygroundShipmentInput.model_validate_json(proposal.input)
        else:
            OpeningStockInput.model_validate_json(proposal.input)
    elif proposal.type == "tool:reservation_release":
        PlaygroundReleaseInput.model_validate_json(proposal.input)
    elif proposal.type == "tool:order_create":
        PlaygroundOrderProposalInput.model_validate_json(proposal.input)
    elif proposal.type in {
        "tool:sales_invoice_record",
        "tool:supplier_invoice_record",
        "tool:sales_credit_record",
    }:
        PlaygroundInvoiceInput.model_validate_json(proposal.input)
    elif proposal.type == "tool:customer_refund_post":
        PlaygroundRefundInput.model_validate_json(proposal.input)
    elif proposal.type in {"tool:customer_payment_post", "tool:supplier_payment_post"}:
        PlaygroundPaymentInput.model_validate_json(proposal.input)
    else:
        PlaygroundReservationInput.model_validate_json(proposal.input)
    token = _decision_authority.set(
        _DecisionAuthority(
            session,
            connection,
            run_id,
            user_id,
            run.tenant_id,
            proposal_id,
            operation,
            proposal.input,
        )
    )
    try:
        yield
    finally:
        _decision_authority.reset(token)


def _current_decision(session: Session, tenant_id: str) -> _DecisionAuthority | None:
    authority = _decision_authority.get()
    if authority is None:
        return None
    current_connection = session.connection()

    def backend_connection(connection: Connection):
        # A Session may create a fresh SQLAlchemy Connection wrapper after a
        # commit while retaining the same DBAPI connection.  The decision is
        # pinned to that backend connection, not to a transient wrapper.
        raw = connection.connection
        return getattr(raw, "driver_connection", raw)

    if (
        authority.session is not session
        or authority.tenant_id != tenant_id
        or backend_connection(current_connection)
        is not backend_connection(authority.connection)
        or authority.connection.closed
        or authority.connection.invalidated
    ):
        raise PlaygroundOperationDenied(
            "Playground decision context is no longer valid."
        )
    require_playground_run(session, authority.run_id, authority.user_id, for_write=True)
    return authority


def require_proposal_decision(
    session: Session, tenant_id: str, proposal_id: str, operation: str
) -> None:
    authority = _current_decision(session, tenant_id)
    if (
        authority
        and authority.proposal_id == proposal_id
        and authority.operation == operation
    ):
        return
    with session.no_autoflush:
        playground_step = session.scalar(
            select(PlaygroundStep.id).where(
                PlaygroundStep.tenant_id == tenant_id,
                PlaygroundStep.proposal_id == proposal_id,
            )
        )
        # Spec 182: a Storyline chapter is a step of a practice run and is decided
        # through the ordinary practice-company path, not the lesson decision scope.
        storyline_step = playground_step is not None and session.scalar(
            select(PlaygroundRun.storyline_key)
            .join(
                PlaygroundStep,
                (PlaygroundStep.run_id == PlaygroundRun.id)
                & (PlaygroundStep.tenant_id == PlaygroundRun.tenant_id),
            )
            .where(PlaygroundStep.id == playground_step)
        )
    if playground_step is not None and not storyline_step:
        raise PlaygroundOperationDenied("Review this action in its Playground run.")
    require_business_operation(session, tenant_id, operation)


def require_decision_action(
    session: Session,
    tenant_id: str,
    action_id: str | None,
    *,
    event_type: str | None = None,
) -> None:
    """Prevent a permitted handler from losing or substituting its causal identity."""
    authority = _current_decision(session, tenant_id)
    order_decision = (
        authority is not None
        and session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == authority.proposal_id,
            )
        )
        == "tool:order_create"
    )
    finance_decision = authority is not None and session.scalar(
        select(ChangeProposal.type).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == authority.proposal_id,
        )
    ) in {
        "tool:sales_invoice_record",
        "tool:customer_payment_post",
        "tool:supplier_invoice_record",
        "tool:supplier_payment_post",
        "tool:sales_credit_record",
        "tool:customer_refund_post",
    }
    reserve_decision = (
        authority is not None
        and session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == authority.proposal_id,
            )
        )
        == "tool:reserve"
    )
    master_type = (
        session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == authority.proposal_id,
            )
        )
        if authority is not None
        else None
    )
    master_decision = master_type in {f"tool:{tool}" for tool in MASTER_TOOLS}
    if master_decision:
        family, mode = master_type.removeprefix("tool:").split("_")
        if (
            action_id != authority.proposal_id
            or event_type != f"{family}.{'created' if mode == 'create' else 'updated'}"
        ):
            raise PlaygroundOperationDenied(
                "Master-data event must match its reviewed action."
            )
        return
    release_decision = (
        authority is not None
        and session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == authority.proposal_id,
            )
        )
        == "tool:reservation_release"
    )
    if release_decision and event_type not in {None, "reservation.released"}:
        raise PlaygroundOperationDenied(
            "Reservation release cannot emit another event type."
        )
    shipment_decision = (
        authority is not None
        and session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == authority.proposal_id,
            )
        )
        == "tool:movement_create"
        and json.loads(authority.intent).get("movement_type") == "shipment"
    )
    receipt_decision = (
        authority is not None
        and json.loads(authority.intent).get("movement_type") == "receipt"
    )
    if authority is not None and (
        (authority.proposal_id != action_id and not shipment_decision)
        or (
            event_type is not None
            and not order_decision
            and not reserve_decision
            and not (release_decision and event_type == "reservation.released")
            and not (
                master_type
                in {"tool:sales_invoice_record", "tool:supplier_invoice_record"}
                and event_type == "invoice.recorded"
            )
            and not shipment_decision
            and not (
                receipt_decision
                and event_type in {"movement.recorded", "commitment.fulfilled"}
            )
            and not (
                finance_decision
                and event_type
                in {
                    "source_record.stored",
                    "document.recorded",
                    "ledger.posted",
                    "settlement.allocated",
                }
            )
            and event_type != "movement.recorded"
        )
    ):
        raise PlaygroundOperationDenied(
            "Playground action identity does not match the confirmed proposal."
        )


def require_decision_release(
    session: Session, tenant_id: str, reservation_id: str, action_id: str | None
) -> None:
    """Only the reservation in the confirmed proposal may be released."""
    authority = _current_decision(session, tenant_id)
    if authority is None:
        return
    if (
        action_id != authority.proposal_id
        or json.loads(authority.intent) != {"reservation_id": reservation_id}
        or session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == authority.proposal_id,
            )
        )
        != "tool:reservation_release"
    ):
        raise PlaygroundOperationDenied(
            "Reservation does not match the confirmed Playground review."
        )


def require_decision_finance(
    session: Session, tenant_id: str, tool: str, actual: dict, action_id: str | None
) -> None:
    """Bind the shared finance entry point to the exact reviewed sandbox intent."""
    authority = _current_decision(session, tenant_id)
    if authority is None:
        return
    model = (
        PlaygroundInvoiceInput
        if tool
        in {"sales_invoice_record", "supplier_invoice_record", "sales_credit_record"}
        else PlaygroundRefundInput
        if tool == "customer_refund_post"
        else PlaygroundPaymentInput
    )
    expected = model.model_validate_json(authority.intent).model_dump(
        mode="json", exclude_none=True
    )
    supplied = model.model_validate(actual).model_dump(mode="json", exclude_none=True)
    if (
        action_id != authority.proposal_id
        or expected != supplied
        or session.scalar(
            select(BusinessEvent.id)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == action_id,
                BusinessEvent.event_type == "ledger.posted",
            )
            .limit(1)
        )
    ):
        raise PlaygroundOperationDenied(
            "Finance action does not match the confirmed Playground review."
        )


def require_decision_movement(
    session: Session, tenant_id: str, actual: dict, *, extra_identity: bool
) -> None:
    authority = _current_decision(session, tenant_id)
    if authority is None:
        return
    expected = json.loads(authority.intent)
    keys = ("movement_type", "item_id", "to_location_id")
    if expected.get("movement_type") == "shipment":
        keys = ("movement_type", "item_id", "from_location_id", "commitment_id")
    elif expected.get("movement_type") in {"receipt", "return"}:
        keys = (
            "movement_type",
            "item_id",
            "to_location_id",
            "from_location_id",
            "commitment_id",
        )
    matches = all(actual.get(key) == expected.get(key) for key in keys)
    matches = matches and Decimal(str(actual["quantity"])) == Decimal(
        expected["quantity"]
    )
    matches = matches and actual["occurred_at"] == datetime.fromisoformat(
        expected["occurred_at"]
    )
    if (
        (extra_identity and expected.get("movement_type") != "shipment")
        or not matches
        or session.scalar(
            select(BusinessEvent.id)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == authority.proposal_id,
                BusinessEvent.event_type == "movement.recorded",
            )
            .limit(1)
        )
    ):
        raise PlaygroundOperationDenied(
            "Movement does not match the single confirmed Playground action."
        )


@contextmanager
def _proposal_creation_scope(
    session: Session, run_id: str, user_id: str, tool_name: str, arguments: dict
):
    """Internal exact-intent permission; no execution and no intermediate commit."""
    run = require_playground_run(session, run_id, user_id, for_write=True)
    supported = tool_name == "movement_create" and arguments.get("movement_type") in {
        "opening_stock",
        "shipment",
        "receipt",
        "return",
    }
    supported = supported or tool_name in MASTER_TOOLS | {
        "order_create",
        "reserve",
        "reservation_release",
        "sales_invoice_record",
        "customer_payment_post",
        "supplier_invoice_record",
        "supplier_payment_post",
        "sales_credit_record",
        "customer_refund_post",
    }
    if not supported:
        raise PlaygroundOperationDenied(
            "This Playground proposal is not supported yet."
        )
    token = _proposal_authority.set(
        _ProposalAuthority(
            session,
            session.get_transaction(),
            run_id,
            user_id,
            run.tenant_id,
            tool_name,
            json.dumps(arguments, sort_keys=True, allow_nan=False),
        )
    )

    def deny_partial_commit(_session: Session) -> None:
        raise PlaygroundOperationDenied(
            "Playground proposal and step must commit together."
        )

    event.listen(session, "before_commit", deny_partial_commit)
    try:
        yield
    finally:
        event.remove(session, "before_commit", deny_partial_commit)
        _proposal_authority.reset(token)


def require_proposal_creation(
    session: Session, tenant_id: str, tool_name: str, arguments: dict
) -> None:
    profile_finance = _profile_finance_authority.get()
    if (
        profile_finance is not None
        and profile_finance[0] is session
        and profile_finance[1] is session.get_transaction()
        and profile_finance[4] == tenant_id
        and tool_name == "finance.adjustment.accept"
        and profile_finance[5]
        == json.dumps(arguments, sort_keys=True, allow_nan=False)
    ):
        require_playground_run(session, profile_finance[2], profile_finance[3])
        return
    profile_cost = _profile_cost_authority.get()
    if (
        profile_cost is not None
        and profile_cost[0] is session
        and profile_cost[1] is session.get_transaction()
        and profile_cost[4] == tenant_id
        and tool_name == "cost.change"
        and profile_cost[5] == json.dumps(arguments, sort_keys=True, allow_nan=False)
    ):
        require_playground_run(session, profile_cost[2], profile_cost[3])
        return
    authority = _proposal_authority.get()
    if (
        authority is not None
        and authority.session is session
        and authority.transaction is session.get_transaction()
        and authority.tenant_id == tenant_id
        and authority.tool_name == tool_name
        and authority.intent == json.dumps(arguments, sort_keys=True, allow_nan=False)
    ):
        require_playground_run(
            session, authority.run_id, authority.user_id, for_write=True
        )
        return
    require_business_operation(session, tenant_id, "proposal_create")


@contextmanager
def _seed_scope(session: Session, run_id: str, user_id: str):
    """Internal, transaction-bound permission for fixed reference setup only."""
    session.scalar(select(AppUser.id).where(AppUser.id == user_id).with_for_update())
    run = require_playground_run(session, run_id, user_id)
    if run.status != "initializing":
        raise PlaygroundOperationDenied("Playground setup is not available.")
    transaction = session.get_transaction()
    if transaction is None:
        raise PlaygroundOperationDenied("Playground setup requires a transaction.")
    token = _seed_authority.set(
        _SeedAuthority(session, transaction, run.id, user_id, run.tenant_id)
    )

    def deny_partial_commit(_session: Session) -> None:
        raise PlaygroundOperationDenied("Playground setup must commit atomically.")

    event.listen(session, "before_commit", deny_partial_commit)
    try:
        yield
    finally:
        event.remove(session, "before_commit", deny_partial_commit)
        _seed_authority.reset(token)


_master_execution: ContextVar[tuple[Session, str] | None] = ContextVar(
    "playground_master_execution", default=None
)


def require_master_call(
    session: Session,
    tenant_id: str,
    tool: str,
    records: list[dict],
    action_id: str | None,
) -> None:
    """Recheck exact intent at the shared service, before any record is changed."""
    decision = _current_decision(session, tenant_id)
    if decision is not None and (
        _master_execution.get() != (session, decision.proposal_id)
        or action_id != decision.proposal_id
        or {"records": records} != json.loads(decision.intent)
        or session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == decision.proposal_id,
            )
        )
        != f"tool:{tool}"
    ):
        raise PlaygroundOperationDenied(
            "Master-data service differs from the reviewed action."
        )


@contextmanager
def master_tool_execution(session: Session, tenant_id: str, tool: str, arguments: dict):
    """Bind the shared master-data call tree to the exact reviewed tool payload."""
    decision = _current_decision(session, tenant_id)
    if decision is None:
        yield
        return
    actual = {key: value for key, value in arguments.items() if key != "_action_id"}
    if (
        tool not in MASTER_TOOLS
        or arguments.get("_action_id") != decision.proposal_id
        or actual != json.loads(decision.intent)
        or session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == decision.proposal_id,
            )
        )
        != f"tool:{tool}"
    ):
        raise PlaygroundOperationDenied(
            "Master-data call differs from the reviewed action."
        )
    token = _master_execution.set((session, decision.proposal_id))
    try:
        yield
    finally:
        _master_execution.reset(token)


def _profile_authority_holds(session: Session, profile: tuple, tenant_id: str) -> bool:
    """Whether this profile may still write, established once per transaction.

    Spec 181 FR-001: the authority check is established once per transaction and
    reused by every core service call within it. It used to run per call, and the
    ingest measurement found the cost: `playground_run` read 51 times and `tenant`
    73 times while recording one payment, because `require_playground_run` is a
    four-table join that deliberately re-reads, and every service call asked again.

    What is cached is one transaction's answer, and it is dropped the moment
    anything in that transaction writes a `Tenant` or a `PlaygroundRun` — the two
    records the answer depends on. A refusal that would have happened still
    happens; it is only asked once.
    """
    key = (session, session.get_transaction(), tenant_id, profile[2], profile[3])
    if _profile_checked.get() == key:
        return True
    run = require_playground_run(session, profile[2], profile[3])
    tenant = session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if run.status in {"initializing", "active"} and tenant.archived_at is None:
        _profile_checked.set(key)
        return True
    return False


def require_core_operation(session: Session, tenant_id: str, operation: str) -> None:
    """Permit only private initial reference setup; egress has no such exception."""
    profile_cost = _profile_cost_authority.get()
    if (
        profile_cost is not None
        and profile_cost[0] is session
        and profile_cost[1] is session.get_transaction()
        and profile_cost[4] == tenant_id
        and operation in {"execute_cost_change", "emit_business_event"}
    ):
        run = require_playground_run(session, profile_cost[2], profile_cost[3])
        tenant = session.get(Tenant, tenant_id)
        if run.status == "initializing" and tenant.archived_at is None:
            return
        raise PlaygroundOperationDenied("Profile costing authority is unavailable.")
    profile = _profile_authority.get()
    if (
        profile
        and profile[0] is session
        and profile[1] is session.get_transaction()
        and profile[4] == tenant_id
        and operation in profile[5]
        and _profile_authority_holds(session, profile, tenant_id)
    ):
        return
    if profile is not None:
        raise PlaygroundOperationDenied(
            "Profile authority does not permit this operation."
        )
    decision = _current_decision(session, tenant_id)
    if (
        decision
        and decision.operation == "proposal_execute"
        and (
            operation == "emit_business_event"
            or (
                operation == "record_movement"
                and session.scalar(
                    select(ChangeProposal.type).where(
                        ChangeProposal.tenant_id == tenant_id,
                        ChangeProposal.id == decision.proposal_id,
                    )
                )
                == "tool:movement_create"
            )
        )
    ):
        status = session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == decision.proposal_id,
            )
        )
        if status == "executing":
            return
    if decision and decision.operation == "proposal_execute":
        proposal_type = session.scalar(
            select(ChangeProposal.type).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == decision.proposal_id,
            )
        )
        if proposal_type in {
            f"tool:{tool}" for tool in MASTER_TOOLS
        } and _master_execution.get() == (session, decision.proposal_id):
            family, mode = proposal_type.removeprefix("tool:").split("_")
            plural = {"party": "parties", "item": "items", "location": "locations"}[
                family
            ]
            if operation in {
                f"{mode}_{family}",
                f"{mode}_{plural}",
                "create_master_source_record",
                *({"update_master_source_reference"} if mode == "update" else set()),
            } and (
                session.scalar(
                    select(ChangeProposal.status).where(
                        ChangeProposal.tenant_id == tenant_id,
                        ChangeProposal.id == decision.proposal_id,
                    )
                )
                == "executing"
            ):
                return
        if proposal_type == "tool:order_create" and operation in {
            "create_manual_order",
            "store_source_record",
            "create_master_source_record",
            "create_manual_document_with_lines",
            "create_commitment",
            "emit_business_event",
        }:
            return
        if proposal_type == "tool:reserve" and operation in {
            "reserve",
            "emit_business_event",
        }:
            return
        if proposal_type == "tool:reservation_release" and operation in {
            "release_reservation",
            "emit_business_event",
        }:
            return
        financial_operations = {
            "tool:sales_credit_record": {
                "record_sales_credit",
                "create_master_source_record",
                "store_source_record",
                "create_manual_document_with_lines",
                "post_sales_credit_note",
                "post_ledger",
            },
            "tool:customer_refund_post": {
                "post_customer_refund",
                "record_customer_refund",
                "create_document",
                "post_ledger",
                "allocate_settlement",
            },
            "tool:supplier_invoice_record": {
                "record_supplier_invoice",
                "create_master_source_record",
                "store_source_record",
                "create_manual_document_with_lines",
                "post_supplier_invoice",
                "post_ledger",
            },
            "tool:supplier_payment_post": {
                "post_supplier_payment",
                "record_supplier_payment",
                "create_document",
                "post_ledger",
                "allocate_settlement",
            },
            "tool:sales_invoice_record": {
                "record_sales_invoice",
                "create_master_source_record",
                "store_source_record",
                "create_manual_document_with_lines",
                "post_sales_invoice",
                "post_ledger",
            },
            "tool:customer_payment_post": {
                "post_customer_payment",
                "record_customer_payment",
                "create_document",
                "post_ledger",
                "allocate_settlement",
            },
        }
        if (
            operation in financial_operations.get(proposal_type, set())
            and session.scalar(
                select(ChangeProposal.status).where(
                    ChangeProposal.tenant_id == tenant_id,
                    ChangeProposal.id == decision.proposal_id,
                )
            )
            == "executing"
        ):
            return
    authority = _seed_authority.get()
    if (
        authority is not None
        and authority.session is session
        and authority.tenant_id == tenant_id
        and operation in _SEED_OPERATIONS
        and authority.transaction is session.get_transaction()
    ):
        run = require_playground_run(session, authority.run_id, authority.user_id)
        tenant = session.get(Tenant, tenant_id)
        if run.status == "initializing" and tenant.archived_at is None:
            return
    require_business_operation(session, tenant_id, operation)


class PlaygroundOperationDenied(InvalidOperation):
    """A permanent policy failure, not a retryable provider failure."""

    code = "playground_operation_denied"


def require_playground_account(session: Session, user_id: str) -> AppUser:
    """Recheck account admission without acquiring a mutation lock."""
    user = session.scalar(
        select(AppUser)
        .where(AppUser.id == user_id)
        .execution_options(populate_existing=True)
    )
    if user is None:
        raise NotFound("Account not found.")
    if not account_eligible(session, user, allow_pending=True):
        raise PlaygroundOperationDenied(
            "A verified, enabled account is required for Playground."
        )
    return user


def require_playground_run(
    session: Session,
    run_id: str,
    user_id: str | None,
    *,
    for_write: bool = False,
) -> PlaygroundRun:
    """Resolve only the actor's own sandbox, checking current persisted authority.

    This is an ownership check, not permission to execute arbitrary operations.
    The caller must still enforce the supported action, confirmation and run lock.
    """
    if not user_id:
        raise NotFound("Playground run not found.")
    with session.no_autoflush:
        result = session.execute(
            select(
                PlaygroundRun,
                AppUser,
                Tenant.archived_at,
            )
            .join(Tenant, Tenant.id == PlaygroundRun.tenant_id)
            .join(AppUser, AppUser.id == PlaygroundRun.owner_user_id)
            .join(
                TenantMembership,
                (TenantMembership.tenant_id == PlaygroundRun.tenant_id)
                & (TenantMembership.user_id == PlaygroundRun.owner_user_id),
            )
            .where(
                PlaygroundRun.id == run_id,
                PlaygroundRun.owner_user_id == user_id,
                Tenant.purpose == "playground",
                TenantMembership.status == "active",
                TenantMembership.role == "owner",
            )
            .execution_options(populate_existing=True)
        ).one_or_none()
    if result is None:
        raise NotFound("Playground run not found.")
    run, owner, tenant_archived_at = result
    if not account_eligible(session, owner, allow_pending=True):
        raise PlaygroundOperationDenied(
            "A verified, enabled account is required for Playground."
        )
    if for_write and (run.status != "active" or tenant_archived_at is not None):
        raise PlaygroundOperationDenied(
            "This Playground run is read-only or not ready."
        )
    return run


_PRACTICE_APP_OPERATIONS = frozenset(
    [
        "create_party",
        "create_parties",
        "update_party",
        "update_parties",
        "create_item",
        "create_items",
        "update_item",
        "update_items",
        "create_location",
        "create_locations",
        "update_location",
        "update_locations",
        "create_master_source_record",
        "update_master_source_reference",
        "set_master_data_active",
        "create_party_group",
        "update_party_group",
        "add_party_group_member",
        "create_payment_term",
        "update_payment_term",
        "create_price_list",
        "update_price_list",
        "create_price_list_entry",
        "assign_group_price_list",
        "assign_party_price_list",
        "store_source_record",
        "create_document",
        "create_manual_document_with_lines",
        "create_manual_order",
        "correct_manual_document",
        "correct_manual_document_lines",
        "record_corrected_document_source",
        "observe_fact",
        "emit_business_event",
        "create_commitment",
        "cancel_commitment",
        "revise_commitment_due_date",
        "hold_commitment",
        "release_commitment_hold",
        "hold_document_commitments",
        "release_document_holds",
        "hold_party_delivery",
        "release_party_delivery_hold",
        "close_stale_promises",
        "reserve",
        "release_reservation",
        "record_movement",
        "correct_movement",
        "create_lot",
        "create_serial_unit",
        "create_handling_unit",
        "finance_account_maintain",
        "finance_reference_maintain",
        "finance_component_assign",
        "finance_source_mapping_set",
        "finance_target_maintain",
        "post_ledger",
        "reverse_ledger_posting_group",
        "allocate_settlement",
        "record_sales_invoice",
        "post_sales_invoice",
        "record_supplier_invoice",
        "post_supplier_invoice",
        "record_customer_payment",
        "post_customer_payment",
        "record_supplier_payment",
        "allocate_settlement",
        "post_supplier_payment",
        "record_sales_credit",
        "post_sales_credit_note",
        "post_supplier_credit_note",
        "record_customer_refund",
        "post_customer_refund",
        "record_supplier_refund",
        "post_supplier_refund",
        "allocate_credit_note",
        "allocate_supplier_credit_note",
        "enqueue_source",
        "enqueue_shopify_order",
        "ingest_shopify_order",
        "process_import_job",
        "process_pending_import_jobs",
        "process_shopify_import_job",
        "retry_import_job",
        "source_system_create",
        "source_system_update",
        "source_capability_create",
        "source_capability_update",
        "artifact_stage",
        "artifact_interpret",
        "proposal_create",
        "proposal_approve",
        "proposal_reject",
        "proposal_execute",
        "create_chat_session",
        "send_chat_message",
        # Feature 169: the App copilot's provider call is a reviewed practice
        # operation; its tool access is decided in the chat loop, its mutations
        # stay behind the proposal boundary like every other practice operation.
        "generic_provider_call",
        # Practice companies use the same owner-scoped AI configuration as an
        # ordinary company. This admits only credential custody and resolution;
        # chat mutations still remain behind the existing proposal boundary.
        "ai_settings",
        "ai_settings_update",
        "ai_key_resolve",
        "generic_copilot_context",
        "secret_create",
        "secret_replace",
        "secret_revoke",
        "secret_resolve",
        "add_chat_assistant_message",
        "archive_chat_session",
        "restore_chat_session",
        "capture_gap",
        "add_gap_entry",
        "recommend_gap",
        "decide_gap",
        "prepare_implementation",
        "activate_rule",
        "disable_rule",
        "replay_rule",
        "evaluate_active_rules",
        "ensure_demo",
    ]
)


def practice_company_runs(
    session: Session, user_id: str | None = None, *, tenant_id: str | None = None
) -> dict[str, str]:
    """Persisted eligibility, independent of cached labels and transport hints."""
    if user_id is None and tenant_id is None:
        raise ValueError("Practice eligibility requires an owner or tenant scope.")
    query = (
        select(PlaygroundRun.tenant_id, PlaygroundRun.id)
        .join(Tenant, Tenant.id == PlaygroundRun.tenant_id)
        .join(AppUser, AppUser.id == PlaygroundRun.owner_user_id)
        .join(
            TenantMembership,
            (TenantMembership.tenant_id == Tenant.id)
            & (TenantMembership.user_id == AppUser.id),
        )
        .where(
            PlaygroundRun.sandbox_kind == "practice",
            PlaygroundRun.status == "active",
            Tenant.purpose == "playground",
            Tenant.archived_at.is_(None),
            account_eligible_clause(session),
            TenantMembership.role == "owner",
            TenantMembership.status == "active",
        )
    )
    if user_id is not None:
        query = query.where(PlaygroundRun.owner_user_id == user_id)
    if tenant_id is not None:
        query = query.where(PlaygroundRun.tenant_id == tenant_id)
    with session.no_autoflush:
        return dict(session.execute(query).all())


def require_business_operation(
    session: Session, tenant_id: str, operation: str
) -> None:
    """Permit local App operations for active practice companies; isolate quick runs.

    Read the persisted purpose without flushing pending changes or trusting a
    caller-supplied Tenant, company name, cached role or environment setting.
    Only reviewed local operation names are admitted for practice tenants.
    """
    authority = _profile_authority.get()
    if (
        authority is not None
        and operation in {"source_system_create", "source_capability_create"}
        and operation in authority[5]
    ):
        require_core_operation(session, tenant_id, operation)
        return
    if _chat_authority.get() is not None:
        if operation == "generic_provider_call" and playground_chat_active(
            session, tenant_id
        ):
            return
        raise PlaygroundOperationDenied("The sandbox companion is read-only.")
    if (
        _seed_authority.get() is not None
        or _profile_authority.get() is not None
        or _proposal_authority.get() is not None
        or _decision_authority.get() is not None
    ):
        raise PlaygroundOperationDenied(
            "Playground internal scopes cannot access business operations."
        )
    purpose = _company_purpose(session, tenant_id)
    if purpose is None:
        raise NotFound("Company not found.")
    if (
        purpose == "playground"
        and operation in _PRACTICE_APP_OPERATIONS
        and tenant_id in practice_company_runs(session, tenant_id=tenant_id)
    ):
        return
    if purpose != "business":
        raise PlaygroundOperationDenied("Playground does not support this operation.")


_PROFILE_OPERATIONS = _SEED_OPERATIONS | frozenset(
    {
        "store_source_record",
        "create_document",
        "create_manual_document_with_lines",
        "create_commitment",
        "reserve",
        "release_reservation",
        "record_movement",
        "cancel_commitment",
        "hold_commitment",
        "release_commitment_hold",
        "correct_movement",
        "post_sales_invoice",
        "post_sales_credit_note",
        "allocate_credit_note",
        "post_ledger",
        "create_source_system",
        "create_source_capability",
        # Feature 204: the profile also settles what it bills and buys, so a demo
        # company shows money moving instead of an order book nobody ever paid.
        # The supplier invoice is built the way the sales invoice already is, with
        # `create_manual_document_with_lines` and its posting entry point.
        "post_customer_payment",
        "record_customer_payment",
        "post_supplier_invoice",
        "post_supplier_credit_note",
        "allocate_supplier_credit_note",
        "post_supplier_payment",
        "record_supplier_payment",
        "allocate_settlement",
        "finance_account_maintain",
    }
)
_INTAKE_OPERATIONS = frozenset(
    {
        "store_source_record",
        "enqueue_source",
        "process_import_job",
        "create_manual_document_with_lines",
        "create_commitment",
        "emit_business_event",
    }
)
# Feature 168: the settlement stream may post the invoice a synthetic source
# states, record payments and allocate unambiguous references, and nothing else.
# Orders keep the narrower intake set, so an order can never book money.
_SETTLEMENT_OPERATIONS = _INTAKE_OPERATIONS | frozenset(
    {
        "create_document",
        "post_ledger",
        "post_sales_invoice",
        "record_customer_payment",
        "allocate_settlement",
    }
)
_profile_authority: ContextVar[tuple | None] = ContextVar(
    "company_profile_authority", default=None
)
#: The transaction whose profile authority has already been established, so the
#: next service call in it does not ask again. Forgotten whenever the records that
#: answer it are written; see `_forget_profile_authority`.
_profile_checked: ContextVar[tuple | None] = ContextVar(
    "company_profile_checked", default=None
)
#: The company purpose this transaction has already read, with the transaction and
#: the company it belongs to. See `_company_purpose`.
_purpose_read: ContextVar[tuple | None] = ContextVar(
    "company_purpose_read", default=None
)


def _company_purpose(session: Session, tenant_id: str) -> str | None:
    """What this company is for, read once per transaction.

    Spec 181 FR-001: every service call in a write path asks whether this company
    may be written to, and the ingest measurement found the purpose read five times
    in one payment's call tree. It cannot change underneath the answer — the database
    refuses it, with a trigger that raises `Tenant purpose is immutable` on any update
    of that column — so reading it again inside one transaction can only produce what
    it produced the first time.

    Only a company that was *found* is remembered. A company created later in the
    same transaction must be seen when it is asked about, which is why absence is
    never cached; and a transaction that writes a `Tenant` drops the answer with the
    profile authority's (see `_forget_profile_authority`).
    """
    key = (session, session.get_transaction(), tenant_id)
    remembered = _purpose_read.get()
    if remembered is not None and remembered[0] == key:
        return remembered[1]
    with session.no_autoflush:
        purpose = session.scalar(select(Tenant.purpose).where(Tenant.id == tenant_id))
    if purpose is not None:
        _purpose_read.set((key, purpose))
    return purpose


def _forget_profile_authority(session: Session, flush_context, instances) -> None:
    """Drop the cached answer when this transaction changes what it rests on."""
    for record in (*session.new, *session.dirty, *session.deleted):
        if isinstance(record, (Tenant, PlaygroundRun)):
            _profile_checked.set(None)
            if isinstance(record, Tenant):
                _purpose_read.set(None)
            return


event.listen(Session, "before_flush", _forget_profile_authority)

_profile_cost_authority: ContextVar[tuple | None] = ContextVar(
    "company_profile_cost_authority", default=None
)
_profile_finance_authority: ContextVar[tuple | None] = ContextVar(
    "company_profile_finance_authority", default=None
)


@contextmanager
def profile_cost_action_scope(
    session: Session, run_id: str, actor_id: str, arguments: dict
):
    """Bind one fixed v2 profile cost action to its setup transaction."""
    from reality.demo.international import PROFILE_VERSION

    run = require_playground_run(session, run_id, actor_id)
    transaction = session.get_transaction()
    if (
        transaction is None
        or run.status != "initializing"
        or run.preset_key != "international-demo"
        or run.preset_version != PROFILE_VERSION
    ):
        raise PlaygroundOperationDenied("Profile costing authority is unavailable.")
    intent = json.dumps(arguments, sort_keys=True, allow_nan=False)
    token = _profile_cost_authority.set(
        (session, transaction, run.id, actor_id, run.tenant_id, intent)
    )
    try:
        yield
    finally:
        _profile_cost_authority.reset(token)


def profile_cost_owner_active(
    session: Session, tenant_id: str, actor_id: str
) -> bool:
    """Recognize only the owner bound to the current fixed profile cost action."""
    authority = _profile_cost_authority.get()
    if (
        authority is None
        or authority[0] is not session
        or authority[1] is not session.get_transaction()
        or authority[3] != actor_id
        or authority[4] != tenant_id
    ):
        return False
    run = require_playground_run(session, authority[2], actor_id)
    return run.status == "initializing"


@contextmanager
def profile_finance_action_scope(
    session: Session, run_id: str, actor_id: str, arguments: dict
):
    """Bind one authored profile settlement decision to setup's confirmation."""
    from reality.demo.international import PROFILE_VERSION

    run = require_playground_run(session, run_id, actor_id)
    transaction = session.get_transaction()
    if (
        transaction is None
        or run.status != "initializing"
        or run.preset_key != "international-demo"
        or run.preset_version != PROFILE_VERSION
    ):
        raise PlaygroundOperationDenied("Profile finance authority is unavailable.")
    intent = json.dumps(arguments, sort_keys=True, allow_nan=False)
    token = _profile_finance_authority.set(
        (session, transaction, run.id, actor_id, run.tenant_id, intent)
    )
    try:
        yield
    finally:
        _profile_finance_authority.reset(token)


@contextmanager
def _profile_scope(session: Session, run_id: str, actor_id: str):
    """Only fixed approved initialization may seed operational reality."""
    from reality.demo.international import PROFILE_VERSION

    run = require_playground_run(session, run_id, actor_id)
    if (
        run.status != "initializing"
        or run.preset_key not in {"international-demo", "atlas-execution"}
        or run.preset_version
        != (PROFILE_VERSION if run.preset_key == "international-demo" else 1)
    ):
        raise PlaygroundOperationDenied("Profile initialization is unavailable.")
    with _bound_profile_scope(session, run, actor_id, _PROFILE_OPERATIONS):
        yield


@contextmanager
def storyline_seed_scope(session: Session, run_id: str, actor_id: str):
    """Spec 182: a storyline seed replays ordinary app commands before chapter 1.

    The seed may do what a person could do in the practice company by hand, and
    nothing more. Atomicity is the caller's: it runs the seed on a savepoint-joined
    session inside its own savepoint, so a handler's commit releases a savepoint
    and a failure rolls the whole company back. The authority binds to the current
    transaction, so the caller re-enters this scope after every handler commit.
    """
    run = require_playground_run(session, run_id, actor_id)
    if (
        run.status != "initializing"
        or run.preset_key != "storyline"
        or run.storyline_key is None
    ):
        raise PlaygroundOperationDenied("Storyline initialization is unavailable.")
    session.connection()  # autobegin, so the authority binds to a live transaction
    transaction = session.get_transaction()
    if transaction is None:
        raise PlaygroundOperationDenied("Storyline seed requires a transaction.")
    token = _profile_authority.set(
        (
            session,
            transaction,
            run.id,
            actor_id,
            run.tenant_id,
            _PRACTICE_APP_OPERATIONS | _PROFILE_OPERATIONS,
        )
    )
    try:
        yield
    finally:
        _profile_authority.reset(token)


@contextmanager
def _bound_profile_scope(
    session: Session, run: PlaygroundRun, actor_id: str, operations: frozenset[str]
):
    transaction = session.get_transaction()
    if transaction is None:
        raise PlaygroundOperationDenied("Profile operation requires a transaction.")
    token = _profile_authority.set(
        (session, transaction, run.id, actor_id, run.tenant_id, operations)
    )

    def deny_commit(_session: Session) -> None:
        if _session.in_nested_transaction():
            return
        raise PlaygroundOperationDenied("Profile operation must commit atomically.")

    event.listen(session, "before_commit", deny_commit)
    try:
        yield
    finally:
        event.remove(session, "before_commit", deny_commit)
        _profile_authority.reset(token)


def require_demo_intake(
    session: Session, tenant_id: str, *, settlement: bool = False
) -> None:
    """Admit the synthetic interpreter only under its own bounded authority.

    Orders require exactly the intake set; invoices and payments require exactly
    the settlement set. Neither accepts the other, so an order interpreter can
    never run with money-posting rights.
    """
    expected = _SETTLEMENT_OPERATIONS if settlement else _INTAKE_OPERATIONS
    authority = _profile_authority.get()
    if authority is None or authority[5] != expected:
        raise PlaygroundOperationDenied(
            "Demo intake requires its current connection authority."
        )
    require_core_operation(session, tenant_id, "process_import_job")
