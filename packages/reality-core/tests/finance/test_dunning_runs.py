"""Spec 295: a company dunning schedule, a reviewed dunning run and collection handover."""

import json
from datetime import date
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from reality.db.core import (
    BusinessEvent,
    CollectionHandover,
    CollectionHandoverInvoice,
    DunningScheduleLevel,
    SourceRecord,
)
from reality.services import core, dunning_runs
from reality.services.finance.accounts import (
    create_account,
    list_accounts,
    set_default_account,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)

# --- T005: the three records and their constraints ------------------------------


def _source(session, tenant, kind):
    return core.create_master_source_record(
        session, tenant, kind, "manual", core.uid("t005"), {}
    )


def _insert(session, record):
    with session.begin_nested():
        session.add(record)
        session.flush()


def _level(session, tenant, **columns):
    values = {
        "id": core.uid("dsl"),
        "tenant_id": tenant,
        "level": 1,
        "wait_days": 7,
        "fee_amount": Decimal(0),
        "source_record_id": _source(session, tenant, "dunning_schedule").id,
        **columns,
    }
    return DunningScheduleLevel(**values)


def test_a_schedule_level_is_one_of_three_and_never_negative(session, business):
    tenant = business.tenant.id
    # Positive control: levels 1 to 3 with zero values are valid.
    for level in (1, 2, 3):
        _insert(session, _level(session, tenant, level=level, wait_days=0))

    for columns, constraint in (
        ({"level": 0}, "ck_dunning_schedule_level_level"),
        ({"level": 4}, "ck_dunning_schedule_level_level"),
        ({"level": 1, "wait_days": -1}, "ck_dunning_schedule_level_wait_days"),
        ({"level": 1, "fee_amount": Decimal("-0.01")}, "ck_dunning_schedule_level_fee"),
    ):
        with pytest.raises(IntegrityError, match=constraint):
            _insert(session, _level(session, tenant, **columns))


def test_a_company_states_each_level_once(session, business):
    tenant = business.tenant.id
    _insert(session, _level(session, tenant, level=2))

    with pytest.raises(IntegrityError, match="uq_dunning_schedule_level_level"):
        _insert(session, _level(session, tenant, level=2))


def _invoice(session, business, number):
    tenant = business.tenant.id
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        number,
        business.customer.id,
        "100",
        document_date="2026-01-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    return invoice


def _handover(session, business, **columns):
    tenant = business.tenant.id
    values = {
        "id": core.uid("col"),
        "tenant_id": tenant,
        "party_id": business.customer.id,
        "handover_date": date.fromisoformat("2026-11-01"),
        "reason": "No payment after the third reminder",
        "source_record_id": _source(session, tenant, "collection_handover").id,
        **columns,
    }
    return CollectionHandover(**values)


def test_an_invoice_is_handed_to_collection_once(session, business):
    tenant = business.tenant.id
    invoice = _invoice(session, business, "INV-T005-COL")
    first = _handover(session, business)
    _insert(session, first)
    # Positive control: the first link is accepted.
    _insert(
        session,
        CollectionHandoverInvoice(
            id=core.uid("chi"),
            tenant_id=tenant,
            handover_id=first.id,
            invoice_id=invoice.id,
        ),
    )

    second = _handover(session, business)
    _insert(session, second)
    with pytest.raises(IntegrityError, match="uq_collection_handover_invoice_invoice"):
        _insert(
            session,
            CollectionHandoverInvoice(
                id=core.uid("chi"),
                tenant_id=tenant,
                handover_id=second.id,
                invoice_id=invoice.id,
            ),
        )


def test_a_handover_states_a_reason_and_has_its_own_source(session, business):
    with pytest.raises(IntegrityError, match="ck_collection_handover_reason"):
        _insert(session, _handover(session, business, reason="  "))

    first = _handover(session, business)
    _insert(session, first)
    with pytest.raises(IntegrityError, match="uq_collection_handover_source"):
        _insert(
            session,
            _handover(session, business, source_record_id=first.source_record_id),
        )


# --- T010: the company dunning schedule -----------------------------------------

SCHEDULE = [
    {"level": 1, "wait_days": 7, "fee_amount": "0"},
    {"level": 2, "wait_days": 14, "fee_amount": "5"},
    {"level": 3, "wait_days": 14, "fee_amount": "10.50"},
]


def _fee_account(session, tenant):
    state = list_accounts(session, tenant)
    if "dunning_fee_revenue" in state["defaults"]:
        return
    account = create_account(
        session,
        tenant,
        code="dunning_fee_revenue",
        name="Dunning fee revenue",
        role="dunning_fee_revenue",
        expected_revision=state["revision"],
    )
    set_default_account(
        session,
        tenant,
        role="dunning_fee_revenue",
        account_id=account["id"],
        expected_revision=list_accounts(session, tenant)["revision"],
    )


