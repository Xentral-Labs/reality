from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Commitment, Item, Movement, Party
from reality.demo.normal_month import SCENARIO_ACTION, run_normal_month
from reality.services.core import create_tenant
from reality.services.exceptions import operational_exceptions


def test_normal_month_is_complete_deterministic_and_safe_to_rerun(session):
    tenant = create_tenant(session, "September 2026 Demo")

    first = run_normal_month(session, tenant.id)
    counts = {
        model.__tablename__: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant.id)
        )
        for model in [Party, Item, Commitment, Movement, ChangeProposal]
    }
    second = run_normal_month(session, tenant.id)
    repeated_counts = {
        model.__tablename__: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant.id)
        )
        for model in [Party, Item, Commitment, Movement, ChangeProposal]
    }

    assert first == second
    assert counts == repeated_counts
    assert first["physical"] == Decimal("6.0000")
    assert first["reserved"] == 0
    assert first["receivable"] == Decimal("870.0000")
    assert counts["party"] == 6
    assert counts["item"] == 5
    assert (
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(
                ChangeProposal.tenant_id == tenant.id,
                ChangeProposal.type == SCENARIO_ACTION,
            )
        )
        == 1
    )


def test_the_month_ends_with_exactly_these_exceptions(session):
    """Pin what a full ERP month leaves in the queue.

    The month is meant to end with these standing. A demo that reconciles to
    nothing shows an ERP where nothing ever goes wrong, which is not the product
    being demonstrated: the queue is where a month's loose ends become visible.
    Do not resolve these by making the demo tidier.

    Nothing asserted this before, so a new exception class could change what the
    demo shows and no gate would notice. Every entry below is named with the act
    that produces it: a change here is a change to the story, and this test
    forces someone to argue it rather than make it in passing.
    """
    tenant = create_tenant(session, "September 2026 Queue")
    run_normal_month(session, tenant.id)

    counts: dict[str, int] = {}
    for row in operational_exceptions(
        session,
        tenant.id,
        as_of=datetime(2026, 9, 22, tzinfo=UTC),
    ):
        counts[row.class_id] = counts.get(row.class_id, 0) + 1

    if "overdue_receivable" in counts or "overdue_payable" in counts:
        from reality.services.core import aging_register
        import reality.services.exceptions as ex
        rows = [
            {
                "type": r["document"].type,
                "document_date": str(r["document"].document_date),
                "due": str(r["due_date"]),
                "term": getattr(r.get("payment_term"), "due_days", None),
                "party_term": r.get("party_payment_term_id"),
                "status": r["status"],
                "open": str(r["open"]),
                "origin": r.get("origin"),
            }
            for r in aging_register(session, tenant.id, as_of=datetime(2026, 9, 22, tzinfo=UTC))
        ]
        details = [
            (row.class_id, row.values if hasattr(row, "values") else None)
            for row in operational_exceptions(session, tenant.id, as_of=datetime(2026, 9, 22, tzinfo=UTC))
            if row.class_id.startswith("overdue")
        ]
        raise AssertionError(f"DIAG rows={rows} details={details!r}")
    assert counts == {
        # Both Shopify orders ship in full against their commitments, and the
        # month's only sales invoice is a header with no lines, so no invoice
        # line bills either order line. Reality is right to say so.
        "shipped_not_billed": 2,
        # Two units come back into the Returns Area on day 18. The write path
        # refuses to link a return to the delivery it reverses, so the movement
        # can only be recorded orphaned — which is what this class reports.
        "unexplained_movement": 1,
    }
