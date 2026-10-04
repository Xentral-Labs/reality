"""Spec 309 FR-001/FR-005, SC-003: the company currency and company-currency amounts."""

from decimal import Decimal

import pytest
from sqlalchemy import select, text

from reality.db.core import LedgerEntry, SourceRecord
from reality.services import core
from reality.services.finance.company_currency import (
    company_currency,
    company_currency_state,
    set_company_currency,
)


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _document(session, business, currency="EUR", number="SI-309"):
    return core.create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        business.supplier.id,
        "100",
        currency=currency,
    )


def _exchange_account(session, tenant):
    account = reviewed_create_account(
        session,
        tenant,
        code="exchange_difference",
        name="Exchange differences",
        role="exchange_difference",
    )
    reviewed_set_default_account(
        session, tenant, role="exchange_difference", account_id=account["id"]
    )


def _post(session, business, document, postings, **options):
    return core.post_ledger(
        session,
        business.tenant.id,
        document.id,
        business.supplier.id,
        postings,
        currency=document.currency,
        **options,
    )


def _company(entries):
    return [
        (entry.account, entry.debit_credit, entry.company_amount, entry.exchange_rate)
        for entry in entries
    ]


def test_the_company_currency_is_eur_until_stated(session, business):
    tenant = business.tenant.id
    assert company_currency(session, tenant) == "EUR"

    set_company_currency(session, tenant, "chf")

    assert company_currency_state(session, tenant)["currency"] == "CHF"
    (version,) = session.scalars(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == "internal_company_currency",
        )
    )
    assert version.external_id == tenant


def test_the_company_currency_cannot_change_after_a_posting(session, business):
    tenant = business.tenant.id
    _refused(
        "company_currency_invalid",
        lambda: set_company_currency(session, tenant, "EURO"),
    )
    document = _document(session, business)
    _post(
        session,
        business,
        document,
        [("inventory", "debit", "100"), ("accounts_payable", "credit", "100")],
    )

    _refused(
        "company_currency_has_postings",
        lambda: set_company_currency(session, tenant, "USD"),
    )
    # Positive control: restating the currency in force is allowed.
    assert set_company_currency(session, tenant, "EUR")["currency"] == "EUR"


def test_a_company_currency_posting_carries_its_amount_twice(session, business):
    document = _document(session, business)

    entries = _post(
        session,
        business,
        document,
        [("inventory", "debit", "100"), ("accounts_payable", "credit", "100")],
    )

    assert _company(entries) == [
        ("inventory", "debit", Decimal(100), Decimal(1)),
        ("accounts_payable", "credit", Decimal(100), Decimal(1)),
    ]
    _refused(
        "exchange_rate_not_applicable",
        lambda: _post(
            session,
            business,
            _document(session, business, number="SI-309B"),
            [("inventory", "debit", "1"), ("accounts_payable", "credit", "1")],
            exchange_rate="0.9",
        ),
    )


def test_a_foreign_posting_is_converted_at_the_stated_rate(session, business):
    document = _document(session, business, "USD")

    entries = _post(
        session,
        business,
        document,
        [
            ("inventory", "debit", "333.33"),
            ("inventory", "debit", "333.33"),
            ("inventory", "debit", "333.34"),
            ("accounts_payable", "credit", "1000"),
        ],
        exchange_rate="0.91234",
    )

    company = [entry.company_amount for entry in entries]
    # 333.33 × 0.91234 = 304.11 twice; the last debit takes the remainder of 912.34.
    assert company == [
        Decimal("304.11"),
        Decimal("304.11"),
        Decimal("304.12"),
        Decimal("912.34"),
    ]
    assert {entry.exchange_rate for entry in entries} == {Decimal("0.91234")}
    core._ledger_group_entries(session, business.tenant.id, entries[0].posting_group_id)


def test_a_foreign_posting_without_a_rate_stays_unconverted(session, business):
    document = _document(session, business, "USD")

    entries = _post(
        session,
        business,
        document,
        [("inventory", "debit", "10"), ("accounts_payable", "credit", "10")],
    )

    assert {entry.company_amount for entry in entries} == {None}


