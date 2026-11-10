"""Spec390: exact retained read diagnosis is not preparation or acceptance."""

import json
from pathlib import Path

import pytest
import test_shopify_buyer_mapping as mapping_support
from sqlalchemy import event, select
from test_shopify_buyer_mapping import commit, prepare, proof

from reality.db.core import (
    ChangeProposal,
    Commitment,
    Document,
    ImportJob,
    InterpretationOutcome,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    PartyRole,
    SourceRecord,
    SourceStream,
    uid,
)
from reality.services import shopify_intake_preflight as preflight
from reality.services.core import InterpretationNeedsReview, InvalidOperation
from reality.services.intake import prepare_intake
from reality.services.shopify_graphql import capture_shopify_graphql_source


@pytest.fixture
def bound(session, business):
    return mapping_support.bound.__wrapped__(session, business)


def arguments(x):
    return {
        "source_record_id": x["source"].id,
        "import_job_id": x["job"].id,
        "source_hash": x["source"].payload_hash,
        "source_version": x["source"].version,
    }


def read(session, x):
    return preflight.shopify_source_intake_preflight(
        session, x["policy"].tenant_id, **arguments(x)
    )


def mapped(session, x):
    review = prepare(session, x)
    commit(session, x, review, proof(x, review))
    return x


def with_references(session, x):
    raw = {**x["raw"], "id": "gid://shopify/Order/1005", "name": "#1005"}
    acquisition = json.loads(x["job_input"])["acquisition"]
    source, job = capture_shopify_graphql_source(
        session,
        x["policy"].tenant_id,
        order=raw,
        acquisition=acquisition,
        company_party_id=x["business"].company.id,
        location_id=x["business"].location.id,
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, x["policy"].tenant_id, job.id)
    policy = x["policy"].model_copy(
        update={
            "source_record_id": source.id,
            "import_job_id": job.id,
            "source_hash": source.payload_hash,
            "source_version": source.version,
            "order_id": raw["id"],
        }
    )
    return {
        **x,
        "source": source,
        "job": job,
        "policy": policy,
        "raw": raw,
        "job_input": job.input,
    }


def snapshot(session):
    result = {}
    for model in [
        SourceRecord,
        SourceStream,
        ImportJob,
        InterpretationOutcome,
        ChangeProposal,
        Party,
        PartyRole,
        Location,
        Item,
        Document,
        Commitment,
        Movement,
        LedgerEntry,
    ]:
        rows = session.execute(select(model.__table__)).mappings().all()
        result[model.__tablename__] = sorted(
            [json.dumps(dict(row), sort_keys=True, default=str) for row in rows]
        )
    return result


def test_exact_mapped_source_explains_remaining_work_without_any_write(session, bound):
    x = mapped(session, bound)
    session.flush()
    before = snapshot(session)
    statements = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        result = read(session, x)
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
    assert snapshot(session) == before
    assert all(
        s.lstrip().split()[0].upper()
        not in {"INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"}
        for s in statements
    )
    assert result["buyer"]["status"] == "verified"
    assert result["source_binding"]["tenant_id"] == x["policy"].tenant_id
    assert result["company"]["status"] == result["location"]["status"] == "missing"
    assert result["lines"][0]["item_status"] == "matched"
    assert result["lines"][0]["source_unit"] is None
    assert result["lines"][0]["stock_unit"] == x["business"].item.unit
    assert (
        result["preparation_performed"] is result["business_effects_accepted"] is False
    )
    assert result["financial"]["line_totals"] == "not_interpreted"
    assert "unit_mapping_not_proved" in {i["code"] for i in result["blockers"]}


def test_retained_existing_company_location_are_observed_never_chosen(session, bound):
    x = mapped(session, with_references(session, bound))
    result = read(session, x)
    assert result["company"]["status"] == result["location"]["status"] == "matched"
    assert result["company"]["record_id"] == x["business"].company.id
    assert result["location"]["record_id"] == x["business"].location.id
    x["business"].location.allows_stock = False
    session.flush()
    assert read(session, x)["location"]["status"] == "stock_not_allowed"


