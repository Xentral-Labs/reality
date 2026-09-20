"""The palette searches complete scoped sets before limiting results."""

import pytest

from reality.domain.search import RecordTarget, SearchRequest
from reality.services.core import NotFound, create_item, create_tenant
from reality.services.global_search import resolve_search_targets, search_company
from reality.services.memberships import Principal


def test_exact_prefix_typo_and_complete_pagination(session, business):
    tenant = business.tenant.id
    for i in range(55):
        create_item(session, tenant, f"WARE-{i:03}", f"Warehouse {i:03}")
    other = create_tenant(session, "Other")
    hidden = create_item(session, other.id, "WARE-SECRET", "Warehouse secret")
    seen = []
    cursor = None
    while True:
        page = search_company(
            session,
            tenant,
            None,
            SearchRequest(
                provider="items_locations", query="warehose", limit=7, cursor=cursor
            ),
        )
        seen.extend(page.items)
        if not page.has_more:
            break
        assert page.next_cursor
        cursor = page.next_cursor
    assert len(seen) == 56  # includes the existing warehouse location
    assert len({hit.key for hit in seen}) == 56
    assert all(hidden.id != hit.target.id for hit in seen)
    exact = search_company(
        session,
        tenant,
        None,
        SearchRequest(provider="items_locations", query="WARE-054", limit=1),
    )
    assert exact.items[0].tier == 0
    assert exact.items[0].label == "Warehouse 054"


def test_cursor_scope_no_flush_and_resolution(session, business):
    tenant = business.tenant.id
    page = search_company(
        session, tenant, None, SearchRequest(provider="partners", query="GmbH", limit=1)
    )
    assert page.has_more
    with pytest.raises(ValueError):
        search_company(
            session,
            tenant,
            None,
            SearchRequest(
                provider="partners", query="different", cursor=page.next_cursor
            ),
        )
    with pytest.raises(NotFound):
        search_company(
            session,
            tenant,
            Principal("missing"),
            SearchRequest(provider="partners", query="Muller"),
        )
    resolved = resolve_search_targets(
        session,
        tenant,
        None,
        [
            RecordTarget(record_kind="party", id=business.customer.id),
            RecordTarget(record_kind="item", id=business.customer.id),
        ],
    )
    assert [hit.target.id for hit in resolved] == [business.customer.id]
    assert resolved[0].roles == ["customer"]
    assert (
        search_company(session, tenant, None, SearchRequest(provider="partners")).items
        == []
    )


def test_reports_are_owner_scoped_and_search_does_not_flush(
    session, business, scheduled_owner
):
    from reality.db.analytics import AnalyticsReport
    from reality.db.core import Item
    from reality.services.memberships import Principal

    report = AnalyticsReport(
        id="search_report",
        tenant_id=business.tenant.id,
        owner_user_id=scheduled_owner.id,
        name="Private warehouse report",
        definition={},
        kind="graph",
        model_version="test",
        create_request_id="search_create",
        create_payload_hash="test",
        last_request_id="search_create",
        last_payload_hash="test",
    )
    session.add(report)
    session.flush()
    actor = Principal(scheduled_owner.id)
    result = search_company(
        session,
        business.tenant.id,
        actor,
        SearchRequest(provider="reports", query="warehouse"),
    )
    assert [hit.target.id for hit in result.items] == [report.id]
    report.deleted_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )
    session.flush()
    assert not search_company(
        session,
        business.tenant.id,
        actor,
        SearchRequest(provider="reports", query="warehouse"),
    ).items
    pending = Item(
        id="never_flush_search",
        tenant_id=business.tenant.id,
        sku="not-flushed",
        name="Pending",
    )
    session.add(pending)
    assert not search_company(
        session,
        business.tenant.id,
        actor,
        SearchRequest(provider="items_locations", query="not-flushed"),
    ).items
    assert pending in session.new
    session.expunge(pending)


