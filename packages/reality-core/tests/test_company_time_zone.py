"""Spec 349: the company time zone business days are counted in."""
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from intake_review_support import accept_import_job
from sqlalchemy import select

from reality.db.core import Document, SourceRecord
from reality.domain.calendar import business_day
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.company_time_zone import (
    company_day,
    company_time_zone_state,
    set_company_time_zone,
)
from reality.tools.application import approve_and_execute_proposal

BERLIN = ZoneInfo("Europe/Berlin")
NEW_YORK = ZoneInfo("America/New_York")


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _shop_order(order_id, sku, created_at):
    return {
        "id": order_id,
        "name": f"#{order_id}",
        "currency": "EUR",
        "total_price": "40.00",
        "created_at": created_at,
        "updated_at": created_at,
        "line_items": [
            {"id": order_id * 10, "sku": sku, "quantity": 4, "price": "10.00"}
        ],
    }


def _net30(session, tenant):
    """Thirty days from 1 October: due 31 October."""
    core.create_payment_term(session, tenant, "NET30", "Net 30 days", 30)
    return "NET30"


def _order_day(session, business, order_id, created_at):
    tenant = business.tenant.id
    _, job = core.enqueue_shopify_order(
        session,
        tenant,
        _shop_order(order_id, business.item.sku, created_at),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    _, document, _, _ = accept_import_job(session, tenant, job.id)
    return document.document_date


def test_a_stated_day_never_moves_and_an_instant_takes_the_local_day():
    """
    BUSINESS TEST:
    A stated day keeps its day in every zone; an instant becomes the local day.
    GIVEN:
    Days stated as text or as midnight UTC, and instants with offsets, read in
    Berlin and New York.
    WHEN:
    The business day is taken.
    THEN:
    Stated days stay; 23:30 local belongs to that local day, 00:30 to the next.
    BUSINESS RULES:
    calendar.business_day.stated
    calendar.business_day.instant
    """
    assert business_day("2026-10-31", NEW_YORK) == date(2026, 10, 31)
    assert business_day(datetime(2026, 10, 31, tzinfo=UTC), NEW_YORK) == date(
        2026, 10, 31
    )
    assert business_day("2026-10-31T23:30:00+01:00", BERLIN) == date(2026, 10, 31)
    assert business_day("2026-11-01T00:30:00+01:00", BERLIN) == date(2026, 11, 1)
    assert business_day("2026-10-31T23:30:00-04:00", NEW_YORK) == date(2026, 10, 31)
    # Positive control: the same New York instant is 1 November in UTC and Berlin.
    assert business_day("2026-10-31T23:30:00-04:00", UTC) == date(2026, 11, 1)
    assert business_day("2026-10-31T23:30:00-04:00", BERLIN) == date(2026, 11, 1)


@pytest.mark.parametrize(
    ("instant", "day"),
    [
        # Spring forward: 02:00 CET jumps to 03:00 CEST on 29 March 2026.
        ("2026-03-28T23:30:00Z", date(2026, 3, 29)),
        ("2026-03-29T21:59:00Z", date(2026, 3, 29)),
        ("2026-03-29T22:00:00Z", date(2026, 3, 30)),
        # Fall back: 03:00 CEST returns to 02:00 CET on 25 October 2026.
        ("2026-10-24T21:59:00Z", date(2026, 10, 24)),
        ("2026-10-24T22:00:00Z", date(2026, 10, 25)),
        ("2026-10-25T22:59:00Z", date(2026, 10, 25)),
        ("2026-10-25T23:00:00Z", date(2026, 10, 26)),
    ],
)
def test_daylight_saving_moves_the_local_midnight(instant, day):
    """
    BUSINESS TEST:
    The local midnight follows daylight saving time.
    GIVEN:
    Instants around the Berlin clock changes of 2026.
    WHEN:
    The Berlin business day is taken.
    THEN:
    Midnight is 23:00 UTC in winter time and 22:00 UTC in summer time.
    BUSINESS RULES:
    calendar.business_day.instant
    """
    assert business_day(instant, BERLIN) == day


def test_the_time_zone_is_utc_until_stated_and_is_versioned(session, business):
    """
    BUSINESS TEST:
    A company counts in UTC until it states its zone.
    GIVEN:
    A company that stated no zone.
    WHEN:
    It states Europe/Berlin.
    THEN:
    The read shows Berlin as stated, kept as a version of its source stream.
    BUSINESS RULES:
    company_time_zone.zone
    company_time_zone.state
    """
    tenant = business.tenant.id
    assert company_time_zone_state(session, tenant) == {
        "time_zone": "UTC",
        "stated": False,
        "source_record_id": None,
    }

    set_company_time_zone(session, tenant, "Europe/Berlin")

    state = company_time_zone_state(session, tenant)
    assert (state["time_zone"], state["stated"]) == ("Europe/Berlin", True)
    (version,) = session.scalars(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == "internal_company_time_zone",
        )
    )
    assert version.external_id == tenant