def test_buyer_missing_or_historical_changed_customer_is_not_current_mapping(
    session, bound
):
    assert read(session, bound)["buyer"] == {"status": "missing", "mapping": None}
    mapped(session, bound)
    bound["business"].customer.is_active = False
    session.flush()
    result = read(session, bound)
    assert result["buyer"]["status"] == "stale"
    assert result["buyer"]["mapping"]["current_basis"]["customer_current"] is False


@pytest.mark.parametrize(
    "change",
    [
        {"source_hash": "b" * 64},
        {"source_version": 2},
        {"import_job_id": "unknown"},
        {"source_record_id": "unknown"},
    ],
)
def test_wrong_expected_basis_never_returns_fresh_report(session, bound, change):
    with pytest.raises(InvalidOperation):
        preflight.shopify_source_intake_preflight(
            session, bound["policy"].tenant_id, **{**arguments(bound), **change}
        )


def test_duplicate_active_sku_has_no_chosen_item_or_unit(session, bound):
    original = bound["business"].item
    session.add(
        Item(
            id=uid("itm"),
            tenant_id=original.tenant_id,
            sku=original.sku,
            name="Ambiguous legacy item",
            unit="box",
            is_active=True,
        )
    )
    session.flush()
    line = read(session, bound)["lines"][0]
    assert line["item_status"] == "ambiguous"
    assert line["item_id"] is line["item_digest"] is line["stock_unit"] is None


def test_schema_examples_are_native_valid_and_unicode_digest_is_canonical():
    from jsonschema import Draft202012Validator

    from reality.domain.shopify_intake_preflight import PreflightReport, semantic_digest

    folder = (
        Path(__file__).resolve().parents[3]
        / "specs/390-shopify-intake-preflight/contracts"
    )
    for schema, example in [
        ("input.schema.json", "request.example.json"),
        ("response.schema.json", "response.example.json"),
    ]:
        validator = Draft202012Validator(json.loads((folder / schema).read_text()))
        validator.validate(json.loads((folder / example).read_text()))
    report = json.loads((folder / "response.example.json").read_text())
    assert PreflightReport.model_validate(report)
    assert semantic_digest(report) == report["output_digest"]
    report["observed_at"] = "2026-11-10T12:00:00Z"
    assert semantic_digest(report) == report["output_digest"]
    report["buyer"]["mapping"]["customer"]["label"] = "Changed buyer"
    assert semantic_digest(report) != report["output_digest"]


def test_stale_latest_source_and_foreign_tenant_are_unavailable(session, bound):
    from reality.services.core import create_tenant

    other = create_tenant(session, "Foreign preflight tenant")
    with pytest.raises(InvalidOperation):
        preflight.shopify_source_intake_preflight(session, other.id, **arguments(bound))
    raw = {**bound["raw"], "updatedAt": "2026-11-09T12:01:00Z"}
    capture_shopify_graphql_source(
        session,
        bound["policy"].tenant_id,
        order=raw,
        acquisition=json.loads(bound["job_input"])["acquisition"],
    )
    with pytest.raises(InvalidOperation):
        read(session, bound)


@pytest.mark.parametrize("status", ["inactive", "not_found", "missing_sku"])
def test_non_eligible_items_do_not_supply_default_unit(session, bound, status):
    item = bound["business"].item
    if status == "inactive":
        item.is_active = False
    elif status == "not_found":
        item.sku = "OTHER-SKU"
    else:
        # This fixture creates a new immutable observation; the service never rewrites it.
        raw = {
            **bound["raw"],
            "id": "gid://shopify/Order/1006",
            "name": "#1006",
            "lineItems": {
                "nodes": [{**bound["raw"]["lineItems"]["nodes"][0], "sku": None}],
                "pageInfo": {"hasNextPage": False},
            },
        }
        source, job = capture_shopify_graphql_source(
            session,
            bound["policy"].tenant_id,
            order=raw,
            acquisition=json.loads(bound["job_input"])["acquisition"],
        )
        with pytest.raises(InterpretationNeedsReview):
            prepare_intake(session, bound["policy"].tenant_id, job.id)
        bound = {**bound, "source": source, "job": job}
    session.flush()
    line = read(session, bound)["lines"][0]
    assert line["item_status"] == status
    assert line["stock_unit"] is line["source_unit"] is line["item_id"] is None


