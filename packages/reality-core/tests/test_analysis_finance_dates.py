"""Analysis uses canonical finance positions and calendar-date semantics."""

from decimal import Decimal

import pytest

from reality.domain.traversal import Traversal
from reality.services import core
from reality.services.analytics.graph_model import reporting_catalog
from reality.services.analytics.traversal import TraversalRefused, run_traversal


def ask(session, tenant, **query):
    return run_traversal(session, tenant, Traversal.model_validate(query))


def invoice(
    session, business, number, amount="100", kind="sales_invoice", day="2026-08-01"
):
    tenant = business.tenant.id
    doc = core.create_document(
        session, tenant, kind, number, business.customer.id, amount, document_date=day
    )
    if kind == "sales_invoice":
        core.post_sales_invoice(session, tenant, doc.id)
    else:
        core.post_supplier_invoice(session, tenant, doc.id)
    return doc


def test_signed_postings_match_account_balance(session, business):
    tenant = business.tenant.id
    invoice(session, business, "SIGNED")
    core.record_customer_payment(session, tenant, business.customer.id, "30")
    result = ask(
        session,
        tenant,
        **{
            "from": "posting",
            "as": "p",
            "measures": ["posted_amount"],
            "group_by": [{"field": "p.currency"}],
            "follow": [{"edge": "posting_account", "as": "a"}],
            "filter": [{"field": "a.role", "op": "eq", "value": "accounts_receivable"}],
        },
    )
    assert Decimal(result.rows[0]["posted_amount"]) == Decimal(70)


def test_an_impossible_day_is_refused_and_an_absent_one_still_groups(session, business):
    """A day the calendar does not have never reaches the column (spec 234).

    It used to be stored as text and skipped again by every reader, so the same
    invalid value was re-judged on each read and counted as "unknown" beside
    documents that genuinely stated no date. The two are different: one is a
    mistake to refuse, the other is an absence to report.
    """
    tenant = business.tenant.id
    for n, day in enumerate(["2024-02-29", "2024-03-01", ""]):
        core.create_document(
            session,
            tenant,
            "sales_order",
            f"DATE-{n}",
            business.customer.id,
            "10",
            document_date=day,
        )
    for n, impossible in enumerate(["2023-02-29", "2024-13-01", "oops"]):
        with pytest.raises(core.InvalidOperation, match="YYYY-MM-DD"):
            core.create_document(
                session,
                tenant,
                "sales_order",
                f"BAD-{n}",
                business.customer.id,
                "10",
                document_date=impossible,
            )
        session.rollback()
    query = {
        "from": "order",
        "as": "o",
        "measures": ["stated_order_amount"],
        "group_by": [
            {"field": "o.document_date", "bucket": "month"},
            {"field": "o.currency"},
        ],
    }
    result = ask(session, tenant, **query)
    amounts = {
        row["o.document_date"]: Decimal(row["stated_order_amount"])
        for row in result.rows
    }
    assert amounts == {
        "2024-02": Decimal(10),
        "2024-03": Decimal(10),
        None: Decimal(10),
    }
    query["filter"] = [
        {"field": "o.document_date", "op": "gte", "value": "2024-02-01"},
        {"field": "o.document_date", "op": "lt", "value": "2024-03-01"},
    ]
    assert len(ask(session, tenant, **query).rows) == 1
    prop = next(
        p
        for p in reporting_catalog("order")["nodes"][0]["properties"]
        if p["key"] == "document_date"
    )
    assert prop["kind"] == "time" and prop["temporal"] == "date"


def test_financial_positions_match_canonical_aging(session, business):
    tenant = business.tenant.id
    doc = invoice(session, business, "PARTIAL")
    invoice(session, business, "SUPPLIER", "80", kind="supplier_invoice")
    core.create_document(
        session, tenant, "sales_invoice", "UNPOSTED", business.customer.id, "900"
    )
    entries = core.record_customer_payment(session, tenant, business.customer.id, "30")
    payment = next(e for e in entries if e.account == "accounts_receivable")
    core.allocate_settlement(
        session,
        tenant,
        payment.id,
        core._settlement_control_entry(session, tenant, doc.id).id,
        "30",
    )
    canonical = {r["document"].id: r for r in core.aging_register(session, tenant)}
    result = ask(
        session,
        tenant,
        **{
            "from": "customer_open_item",
            "as": "i",
            "group_by": [
                {"field": f"i.{key}"}
                for key in [
                    "id",
                    "currency",
                    "due_date",
                    "days_overdue",
                    "settlement_status",
                ]
            ],
            "measures": ["customer_open_amount", "customer_overdue_amount"],
        },
    )
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row["i.id"] == doc.id
    assert (
        Decimal(row["customer_open_amount"]) == canonical[doc.id]["open"] == Decimal(70)
    )
    assert row["i.settlement_status"] == canonical[doc.id]["status"] == "partial"
    assert row["i.due_date"] == canonical[doc.id]["due_date"].isoformat()
    assert row["i.days_overdue"] == canonical[doc.id]["days_overdue"]
    assert result.statements > 1
    assert "finance_aging" in result.sql
    assert (
        len(
            ask(
                session,
                tenant,
                **{
                    "from": "supplier_open_item",
                    "as": "s",
                    "group_by": [{"field": "s.id"}],
                },
            ).rows
        )
        == 1
    )
    other = core.create_tenant(session, "Other analysis")
    assert not ask(
        session,
        other.id,
        **{"from": "customer_open_item", "as": "i", "group_by": [{"field": "i.id"}]},
    ).rows


