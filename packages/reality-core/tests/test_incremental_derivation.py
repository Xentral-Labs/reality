"""Incremental refresh and full rebuild must leave the same rows (spec 241 FR-006).

This file is the safety net, and it is written before any builder narrows. The
danger in deriving by change is not slowness: it is a builder asked for the rows of
one record that misses a row the change affects indirectly — a blocker that clears,
a total that shifts. The result is a stored projection that is quietly wrong, which
is worse than a slow one.

So the property is stated as a property, and a second test deliberately breaks a
builder to prove the first one would notice. A net that has never caught anything is
not known to be a net.
"""

import json

from sqlalchemy import select

from reality.db.core import ProjectionRow
from reality.services import projections
from reality.services.core import (
    create_commitment,
    create_document,
    post_sales_invoice,
    record_customer_payment,
    record_movement,
)

#: Fields that record *when* a row was derived rather than what it says. Two
#: refreshes a second apart differ in these and in nothing else, so comparing them
#: would make the property fail for a reason that has nothing to do with narrowing.
EVALUATION_TIME_FIELDS = {"as_of"}


def _content(payload):
    """A payload without the moment it was evaluated."""
    if isinstance(payload, dict):
        return {
            key: _content(value)
            for key, value in payload.items()
            if key not in EVALUATION_TIME_FIELDS
        }
    if isinstance(payload, list):
        return [_content(item) for item in payload]
    return payload


def snapshot(session, tenant_id: str) -> dict[tuple[str, str], object]:
    """Every stored row, by projection and key, with what it says.

    The payload is compared without its evaluation timestamp: an exception carries
    the moment it was judged, and the property here is that incremental and full
    derivation agree about the business, not that they ran in the same second.
    """
    return {
        (row.projection_name, row.record_key): _content(json.loads(row.payload))
        for row in session.scalars(
            select(ProjectionRow).where(ProjectionRow.tenant_id == tenant_id)
        )
    }


def a_little_business(session, business) -> None:
    """Enough of an order-to-cash to give every projection something to hold."""
    tenant = business.tenant.id
    order = create_document(
        session,
        tenant,
        "sales_order",
        "ORD-241",
        business.customer.id,
        "100",
        document_date="2026-08-01",
    )
    create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "4",
        "2026-08-10T00:00:00+00:00",
        document_id=order.id,
    )
    invoice = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-241",
        business.customer.id,
        "100",
        document_date="2026-08-02",
    )
    post_sales_invoice(session, tenant, invoice.id)
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "6",
        to_location_id=business.location.id,
    )
    # A payment, so the payments projection holds something and the coverage test
    # below can insist that every projection is inside the property.
    record_customer_payment(session, tenant, business.customer.id, "40")


def test_incremental_refresh_and_full_rebuild_leave_the_same_rows(session, business):
    """FR-006: the property, stated as a property.

    Today both paths run the same derivation, so this passes for a reason that will
    change. It is written now because the moment a builder narrows, this is the only
    thing standing between an optimisation and a silently wrong projection.
    """
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    incremental = snapshot(session, tenant)
    assert incremental, "the fixture produced no projection rows to compare"

    projections.refresh_operational_projections(session, tenant, force=True)
    full = snapshot(session, tenant)

    assert incremental == full


def test_the_comparison_notices_a_builder_that_drops_a_row(
    session, business, monkeypatch
):
    """The positive control: a net that has never caught anything is not a net.

    A builder is made to withhold one row — exactly the failure a wrong narrowing
    produces — and the comparison must fail. Without this, the test above would keep
    passing after somebody broke the thing it guards.
    """
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    complete = snapshot(session, tenant)

    original = projections.derive_projection_rows

    def short(session_, tenant_id, projection_name):
        rows = original(session_, tenant_id, projection_name)
        if projection_name == projections.DOCUMENT_REGISTER and rows:
            rows.pop(next(iter(rows)))
        return rows

    monkeypatch.setattr(projections, "derive_projection_rows", short)
    projections.refresh_operational_projections(session, tenant, force=True)
    narrowed = snapshot(session, tenant)

    assert narrowed != complete, (
        "a builder withheld a row and the comparison did not notice; the property "
        "test above is not guarding anything"
    )
    missing = set(complete) - set(narrowed)
    assert missing and all(name == projections.DOCUMENT_REGISTER for name, _ in missing)