def test_company_role_and_location_never_expose_foreign_records(session, bound):
    from sqlalchemy import delete

    from reality.services.core import create_location, create_tenant

    x = with_references(session, bound)
    session.execute(
        delete(PartyRole).where(
            PartyRole.tenant_id == x["policy"].tenant_id,
            PartyRole.party_id == x["business"].company.id,
            PartyRole.role == "company",
        )
    )
    session.flush()
    assert read(session, x)["company"]["status"] == "role_mismatch"
    foreign = create_tenant(session, "Foreign location company")
    other = create_location(session, foreign.id, "FOREIGN-LOCATION-CANARY")
    # Only fixture setup changes retained input to model a bad legacy reference.
    original = x["job"].input
    context = json.loads(original)
    context["location_id"] = other.id
    x["job"].input = json.dumps(context)
    session.flush()
    result = read(session, x)
    assert result["location"] == {
        "status": "not_found",
        "record_id": other.id,
        "label": None,
        "digest": None,
    }
    assert "FOREIGN-LOCATION-CANARY" not in json.dumps(result)
    assert x["job"].input == json.dumps(context)


def test_unsupported_selected_entity_has_no_interpreted_financial_or_item_claims(
    session, bound
):
    raw = {
        **bound["raw"],
        "id": "gid://shopify/Order/1007",
        "name": "#1007",
        "displayFulfillmentStatus": "FULFILLED",
    }
    source, job = capture_shopify_graphql_source(
        session,
        bound["policy"].tenant_id,
        order=raw,
        acquisition=json.loads(bound["job_input"])["acquisition"],
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, bound["policy"].tenant_id, job.id)
    result = read(session, {**bound, "source": source, "job": job})
    assert result["source_interpretation"]["status"] == "requires_review"
    assert result["financial"]["currency"] is result["financial"]["order_total"] is None
    assert result["lines"] == []
    assert result["coverage"]["lines_complete"] is False


def test_complete_and_bounded_selected_coverage_is_explicit(session, bound):
    base = bound["raw"]["lineItems"]["nodes"][0]
    raw = {
        **bound["raw"],
        "id": "gid://shopify/Order/1008",
        "name": "#1008",
        "lineItems": {
            "nodes": [
                {**base, "id": f"gid://shopify/LineItem/{i + 1}", "sku": None}
                for i in range(101)
            ],
            "pageInfo": {"hasNextPage": False},
        },
    }
    source, job = capture_shopify_graphql_source(
        session,
        bound["policy"].tenant_id,
        order=raw,
        acquisition=json.loads(bound["job_input"])["acquisition"],
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, bound["policy"].tenant_id, job.id)
    result = read(session, {**bound, "source": source, "job": job})
    assert len(result["lines"]) == 100
    assert result["coverage"] == {
        "scope": "retained_selected_entity",
        "line_count": 101,
        "returned_line_count": 100,
        "lines_complete": False,
    }
    assert {"code": "line_coverage_incomplete", "affected_line_count": 1} in result[
        "blockers"
    ]


def test_report_digest_changes_with_master_basis_but_not_time(
    session, bound, monkeypatch
):
    from datetime import UTC, datetime

    a = read(session, bound)
    monkeypatch.setattr(
        preflight.core, "now", lambda: datetime(2026, 11, 10, tzinfo=UTC)
    )
    assert read(session, bound)["output_digest"] == a["output_digest"]
    bound["business"].item.name = "Changed item meaning"
    session.flush()
    assert read(session, bound)["output_digest"] != a["output_digest"]