def test_an_unknown_zone_is_refused(session, business):
    """
    BUSINESS TEST:
    Only UTC or a known IANA zone can be stated.
    GIVEN:
    A company.
    WHEN:
    It states an offset or a made-up zone.
    THEN:
    The statement is refused with company_time_zone_invalid.
    BUSINESS RULES:
    company_time_zone.set.invalid
    """
    tenant = business.tenant.id
    for stated in ("+01:00", "Europe/Atlantis", ""):
        _refused(
            "company_time_zone_invalid",
            lambda stated=stated: set_company_time_zone(session, tenant, stated),
        )
    assert company_time_zone_state(session, tenant)["stated"] is False


def test_an_agent_states_the_zone_and_a_person_confirms(session, business):
    """
    BUSINESS TEST:
    The zone is stated through the reviewed tool shared by every surface.
    GIVEN:
    A company in UTC.
    WHEN:
    An agent proposes Europe/Berlin and a person confirms.
    THEN:
    The review shows current and proposed; only the confirmation changes it.
    BUSINESS RULES:
    company_time_zone.review
    company_time_zone.set.event
    """
    tenant = business.tenant.id
    schema = MCP_TOOL_REGISTRY["company_time_zone_set_propose"].input_schema
    assert (schema["additionalProperties"], schema["required"]) == (
        False,
        ["time_zone"],
    )
    proposed = MCP_TOOL_REGISTRY["company_time_zone_set_propose"].handler(
        session, tenant, {"time_zone": "Europe/Berlin"}
    )
    assert proposed["preview"]["company_time_zone"] == {
        "current": "UTC",
        "proposed": "Europe/Berlin",
    }
    assert company_time_zone_state(session, tenant)["stated"] is False

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )

    read = MCP_TOOL_REGISTRY["company_time_zone"].handler(session, tenant, {})
    assert (read["time_zone"], read["stated"]) == ("Europe/Berlin", True)


def test_a_review_that_saw_another_zone_is_refused(session, business):
    """
    BUSINESS TEST:
    A confirmation never applies a zone over one stated after its review.
    GIVEN:
    A review that saw no stated zone.
    WHEN:
    Someone states New York before the confirmation runs.
    THEN:
    The confirmation is refused with company_time_zone_changed_since_review.
    BUSINESS RULES:
    company_time_zone.set.changed
    """
    tenant = business.tenant.id
    set_company_time_zone(session, tenant, "America/New_York")
    _refused(
        "company_time_zone_changed_since_review",
        lambda: set_company_time_zone(session, tenant, "Europe/Berlin", _expected=None),
    )


def test_a_shop_order_is_dated_on_the_companys_day(session, business):
    """
    BUSINESS TEST:
    A shop order is dated on the day the company lives its instant on.
    GIVEN:
    A Berlin company and shop orders at 23:30 on 31 October and 00:30 on
    1 November, Berlin time.
    WHEN:
    The orders are interpreted.
    THEN:
    The first is dated 31 October and the second 1 November.
    BUSINESS RULES:
    company_time_zone.day
    """
    set_company_time_zone(session, business.tenant.id, "Europe/Berlin")

    assert _order_day(session, business, 3491, "2026-10-31T23:30:00+01:00") == date(
        2026, 10, 31
    )
    assert _order_day(session, business, 3492, "2026-11-01T00:30:00+01:00") == date(
        2026, 11, 1
    )