def test_every_materialized_projection_is_covered_by_the_comparison(session, business):
    """A projection nobody built is a projection the property says nothing about."""
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant, force=True)
    built = {name for name, _ in snapshot(session, tenant)}
    missing = set(projections.MATERIALIZED_PROJECTIONS) - built
    assert not missing, (
        f"{sorted(missing)} produced no rows for this fixture, so the equivalence "
        "property does not cover them. Give the fixture a record they hold, or say "
        "here why they are empty."
    )


# --- the change set, and when it refuses to narrow (FR-001, FR-002, SC-004) ------


def test_the_change_set_names_the_records_whose_events_fell_in_the_window(
    session, business
):
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant, force=True)
    before = projections._latest_sequence(session, tenant)

    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-LATER",
        business.customer.id,
        "10",
        document_date="2026-08-05",
    )
    after = projections._latest_sequence(session, tenant)

    narrowing = projections.change_set(
        session, tenant, projections.DOCUMENT_REGISTER, before, after
    )
    assert narrowing.narrowed, narrowing.reason
    assert narrowing.subjects
    # Only what changed in the window, not the company.
    assert sum(len(ids) for ids in narrowing.subjects.values()) <= 4


def test_an_unknown_event_type_refuses_to_narrow(session, business):
    """Nothing may be assumed about what an unrecognised event left alone."""
    from reality.db.core import BusinessEvent, now, uid

    tenant = business.tenant.id
    a_little_business(session, business)
    before = projections._latest_sequence(session, tenant)
    session.add(
        BusinessEvent(
            id=uid("bev"),
            tenant_id=tenant,
            sequence=before + 1,
            event_type="something.the.catalog.does.not.list",
            schema_version=1,
            subject_type="document",
            subject_id="doc_probe",
            occurred_at=now(),
            payload="{}",
        )
    )
    session.flush()

    narrowing = projections.change_set(
        session, tenant, projections.DOCUMENT_REGISTER, before, before + 1
    )
    assert not narrowing.narrowed
    assert "unknown event type" in narrowing.reason


def test_too_many_changes_are_a_rebuild_wearing_another_name(session, business):
    """Visiting ten thousand records one at a time is slower than the company."""
    tenant = business.tenant.id
    a_little_business(session, business)
    before = 0
    after = projections._latest_sequence(session, tenant)
    monkey = projections.MAX_NARROWED_SUBJECTS
    try:
        projections.MAX_NARROWED_SUBJECTS = 1
        narrowing = projections.change_set(
            session, tenant, projections.DOCUMENT_REGISTER, before, after
        )
    finally:
        projections.MAX_NARROWED_SUBJECTS = monkey
    assert not narrowing.narrowed
    assert "too many" in narrowing.reason


def test_a_refresh_reports_which_projections_narrowed(session, business):
    """SC-004: all builders declining must look like that, not like success."""
    tenant = business.tenant.id
    a_little_business(session, business)
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant, force=True)
    assert report, "a refresh that built projections reported nothing about narrowing"
    # A forced rebuild narrows nothing, and says so rather than staying silent.
    assert all(reason for reason in report.values())
    assert set(report) <= set(projections.MATERIALIZED_PROJECTIONS)


# --- the first builder that narrows: the journal (FR-002, FR-003) ----------------


def _journal(session, tenant_id):
    return {
        key: payload
        for (name, key), payload in snapshot(session, tenant_id).items()
        if name == projections.JOURNAL
    }


def test_a_second_invoice_narrows_the_journal_and_agrees_with_the_company(
    session, business
):
    """The property again, on the path that now actually derives by change.

    The first two tests pass whether or not anything narrows. This one asserts that
    the journal did narrow — otherwise it would keep passing after a change quietly
    turned narrowing off, and prove nothing.
    """
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)

    second = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-241-B",
        business.customer.id,
        "60",
        document_date="2026-08-03",
    )
    post_sales_invoice(session, tenant, second.id)

    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report.get(projections.JOURNAL) is None, (
        f"the journal declined to narrow: {report.get(projections.JOURNAL)}"
    )
    narrowed = _journal(session, tenant)

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _journal(session, tenant)
    assert len(narrowed) > 2