def test_requested_overrides_and_oversized_report_are_refused(
    session, bound, monkeypatch
):
    with pytest.raises(InvalidOperation):
        preflight.shopify_source_intake_preflight(
            session,
            bound["policy"].tenant_id,
            **arguments(bound),
            customer_party_id=bound["business"].customer.id,
        )
    import reality.domain.shopify_intake_preflight as contracts

    monkeypatch.setattr(contracts, "MAX_REPORT_BYTES", 100)
    with pytest.raises(InvalidOperation):
        read(session, bound)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_lines",
        "wrong_buyer_status",
        "matched_reference_missing",
        "ambiguous_chosen_item",
        "wrong_count",
    ],
)
def test_report_semantics_reject_malformed_fresh_looking_values(mutation):
    from reality.domain.shopify_intake_preflight import PreflightReport, semantic_digest

    folder = (
        Path(__file__).resolve().parents[3]
        / "specs/390-shopify-intake-preflight/contracts"
    )
    report = json.loads((folder / "response.example.json").read_text())
    if mutation == "duplicate_lines":
        report["lines"].append(report["lines"][0])
        report["coverage"].update(line_count=2, returned_line_count=2)
    elif mutation == "wrong_buyer_status":
        report["buyer"]["status"] = "missing"
    elif mutation == "matched_reference_missing":
        report["company"]["status"] = "matched"
    elif mutation == "ambiguous_chosen_item":
        report["lines"][0]["item_status"] = "ambiguous"
    else:
        report["coverage"]["returned_line_count"] = 0
    report["output_digest"] = semantic_digest(report)
    with pytest.raises(ValueError):
        PreflightReport.model_validate(report)


