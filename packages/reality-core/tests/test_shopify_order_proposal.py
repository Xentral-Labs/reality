"""Spec391: an explicit proposed mapping is not order acceptance."""

import json
from uuid import uuid4

import pytest
import test_shopify_buyer_mapping as support
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Commitment, Document, LedgerEntry, Movement
from reality.services import shopify_order_proposal as orders
from reality.services.core import InterpretationNeedsReview, InvalidOperation
from reality.services.intake import prepare_intake
from reality.services.shopify_graphql import capture_shopify_graphql_source


@pytest.fixture
def selected(session, business):
    x = support.bound.__wrapped__(session, business)
    review = support.prepare(session, x)
    support.commit(session, x, review, support.proof(x, review))
    request = {
        "request_id": str(uuid4()),
        "source_record_id": x["source"].id,
        "import_job_id": x["job"].id,
        "source_hash": x["source"].payload_hash,
        "source_version": x["source"].version,
        "buyer_review_id": review["review_id"],
        "buyer_review_digest": review["review_digest"],
        "company_party_id": business.company.id,
        "location_id": business.location.id,
        "lines": [
            {
                "source_line_id": x["raw"]["lineItems"]["nodes"][0]["id"],
                "item_id": business.item.id,
                "stock_unit": business.item.unit,
                "quantity_semantics": "one_source_count_is_one_stock_unit",
            }
        ],
    }
    return x, request


def counts(session):
    return {
        m.__name__: session.scalar(select(func.count()).select_from(m))
        for m in [Document, Commitment, Movement, LedgerEntry]
    }