def test_a_payment_and_an_overdue_day_follow_the_zone(session, business):
    """
    BUSINESS TEST:
    Days derived from instants follow the company's zone.
    GIVEN:
    An invoice due 31 October and the moment 23:30 UTC on 31 October, which is
    already 1 November in Berlin.
    WHEN:
    The aging is read and a payment is recorded at that moment.
    THEN:
    In UTC nothing is overdue and the payment is dated 31 October; in Berlin the
    invoice is a day overdue and the payment is dated 1 November.
    BUSINESS RULES:
    company_time_zone.day
    company_time_zone.today
    """
    tenant = business.tenant.id
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-349",
        business.customer.id,
        "100",
        document_date="2026-10-01",
        payment_term_code=_net30(session, tenant),
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    moment = datetime(2026, 10, 31, 23, 30, tzinfo=UTC)

    def overdue():
        (row,) = [
            row
            for row in core.aging_register(session, tenant, as_of=moment)
            if row["document"].id == invoice.id
        ]
        return row["days_overdue"]

    # Positive control: in UTC it is still 31 October.
    assert overdue() == 0
    assert company_day(session, tenant, moment) == date(2026, 10, 31)

    set_company_time_zone(session, tenant, "Europe/Berlin")

    assert overdue() == 1
    core.record_customer_payment(
        session,
        tenant,
        business.customer.id,
        "10",
        payment_number="PAY-349",
        effective_at=moment,
    )
    payment = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "PAY-349"
        )
    )
    assert payment.document_date == date(2026, 11, 1)


def test_a_register_day_filter_uses_the_companys_day(session, business):
    """
    BUSINESS TEST:
    A register filtered by day shows what happened on that local day.
    GIVEN:
    A receipt at 23:30 UTC on 31 October, 1 November in Berlin.
    WHEN:
    The movement register is filtered to 1 November.
    THEN:
    A UTC company does not list it; once Berlin is stated it does.
    BUSINESS RULES:
    company_time_zone.day
    """
    from reality.web.read_models import movement_page

    tenant = business.tenant.id
    movement = core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
        occurred_at=datetime(2026, 10, 31, 23, 30, tzinfo=UTC),
    )

    def listed():
        rows, _ = movement_page(
            session, tenant, date_from="2026-11-01", date_to="2026-11-01"
        )
        return movement.id in {row["movement"].id for row in rows}

    assert listed() is False
    set_company_time_zone(session, tenant, "Europe/Berlin")
    session.info.pop("company_time_zone", None)
    assert listed() is True


def test_the_next_clock_moment_is_the_local_midnight(session, business):
    """
    BUSINESS TEST:
    A due date turns overdue at the company's local midnight.
    GIVEN:
    A Berlin company with an invoice due 31 October 2026, read on that day.
    WHEN:
    The next moment a verdict can change is asked.
    THEN:
    It is midnight in Berlin, 23:00 UTC on 31 October, earlier than the idle
    floor a day later.
    BUSINESS RULES:
    company_time_zone.zone
    """
    from reality.services.exceptions import next_clock_moment

    tenant = business.tenant.id
    set_company_time_zone(session, tenant, "Europe/Berlin")
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-349-C",
        business.customer.id,
        "100",
        document_date="2026-10-01",
        payment_term_code=_net30(session, tenant),
    )
    core.post_sales_invoice(session, tenant, invoice.id)

    moment = next_clock_moment(
        session, tenant, as_of=datetime(2026, 10, 31, 9, tzinfo=UTC)
    )

    assert moment == datetime(2026, 10, 31, 23, tzinfo=UTC)


def test_another_company_keeps_its_own_zone(session, business):
    """
    BUSINESS TEST:
    A stated zone belongs to one company.
    GIVEN:
    One company states Berlin.
    WHEN:
    Another company reads its zone.
    THEN:
    It is still UTC.
    BUSINESS RULES:
    company_time_zone.state
    """
    set_company_time_zone(session, business.tenant.id, "Europe/Berlin")
    other = core.create_tenant(session, "Other GmbH")

    assert company_time_zone_state(session, other.id)["time_zone"] == "UTC"