def test_narrowing_the_journal_leaves_the_rows_it_did_not_look_at(session, business):
    """FR-003: a partial result is merged, not published as the whole projection."""
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    before = _journal(session, tenant)
    assert before

    second = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-241-C",
        business.customer.id,
        "25",
        document_date="2026-08-04",
    )
    post_sales_invoice(session, tenant, second.id)
    projections.refresh_operational_projections(session, tenant)
    after = _journal(session, tenant)

    assert set(before) < set(after), (
        "the earlier entries were dropped by a narrowed run"
    )
    assert all(after[key] == payload for key, payload in before.items())


def test_a_reversal_reaches_the_entries_no_event_names(session, business):
    """The reversing group is created by `ledger.reversed`, which names the original.

    Narrowing on the event's subject alone would leave the reversing entries out of
    the journal. This is the concrete shape of the danger the whole feature is built
    around, so it is pinned rather than trusted.
    """
    from reality.services.core import (
        journal_rows,
        reverse_ledger_posting_group,
    )

    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)

    group_id = journal_rows(session, tenant)[0].posting_group_id
    reverse_ledger_posting_group(
        session, tenant, group_id, reason="an entry posted to the wrong account"
    )

    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report.get(projections.JOURNAL) is None, report.get(projections.JOURNAL)
    narrowed = _journal(session, tenant)

    projections.refresh_operational_projections(session, tenant, force=True)
    complete = _journal(session, tenant)
    assert narrowed == complete
    reversing = {
        payload["posting_group_id"]
        for payload in complete.values()
        if payload["posting_group_id"] != group_id
    }
    assert reversing, "the fixture produced no reversing entries to miss"


def test_a_payment_run_is_a_change_the_journal_declines_to_narrow(session, business):
    """`payments.run` names the tenant, which is not a record a builder can visit."""
    changes = projections.ChangeSet({"tenant": frozenset({business.tenant.id})})
    outcome = projections._narrowed_journal(session, business.tenant.id, changes)
    assert isinstance(outcome, str)
    assert "tenant" in outcome


def test_a_version_change_evaluates_the_whole_projection(
    session, business, monkeypatch
):
    """FR-005: a new row shape applies to rows no event touched."""
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    monkeypatch.setattr(
        projections, "PROJECTION_VERSION", projections.PROJECTION_VERSION + 1
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report[projections.JOURNAL] == "projection version changed"


def test_a_narrowed_journal_writes_only_the_entries_that_changed(session, business):
    """What the feature is for, as a count rather than a stopwatch.

    Rows written is machine-independent; milliseconds are not. The full path writes
    every entry in the company, the narrowed path writes the posting group that
    changed, and the gap is the whole point of spec 181 FR-002.
    """
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    whole_company = projections.rebuild_projections(
        session, tenant, [projections.JOURNAL], force=True
    )
    session.commit()

    invoice = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-241-D",
        business.customer.id,
        "15",
        document_date="2026-08-06",
    )
    post_sales_invoice(session, tenant, invoice.id)
    written = projections.rebuild_projections(session, tenant, [projections.JOURNAL])
    session.commit()

    assert written < whole_company
    assert written == 2, "one sales invoice posts a two-sided entry and nothing else"


# --- the second builder: the document register (FR-002) --------------------------


def _register(session, tenant_id):
    return {
        key: payload
        for (name, key), payload in snapshot(session, tenant_id).items()
        if name == projections.DOCUMENT_REGISTER
    }


def test_a_new_order_narrows_the_document_register_and_agrees_with_the_company(
    session, business
):
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    before = _register(session, tenant)
    assert len(before) > 1

    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-241-E",
        business.customer.id,
        "30",
        document_date="2026-08-07",
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report.get(projections.DOCUMENT_REGISTER) is None, report.get(
        projections.DOCUMENT_REGISTER
    )
    narrowed = _register(session, tenant)

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _register(session, tenant)
    # FR-003: the documents nobody touched are still there, unchanged.
    assert set(before) < set(narrowed)
    assert all(narrowed[key] == payload for key, payload in before.items())


def test_a_party_change_reaches_every_document_that_cites_it(session, business):
    """A party is one record and many rows; the builder must resolve all of them."""
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    mine = {
        key
        for key, payload in _register(session, tenant).items()
        if payload["party_id"] == business.customer.id
    }
    assert len(mine) > 1, "the fixture gave this party only one document"

    changes = projections.ChangeSet({"party": frozenset({business.customer.id})})
    outcome = projections._narrowed_document_register(session, tenant, changes)
    assert isinstance(outcome, projections.NarrowedRows), outcome
    assert mine <= outcome.covers


