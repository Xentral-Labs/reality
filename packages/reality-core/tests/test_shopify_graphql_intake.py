"""Spec 388: original GraphQL entity -> retained exact review, never acceptance."""

import copy
import json

import pytest
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Commitment, Document, Movement
from reality.integrations.shopify.graphql import GraphQLOrderNeedsReview, project_order
from reality.services.core import (
    InterpretationNeedsReview,
    NotFound,
    create_tenant,
    enqueue_shopify_order,
)
from reality.services.intake import prepare_intake, review_intake
from reality.services.shopify_graphql import capture_shopify_graphql_source


def order():
    return {
        "id": "gid://shopify/Order/1004",
        "name": "#1004",
        "createdAt": "2026-11-09T12:00:00Z",
        "updatedAt": "2026-11-09T12:00:00Z",
        "cancelledAt": None,
        "displayFulfillmentStatus": "UNFULFILLED",
        "currencyCode": "EUR",
        "totalPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "EUR"}},
        "customer": None,
        "unknownOriginal": {"private": "PRESERVE-ORIGINAL"},
        "lineItems": {
            "nodes": [
                {
                    "id": "gid://shopify/LineItem/41",
                    "name": "Bike Light",
                    "sku": "BIKE-LIGHT",
                    "quantity": 2,
                    "currentQuantity": 2,
                    "requiresShipping": True,
                    "originalUnitPriceSet": {
                        "shopMoney": {"amount": "5.00", "currencyCode": "EUR"}
                    },
                    "originalUnknown": "keep",
                }
            ],
            "pageInfo": {"hasNextPage": False, "endCursor": "cursor"},
        },
    }


def mapping(business):
    return {
        "company_party_id": business.company.id,
        "customer_party_id": business.customer.id,
        "location_id": business.location.id,
    }


def test_projection_is_received_not_recomputed_and_original_is_unchanged():
    raw = order()
    before = copy.deepcopy(raw)
    projection = project_order(raw, "1004")
    assert projection["total_price"] == "10.00"
    assert projection["line_items"][0]["price"] == "5.00"
    assert "total_price" not in projection["line_items"][0]
    assert raw == before


@pytest.mark.parametrize(
    "change",
    ["identity", "partial", "currency", "quantity", "cancelled", "fulfillment"],
)
def test_unsupported_projection_requires_review(change):
    raw = order()
    if change == "identity":
        raw["id"] = "gid://shopify/Order/999"
    if change == "partial":
        raw["lineItems"]["pageInfo"]["hasNextPage"] = True
    if change == "currency":
        raw["totalPriceSet"]["shopMoney"]["currencyCode"] = "USD"
    if change == "quantity":
        raw["lineItems"]["nodes"][0]["currentQuantity"] = 1
    if change == "cancelled":
        raw["cancelledAt"] = "2026-11-09T13:00:00Z"
    if change == "fulfillment":
        raw["displayFulfillmentStatus"] = "FULFILLED"
    with pytest.raises(GraphQLOrderNeedsReview):
        project_order(raw, "1004")