@pytest.mark.parametrize(
    "changed",
    ["item_unit", "location", "company_role", "sku_ambiguity", "accepted_order"],
)
def test_two_session_master_change_during_read_refuses_mixed_report(
    postgres_database, monkeypatch, request, changed
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from types import SimpleNamespace

    from sqlalchemy import create_engine, delete
    from sqlalchemy.orm import Session

    from reality.db.core import Base
    from reality.services.core import (
        create_item,
        create_location,
        create_party,
        create_tenant,
    )

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    request.addfinalizer(engine.dispose)
    request.addfinalizer(session.close)
    tenant = create_tenant(session, "Owned concurrent preflight company")
    business = SimpleNamespace(
        tenant=tenant,
        company=create_party(session, tenant.id, "Existing company", "company"),
        customer=create_party(session, tenant.id, "Existing buyer", "customer"),
        item=create_item(session, tenant.id, "BIKE-LIGHT", "Light"),
        location=create_location(session, tenant.id, "Existing location"),
    )
    x = mapped(
        session,
        with_references(session, mapping_support.bound.__wrapped__(session, business)),
    )
    session.commit()
    reached, changed_done = Event(), Event()
    original = preflight._item_check

    def delayed(*args, **kwargs):
        result = original(*args, **kwargs)
        if not reached.is_set():
            reached.set()
            assert changed_done.wait(5)
        return result

    monkeypatch.setattr(preflight, "_item_check", delayed)

    def actual_read():
        with Session(engine) as reader:
            try:
                read(reader, x)
            except InvalidOperation:
                return "unavailable"
            return "incorrect_mixed_report"

    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(actual_read)
        assert reached.wait(5)
        try:
            with Session(engine) as writer:
                if changed == "item_unit":
                    writer.get(
                        Item, {"tenant_id": tenant.id, "id": business.item.id}
                    ).unit = "box"
                elif changed == "location":
                    writer.get(
                        Location, {"tenant_id": tenant.id, "id": business.location.id}
                    ).allows_stock = False
                elif changed == "company_role":
                    writer.execute(
                        delete(PartyRole).where(
                            PartyRole.tenant_id == tenant.id,
                            PartyRole.party_id == business.company.id,
                            PartyRole.role == "company",
                        )
                    )
                elif changed == "accepted_order":
                    writer.add(
                        Document(
                            id=uid("doc"),
                            tenant_id=tenant.id,
                            type="sales_order",
                            number="Concurrent accepted order",
                            source_record_id=x["source"].id,
                            party_id=business.customer.id,
                        )
                    )
                else:
                    writer.add(
                        Item(
                            id=uid("itm"),
                            tenant_id=tenant.id,
                            sku="BIKE-LIGHT",
                            name="New active duplicate",
                            unit="pcs",
                            is_active=True,
                        )
                    )
                writer.commit()
        finally:
            changed_done.set()
        assert result.result(timeout=5) == "unavailable"


def test_source_stated_total_and_uninterpreted_extra_fields_are_not_recomputed(
    session, bound
):
    raw = {
        **bound["raw"],
        "id": "gid://shopify/Order/1009",
        "name": "#1009",
        "totalPriceSet": {"shopMoney": {"amount": "13.2700", "currencyCode": "EUR"}},
        "lineItems": {
            "nodes": [
                {
                    **bound["raw"]["lineItems"]["nodes"][0],
                    "discountedTotalSet": {
                        "shopMoney": {"amount": "12.34", "currencyCode": "EUR"}
                    },
                    "unit": "box",
                }
            ],
            "pageInfo": {"hasNextPage": False},
        },
    }
    source, job = capture_shopify_graphql_source(
        session,
        bound["policy"].tenant_id,
        order=raw,
        acquisition=json.loads(bound["job_input"])["acquisition"],
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, bound["policy"].tenant_id, job.id)
    result = read(session, {**bound, "source": source, "job": job})
    assert result["financial"]["order_total"] == "13.2700"
    assert result["financial"]["line_totals"] == "not_interpreted"
    assert result["lines"][0]["source_unit"] is None
    assert json.loads(source.payload) == raw


def test_same_external_already_accepted_order_is_not_supported_first_intake(
    session, bound
):
    from reality.services.core import create_tenant
    from reality.services.shopify_source_reads import accepted_order_exists

    session.add(
        Document(
            id=uid("doc"),
            tenant_id=bound["policy"].tenant_id,
            type="sales_order",
            number="Existing accepted order",
            source_record_id=bound["source"].id,
            party_id=bound["business"].customer.id,
        )
    )
    session.flush()
    result = read(session, bound)
    assert result["source_interpretation"]["status"] == "requires_review"
    assert result["lines"] == []
    foreign = create_tenant(session, "Foreign accepted order read")
    assert accepted_order_exists(session, foreign.id, bound["source"]) is None


def test_read_does_not_autoflush_unrelated_pending_master_changes(session, bound):
    pending = Party(
        id=uid("par"),
        tenant_id=bound["policy"].tenant_id,
        type="customer",
        name="Unrelated pending customer",
    )
    session.add(pending)
    statements = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        read(session, bound)
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
    assert pending in session.new
    assert all(
        statement.lstrip().split()[0].upper() != "INSERT" for statement in statements
    )
    session.expunge(pending)


def test_valid_large_source_cannot_publish_oversized_partial_report(session, bound):
    sku = "X" * 200
    bound["business"].item.sku = sku
    session.flush()
    base = bound["raw"]["lineItems"]["nodes"][0]
    raw = {
        **bound["raw"],
        "id": "gid://shopify/Order/1010",
        "name": "#1010",
        "lineItems": {
            "nodes": [
                {**base, "id": f"gid://shopify/LineItem/{i + 1}", "sku": sku}
                for i in range(100)
            ],
            "pageInfo": {"hasNextPage": False},
        },
    }
    source, job = capture_shopify_graphql_source(
        session,
        bound["policy"].tenant_id,
        order=raw,
        acquisition=json.loads(bound["job_input"])["acquisition"],
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, bound["policy"].tenant_id, job.id)
    before = snapshot(session)
    with pytest.raises(InvalidOperation):
        read(session, {**bound, "source": source, "job": job})
    assert snapshot(session) == before
