"""Real business writes remain guarded even when adapters and the worker are bypassed."""

import pytest
from sqlalchemy import select
from test_operational_cases import activate, order

from reality.db.core import Commitment, Movement
from reality.db.operational_cases import OperationalCase
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.case_action_guards import automated_execution
from reality.services.memberships import Principal


@pytest.mark.parametrize(
    "operation",
    [
        "reserve",
        "revise",
        "cancel",
        "hold",
        "release_hold",
        "hold_order",
        "release_order_holds",
        "hold_party",
        "release_party_hold",
        "movement",
        "append",
        "plan",
        "packaged",
        "substitute",
        "drop_ship",
    ],
)
def test_actual_lower_write_boundaries_refuse_after_takeover(
    session, business, scheduled_owner, operation
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    case_id = cases.object_cases(session, business.tenant.id, "commitment", promise.id)[
        0
    ]
    cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take",
        confirmed=True,
    )
    from reality.services.drop_shipping import record_drop_shipment
    from reality.services.outbound_deliveries import plan_outbound_delivery
    from reality.services.receipt_deviations import accept_substitute
    from reality.services.shipments import record_packaged_execution

    calls = {
        "reserve": lambda: core.reserve(session, business.tenant.id, promise.id, "1"),
        "revise": lambda: core.revise_commitment(
            session, business.tenant.id, promise.id, quantity="20"
        ),
        "cancel": lambda: core.cancel_commitment(
            session, business.tenant.id, promise.id, reason="Repair"
        ),
        "hold": lambda: core.hold_commitment(
            session, business.tenant.id, promise.id, "manual"
        ),
        "release_hold": lambda: core.release_commitment_hold(
            session, business.tenant.id, promise.id
        ),
        "hold_order": lambda: core.hold_document_commitments(
            session, business.tenant.id, promise.document_id, "manual"
        ),
        "release_order_holds": lambda: core.release_document_holds(
            session, business.tenant.id, promise.document_id
        ),
        "hold_party": lambda: core.hold_party_delivery(
            session, business.tenant.id, business.customer.id, "manual"
        ),
        "release_party_hold": lambda: core.release_party_delivery_hold(
            session, business.tenant.id, business.customer.id
        ),
        "movement": lambda: core.record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            "1",
            from_location_id=business.location.id,
            commitment_id=promise.id,
        ),
        "append": lambda: core._append_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            "1",
            from_location_id=business.location.id,
            commitment_id=promise.id,
        ),
        "plan": lambda: plan_outbound_delivery(
            session,
            business.tenant.id,
            customer_id=business.customer.id,
            lines=[{"commitment_id": promise.id, "quantity": "1"}],
        ),
        "packaged": lambda: record_packaged_execution(
            session,
            business.tenant.id,
            direction="outbound",
            purpose="customer_delivery",
            counterparty_id=business.customer.id,
            movements=[
                {
                    "commitment_id": promise.id,
                    "item_id": business.item.id,
                    "quantity": "1",
                    "from_location_id": business.location.id,
                }
            ],
        ),
        "substitute": lambda: accept_substitute(
            session, business.tenant.id, promise.id, business.item.id, "Repair"
        ),
        "drop_ship": lambda: record_drop_shipment(
            session,
            business.tenant.id,
            supplier_commitment_id="unused-supplier",
            customer_commitment_id=promise.id,
            quantity="1",
        ),
    }
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        calls[operation]()
    assert (
        session.scalar(select(Movement).where(Movement.tenant_id == business.tenant.id))
        is None
    )
    assert core.commitment_quantity(session, business.tenant.id, promise.id) == 30


def test_new_goal_and_case_rollback_together_at_canonical_leaf(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    doc = core.create_document(
        session,
        business.tenant.id,
        "sales_order",
        "ROLLBACK",
        business.customer.id,
        "0",
    )
    with session.begin_nested() as transaction:
        promise = core.create_commitment(
            session,
            business.tenant.id,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "2",
            None,
            document_id=doc.id,
            _commit=False,
        )
        assert cases.object_cases(session, business.tenant.id, "commitment", promise.id)
        transaction.rollback()
    assert (
        session.scalar(
            select(Commitment).where(Commitment.tenant_id == business.tenant.id)
        )
        is None
    )
    assert (
        session.scalar(
            select(OperationalCase).where(
                OperationalCase.tenant_id == business.tenant.id
            )
        )
        is None
    )