def test_a_party_with_more_documents_than_the_ceiling_declines(
    session, business, monkeypatch
):
    """One record reaching the whole company is the slow path with extra steps."""
    tenant = business.tenant.id
    a_little_business(session, business)
    monkeypatch.setattr(projections, "MAX_NARROWED_ROWS", 1)
    changes = projections.ChangeSet({"party": frozenset({business.customer.id})})
    outcome = projections._narrowed_document_register(session, tenant, changes)
    assert isinstance(outcome, str)
    assert "not worth visiting one at a time" in outcome


def test_the_register_declines_a_subject_it_cannot_resolve(session, business):
    changes = projections.ChangeSet({"item": frozenset({business.item.id})})
    outcome = projections._narrowed_document_register(
        session, business.tenant.id, changes
    )
    assert isinstance(outcome, str)
    assert "item" in outcome


def test_a_narrowed_register_writes_only_the_documents_that_changed(session, business):
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    whole_company = projections.rebuild_projections(
        session, tenant, [projections.DOCUMENT_REGISTER], force=True
    )
    session.commit()

    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-241-F",
        business.customer.id,
        "12",
        document_date="2026-08-08",
    )
    written = projections.rebuild_projections(
        session, tenant, [projections.DOCUMENT_REGISTER]
    )
    session.commit()

    assert whole_company > 1
    assert written == 1, "one new order is one register row"


def test_a_promise_made_against_an_existing_order_updates_that_order_row(
    session, business
):
    """The changed record is a commitment; the row that changes belongs to a document.

    This is the shape the whole feature has to get right: the subject of the event is
    not the key of the row. Resolving it wrongly leaves `commitment_ids` stale, and
    the register would quietly disagree with the promises it lists.
    """
    tenant = business.tenant.id
    a_little_business(session, business)
    order = create_document(
        session,
        tenant,
        "sales_order",
        "ORD-241-G",
        business.customer.id,
        "80",
        document_date="2026-08-09",
    )
    projections.refresh_operational_projections(session, tenant)
    assert _register(session, tenant)[order.id]["commitment_ids"] == []

    create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        "2026-08-20T00:00:00+00:00",
        document_id=order.id,
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report.get(projections.DOCUMENT_REGISTER) is None, report.get(
        projections.DOCUMENT_REGISTER
    )
    assert _register(session, tenant)[order.id]["commitment_ids"] != []

    projections.refresh_operational_projections(session, tenant, force=True)
    assert _register(session, tenant)[order.id]["commitment_ids"] != []


# --- the third builder: stock (FR-002) -------------------------------------------


def _stock(session, tenant_id):
    return {
        key: payload
        for (name, key), payload in snapshot(session, tenant_id).items()
        if name == projections.INVENTORY
    }


def test_a_receipt_narrows_stock_and_agrees_with_the_company(session, business):
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    before = _stock(session, tenant)[business.item.id]["physical"]

    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "3",
        to_location_id=business.location.id,
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report.get(projections.INVENTORY) is None, report.get(projections.INVENTORY)
    narrowed = _stock(session, tenant)
    assert narrowed[business.item.id]["physical"] != before

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _stock(session, tenant)