def test_original_entity_prepares_one_real_proposal_without_business_effects(
    session, business
):
    raw = order()
    source, job = capture_shopify_graphql_source(
        session, business.tenant.id, order=raw, **mapping(business)
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert proposal.status == "proposed"
    assert review["plan"]["source_record_id"] == source.id
    assert review["plan"]["source_hash"] == source.payload_hash
    assert review["plan"]["effects"][0]["arguments"]["lines"][0]["gross_amount"] is None
    assert (
        review["plan"]["effects"][0]["arguments"]["_source_line_payloads"]
        == raw["lineItems"]["nodes"]
    )
    assert json.loads(source.payload) == raw
    again, replay = capture_shopify_graphql_source(
        session, business.tenant.id, order=raw, **mapping(business)
    )
    assert (again.id, replay.id) == (source.id, job.id)
    assert prepare_intake(session, business.tenant.id, job.id).id == proposal.id
    for model in (Document, Commitment, Movement):
        assert session.scalar(select(func.count()).select_from(model)) == 0
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == 1


def test_missing_buyer_is_retained_review_not_fabricated_proposal(session, business):
    source, job = capture_shopify_graphql_source(
        session,
        business.tenant.id,
        order=order(),
        company_party_id=business.company.id,
        location_id=business.location.id,
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, business.tenant.id, job.id)
    session.refresh(job)
    assert job.status == "review_required"
    assert json.loads(job.error)["reason_code"] == "shopify_graphql_mapping_required"
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == 0
    assert json.loads(source.payload) == order()


def test_foreign_mapping_never_prepares_or_exposes_foreign_records(session, business):
    other = create_tenant(session, "Other synthetic company")
    source, job = capture_shopify_graphql_source(
        session, other.id, order=order(), **mapping(business)
    )
    with pytest.raises(NotFound):
        prepare_intake(session, other.id, job.id)
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == 0
    assert source.tenant_id == other.id


def test_legacy_accepted_order_identity_cannot_be_created_again_via_graphql(
    session, business
):
    from pathlib import Path

    from reality.services.intake import apply_prepared_intake

    raw = json.loads(
        (Path(__file__).parents[1] / "fixtures/shopify/order_10473.json").read_text()
    )
    source, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        raw,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    apply_prepared_intake(
        session, business.tenant.id, proposal.id, review["digest"], confirmed=True
    )
    graph = order()
    graph["id"] = f"gid://shopify/Order/{source.external_id}"
    _, next_job = capture_shopify_graphql_source(
        session, business.tenant.id, order=graph, **mapping(business)
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, business.tenant.id, next_job.id)
    assert session.scalar(select(func.count()).select_from(Document)) == 1


def test_mcp_capture_permission_never_grants_generic_confirmation(session, business):
    from reality.mcp.catalog import dispatch_mcp_tool
    from reality.mcp.principal import MCPPrincipal

    principal = MCPPrincipal(
        authentication_kind="manual",
        credential_id="synthetic",
        grant_id=None,
        user_id=None,
        tenant_id=business.tenant.id,
        client_id="test",
        scopes=frozenset(),
        allowed_tools=frozenset({"shopify_order_graphql_capture"}),
    )
    result = dispatch_mcp_tool(
        session,
        principal,
        "shopify_order_graphql_capture",
        {"order": order(), **mapping(business)},
    )
    assert result["business_effects_accepted"] is False
    assert result["source_record_id"]
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    with pytest.raises(PermissionError):
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {"proposal_id": "foreign"},
        )
    with pytest.raises(PermissionError):
        dispatch_mcp_tool(
            session, principal, "source_record_ingest_propose", {"payload": {}}
        )


def test_capture_replay_cannot_silently_replace_missing_frozen_buyer(session, business):
    from reality.services.core import InvalidOperation

    source, job = capture_shopify_graphql_source(
        session,
        business.tenant.id,
        order=order(),
        company_party_id=business.company.id,
        location_id=business.location.id,
    )
    with pytest.raises(InvalidOperation, match="frozen mappings"):
        capture_shopify_graphql_source(
            session, business.tenant.id, order=order(), **mapping(business)
        )
    session.refresh(job)
    assert "customer_party_id" not in json.loads(job.input)
    assert json.loads(source.payload) == order()


@pytest.mark.parametrize(
    "bad",
    [
        {"updatedAt": "2026-11-09T12:00:00"},
        {"id": "gid://shopify/Order/not-an-id"},
        {"unknownOriginal": float("nan")},
    ],
)
def test_capture_invalid_identity_time_and_non_json_are_refused_before_source(
    session, business, bad
):
    from reality.db.core import SourceRecord
    from reality.services.core import InvalidOperation

    raw = order()
    raw.update(bad)
    with pytest.raises(InvalidOperation):
        capture_shopify_graphql_source(session, business.tenant.id, order=raw)
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == 0


def test_acquisition_context_requires_exact_named_shop_when_present(session, business):
    from reality.services.core import InvalidOperation

    acquisition = {
        "shop": "pilot.myshopify.com",
        "api_version": "2026-07",
        "query_digest": "a" * 64,
        "observed_at": "2026-11-09T12:00:00Z",
        "coverage": "complete-selected-order",
    }
    _, job = capture_shopify_graphql_source(
        session, business.tenant.id, order=order(), acquisition=acquisition
    )
    assert json.loads(job.input)["acquisition"] == acquisition
    for bad in [
        {key: value for key, value in acquisition.items() if key != "shop"},
        {**acquisition, "shop": "https://untrusted.example"},
    ]:
        with pytest.raises(InvalidOperation):
            capture_shopify_graphql_source(
                session, business.tenant.id, order=order(), acquisition=bad
            )