def test_financial_currency_and_snapshot_guards(session, business):
    tenant = business.tenant.id
    with pytest.raises(TraversalRefused):
        ask(
            session,
            tenant,
            **{
                "from": "customer_open_item",
                "as": "i",
                "measures": ["customer_open_amount"],
            },
        )
    with pytest.raises(TraversalRefused):
        ask(
            session,
            tenant,
            **{
                "from": "customer_open_item",
                "as": "i",
                "measures": ["customer_open_amount"],
                "group_by": [
                    {"field": "i.currency"},
                    {"field": "i.due_date", "bucket": "month"},
                ],
            },
        )


def test_reversed_payment_and_invoice_keep_canonical_positions(session, business):
    tenant = business.tenant.id
    doc = invoice(session, business, "REVERSALS")
    entries = core.record_customer_payment(session, tenant, business.customer.id, "100")
    payment = next(e for e in entries if e.account == "accounts_receivable")
    control = core._settlement_control_entry(session, tenant, doc.id)
    core.allocate_settlement(session, tenant, payment.id, control.id, "100")
    query = {
        "from": "customer_open_item",
        "as": "i",
        "group_by": [{"field": "i.currency"}, {"field": "i.settlement_status"}],
        "measures": ["customer_open_amount"],
    }
    assert Decimal(ask(session, tenant, **query).rows[0]["customer_open_amount"]) == 0
    core.reverse_ledger_posting_group(
        session, tenant, payment.posting_group_id, reason="Payment reversed"
    )
    assert Decimal(ask(session, tenant, **query).rows[0]["customer_open_amount"]) == 100
    core.reverse_ledger_posting_group(
        session, tenant, control.posting_group_id, reason="Invoice reversed"
    )
    result = ask(session, tenant, **query).rows[0]
    assert result["i.settlement_status"] == "reversed"
    assert Decimal(result["customer_open_amount"]) == 0


def test_opening_due_date_and_no_cross_currency_sum(session, business):
    from reality.services.finance.accounts import initialize_accounts, list_accounts
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.opening.import",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "source_namespace": "old_erp",
            "snapshot_key": "cutover",
            "cutover_date": "2026-01-01",
            "coverage_kind": "individual",
            "reason": "Received opening positions",
            "items": [
                {
                    "party_id": business.customer.id,
                    "direction": "customer_debt",
                    "currency": currency,
                    "amount": amount,
                    "external_item_key": currency,
                    "reference": currency,
                    "due_date": "2025-12-01",
                }
                for currency, amount in [("EUR", "500"), ("USD", "800")]
            ],
        },
        actor_type="human",
    )
    approve_and_execute_proposal(session, tenant, proposal.id)
    result = ask(
        session,
        tenant,
        **{
            "from": "customer_open_item",
            "as": "i",
            "group_by": [{"field": "i.currency"}, {"field": "i.due_date"}],
            "measures": ["customer_open_amount"],
        },
    )
    assert {
        row["i.currency"]: Decimal(row["customer_open_amount"]) for row in result.rows
    } == {"EUR": Decimal(500), "USD": Decimal(800)}
    assert all(row["i.due_date"] == "2025-12-01" for row in result.rows)


def test_finance_limit_refuses_before_derivation(session, business, monkeypatch):
    from reality.services.analytics import finance_relation

    invoice(session, business, "LIMIT")
    monkeypatch.setattr(finance_relation, "MAX_FINANCE_DOCUMENTS", 0)
    with pytest.raises(TraversalRefused) as failure:
        ask(
            session,
            business.tenant.id,
            **{
                "from": "customer_open_item",
                "as": "i",
                "group_by": [{"field": "i.id"}],
            },
        )
    assert failure.value.code == "finance_limit"


def test_chat_validation_accepts_registered_financial_positions():
    from reality.services.analytics.interpretation import checked_interpretation

    value = checked_interpretation(
        {
            "status": "ready",
            "question": {
                "from": "customer_open_item",
                "as": "i",
                "group_by": [{"field": "i.currency"}],
                "measures": ["customer_open_amount"],
            },
        }
    )
    assert value["status"] == "ready"
