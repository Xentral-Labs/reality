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
    DunningNotice,
    DunningNoticeInvoice,
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


# --- T012: preparing a run ----------------------------------------------------------


def _dated_invoice(
    session, business, number, day, *, party=None, amount="100", currency="EUR"
):
    tenant = business.tenant.id
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        number,
        (party or business.customer).id,
        amount,
        currency=currency,
        document_date=day,
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    return invoice


def _context(session, tenant, run_date, **arguments):
    return run_read_tool(
        session,
        tenant,
        "finance.dunning.run_context",
        {"run_date": run_date, **arguments},
    )


def _proposed(context):
    return {
        item["invoice_id"]: notice["level"]
        for notice in context["notices"]
        for item in notice["items"]
    }


def _left_out(context):
    return {item["invoice_id"]: item["code"] for item in context["left_out"]}


def _scheduled(session, business):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    _set_schedule(session, tenant)
    return tenant


def _notice(session, tenant, invoice, level, day):
    return _execute(
        session,
        tenant,
        "finance.dunning.record",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "invoice_ids": [invoice.id],
            "level": level,
            "notice_date": day,
        },
    )


def test_level_one_waits_for_its_days_overdue(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T012-L1", "2026-09-01")

    # Six days overdue: level 1 waits seven days, so the item waits.
    early = _context(session, tenant, "2026-09-07")
    assert _proposed(early) == {}
    assert _left_out(early) == {invoice.id: "waiting"}
    assert early["left_out"][0]["eligible_on"] == "2026-09-08"

    due = _context(session, tenant, "2026-09-08")
    assert _proposed(due) == {invoice.id: 1}
    notice = due["notices"][0]
    assert notice["fee_amount"] == "0.0000"
    assert notice["items"][0]["wait_days"] == 7
    assert notice["items"][0]["previous_notice_id"] is None


def test_the_next_level_waits_for_its_days_since_the_last_notice(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T012-L2", "2026-08-01")
    first = _notice(session, tenant, invoice, 1, "2026-09-01")

    assert _left_out(_context(session, tenant, "2026-09-14")) == {invoice.id: "waiting"}
    due = _context(session, tenant, "2026-09-15")
    assert _proposed(due) == {invoice.id: 2}
    item = due["notices"][0]["items"][0]
    assert item["previous_notice_id"] == first["id"]
    assert item["previous_level"] == 1
    assert item["previous_notice_date"] == "2026-09-01"
    assert due["notices"][0]["fee_amount"] == "5.0000"


def test_a_reversed_notice_does_not_count(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T012-REV", "2026-08-01")
    kept = _notice(session, tenant, invoice, 1, "2026-08-20")
    wrong = _notice(session, tenant, invoice, 2, "2026-09-05")
    _execute(
        session,
        tenant,
        "finance.dunning.reverse",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "notice_id": wrong["id"],
            "reason": "Sent in error",
        },
    )

    context = _context(session, tenant, "2026-09-10")
    assert _proposed(context) == {invoice.id: 2}
    assert context["notices"][0]["items"][0]["previous_notice_id"] == kept["id"]


def test_notices_group_by_customer_currency_and_level(session, business):
    tenant = _scheduled(session, business)
    other = reviewed_create_party(session, tenant, "Weber AG", "customer")
    first = _dated_invoice(session, business, "INV-T012-A", "2026-08-01")
    second = _dated_invoice(session, business, "INV-T012-B", "2026-08-02")
    dollars = _dated_invoice(
        session, business, "INV-T012-USD", "2026-08-01", currency="USD"
    )
    escalated = _dated_invoice(session, business, "INV-T012-C", "2026-07-01")
    _notice(session, tenant, escalated, 1, "2026-08-01")
    weber = _dated_invoice(session, business, "INV-T012-W", "2026-08-01", party=other)

    context = _context(session, tenant, "2026-09-01")

    groups = {
        (notice["party_id"], notice["currency"], notice["level"]): sorted(
            item["invoice_id"] for item in notice["items"]
        )
        for notice in context["notices"]
    }
    customer = business.customer.id
    assert groups == {
        (customer, "EUR", 1): sorted([first.id, second.id]),
        (customer, "USD", 1): [dollars.id],
        (customer, "EUR", 2): [escalated.id],
        (other.id, "EUR", 1): [weber.id],
    }


def test_a_run_can_be_limited_to_selected_customers(session, business):
    tenant = _scheduled(session, business)
    other = reviewed_create_party(session, tenant, "Weber AG", "customer")
    mine = _dated_invoice(session, business, "INV-T012-MINE", "2026-08-01")
    _dated_invoice(session, business, "INV-T012-THEIRS", "2026-08-01", party=other)

    context = _context(session, tenant, "2026-09-01", party_ids=[business.customer.id])

    assert _proposed(context) == {mine.id: 1}
    assert context["party_ids"] == [business.customer.id]


def test_unapplied_customer_credit_leaves_the_customer_out(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T012-CREDIT", "2026-08-01")
    # Positive control: without the credit the item is proposed.
    assert _proposed(_context(session, tenant, "2026-09-01")) == {invoice.id: 1}

    core.record_customer_payment(session, tenant, business.customer.id, "30")

    context = _context(session, tenant, "2026-09-01")
    assert _proposed(context) == {}
    assert _left_out(context) == {invoice.id: "credit_available"}


def test_paid_and_supplier_items_are_not_dunned(session, business):
    tenant = _scheduled(session, business)
    paid = _dated_invoice(session, business, "INV-T012-PAID", "2026-08-01")
    core.post_customer_payment(session, tenant, paid.id, "100")
    partly = _dated_invoice(session, business, "INV-T012-PART", "2026-08-01")
    core.post_customer_payment(session, tenant, partly.id, "40")
    supplier = core.create_document(
        session,
        tenant,
        "supplier_invoice",
        "SUP-T012",
        business.supplier.id,
        "100",
        document_date="2026-08-01",
    )
    core.post_supplier_invoice(session, tenant, supplier.id)

    context = _context(session, tenant, "2026-09-01")

    assert _proposed(context) == {partly.id: 1}
    assert Decimal(context["notices"][0]["items"][0]["open"]) == 60


def test_a_run_needs_a_schedule_and_a_date(session, business):
    tenant = business.tenant.id
    with pytest.raises(core.InvalidOperation) as refused:
        _context(session, tenant, "2026-09-01")
    assert refused.value.code == "dunning_schedule_missing"

    _scheduled(session, business)
    with pytest.raises(core.InvalidOperation) as refused:
        _context(session, tenant, "first of September")
    assert refused.value.code == "dunning_run_date_invalid"


def test_preparing_a_run_records_nothing(session, business):
    tenant = _scheduled(session, business)
    _dated_invoice(session, business, "INV-T012-NOTHING", "2026-08-01")
    before = session.scalar(select(func.count()).select_from(DunningNotice))

    context = _context(session, tenant, "2026-09-01")
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.dunning.run",
        {
            "schedule_source_record_id": context["schedule_source_record_id"],
            "run_date": "2026-09-01",
            "items": [
                {"invoice_id": item["invoice_id"], "level": notice["level"]}
                for notice in context["notices"]
                for item in notice["items"]
            ],
        },
    )

    assert session.scalar(select(func.count()).select_from(DunningNotice)) == before
    review = json.loads(proposal.output)["dunning_run"]
    assert [notice["level"] for notice in review["notices"]] == [1]


# --- T014: confirming a run -----------------------------------------------------------


def _run(session, tenant, run_date, items, **arguments):
    return _execute(
        session,
        tenant,
        "finance.dunning.run",
        {
            "schedule_source_record_id": _schedule_source(session, tenant),
            "run_date": run_date,
            "items": items,
            **arguments,
        },
    )


def _schedule_source(session, tenant):
    return dunning_runs.schedule(session, tenant)["source_record_id"]


def _all_items(context):
    return [
        {"invoice_id": item["invoice_id"], "level": notice["level"]}
        for notice in context["notices"]
        for item in notice["items"]
    ]


def test_a_confirmed_run_records_spec_247_notices_with_schedule_fees(session, business):
    tenant = _scheduled(session, business)
    fresh = _dated_invoice(session, business, "INV-T014-L1", "2026-08-01")
    older = _dated_invoice(session, business, "INV-T014-L2", "2026-07-01")
    _notice(session, tenant, older, 1, "2026-08-01")

    context = _context(session, tenant, "2026-09-01")
    receipt = _run(session, tenant, "2026-09-01", _all_items(context))

    assert receipt["skipped"] == []
    by_level = {notice["level"]: notice for notice in receipt["notices"]}
    assert by_level[1]["invoice_ids"] == [fresh.id]
    assert by_level[1]["fee_document_id"] is None
    assert by_level[2]["invoice_ids"] == [older.id]
    assert by_level[2]["fee_amount"] == "5.0000"
    assert (
        core.open_invoice_amount(session, tenant, by_level[2]["fee_document_id"]) == 5
    )
    for notice in receipt["notices"]:
        source = record_by_id(session, SourceRecord, notice["source_record_id"])
        assert (
            json.loads(source.payload)["dunning_run_source_record_id"]
            == (receipt["run_source_record_id"])
        )
    after = _context(session, tenant, "2026-09-01")
    assert _proposed(after) == {}
    assert _left_out(after) == {fresh.id: "waiting", older.id: "waiting"}


def test_a_deselected_item_is_not_dunned(session, business):
    tenant = _scheduled(session, business)
    chosen = _dated_invoice(session, business, "INV-T014-CHOSEN", "2026-08-01")
    other = _dated_invoice(session, business, "INV-T014-OTHER", "2026-08-01")

    receipt = _run(
        session, tenant, "2026-09-01", [{"invoice_id": chosen.id, "level": 1}]
    )

    assert [notice["invoice_ids"] for notice in receipt["notices"]] == [[chosen.id]]
    assert _proposed(_context(session, tenant, "2026-09-01")) == {other.id: 1}


def test_an_item_paid_after_preparation_is_skipped(session, business):
    tenant = _scheduled(session, business)
    paid = _dated_invoice(session, business, "INV-T014-PAID", "2026-08-01")
    still = _dated_invoice(session, business, "INV-T014-STILL", "2026-08-01")
    context = _context(session, tenant, "2026-09-01")
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.dunning.run",
        {
            "schedule_source_record_id": context["schedule_source_record_id"],
            "run_date": "2026-09-01",
            "items": _all_items(context),
        },
    )
    core.post_customer_payment(session, tenant, paid.id, "100")

    receipt = json.loads(
        approve_and_execute_proposal(session, tenant, proposal.id).output
    )

    assert [notice["invoice_ids"] for notice in receipt["notices"]] == [[still.id]]
    assert receipt["skipped"] == [
        {"invoice_id": paid.id, "number": "INV-T014-PAID", "level": 1, "code": "paid"}
    ]


def test_a_second_run_on_the_same_day_does_not_dun_twice(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T014-TWICE", "2026-08-01")
    items = [{"invoice_id": invoice.id, "level": 1}]
    arguments = {
        "schedule_source_record_id": _schedule_source(session, tenant),
        "run_date": "2026-09-01",
        "items": items,
    }
    first = create_change_proposal(session, tenant, "finance.dunning.run", arguments)
    second = create_change_proposal(session, tenant, "finance.dunning.run", arguments)

    approve_and_execute_proposal(session, tenant, first.id)
    receipt = json.loads(
        approve_and_execute_proposal(session, tenant, second.id).output
    )

    assert receipt["notices"] == []
    assert receipt["skipped"] == [
        {
            "invoice_id": invoice.id,
            "number": "INV-T014-TWICE",
            "level": 1,
            "code": "level_changed",
        }
    ]
    assert (
        session.scalar(
            select(func.count())
            .select_from(DunningNoticeInvoice)
            .where(DunningNoticeInvoice.invoice_id == invoice.id)
        )
        == 1
    )


def test_replaying_a_confirmed_run_returns_the_same_receipt(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T014-REPLAY", "2026-08-01")
    receipt = _run(
        session, tenant, "2026-09-01", [{"invoice_id": invoice.id, "level": 1}]
    )
    proposal_id = session.scalar(
        select(SourceRecord.external_id).where(
            SourceRecord.id == receipt["run_source_record_id"]
        )
    )

    again = dunning_runs.confirm_run(
        session,
        tenant,
        run_date="2026-09-01",
        items=[{"invoice_id": invoice.id, "level": 1}],
        schedule_source_record_id="unused on replay",
        action_id=proposal_id,
        actor_id=None,
    )

    assert again == receipt


def test_a_run_item_must_be_a_customer_invoice(session, business):
    tenant = _scheduled(session, business)
    # Positive control: a customer invoice is accepted as an item.
    invoice = _dated_invoice(session, business, "INV-T014-ITEM", "2026-08-01")
    _run(session, tenant, "2026-09-01", [{"invoice_id": invoice.id, "level": 1}])
    supplier = core.create_document(
        session, tenant, "supplier_invoice", "SUP-T014", business.supplier.id, "10"
    )

    with pytest.raises(core.InvalidOperation) as refused:
        _run(session, tenant, "2026-09-02", [{"invoice_id": supplier.id, "level": 1}])
    assert refused.value.code == "dunning_run_item_unknown"


def test_a_failing_notice_leaves_the_whole_run_unrecorded(
    session, business, monkeypatch
):
    tenant = _scheduled(session, business)
    first = _dated_invoice(session, business, "INV-T014-ATOM-1", "2026-08-01")
    other = reviewed_create_party(session, tenant, "Weber AG", "customer")
    second = _dated_invoice(
        session, business, "INV-T014-ATOM-2", "2026-08-01", party=other
    )
    real = dunning_runs._record_notice
    calls = []

    def failing(*args, **kwargs):
        calls.append(kwargs["source_key"])
        if len(calls) == 2:
            raise RuntimeError("storage failed")
        return real(*args, **kwargs)

    monkeypatch.setattr(dunning_runs, "_record_notice", failing)
    before = session.scalar(select(func.count()).select_from(DunningNotice))
    with pytest.raises(RuntimeError):
        _run(
            session,
            tenant,
            "2026-09-01",
            [
                {"invoice_id": first.id, "level": 1},
                {"invoice_id": second.id, "level": 1},
            ],
        )
    session.rollback()

    assert len(calls) == 2
    assert session.scalar(select(func.count()).select_from(DunningNotice)) == before


# --- T016: collection handover --------------------------------------------------------


def _at_level_three(session, business, number, party=None):
    tenant = business.tenant.id
    invoice = _dated_invoice(session, business, number, "2026-05-01", party=party)
    for level, day in ((1, "2026-06-01"), (2, "2026-07-01"), (3, "2026-08-01")):
        _notice(session, tenant, invoice, level, day)
    return invoice


def _hand_over(session, tenant, invoices, reason="No payment after the third reminder"):
    return _execute(
        session,
        tenant,
        "finance.dunning.collection.handover",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "invoice_ids": [invoice.id for invoice in invoices],
            "handover_date": "2026-09-01",
            "reason": reason,
        },
    )


def test_an_item_after_level_three_is_ready_and_handed_to_collection(session, business):
    tenant = _scheduled(session, business)
    invoice = _at_level_three(session, business, "INV-T016-READY")
    context = _context(session, tenant, "2026-09-01")
    assert [item["invoice_id"] for item in context["ready_for_collection"]] == [
        invoice.id
    ]
    assert (
        core.active_party_delivery_hold(session, tenant, business.customer.id) is None
    )

    handover = _hand_over(session, tenant, [invoice])

    assert handover["invoice_ids"] == [invoice.id]
    assert handover["hold_placed"] is True
    hold = core.active_party_delivery_hold(session, tenant, business.customer.id)
    assert hold.id == handover["hold_id"] and hold.reason_code == "collection"
    after = _context(session, tenant, "2026-12-01")
    assert after["ready_for_collection"] == []
    assert _left_out(after) == {invoice.id: "in_collection"}
    listed = run_read_tool(session, tenant, "finance.dunning.collection_handovers", {})
    assert [row["id"] for row in listed] == [handover["id"]]


def test_an_active_delivery_hold_is_kept(session, business):
    tenant = _scheduled(session, business)
    invoice = _at_level_three(session, business, "INV-T016-KEEP")
    existing = core.hold_party_delivery(
        session, tenant, business.customer.id, "credit_check"
    )

    handover = _hand_over(session, tenant, [invoice])

    assert handover["hold_id"] == existing.id and handover["hold_placed"] is False


@pytest.mark.parametrize("level", [1, 2])
def test_collection_needs_a_level_three_notice(session, business, level):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, f"INV-T016-L{level}", "2026-05-01")
    for step in range(1, level + 1):
        _notice(session, tenant, invoice, step, f"2026-0{5 + step}-01")

    with pytest.raises(core.InvalidOperation) as refused:
        _hand_over(session, tenant, [invoice])
    assert refused.value.code == "collection_level_missing"


def test_collection_refusals_name_their_reason(session, business):
    tenant = _scheduled(session, business)
    other = reviewed_create_party(session, tenant, "Weber AG", "customer")
    mine = _at_level_three(session, business, "INV-T016-MINE")
    theirs = _at_level_three(session, business, "INV-T016-THEIRS", party=other)
    paid = _at_level_three(session, business, "INV-T016-PAID")
    core.post_customer_payment(session, tenant, paid.id, "100")

    for invoices, reason, code in (
        ([mine, theirs], "Unpaid", "collection_mixed_customers"),
        ([paid], "Unpaid", "collection_invoice_not_open"),
        ([mine], "  ", "collection_reason_missing"),
    ):
        with pytest.raises(core.InvalidOperation) as refused:
            _hand_over(session, tenant, invoices, reason)
        assert refused.value.code == code

    _hand_over(session, tenant, [mine])
    with pytest.raises(core.InvalidOperation) as refused:
        _hand_over(session, tenant, [mine])
    assert refused.value.code == "collection_already_handed_over"


def test_a_run_reviewed_under_an_older_schedule_is_stale(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T014-STALE", "2026-08-01")
    context = _context(session, tenant, "2026-09-01")
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.dunning.run",
        {
            "schedule_source_record_id": context["schedule_source_record_id"],
            "run_date": "2026-09-01",
            "items": [{"invoice_id": invoice.id, "level": 1}],
        },
    )
    _set_schedule(session, tenant, [{**entry, "fee_amount": "2"} for entry in SCHEDULE])

    with pytest.raises(core.Conflict) as refused:
        approve_and_execute_proposal(session, tenant, proposal.id)
    assert refused.value.code == "dunning_preview_stale"


def _statements(session, action):
    from sqlalchemy import event

    count = 0

    def counted(*_):
        nonlocal count
        count += 1

    engine = session.get_bind()
    event.listen(engine, "before_cursor_execute", counted)
    try:
        action()
    finally:
        event.remove(engine, "before_cursor_execute", counted)
    return count


def test_preparing_a_run_does_not_query_per_invoice(session, business):
    tenant = _scheduled(session, business)
    other = reviewed_create_party(session, tenant, "Weber AG", "customer")
    for index in range(2):
        invoice = _dated_invoice(session, business, f"INV-T013-A{index}", "2026-07-01")
        _notice(session, tenant, invoice, 1, "2026-08-01")
    few = _statements(session, lambda: _context(session, tenant, "2026-09-01"))

    for index in range(6):
        invoice = _dated_invoice(
            session, business, f"INV-T013-B{index}", "2026-07-01", party=other
        )
        _notice(session, tenant, invoice, 1, "2026-08-01")
    many = _statements(session, lambda: _context(session, tenant, "2026-09-01"))

    assert len(_proposed(_context(session, tenant, "2026-09-01"))) == 8
    assert 0 < few == many


# --- T018: the invoice explains its dunning -------------------------------------------


def _dunning_section(session, tenant, invoice):
    from reality.web.api import document_inspector

    return next(
        (
            section["rows"]
            for section in document_inspector(session, tenant, invoice.id)["sections"]
            if section["title"] == "Dunning"
        ),
        None,
    )


def test_the_invoice_names_its_level_notice_and_handover(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T018", "2026-05-01")
    # Positive control for the absence: no notice, no section.
    assert _dunning_section(session, tenant, invoice) is None

    invoice = _at_level_three(session, business, "INV-T018-L3")
    rows = _dunning_section(session, tenant, invoice)
    notice_document = session.scalar(
        select(DunningNotice.document_id)
        .join(
            DunningNoticeInvoice,
            DunningNoticeInvoice.notice_id == DunningNotice.id,
        )
        .where(DunningNoticeInvoice.invoice_id == invoice.id, DunningNotice.level == 3)
    )
    assert [(row["label"], row["value"]) for row in rows] == [("Dunning level", 3)]
    assert rows[0]["link"] == {"kind": "document", "id": notice_document}

    handover = _hand_over(session, tenant, [invoice])
    rows = _dunning_section(session, tenant, invoice)
    assert [row["label"] for row in rows] == ["Dunning level", "Collection"]
    assert rows[1]["link"]["id"] == handover["source_record_id"]


# --- Review round (T027) ----------------------------------------------------------


@pytest.mark.parametrize(
    "entry",
    [
        {"level": 3, "wait_days": 3651, "fee_amount": "0"},
        {"level": 3, "wait_days": 14, "fee_amount": "1000000.01"},
    ],
)
def test_a_schedule_value_outside_its_bounds_is_refused(session, business, entry):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    # Positive control: the bounds themselves are accepted.
    _set_schedule(
        session,
        tenant,
        [
            SCHEDULE[0],
            SCHEDULE[1],
            {"level": 3, "wait_days": 3650, "fee_amount": "1000000"},
        ],
    )
    with pytest.raises(core.InvalidOperation) as refused:
        _set_schedule(session, tenant, [SCHEDULE[0], SCHEDULE[1], entry])
    assert refused.value.code == "dunning_schedule_value_invalid"


@pytest.mark.parametrize("wait_days", [True, 7.0])
def test_a_schedule_is_not_coerced_from_a_bool_or_a_float(session, business, wait_days):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    with pytest.raises(core.InvalidOperation):
        _set_schedule(
            session, tenant, [{**SCHEDULE[0], "wait_days": wait_days}, *SCHEDULE[1:]]
        )
    assert dunning_runs.schedule(session, tenant)["levels"] == []


def test_the_run_review_names_what_confirmation_will_skip(session, business):
    tenant = _scheduled(session, business)
    due = _dated_invoice(session, business, "INV-T027-DUE", "2026-08-01")
    wrong = _dated_invoice(session, business, "INV-T027-WRONG", "2026-08-01")
    context = _context(session, tenant, "2026-09-01")

    proposal = create_change_proposal(
        session,
        tenant,
        "finance.dunning.run",
        {
            "schedule_source_record_id": context["schedule_source_record_id"],
            "run_date": "2026-09-01",
            "items": [
                {"invoice_id": due.id, "level": 1},
                {"invoice_id": wrong.id, "level": 2},
            ],
        },
    )
    review = json.loads(proposal.output)["dunning_run"]
    receipt = json.loads(
        approve_and_execute_proposal(session, tenant, proposal.id).output
    )

    assert [
        item["invoice_id"] for notice in review["notices"] for item in notice["items"]
    ] == [due.id]
    assert (
        review["will_skip"]
        == receipt["skipped"]
        == [
            {
                "invoice_id": wrong.id,
                "number": "INV-T027-WRONG",
                "level": 2,
                "code": "level_changed",
            }
        ]
    )


def test_a_run_proposal_under_a_changed_schedule_is_refused(session, business):
    tenant = _scheduled(session, business)
    invoice = _dated_invoice(session, business, "INV-T027-OLD", "2026-08-01")
    context = _context(session, tenant, "2026-09-01")
    _set_schedule(session, tenant, [{**entry, "fee_amount": "3"} for entry in SCHEDULE])

    with pytest.raises(core.InvalidOperation) as refused:
        create_change_proposal(
            session,
            tenant,
            "finance.dunning.run",
            {
                "schedule_source_record_id": context["schedule_source_record_id"],
                "run_date": "2026-09-01",
                "items": [{"invoice_id": invoice.id, "level": 1}],
            },
        )
    assert refused.value.code == "dunning_preview_stale"


def test_an_open_item_outside_the_run_is_not_due_rather_than_paid(session, business):
    tenant = _scheduled(session, business)
    other = reviewed_create_party(session, tenant, "Weber AG", "customer")
    mine = _dated_invoice(session, business, "INV-T027-MINE", "2026-08-01")
    theirs = _dated_invoice(
        session, business, "INV-T027-THEIRS", "2026-08-01", party=other
    )
    paid = _dated_invoice(session, business, "INV-T027-PAID", "2026-08-01", party=other)
    core.post_customer_payment(session, tenant, paid.id, "100")

    receipt = _run(
        session,
        tenant,
        "2026-09-01",
        [
            {"invoice_id": mine.id, "level": 1},
            {"invoice_id": theirs.id, "level": 1},
            {"invoice_id": paid.id, "level": 1},
        ],
        party_ids=[business.customer.id],
    )

    assert {item["invoice_id"]: item["code"] for item in receipt["skipped"]} == {
        theirs.id: "not_due",
        paid.id: "paid",
    }


def test_items_ready_for_collection_name_their_last_notice(session, business):
    tenant = _scheduled(session, business)
    invoice = _at_level_three(session, business, "INV-T027-READY")
    ready = _context(session, tenant, "2026-09-01")["ready_for_collection"]

    assert ready[0]["last_notice_id"] == ready[0]["previous_notice_id"]
    assert ready[0]["invoice_id"] == invoice.id


def test_customers_of_a_run_are_a_list(session, business):
    tenant = _scheduled(session, business)
    with pytest.raises(core.InvalidOperation) as refused:
        dunning_runs.run_context(
            session, tenant, run_date="2026-09-01", party_ids=business.customer.id
        )
    assert refused.value.code == "dunning_run_parties_invalid"


from intake_review_support import reviewed_create_party