def test_only_an_exchange_difference_carries_no_document_amount(session, business):
    tenant = business.tenant.id
    _exchange_account(session, tenant)
    document = _document(session, business, "USD")

    entries = _post(
        session,
        business,
        document,
        [
            ("accounts_payable", "debit", "100"),
            ("cash", "credit", "100"),
            ("exchange_difference", "credit", "0"),
        ],
        company_amounts=["92.00", "91.24", "0.76"],
    )
    assert [entry.amount for entry in entries][-1] == 0
    assert entries[-1].company_amount == Decimal("0.76")

    # Zero on another account is refused as any amount that is not positive.
    _refused(
        "master_data_field_not_positive",
        lambda: _post(
            session,
            business,
            _document(session, business, "USD", number="SI-309N"),
            [
                ("accounts_payable", "debit", "100"),
                ("cash", "credit", "100"),
                ("inventory", "credit", "0"),
            ],
            company_amounts=["92", "91.24", "0.76"],
        ),
    )
    for postings, company in (
        # Not balanced in the company currency.
        (
            [
                ("accounts_payable", "debit", "100"),
                ("cash", "credit", "100"),
                ("exchange_difference", "credit", "0"),
            ],
            ["92", "91.24", "0.70"],
        ),
    ):
        _refused(
            "ledger_posting_group_must_balance",
            lambda postings=postings, company=company: _post(
                session,
                business,
                _document(
                    session, business, "USD", number=f"SI-{len(company)}-{company[-1]}"
                ),
                postings,
                company_amounts=company,
            ),
        )
    # A zero entry in a company-currency group is refused too.
    _refused(
        "ledger_posting_group_must_balance",
        lambda: _post(
            session,
            business,
            _document(session, business, number="SI-309Z"),
            [
                ("accounts_payable", "debit", "1"),
                ("cash", "credit", "1"),
                ("exchange_difference", "credit", "0"),
            ],
        ),
    )


def test_a_reversal_takes_back_the_company_amounts(session, business):
    tenant = business.tenant.id
    document = _document(session, business, "USD")
    (first, _) = _post(
        session,
        business,
        document,
        [("inventory", "debit", "1000"), ("accounts_payable", "credit", "1000")],
        exchange_rate="0.92",
    )

    result = core.reverse_ledger_posting_group(
        session, tenant, first.posting_group_id, reason="Wrong rate"
    )

    inverse = session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.posting_group_id == result.reversing_posting_group_id,
        )
    ).all()
    assert sorted((entry.debit_credit, entry.company_amount) for entry in inverse) == [
        ("credit", Decimal("920.00")),
        ("debit", Decimal("920.00")),
    ]


def test_another_company_keeps_its_own_currency(session, business):
    set_company_currency(session, business.tenant.id, "CHF")
    other = core.create_tenant(session, "Other GmbH")

    assert company_currency(session, other.id) == "EUR"


def test_the_table_refuses_a_bad_code_and_a_negative_company_amount(session, business):
    from sqlalchemy.exc import IntegrityError

    entries = _post(
        session,
        business,
        _document(session, business),
        [("inventory", "debit", "1"), ("accounts_payable", "credit", "1")],
    )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            text("UPDATE ledger_entry SET company_amount = -1 WHERE id = :id"),
            {"id": entries[0].id},
        )
    set_company_currency(session, business.tenant.id, "EUR")
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            text("UPDATE company_currency SET currency = 'eu' WHERE tenant_id = :t"),
            {"t": business.tenant.id},
        )


def test_the_migration_backfills_eur_and_guards_its_downgrade(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration 309")
            supplier = reviewed_create_party(session, tenant.id, "Supplier", "supplier")
            tenant_id, supplier_id = tenant.id, supplier.id
        # Create canonical references with the current service, then restore the
        # actual predecessor before posting the unconverted historical entries.
        command.downgrade(config, "0115_chat_scoped_proposals")
        with Session(engine) as session:
            for currency in ("EUR", "USD"):
                document = core.create_document(
                    session,
                    tenant_id,
                    "supplier_invoice",
                    f"SI-{currency}",
                    supplier_id,
                    "10",
                    currency=currency,
                )
                core.post_ledger(
                    session,
                    tenant_id,
                    document.id,
                    supplier_id,
                    [
                        ("inventory", "debit", "10"),
                        ("accounts_payable", "credit", "10"),
                    ],
                    currency=currency,
                )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT currency, company_amount, exchange_rate FROM ledger_entry "
                    "WHERE tenant_id = :t ORDER BY currency, debit_credit"
                ),
                {"t": tenant_id},
            ).all()
        assert [tuple(row) for row in rows] == [
            ("EUR", Decimal("10.0000"), Decimal("1.00000000")),
            ("EUR", Decimal("10.0000"), Decimal("1.00000000")),
            ("USD", None, None),
            ("USD", None, None),
        ]
        # Positive control: nothing converted yet, so the downgrade passes.
        command.downgrade(config, "0115_chat_scoped_proposals")
        command.upgrade(config, "head")
        with Session(engine) as session:
            document = core.create_document(
                session,
                tenant_id,
                "supplier_invoice",
                "SI-USD2",
                supplier_id,
                "10",
                currency="USD",
            )
            core.post_ledger(
                session,
                tenant_id,
                document.id,
                supplier_id,
                [("inventory", "debit", "10"), ("accounts_payable", "credit", "10")],
                currency="USD",
                exchange_rate="0.9",
            )
        with pytest.raises(Exception, match="converted ledger entries"):
            command.downgrade(config, "0115_chat_scoped_proposals")
    finally:
        engine.dispose()
        command.upgrade(config, "head")


from intake_review_support import (
    reviewed_create_account,
    reviewed_create_party,
    reviewed_set_default_account,
)