def test_correcting_a_movement_onto_another_article_reaches_both(session, business):
    """The second trap of this shape, in a different service.

    `movement.corrected` names the movement that was corrected. The compensating and
    replacement movements it appends carry no event of their own, and a replacement may
    name a *different* article. Narrowing on the named movement alone leaves that
    article's stock stale.
    """
    from reality.services.core import correct_movement, create_item

    tenant = business.tenant.id
    other = create_item(session, tenant, "BIKE-BELL", "Bike Bell")
    a_little_business(session, business)
    wrong = record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    projections.refresh_operational_projections(session, tenant)
    assert _stock(session, tenant)[other.id]["physical"] == "0"

    correct_movement(
        session,
        tenant,
        wrong.id,
        reason="the receipt was booked onto the wrong article",
        replacement={
            "type": "receipt",
            "item_id": other.id,
            "quantity": "5",
            "to_location_id": business.location.id,
        },
        _commit=False,
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report.get(projections.INVENTORY) is None, report.get(projections.INVENTORY)
    narrowed = _stock(session, tenant)

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _stock(session, tenant)
    assert narrowed[other.id]["physical"] != "0", (
        "the replacement movement's article kept its stale stock"
    )


def test_stock_declines_a_location_it_cannot_resolve_to_an_article(session, business):
    changes = projections.ChangeSet({"location": frozenset({business.location.id})})
    outcome = projections._narrowed_inventory(session, business.tenant.id, changes)
    assert isinstance(outcome, str)
    assert "location" in outcome


def test_stock_declines_an_observation_about_a_document(session, business):
    """A Fact reaches stock through its subject, and a document is not an article."""
    from reality.db.core import Fact, now, uid

    tenant = business.tenant.id
    a_little_business(session, business)
    fact = Fact(
        id=uid("fct"),
        tenant_id=tenant,
        subject_type="document",
        subject_id="doc_probe",
        predicate="payment_promised",
        value="{}",
        observed_at=now(),
    )
    session.add(fact)
    session.flush()
    changes = projections.ChangeSet({"fact": frozenset({fact.id})})
    outcome = projections._narrowed_inventory(session, tenant, changes)
    assert isinstance(outcome, str)
    assert "document" in outcome


def test_a_narrowed_stock_refresh_writes_only_the_articles_that_changed(
    session, business
):
    from reality.services.core import create_item

    tenant = business.tenant.id
    create_item(session, tenant, "BIKE-PUMP", "Bike Pump")
    create_item(session, tenant, "BIKE-LOCK", "Bike Lock")
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    whole_company = projections.rebuild_projections(
        session, tenant, [projections.INVENTORY], force=True
    )
    session.commit()

    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    written = projections.rebuild_projections(session, tenant, [projections.INVENTORY])
    session.commit()

    assert whole_company >= 3
    assert written == 1, "one receipt touches one article"


# --- the fourth builder: supply and demand (FR-002) ------------------------------


def _supply(session, tenant_id):
    return {
        key: payload
        for (name, key), payload in snapshot(session, tenant_id).items()
        if name == projections.ITEM_SUPPLY_DEMAND
    }


def _promise(session, business, number: str, quantity: str):
    """An order with one open delivery promise on the fixture's article."""
    tenant = business.tenant.id
    order = create_document(
        session,
        tenant,
        "sales_order",
        number,
        business.customer.id,
        "100",
        document_date="2026-08-01",
    )
    return order, create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        "2026-08-20T00:00:00+00:00",
        document_id=order.id,
    )


def test_a_new_promise_narrows_supply_and_demand_and_agrees_with_the_company(
    session, business
):
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    before = _supply(session, tenant)[business.item.id]["open_customer_demand"]

    _promise(session, business, "ORD-241-SD", "2")
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    reason = report.get(projections.ITEM_SUPPLY_DEMAND)
    assert reason is None, reason
    narrowed = _supply(session, tenant)
    assert narrowed[business.item.id]["open_customer_demand"] != before

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _supply(session, tenant)


def test_a_receipt_narrows_supply_and_demand_and_agrees_with_the_company(
    session, business
):
    """Stock moves and the uncovered demand for that article moves with it."""
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    before = _supply(session, tenant)[business.item.id]

    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "7",
        to_location_id=business.location.id,
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    reason = report.get(projections.ITEM_SUPPLY_DEMAND)
    assert reason is None, reason
    narrowed = _supply(session, tenant)
    assert narrowed[business.item.id]["available"] != before["available"]

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _supply(session, tenant)


def test_a_delivery_hold_on_a_party_reaches_the_articles_it_stops(session, business):
    """The subject question, asked of this projection (spec 241).

    `party.delivery_hold_placed` names the party and nothing else. What it stops is
    every open promise to that party, and each of those is about an article whose row
    now counts a blocked order. Resolving only the records the event names would find
    no article at all, and the hold would be invisible in supply and demand until
    something else touched that article.
    """
    from reality.services.core import hold_party_delivery, reserve

    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, commitment = _promise(session, business, "ORD-241-HOLD", "4")
    # Fully reserved, so the only thing that can block this order is the hold.
    reserve(session, tenant, commitment.id, "4", _commit=False)
    projections.refresh_operational_projections(session, tenant)
    assert _supply(session, tenant)[business.item.id]["blocked_order_count"] == 0

    hold_party_delivery(session, tenant, business.customer.id, "credit_check")
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    reason = report.get(projections.ITEM_SUPPLY_DEMAND)
    assert reason is None, reason
    narrowed = _supply(session, tenant)
    assert narrowed[business.item.id]["blocked_order_count"] == 1, (
        "the hold on the party left the article it stops unblocked"
    )

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _supply(session, tenant)


