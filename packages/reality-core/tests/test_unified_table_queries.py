import pytest
from sqlalchemy import select
from test_unified_source_api import client_for

from reality.db.core import Party
from reality.services.core import create_party
from reality.services.projections import OPEN_FINANCIAL_ITEMS, rebuild_projections


@pytest.mark.parametrize(
    "path",
    [
        "facts",
        "master-data?family=customer",
        "delivery-work",
        "warehouse/stock",
        "warehouse/reservations",
        "warehouse/movements",
        "finance/open-items",
        "finance/payments",
        "finance/journal",
        "evidence-documents",
        "data-sources/records",
    ],
)
def test_register_rejects_unknown_sort(session, business, path):
    separator = "&" if "?" in path else "?"
    with client_for(session) as client:
        result = client.get(
            f"/api/tenants/{business.tenant.id}/{path}{separator}sort=not_a_column"
        )
        assert result.status_code == 422


def test_master_sort_applies_before_paging_and_retains_scope(session, business):
    tid = business.tenant.id
    for index in range(28):
        create_party(session, tid, f"Table sample {index:02}", "customer")
    with client_for(session) as client:
        base = f"/api/tenants/{tid}/master-data?family=customer&q=Table%20sample&sort=name&sort_direction=desc&size=25"
        first = client.get(base).json()
        second = client.get(base + "&page=2").json()
        assert first["page"]["total"] == 28
        assert len(first["items"]) == 25
        assert first["items"][0]["name"] == "Table sample 27"
        assert second["items"][-1]["name"] == "Table sample 00"
        assert {r["id"] for r in first["items"]}.isdisjoint(
            r["id"] for r in second["items"]
        )
        for size in (25, 50, 100):
            response = client.get(base.replace("size=25", f"size={size}")).json()
            assert response["page"]["size"] == size
        assert (
            client.get(
                base.replace("sort_direction=desc", "sort_direction=invalid")
            ).status_code
            == 422
        )
    assert (
        len(
            list(
                session.scalars(
                    select(Party).where(
                        Party.tenant_id == tid, Party.name.like("Table sample%")
                    )
                )
            )
        )
        == 28
    )


def test_numeric_sorts_use_full_canonical_amounts_and_keep_totals(session, business):
    from decimal import Decimal

    from reality.services.core import (
        create_document,
        create_item,
        post_sales_invoice,
        record_movement,
    )

    tid = business.tenant.id
    for i, amount in enumerate(["100", "20", "3"]):
        invoice = create_document(
            session, tid, "sales_invoice", f"TABLE-{i}", business.customer.id, amount
        )
        post_sales_invoice(session, tid, invoice.id)
        item = create_item(session, tid, f"TABLE-{i}", f"Table quantity {i}")
        record_movement(
            session,
            tid,
            "receipt",
            item.id,
            amount,
            to_location_id=business.location.id,
        )
    rebuild_projections(session, tid, (OPEN_FINANCIAL_ITEMS,))
    with client_for(session) as client:
        root = f"/api/tenants/{tid}"
        first = client.get(root + "/finance/open-items?sort=open&size=1").json()
        last = client.get(root + "/finance/open-items?sort=open&size=1&page=3").json()
        assert Decimal(first["items"][0]["open"]) == 3
        assert Decimal(last["items"][0]["open"]) == 100
        assert Decimal(first["totals"][0]["open"]) == 123
        for sort in ["number", "date", "amount", "currency"]:
            assert (
                client.get(root + f"/evidence-documents?sort={sort}&size=1").status_code
                == 200
            )
        stock = client.get(
            root + "/warehouse/stock?q=Table%20quantity&sort=available&size=1"
        ).json()
        assert Decimal(stock["items"][0]["available"]) == 3
        assert stock["page"]["total"] == 3


def test_open_items_default_to_newest_document_first(session, business):
    from reality.services.core import create_document, post_sales_invoice

    tid = business.tenant.id
    for number, document_date in [
        ("ORDER-MIDDLE", "2026-03-02"),
        ("ORDER-NEWEST", "2026-03-03"),
        ("ORDER-OLDEST", "2026-03-01"),
    ]:
        invoice = create_document(
            session,
            tid,
            "sales_invoice",
            number,
            business.customer.id,
            "10",
            document_date=document_date,
        )
        post_sales_invoice(session, tid, invoice.id)
    rebuild_projections(session, tid, (OPEN_FINANCIAL_ITEMS,))
    with client_for(session) as client:
        root = f"/api/tenants/{tid}"
        result = client.get(root + "/finance/open-items?flow=receivable").json()
        numbers = [row["number"] for row in result["items"]]
        assert numbers[:3] == ["ORDER-NEWEST", "ORDER-MIDDLE", "ORDER-OLDEST"]
        assert [row["document_date"] for row in result["items"][:3]] == [
            "2026-03-03",
            "2026-03-02",
            "2026-03-01",
        ]
        ascending = client.get(
            root + "/finance/open-items?flow=receivable&sort=date&sort_direction=asc"
        ).json()
        assert [row["number"] for row in ascending["items"]][:3] == [
            "ORDER-OLDEST",
            "ORDER-MIDDLE",
            "ORDER-NEWEST",
        ]