def _execute(session, tenant, command, arguments):
    proposal = create_change_proposal(session, tenant, command, arguments)
    return json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)


def _set_schedule(session, tenant, levels=SCHEDULE):
    return _execute(
        session,
        tenant,
        "finance.dunning.schedule.set",
        {
            "expected_revision": dunning_runs.schedule(session, tenant)["revision"],
            "levels": levels,
        },
    )


def test_the_schedule_is_set_once_for_the_company_and_read_back(session, business):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    assert dunning_runs.schedule(session, tenant)["levels"] == []

    result = _set_schedule(session, tenant)

    expected = [
        {"level": 1, "wait_days": 7, "fee_amount": "0.0000"},
        {"level": 2, "wait_days": 14, "fee_amount": "5.0000"},
        {"level": 3, "wait_days": 14, "fee_amount": "10.5000"},
    ]
    assert result["levels"] == expected
    read = run_read_tool(session, tenant, "finance.dunning.schedule", {})
    assert read["levels"] == expected
    source = record_by_id(session, SourceRecord, read["source_record_id"])
    assert source.source_type == "dunning_schedule"
    assert [entry["wait_days"] for entry in json.loads(source.payload)["levels"]] == [
        7,
        14,
        14,
    ]
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "dunning.schedule_set",
        )
    )
    assert event.source_record_id == source.id


def test_changing_the_schedule_keeps_recorded_notices(session, business):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    _set_schedule(session, tenant)
    invoice = _invoice(session, business, "INV-T010-KEEP")
    notice = _execute(
        session,
        tenant,
        "finance.dunning.record",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "invoice_ids": [invoice.id],
            "level": 2,
            "notice_date": "2026-09-21",
            "fee_amount": "5",
        },
    )

    changed = [{**entry, "fee_amount": "9"} for entry in SCHEDULE]
    result = _set_schedule(session, tenant, changed)

    assert [entry["fee_amount"] for entry in result["levels"]] == ["9.0000"] * 3
    assert (
        session.scalar(
            select(func.count())
            .select_from(DunningScheduleLevel)
            .where(DunningScheduleLevel.tenant_id == tenant)
        )
        == 3
    )
    kept = run_read_tool(
        session, tenant, "finance.dunning.notice", {"notice_id": notice["id"]}
    )
    assert kept["fee_amount"] == "5.0000"


@pytest.mark.parametrize(
    ("levels", "code"),
    [
        (SCHEDULE[:2], "dunning_schedule_incomplete"),
        ([SCHEDULE[0], SCHEDULE[0], SCHEDULE[1]], "dunning_schedule_incomplete"),
        ([], "dunning_schedule_incomplete"),
        (
            [SCHEDULE[0], SCHEDULE[1], {**SCHEDULE[2], "wait_days": -1}],
            "dunning_schedule_value_invalid",
        ),
        (
            [SCHEDULE[0], SCHEDULE[1], {**SCHEDULE[2], "wait_days": "two weeks"}],
            "dunning_schedule_value_invalid",
        ),
        (
            [SCHEDULE[0], {**SCHEDULE[1], "fee_amount": "-1"}, SCHEDULE[2]],
            "dunning_schedule_value_invalid",
        ),
        (
            [SCHEDULE[0], {**SCHEDULE[1], "fee_amount": "1.00001"}, SCHEDULE[2]],
            "dunning_schedule_value_invalid",
        ),
    ],
)
def test_an_incomplete_or_invalid_schedule_is_refused(session, business, levels, code):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    with pytest.raises(core.InvalidOperation) as refused:
        _set_schedule(session, tenant, levels)
    assert refused.value.code == code
    assert dunning_runs.schedule(session, tenant)["levels"] == []


def test_a_fee_needs_the_dunning_fee_account(session, business):
    tenant = business.tenant.id
    # Positive control: a schedule without fees needs no account.
    free = [{**entry, "fee_amount": "0"} for entry in SCHEDULE]
    assert len(_set_schedule(session, tenant, free)["levels"]) == 3

    with pytest.raises(core.InvalidOperation) as refused:
        _set_schedule(session, tenant)
    assert refused.value.code == "finance_account_default_missing"


def test_a_stale_schedule_confirmation_is_refused(session, business):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.dunning.schedule.set",
        {
            "expected_revision": dunning_runs.schedule(session, tenant)["revision"],
            "levels": SCHEDULE,
        },
    )
    _set_schedule(session, tenant)

    with pytest.raises(core.Conflict) as refused:
        approve_and_execute_proposal(session, tenant, proposal.id)
    assert refused.value.code == "dunning_preview_stale"


def test_the_schedule_stays_in_its_company(session, business):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    _set_schedule(session, tenant)
    other = core.create_tenant(session, "Other dunning company")

    assert dunning_runs.schedule(session, other.id)["levels"] == []