def test_supply_and_demand_declines_a_subject_it_cannot_resolve(session, business):
    changes = projections.ChangeSet({"location": frozenset({business.location.id})})
    outcome = projections._narrowed_item_supply_demand(
        session, business.tenant.id, changes
    )
    assert isinstance(outcome, str)
    assert "supply and demand" in outcome and "location" in outcome


def test_closing_promises_names_the_company_and_is_declined(session, business):
    """`promises.closed` names the tenant, which is not an article to visit."""
    changes = projections.ChangeSet({"tenant": frozenset({business.tenant.id})})
    outcome = projections._narrowed_item_supply_demand(
        session, business.tenant.id, changes
    )
    assert isinstance(outcome, str)
    assert "tenant" in outcome


def test_a_narrowed_supply_and_demand_refresh_writes_only_the_articles_that_changed(
    session, business
):
    from reality.services.core import create_item

    tenant = business.tenant.id
    create_item(session, tenant, "BIKE-PUMP", "Bike Pump")
    create_item(session, tenant, "BIKE-LOCK", "Bike Lock")
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    whole_company = projections.rebuild_projections(
        session, tenant, [projections.ITEM_SUPPLY_DEMAND], force=True
    )
    session.commit()

    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    written = projections.rebuild_projections(
        session, tenant, [projections.ITEM_SUPPLY_DEMAND]
    )
    session.commit()

    assert whole_company >= 3
    assert written == 1, "one receipt touches one article"


def test_a_cancelled_promise_leaves_the_demand_it_was_counted_in(session, business):
    """FR-003: a promise that is over is no longer open work.

    The narrowed path reads the promises of the article it was given, and it reads
    only the open ones — the same predicate the whole-company path applies. Without
    it the article would keep the demand of a promise nobody is waiting for, and no
    later event would take it away.
    """
    from reality.services.core import cancel_commitment

    tenant = business.tenant.id
    a_little_business(session, business)
    _, cancelled = _promise(session, business, "ORD-241-GONE", "5")
    projections.refresh_operational_projections(session, tenant)
    with_promise = _supply(session, tenant)[business.item.id]["open_customer_demand"]

    cancel_commitment(session, tenant, cancelled.id, _commit=False)
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    reason = report.get(projections.ITEM_SUPPLY_DEMAND)
    assert reason is None, reason
    narrowed = _supply(session, tenant)
    assert narrowed[business.item.id]["open_customer_demand"] != with_promise, (
        "the cancelled promise is still counted as demand"
    )

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _supply(session, tenant)


# --- the fifth and sixth builders: the queue and its blockers (FR-002) -----------


def _queue(session, tenant_id):
    return {
        key: payload
        for (name, key), payload in snapshot(session, tenant_id).items()
        if name == projections.FULFILLMENT_QUEUE
    }


def _blockers(session, tenant_id):
    return {
        key: payload
        for (name, key), payload in snapshot(session, tenant_id).items()
        if name == projections.FULFILLMENT_BLOCKERS
    }


def test_every_reason_a_promise_can_be_blocked_by_is_declared(session, business):
    """The narrowed blockers refresh deletes by key, so the list must be complete.

    A reason the rules can produce and the list does not name would leave a stale
    blocker behind for ever: no row is produced for it, and no key speaks for it.
    """
    from reality.services.core import hold_commitment, hold_party_delivery

    tenant = business.tenant.id
    _, commitment = _promise(session, business, "ORD-241-ALL", "4")
    hold_commitment(session, tenant, commitment.id, "credit_check", _commit=False)
    hold_party_delivery(session, tenant, business.customer.id, "compliance")
    session.flush()
    projections.refresh_operational_projections(session, tenant)

    reasons = {row["blocker_type"] for row in _blockers(session, tenant).values()}
    assert reasons == set(projections.DELIVERY_BLOCKER_TYPES), (
        "the declared reasons and the rules that produce them have drifted apart"
    )


def test_a_new_order_narrows_the_queue_and_agrees_with_the_company(session, business):
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    before = set(_queue(session, tenant))

    order, _ = _promise(session, business, "ORD-241-Q", "3")
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    for name in (projections.FULFILLMENT_QUEUE, projections.FULFILLMENT_BLOCKERS):
        assert report.get(name) is None, report.get(name)
    narrowed = _queue(session, tenant)
    assert set(narrowed) - before == {order.id}

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _queue(session, tenant)
    assert _blockers(session, tenant)


