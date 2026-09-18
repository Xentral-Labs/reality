"""Overdue shortcuts compose the canonical aging observation before paging."""

from datetime import UTC, date, datetime

from reality.services.core import create_document, post_sales_invoice
from reality.services.finance.worklists import overdue_document_ids


def test_overdue_worklist_uses_aging_and_retains_unknown_due_exclusion(
    session, business
):
    from reality.db.core import PaymentTerm

    term = PaymentTerm(
        id="search_net_10",
        tenant_id=business.tenant.id,
        code="NET10",
        name="Net 10",
        due_days=10,
    )
    session.add(term)
    session.flush()
    old = create_document(
        session, business.tenant.id, "sales_invoice", "OLD", business.customer.id, 100
    )
    today = create_document(
        session, business.tenant.id, "sales_invoice", "TODAY", business.customer.id, 100
    )
    unknown = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "UNKNOWN",
        business.customer.id,
        100,
    )
    for document, day in [(old, date(2026, 9, 1)), (today, date(2026, 9, 8)), (unknown, None)]:
        document.document_date = day
        document.payment_term_id = term.id
        session.flush()
        post_sales_invoice(session, business.tenant.id, document.id)
    assert overdue_document_ids(
        session, business.tenant.id, as_of=datetime(2026, 9, 18, tzinfo=UTC)
    ) == {old.id}