def test_exact_proposal_preserves_source_input_unknown_price_and_no_effects(
    session, selected
):
    x, request = selected
    before = counts(session)
    original = x["source"].payload, x["job"].input
    result = orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
    assert result["status"] == "proposed"
    import os
    from pathlib import Path

    if os.environ.get("REALITY_391_TEST_ARTIFACT_DIR"):
        folder = Path(os.environ["REALITY_391_TEST_ARTIFACT_DIR"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "native-request.json").write_text(
            json.dumps(request, indent=2, ensure_ascii=False) + "\n"
        )
        (folder / "native-response.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        )
    assert (
        result["application_allowed"]
        is result["generic_confirmation_allowed"]
        is result["business_effects_accepted"]
        is False
    )
    document = result["review_projection"]["effects"][0]["arguments"]
    assert (
        document["gross_amount"] == "10.00" and document["lines"][0]["quantity"] == "2"
    )
    assert (
        document["lines"][0]["unit_price"]
        is document["lines"][0]["gross_amount"]
        is None
    )
    assert result["source_price_evidence"][0]["amount"] == "5.00"
    assert (
        result["mapping_bundle"]["state"] == "proposed"
        and "acceptance_not_implemented" in result["holds"]
    )
    assert "_source_line_payloads" not in json.dumps(result)
    assert counts(session) == before
    session.refresh(x["source"])
    session.refresh(x["job"])
    assert (x["source"].payload, x["job"].input) == original
    assert (
        orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
        == result
    )
    assert (
        orders.review_shopify_order(
            session, x["policy"].tenant_id, proposal_id=result["proposal_id"]
        )
        == result
    )
    row = session.scalar(
        select(ChangeProposal).where(ChangeProposal.id == result["proposal_id"])
    )
    assert row.decided_by_user_id is row.decided_via_token_id is None
    assert (
        json.loads(row.input)["proposal"]["plan"]["effects"][0]["arguments"][
            "_source_line_payloads"
        ]
        == x["raw"]["lineItems"]["nodes"]
    )


def test_legacy_graphql_needs_explicit_quantity_semantics(session, business):
    raw = {
        **support.bound.__wrapped__(session, business)["raw"],
        "id": "gid://shopify/Order/2000",
        "name": "#2000",
    }
    _, job = capture_shopify_graphql_source(
        session,
        business.tenant.id,
        order=raw,
        company_party_id=business.company.id,
        customer_party_id=business.customer.id,
        location_id=business.location.id,
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, business.tenant.id, job.id)
    assert all(v == 0 for v in counts(session).values())


def test_master_change_marks_old_meaning_stale_not_refreshed(session, selected):
    x, request = selected
    first = orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
    x["business"].item.name = "Changed item"
    session.flush()
    result = orders.review_shopify_order(
        session, x["policy"].tenant_id, proposal_id=first["proposal_id"]
    )
    assert (
        result["status"] == "stale"
        and result["review_digest"] == first["review_digest"]
    )
    assert result["mapping_bundle"] == first["mapping_bundle"]


@pytest.mark.parametrize(
    "change",
    [
        {"source_hash": "b" * 64},
        {"buyer_review_digest": "b" * 64},
        {"company_party_id": "foreign"},
        {"location_id": "foreign"},
        {"expected_company_digest": "b" * 64},
        {"amount": "1.00"},
    ],
)
def test_bad_request_never_creates_proposal(session, selected, change):
    x, request = selected
    before = session.scalar(select(func.count()).select_from(ChangeProposal))
    with pytest.raises(InvalidOperation):
        orders.prepare_shopify_order(
            session, x["policy"].tenant_id, **{**request, **change}
        )
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == before
    assert all(v == 0 for v in counts(session).values())


def test_nonce_cannot_change_meaning_or_generic_confirmation_execute(session, selected):
    from reality.tools.application import approve_and_execute_proposal

    x, request = selected
    result = orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
    with pytest.raises(InvalidOperation):
        orders.prepare_shopify_order(
            session,
            x["policy"].tenant_id,
            **{**request, "lines": [{**request["lines"][0], "stock_unit": "box"}]},
        )
    with pytest.raises((InvalidOperation, ValueError)):
        approve_and_execute_proposal(
            session, x["policy"].tenant_id, result["proposal_id"], confirmed=True
        )
    assert all(v == 0 for v in counts(session).values())


def test_foreign_proposal_reads_and_preparation_are_non_disclosing(session, selected):
    from reality.services.core import create_tenant

    x, request = selected
    result = orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
    foreign = create_tenant(session, "Foreign order proposal tenant")
    with pytest.raises(InvalidOperation):
        orders.review_shopify_order(
            session, foreign.id, proposal_id=result["proposal_id"]
        )
    with pytest.raises(InvalidOperation):
        orders.prepare_shopify_order(
            session, foreign.id, **{**request, "request_id": str(uuid4())}
        )
    assert all(v == 0 for v in counts(session).values())


def test_product_type_is_master_evidence_not_shipping_inference(session, selected):
    x, request = selected
    x["business"].item.item_type = "service"
    session.flush()
    result = orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
    effects = result["review_projection"]["effects"]
    assert effects[0]["arguments"]["lines"][0]["line_type"] == "service"
    assert "shipping_item_type_requires_review" in result["holds"]
    assert not any(effect["operation"] == "commitment" for effect in effects)


def test_nonshipping_stocked_product_remains_item(session, selected):
    x, request = selected
    raw = {
        **x["raw"],
        "id": "gid://shopify/Order/2001",
        "name": "#2001",
        "lineItems": {
            "nodes": [{**x["raw"]["lineItems"]["nodes"][0], "requiresShipping": False}],
            "pageInfo": {"hasNextPage": False},
        },
    }
    source, job = capture_shopify_graphql_source(
        session,
        x["policy"].tenant_id,
        order=raw,
        acquisition=json.loads(x["job_input"])["acquisition"],
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, x["policy"].tenant_id, job.id)
    y = {
        **x,
        "source": source,
        "job": job,
        "raw": raw,
        "job_input": job.input,
        "policy": x["policy"].model_copy(
            update={
                "source_record_id": source.id,
                "import_job_id": job.id,
                "source_hash": source.payload_hash,
                "source_version": source.version,
                "order_id": raw["id"],
            }
        ),
    }
    buyer = support.prepare(session, y)
    support.commit(session, y, buyer, support.proof(y, buyer))
    request = {
        **request,
        "request_id": str(uuid4()),
        "source_record_id": source.id,
        "import_job_id": job.id,
        "source_hash": source.payload_hash,
        "source_version": source.version,
        "buyer_review_id": buyer["review_id"],
        "buyer_review_digest": buyer["review_digest"],
    }
    result = orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
    assert (
        result["review_projection"]["effects"][0]["arguments"]["lines"][0]["line_type"]
        == "item"
    )
    assert "non_shipping_item_fulfillment_not_interpreted" in result["holds"]


def test_explicit_units_and_complete_membership_are_required(session, selected):
    x, request = selected
    for changed in [
        {**request["lines"][0], "stock_unit": "box"},
        {**request["lines"][0], "quantity_semantics": "default"},
        {**request["lines"][0], "source_line_id": "gid://shopify/LineItem/999"},
    ]:
        with pytest.raises(InvalidOperation):
            orders.prepare_shopify_order(
                session, x["policy"].tenant_id, **{**request, "lines": [changed]}
            )
    assert all(v == 0 for v in counts(session).values())


@pytest.mark.parametrize("phase", ["prepare", "review"])
def test_two_session_change_during_resolution_never_declares_current(
    postgres_database, monkeypatch, request, phase
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from types import SimpleNamespace

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.db.core import Base, Item
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
    tenant = create_tenant(session, "Owned order proposal race")
    business = SimpleNamespace(
        tenant=tenant,
        company=create_party(session, tenant.id, "Company", "company"),
        customer=create_party(session, tenant.id, "Buyer", "customer"),
        item=create_item(session, tenant.id, "BIKE-LIGHT", "Light"),
        location=create_location(session, tenant.id, "Location"),
    )
    _x, arguments = globals()["selected"].__wrapped__(session, business)
    held = (
        orders.prepare_shopify_order(session, tenant.id, **arguments)
        if phase == "review"
        else None
    )
    session.commit()
    entered, changed = Event(), Event()
    original = orders._resolve

    def delayed(*args, **kwargs):
        value = original(*args, **kwargs)
        if not entered.is_set():
            entered.set()
            assert changed.wait(5)
        return value

    monkeypatch.setattr(orders, "_resolve", delayed)

    def actual():
        with Session(engine) as reader:
            try:
                if phase == "review":
                    return orders.review_shopify_order(
                        reader, tenant.id, proposal_id=held["proposal_id"]
                    )["status"]
                orders.prepare_shopify_order(reader, tenant.id, **arguments)
            except InvalidOperation:
                return "refused"
            return "incorrect_current"

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(actual)
        assert entered.wait(5)
        try:
            with Session(engine) as writer:
                writer.get(
                    Item, {"tenant_id": tenant.id, "id": business.item.id}
                ).name = "Changed during read"
                writer.commit()
        finally:
            changed.set()
        assert pending.result(timeout=5) == (
            "stale" if phase == "review" else "refused"
        )


def test_normal_mcp_propose_grant_never_grants_confirmation_and_revoke_is_current(
    session, selected
):
    from reality.db.core import now
    from reality.mcp.auth import create_mcp_access_token
    from reality.mcp.catalog import dispatch_mcp_tool
    from reality.mcp.principal import MCPPrincipal

    x, request = selected
    allowed = ["shopify_source_order_prepare", "shopify_source_order_review"]
    token, _ = create_mcp_access_token(
        session, x["policy"].tenant_id, "Synthetic proposal-only token", allowed
    )
    principal = MCPPrincipal(
        authentication_kind="manual",
        credential_id=token.id,
        grant_id=None,
        user_id=None,
        tenant_id=x["policy"].tenant_id,
        client_id="test",
        scopes=frozenset(),
        allowed_tools=frozenset(allowed),
    )
    result = dispatch_mcp_tool(session, principal, allowed[0], request)
    assert (
        dispatch_mcp_tool(
            session, principal, allowed[1], {"proposal_id": result["proposal_id"]}
        )
        == result
    )
    with pytest.raises(PermissionError):
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {"proposal_id": result["proposal_id"]},
        )
    token.revoked_at = now()
    session.commit()
    with pytest.raises(InvalidOperation):
        dispatch_mcp_tool(session, principal, allowed[0], request)
    assert all(v == 0 for v in counts(session).values())


def test_inactive_selected_item_is_historical_stale_not_read_error(session, selected):
    x, request = selected
    result = orders.prepare_shopify_order(session, x["policy"].tenant_id, **request)
    x["business"].item.is_active = False
    session.flush()
    assert (
        orders.review_shopify_order(
            session, x["policy"].tenant_id, proposal_id=result["proposal_id"]
        )["status"]
        == "stale"
    )