def test_an_order_whose_last_promise_is_finished_leaves_the_queue(session, business):
    """What a narrowed refresh speaks for is the orders it resolved, not its rows.

    A shipment that closes the last open promise of an order produces no queue row
    for it — and that is exactly the refresh that has to remove one.
    """
    from reality.services.core import record_movement

    tenant = business.tenant.id
    order, commitment = _promise(session, business, "ORD-241-DONE", "2")
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    projections.refresh_operational_projections(session, tenant)
    assert order.id in _queue(session, tenant)

    record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    reason = report.get(projections.FULFILLMENT_QUEUE)
    assert reason is None, reason
    narrowed = _queue(session, tenant)
    assert order.id not in narrowed, "the finished order kept its place in the queue"

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _queue(session, tenant)


def test_a_blocker_that_cleared_is_removed_although_nothing_produces_its_row(
    session, business
):
    from reality.services.core import hold_commitment, release_commitment_hold

    tenant = business.tenant.id
    _, commitment = _promise(session, business, "ORD-241-BLK", "2")
    hold_commitment(session, tenant, commitment.id, "credit_check", _commit=False)
    projections.refresh_operational_projections(session, tenant)
    held = f"{commitment.id}:commitment_hold"
    assert held in _blockers(session, tenant)

    release_commitment_hold(session, tenant, commitment.id, _commit=False)
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    reason = report.get(projections.FULFILLMENT_BLOCKERS)
    assert reason is None, reason
    narrowed = _blockers(session, tenant)
    assert held not in narrowed, "the released hold kept its blocker"

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _blockers(session, tenant)


def test_a_correction_that_moves_a_shipment_to_another_promise_reaches_both_orders(
    session, business
):
    """The movement-correction trap, one step worse than in stock.

    `movement.corrected` names the movement that was corrected. The replacement it
    appends carries no event, and it may be booked against a **different promise** —
    the service then settles the status of both promises, so two orders change and
    the one event names neither of them.
    """
    from reality.services.core import correct_movement, record_movement

    tenant = business.tenant.id
    first, first_promise = _promise(session, business, "ORD-241-C1", "2")
    second, _ = _promise(session, business, "ORD-241-C2", "2")
    second_promise = session.scalars(
        select(projections.Commitment).where(
            projections.Commitment.tenant_id == tenant,
            projections.Commitment.document_id == second.id,
        )
    ).one()
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    wrong = record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=first_promise.id,
    )
    projections.refresh_operational_projections(session, tenant)
    assert first.id not in _queue(session, tenant), "the shipped order is finished"
    assert second.id in _queue(session, tenant)

    correct_movement(
        session,
        tenant,
        wrong.id,
        reason="the shipment belonged to the other order",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "2",
            "from_location_id": business.location.id,
            "commitment_id": second_promise.id,
        },
        _commit=False,
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    reason = report.get(projections.FULFILLMENT_QUEUE)
    assert reason is None, reason
    narrowed = _queue(session, tenant)

    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _queue(session, tenant)
    assert first.id in narrowed, "the order the shipment was taken off stayed finished"
    assert second.id not in narrowed, "the order it was moved to stayed open"


def test_the_queue_declines_a_subject_it_cannot_resolve(session, business):
    changes = projections.ChangeSet({"tenant": frozenset({business.tenant.id})})
    outcome = projections._narrowed_fulfillment_queue(
        session, business.tenant.id, changes
    )
    assert isinstance(outcome, str)
    assert "the fulfillment queue" in outcome and "tenant" in outcome


def test_a_narrowed_queue_refresh_writes_only_the_orders_that_changed(
    session, business
):
    tenant = business.tenant.id
    for number in ("ORD-241-W1", "ORD-241-W2", "ORD-241-W3"):
        _promise(session, business, number, "1")
    projections.refresh_operational_projections(session, tenant)
    whole_company = projections.rebuild_projections(
        session, tenant, [projections.FULFILLMENT_QUEUE], force=True
    )
    session.commit()

    _promise(session, business, "ORD-241-W4", "1")
    written = projections.rebuild_projections(
        session, tenant, [projections.FULFILLMENT_QUEUE]
    )
    session.commit()

    assert whole_company >= 3
    assert written == 1, "one new order touches one order"