def test_document_payment_shipment_canonical_authorities(session, business):
    from sqlalchemy import select

    from reality.db.core import LedgerEntry, Shipment, ShipmentPackage, SourceRecord
    from reality.services.core import (
        create_document,
        post_customer_payment,
        post_sales_invoice,
    )

    tenant = business.tenant.id
    invoice = create_document(
        session, tenant, "sales_invoice", "INV-EXACT", business.customer.id, 100
    )
    post_sales_invoice(session, tenant, invoice.id)
    post_customer_payment(session, tenant, invoice.id, 40, payment_number="PAY-EXACT")
    cash = session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant, LedgerEntry.account == "cash"
        )
    )
    payments = search_company(
        session, tenant, None, SearchRequest(provider="finance", query="PAY-EXACT")
    )
    assert [hit.key for hit in payments.items] == [f"ledger_entry:{cash.id}"]
    assert payments.items[0].target.record_kind == "payment"
    assert not search_company(
        session, tenant, None, SearchRequest(provider="reality", query=cash.id)
    ).items
    assert not search_company(
        session, tenant, None, SearchRequest(provider="reality", query="INV-EXACT")
    ).items
    source = SourceRecord(
        id="shipping_source",
        tenant_id=tenant,
        source_system="test",
        source_type="shipment",
        external_id="SHIP-EXT",
        payload="{}",
        payload_hash="1",
        version=1,
    )
    session.add(source)
    session.flush()
    shipment = Shipment(
        id="shipping_record",
        tenant_id=tenant,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        source_record_id=source.id,
    )
    session.add(shipment)
    session.flush()
    session.add_all(
        [
            ShipmentPackage(
                id=f"package_{i}",
                tenant_id=tenant,
                shipment_id=shipment.id,
                tracking_number="TRACK-EXACT",
            )
            for i in range(2)
        ]
    )
    session.flush()
    rows = search_company(
        session, tenant, None, SearchRequest(provider="shipping", query="TRACK-EXACT")
    ).items
    assert [hit.target.id for hit in rows] == [shipment.id]
    assert rows[0].tier == 0
    assert rows[0].label == "SHIP-EXT"


def test_branch_limits_follow_label_order_not_identity_order(session, business):
    from reality.db.core import Item

    for index in range(12):
        session.add(
            Item(
                id=f"ordered_{index:02}",
                tenant_id=business.tenant.id,
                name=f"Unique word {11 - index:02}",
                sku=f"ORDERED-{index}",
            )
        )
    session.flush()
    page = search_company(
        session,
        business.tenant.id,
        None,
        SearchRequest(provider="items_locations", query="Unique", limit=3),
    )
    assert [hit.label for hit in page.items] == [
        "Unique word 00",
        "Unique word 01",
        "Unique word 02",
    ]
    following = search_company(
        session,
        business.tenant.id,
        None,
        SearchRequest(
            provider="items_locations", query="Unique", limit=3, cursor=page.next_cursor
        ),
    )
    assert [hit.label for hit in following.items] == [
        "Unique word 03",
        "Unique word 04",
        "Unique word 05",
    ]


def test_every_materialized_search_cte_carries_its_own_name(session, business):
    """An unnamed CTE is named after the object's `id()`, which CPython reuses.

    SQLAlchemy keys anonymous constructs by `id(object)` (`cache_anon_map.get_anon`)
    and renders them as `anon_1`, `anon_2`… Two CTEs built at different moments can
    therefore share a name once the first object has been collected, and this query
    puts several of them in one `union_all`. The result is
    `CompileError: Multiple, unrelated CTEs found with the same name: 'anon_12'` —
    a failure that appears and disappears with unrelated code, as it did in CI while
    passing locally.

    Naming each one after its family makes the collision impossible, and this test
    holds that rather than the symptom.
    """
    from sqlalchemy import event

    from reality.services.core import create_document, post_sales_invoice

    tenant = business.tenant.id
    invoice = create_document(
        session, tenant, "sales_invoice", "INV-CTE", business.customer.id, 100
    )
    post_sales_invoice(session, tenant, invoice.id)
    create_item(session, tenant, "CTE-ITEM", "Named cte item")
    session.flush()

    seen: list[str] = []
    bind = session.get_bind()

    def capture(conn, cursor, statement, *args):
        if " AS MATERIALIZED (" in statement or "WITH " in statement:
            seen.append(statement)

    event.listen(bind, "before_cursor_execute", capture)
    try:
        search_company(
            session, tenant, None, SearchRequest(provider="finance", query="INV")
        )
    finally:
        event.remove(bind, "before_cursor_execute", capture)

    materialized = [text for text in seen if "AS MATERIALIZED" in text]
    assert materialized, "the search no longer materializes any family"
    for statement in materialized:
        assert "matched_" in statement, statement[:200]
        assert "anon_" not in statement.split(" AS MATERIALIZED")[0], (
            "a materialized search CTE is still unnamed"
        )
