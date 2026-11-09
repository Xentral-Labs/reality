"""Spec392: supported prices remain received evidence, never recomputed authority."""

import copy

import pytest
from test_shopify_graphql_intake import order

from reality.domain.shopify_order_acceptance import inspect_simple_source

TOTAL_FIELDS = ["subtotalPriceSet", "currentSubtotalPriceSet", "currentTotalPriceSet"]
ZERO_FIELDS = [
    "totalDiscountsSet",
    "currentTotalDiscountsSet",
    "totalTaxSet",
    "currentTotalTaxSet",
    "totalShippingPriceSet",
    "currentShippingPriceSet",
    "totalRefundedSet",
    "totalTipReceivedSet",
]
NULL_FIELDS = [
    "originalTotalDutiesSet",
    "currentTotalDutiesSet",
    "originalTotalAdditionalFeesSet",
    "currentTotalAdditionalFeesSet",
]


def complete_order():
    raw = order()
    raw.update(processedAt=raw["createdAt"], edited=False, additionalFees=[])
    for field in TOTAL_FIELDS:
        raw[field] = {"shopMoney": {"amount": "10.00", "currencyCode": "EUR"}}
    for field in ZERO_FIELDS:
        raw[field] = {"shopMoney": {"amount": "0.00", "currencyCode": "EUR"}}
    for field in NULL_FIELDS:
        raw[field] = None
    raw["lineItems"]["nodes"][0].update(
        originalTotalSet={"shopMoney": {"amount": "10.00", "currencyCode": "EUR"}},
        duties=[],
    )
    return raw


def test_complete_source_preserves_strings_and_documented_null_absence():
    raw = complete_order()
    before = copy.deepcopy(raw)
    result = inspect_simple_source(raw)
    assert result["holds"] == []
    assert result["fees"]["status"] == "not_applicable"
    assert result["duties"]["status"] == "not_applicable_no_line_duties"
    assert "amount" not in result["fees"] and "amount" not in result["duties"]
    assert result["lines"][0]["unit_price"] == "5.00"
    assert result["lines"][0]["line_total"] == "10.00"
    assert raw == before


@pytest.mark.parametrize("field", ZERO_FIELDS + NULL_FIELDS)
def test_nonzero_or_unknown_ancillary_money_is_held(field):
    raw = complete_order()
    raw[field] = {"shopMoney": {"amount": "0.01", "currencyCode": "EUR"}}
    assert inspect_simple_source(raw)["holds"]
    del raw[field]
    assert inspect_simple_source(raw)["holds"]


@pytest.mark.parametrize(
    "change",
    [
        "rounding",
        "line",
        "subtotal",
        "currency",
        "edit",
        "partial",
        "fees",
        "duties",
        "quantity",
    ],
)
def test_missing_evidence_and_rounding_are_never_invented(change):
    raw = complete_order()
    line = raw["lineItems"]["nodes"][0]
    if change == "rounding":
        line["originalUnitPriceSet"]["shopMoney"]["amount"] = (
            "3.333333333333333333333333333333333333"
        )
    if change == "line":
        line["originalTotalSet"]["shopMoney"]["amount"] = "9.99"
    if change == "subtotal":
        raw["subtotalPriceSet"]["shopMoney"]["amount"] = "9.99"
    if change == "currency":
        line["originalTotalSet"]["shopMoney"]["currencyCode"] = "USD"
    if change == "edit":
        raw["edited"] = True
    if change == "partial":
        raw["lineItems"]["pageInfo"]["hasNextPage"] = True
    if change == "fees":
        del raw["additionalFees"]
    if change == "duties":
        del line["duties"]
    if change == "quantity":
        line["currentQuantity"] = 1
    assert inspect_simple_source(raw)["holds"]


def test_legacy391_is_held_and_unchanged():
    raw = order()
    before = copy.deepcopy(raw)
    assert inspect_simple_source(raw)["holds"]
    assert raw == before


@pytest.fixture
def acceptance_selected(session, business):
    from datetime import UTC, datetime, timedelta
    from uuid import uuid4

    import test_shopify_buyer_mapping as mapping_support

    from reality.domain.shopify_order_acceptance import AcceptancePolicy
    from reality.mcp.auth import create_mcp_access_token
    from reality.mcp.principal import MCPPrincipal
    from reality.services.company_time_zone import set_company_time_zone
    from reality.services.finance.accounts import lock_finance
    from reality.services.shopify_graphql import capture_shopify_graphql_source

    x = mapping_support.bound.__wrapped__(session, business)
    raw = complete_order()
    raw["updatedAt"] = "2026-11-09T13:00:00Z"
    source, job = capture_shopify_graphql_source(
        session,
        business.tenant.id,
        order=raw,
        acquisition={
            "shop": x["policy"].shop,
            "api_version": "2026-07",
            "query_digest": "b" * 64,
            "observed_at": raw["updatedAt"],
            "coverage": "complete-selected-order",
        },
    )
    x.update(
        source=source,
        job=job,
        raw=raw,
        policy=x["policy"].model_copy(
            update={
                "source_record_id": source.id,
                "import_job_id": job.id,
                "source_hash": source.payload_hash,
                "source_version": source.version,
                "query_digest": "b" * 64,
            }
        ),
    )
    from reality.services.core import InterpretationNeedsReview
    from reality.services.intake import prepare_intake

    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, business.tenant.id, job.id)
    buyer = mapping_support.prepare(session, x)
    mapping_support.commit(session, x, buyer, mapping_support.proof(x, buyer))
    business.customer.credit_limit = 1000
    session.commit()
    set_company_time_zone(session, business.tenant.id, "Europe/Berlin")
    lock_finance(session, business.tenant.id)
    session.commit()
    token, _ = create_mcp_access_token(
        session, business.tenant.id, "Owned synthetic external acceptance token", ["*"]
    )
    principal = MCPPrincipal(
        authentication_kind="manual",
        credential_id=token.id,
        grant_id=None,
        user_id=None,
        tenant_id=business.tenant.id,
        client_id="synthetic-392",
        scopes=frozenset(),
        allowed_tools=frozenset({"*"}),
    )
    policy = AcceptancePolicy(
        purpose="shopify_source_order_acceptance/1",
        tenant_id=business.tenant.id,
        shop=x["policy"].shop,
        query_digest="b" * 64,
        issuer=x["policy"].issuer,
        key_id=x["policy"].key_id,
        public_key=x["policy"].public_key,
        allowed_subjects=["tuesday-person"],
        allowed_token_ids=[token.id],
        currency="EUR",
        max_order_amount="100.00",
        max_order_units=100,
        max_effects=101,
        review_max_age_seconds=300,
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )
    request = {
        "request_id": str(uuid4()),
        "source_record_id": source.id,
        "import_job_id": job.id,
        "source_hash": source.payload_hash,
        "source_version": source.version,
        "buyer_review_id": buyer["review_id"],
        "buyer_review_digest": buyer["review_digest"],
        "company_party_id": business.company.id,
        "location_id": business.location.id,
        "lines": [
            {
                "source_line_id": raw["lineItems"]["nodes"][0]["id"],
                "item_id": business.item.id,
                "stock_unit": business.item.unit,
                "quantity_semantics": "one_source_count_is_one_stock_unit",
            }
        ],
        "interpretation_profile": "shopify_simple_undiscounted_order/1",
        "delivery_terms": "not_promised",
    }
    return {
        **x,
        "acceptance_policy": policy,
        "principal": principal,
        "token": token,
        "request": request,
        "original": (source.payload, job.input),
    }


def test_successor_has_one_complete_source_backed_review_without_business_writes(
    session, acceptance_selected
):
    from sqlalchemy import func, select

    from reality.db.core import Commitment, Document, LedgerEntry, Movement
    from reality.mcp.principal import mcp_principal_context
    from reality.services.shopify_order_acceptance import (
        prepare_order_acceptance,
        review_order_acceptance,
    )

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        result = prepare_order_acceptance(
            session, x["policy"].tenant_id, x["request"], policy=x["acceptance_policy"]
        )
        assert result["eligible_for_exact_authorization"] is True
        assert result["holds"] == []
        document = result["review_projection"]["effects"][0]["arguments"]
        assert document["lines"][0]["unit_price"] == "5.00"
        assert document["lines"][0]["gross_amount"] == "10.00"
        assert document["document_date"] == "2026-11-09"
        assert result["readiness"]["credit"]["status"] == "pass"
        assert (
            prepare_order_acceptance(
                session,
                x["policy"].tenant_id,
                x["request"],
                policy=x["acceptance_policy"],
            )
            == result
        )
        assert (
            review_order_acceptance(
                session,
                x["policy"].tenant_id,
                {"proposal_id": result["proposal_id"]},
                policy=x["acceptance_policy"],
            )
            == result
        )
    assert (x["source"].payload, x["job"].input) == x["original"]
    assert all(
        session.scalar(select(func.count()).select_from(model)) == 0
        for model in [Document, Commitment, Movement, LedgerEntry]
    )


def acceptance_proof(x, review, *, kind="human", **overrides):
    import json
    from datetime import UTC, datetime
    from uuid import uuid4

    from test_shopify_buyer_mapping import b64

    from reality.domain.intake import content_digest

    now = int(datetime.now(UTC).timestamp())
    claims = {
        "iss": x["acceptance_policy"].issuer,
        "aud": "reality:shopify-source-order-acceptance/1",
        "sub": "tuesday-person",
        "iat": now,
        "exp": now + 300,
        "jti": str(uuid4()),
        "purpose": "shopify_source_order_acceptance/1",
        "tenant_id": x["policy"].tenant_id,
        "proposal_id": review["proposal_id"],
        "review_digest": review["review_digest"],
        "source_binding_digest": content_digest(review["source_binding"]),
        "mapping_bundle_digest": content_digest(review["mapping_bundle"]),
        "plan_digest": review["plan_digest"],
        "authorization_kind": kind,
        **overrides,
    }
    header = b64(
        json.dumps(
            {
                "alg": "EdDSA",
                "typ": "tuesday-shopify-order-acceptance+jwt",
                "kid": x["acceptance_policy"].key_id,
            },
            separators=(",", ":"),
        ).encode()
    )
    body = b64(json.dumps(claims, separators=(",", ":")).encode())
    return f"{header}.{body}.{b64(x['key'].sign(f'{header}.{body}'.encode()))}"


def test_exact_human_acceptance_atomic_receipt_replay_and_original_preserved(
    session, acceptance_selected
):
    from sqlalchemy import func, select

    from reality.db.core import (
        ChangeProposal,
        Commitment,
        Document,
        LedgerEntry,
        Movement,
    )
    from reality.mcp.principal import mcp_principal_context
    from reality.services.shopify_order_acceptance import (
        accept_order,
        order_acceptance_status,
        prepare_order_acceptance,
    )

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        review = prepare_order_acceptance(
            session, x["policy"].tenant_id, x["request"], policy=x["acceptance_policy"]
        )
        signed = acceptance_proof(x, review)
        args = {
            "proposal_id": review["proposal_id"],
            "review_digest": review["review_digest"],
            "approval_proof": signed,
        }
        result = accept_order(
            session, x["policy"].tenant_id, args, policy=x["acceptance_policy"]
        )
        from reality.services.shopify_order_acceptance import review_order_acceptance

        accepted_review = review_order_acceptance(
            session,
            x["policy"].tenant_id,
            {"proposal_id": review["proposal_id"]},
            policy=x["acceptance_policy"],
        )
        assert (
            accepted_review["buyer_mapping_scope"]
            == "existing_buyer_mapping_evidence_at_order_review"
        )
        assert "remaining_review" not in accepted_review["buyer_mapping"]
        assert "current_basis" not in accepted_review["buyer_mapping"]
        assert accepted_review["currentness"] == "historical_accepted_only"
        assert result["verification"] == "applied"
        assert result["approval"]["issuer"] == x["acceptance_policy"].issuer
        assert result["approval"]["authorization_kind"] == "human"
        assert (
            result["original_source_unchanged"]
            is result["import_job_input_unchanged"]
            is True
        )
        assert (
            accept_order(
                session, x["policy"].tenant_id, args, policy=x["acceptance_policy"]
            )
            == result
        )
        assert (
            order_acceptance_status(
                session, x["policy"].tenant_id, {"proposal_id": review["proposal_id"]}
            )["receipt"]
            == result
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    assert session.scalar(select(func.count()).select_from(Commitment)) == 1
    assert session.scalar(select(func.count()).select_from(Movement)) == 0
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    document = session.scalar(select(Document))
    assert document.gross_amount == 10
    assert result["source_stated_order_amount"] == "10.00"
    row = session.scalar(
        select(ChangeProposal).where(ChangeProposal.id == review["proposal_id"])
    )
    assert row.decided_by_user_id is None and row.decided_via_token_id == x["token"].id
    session.refresh(x["source"])
    session.refresh(x["job"])
    assert (x["source"].payload, x["job"].input) == x["original"]
    assert x["job"].status == "completed"


def test_coherent_unrepresentable_source_amount_is_held_without_rounding():
    raw = complete_order()
    line = raw["lineItems"]["nodes"][0]
    line["originalUnitPriceSet"]["shopMoney"]["amount"] = "5.000001"
    line["originalTotalSet"]["shopMoney"]["amount"] = "10.000002"
    for field in (*TOTAL_FIELDS, "totalPriceSet"):
        raw[field]["shopMoney"]["amount"] = "10.000002"
    before = copy.deepcopy(raw)
    assert (
        "source_money_not_exactly_representable_by_canonical_storage"
        in inspect_simple_source(raw)["holds"]
    )
    assert raw == before


def business_counts(session):
    from sqlalchemy import func, select

    from reality.db.core import Commitment, Document, LedgerEntry, Movement

    return {
        model.__name__: session.scalar(select(func.count()).select_from(model))
        for model in [Document, Commitment, Movement, LedgerEntry]
    }


def prepared(session, x):
    from reality.services.shopify_order_acceptance import prepare_order_acceptance

    return prepare_order_acceptance(
        session, x["policy"].tenant_id, x["request"], policy=x["acceptance_policy"]
    )


@pytest.mark.parametrize(
    "change", ["source", "plan", "purpose", "expired", "subject", "issuer"]
)
def test_wrong_or_expired_external_proof_never_creates_business_effects(
    session, acceptance_selected, change
):
    from datetime import UTC, datetime

    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    overrides = {
        "source": {"source_binding_digest": "f" * 64},
        "plan": {"plan_digest": "f" * 64},
        "purpose": {"purpose": "shopify_source_buyer_mapping_only/1"},
        "expired": {"exp": int(datetime.now(UTC).timestamp()) - 1},
        "subject": {"sub": "ungranted-person"},
        "issuer": {"iss": "urn:untrusted"},
    }[change]
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        before = business_counts(session)
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": review["proposal_id"],
                    "review_digest": review["review_digest"],
                    "approval_proof": acceptance_proof(x, review, **overrides),
                },
                policy=x["acceptance_policy"],
            )
        assert business_counts(session) == before


@pytest.mark.parametrize("change", ["token", "customer", "policy", "item", "calendar"])
def test_revocation_and_changed_exact_basis_never_apply(
    session, acceptance_selected, change
):
    from reality.mcp.auth import revoke_mcp_access_token
    from reality.mcp.principal import mcp_principal_context
    from reality.services.company_time_zone import set_company_time_zone
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
    signed = acceptance_proof(x, review)
    if change == "token":
        revoke_mcp_access_token(session, x["policy"].tenant_id, x["token"].id)
    if change == "customer":
        x["business"].customer.credit_limit = 999
        session.commit()
    if change == "item":
        x["business"].item.is_active = False
        session.commit()
    if change == "calendar":
        set_company_time_zone(session, x["policy"].tenant_id, "America/New_York")
    policy = (
        x["acceptance_policy"].model_copy(update={"max_order_units": 1})
        if change == "policy"
        else x["acceptance_policy"]
    )
    with mcp_principal_context(x["principal"]), pytest.raises(InvalidOperation):
        accept_order(
            session,
            x["policy"].tenant_id,
            {
                "proposal_id": review["proposal_id"],
                "review_digest": review["review_digest"],
                "approval_proof": signed,
            },
            policy=policy,
        )
    assert not any(business_counts(session).values())


def test_exact_standing_authority_applies_canonical_order(session, acceptance_selected):
    from datetime import UTC, datetime, timedelta

    from reality.domain.shopify_order_acceptance import StandingMandate
    from reality.mcp.principal import mcp_principal_context
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    mandate = StandingMandate(
        id="synthetic-standing-order",
        revision=1,
        subject="tuesday-person",
        profile="shopify_simple_undiscounted_order/1",
        delivery_terms="not_promised",
        currency="EUR",
        source_created_after="2026-11-09T00:00:00Z",
        max_order_amount="10.00",
        max_total_amount="10.00",
        max_orders=1,
        max_total_units=2,
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )
    x["acceptance_policy"] = x["acceptance_policy"].model_copy(
        update={"mandates": [mandate]}
    )
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        signed = acceptance_proof(
            x, review, kind="standing", mandate_id=mandate.id, mandate_revision=1
        )
        receipt = accept_order(
            session,
            x["policy"].tenant_id,
            {
                "proposal_id": review["proposal_id"],
                "review_digest": review["review_digest"],
                "approval_proof": signed,
            },
            policy=x["acceptance_policy"],
        )
    assert receipt["approval"]["mandate_id"] == mandate.id
    assert receipt["admitted_source_units"] == 2
    assert business_counts(session) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


def test_fault_after_canonical_writes_rolls_back_business_and_approval_receipt(
    session, acceptance_selected, monkeypatch
):
    from sqlalchemy import func, select

    from reality.db.core import ChangeProposal, SourceRecord
    from reality.mcp.principal import mcp_principal_context
    from reality.services import intake
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    original = intake._apply_effects

    def fail_after_effects(*args, **kwargs):
        original(*args, **kwargs)
        raise InvalidOperation(code="intake_review_invalid")

    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        before_sources = session.scalar(select(func.count()).select_from(SourceRecord))
        monkeypatch.setattr(intake, "_apply_effects", fail_after_effects)
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": review["proposal_id"],
                    "review_digest": review["review_digest"],
                    "approval_proof": acceptance_proof(x, review),
                },
                policy=x["acceptance_policy"],
            )
    assert not any(business_counts(session).values())
    assert (
        session.scalar(select(func.count()).select_from(SourceRecord)) == before_sources
    )
    row = session.scalar(
        select(ChangeProposal).where(ChangeProposal.id == review["proposal_id"])
    )
    assert row.status == "proposed" and row.output == "{}"


def test_historical_receipt_survives_proof_expiry_but_different_proof_does_not_alias(
    session, acceptance_selected, monkeypatch
):
    from datetime import timedelta

    from reality.mcp.principal import mcp_principal_context
    from reality.services import core
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import (
        accept_order,
        order_acceptance_status,
    )

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        args = {
            "proposal_id": review["proposal_id"],
            "review_digest": review["review_digest"],
            "approval_proof": acceptance_proof(x, review),
        }
        receipt = accept_order(
            session, x["policy"].tenant_id, args, policy=x["acceptance_policy"]
        )
        other = {**args, "approval_proof": acceptance_proof(x, review)}
        with pytest.raises(InvalidOperation):
            accept_order(
                session, x["policy"].tenant_id, other, policy=x["acceptance_policy"]
            )
        real_now = core.now()
        monkeypatch.setattr(core, "now", lambda: real_now + timedelta(hours=2))
        assert (
            order_acceptance_status(
                session, x["policy"].tenant_id, {"proposal_id": review["proposal_id"]}
            )["receipt"]
            == receipt
        )
        assert (
            accept_order(
                session, x["policy"].tenant_id, args, policy=x["acceptance_policy"]
            )
            == receipt
        )
    assert business_counts(session) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


def recapture_selected(session, x, raw):
    from uuid import uuid4

    import test_shopify_buyer_mapping as support

    from reality.services.core import InterpretationNeedsReview
    from reality.services.intake import prepare_intake
    from reality.services.shopify_graphql import capture_shopify_graphql_source

    source, job = capture_shopify_graphql_source(
        session,
        x["policy"].tenant_id,
        order=raw,
        acquisition={
            "shop": x["policy"].shop,
            "api_version": "2026-07",
            "query_digest": "b" * 64,
            "observed_at": raw["updatedAt"],
            "coverage": "complete-selected-order",
        },
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, x["policy"].tenant_id, job.id)
    x.update(
        source=source,
        job=job,
        raw=raw,
        policy=x["policy"].model_copy(
            update={
                "source_record_id": source.id,
                "import_job_id": job.id,
                "source_hash": source.payload_hash,
                "source_version": source.version,
                "order_id": raw["id"],
            }
        ),
    )
    review = support.prepare(session, x)
    support.commit(session, x, review, support.proof(x, review))
    x["request"] = {
        **x["request"],
        "request_id": str(uuid4()),
        "source_record_id": source.id,
        "import_job_id": job.id,
        "source_hash": source.payload_hash,
        "source_version": source.version,
        "buyer_review_id": review["review_id"],
        "buyer_review_digest": review["review_digest"],
        "lines": [
            {
                **x["request"]["lines"][0],
                "source_line_id": raw["lineItems"]["nodes"][0]["id"],
            }
        ],
    }
    x["original"] = (source.payload, job.input)
    return x


@pytest.mark.parametrize("limit", ["orders", "amount", "units"])
def test_standing_cumulative_quota_blocks_second_distinct_real_order(
    session, acceptance_selected, limit
):
    from datetime import UTC, datetime, timedelta

    from reality.domain.shopify_order_acceptance import StandingMandate
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    mandate = StandingMandate(
        id="finite-cumulative",
        revision=1,
        subject="tuesday-person",
        profile="shopify_simple_undiscounted_order/1",
        delivery_terms="not_promised",
        currency="EUR",
        source_created_after="2026-11-09T00:00:00Z",
        max_order_amount="10.00",
        max_total_amount="10.00" if limit == "amount" else "1000.00",
        max_orders=1 if limit == "orders" else 100,
        max_total_units=2 if limit == "units" else 100,
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )
    x["acceptance_policy"] = x["acceptance_policy"].model_copy(
        update={"mandates": [mandate]}
    )
    with mcp_principal_context(x["principal"]):
        first = prepared(session, x)
        accept_order(
            session,
            x["policy"].tenant_id,
            {
                "proposal_id": first["proposal_id"],
                "review_digest": first["review_digest"],
                "approval_proof": acceptance_proof(
                    x, first, kind="standing", mandate_id=mandate.id, mandate_revision=1
                ),
            },
            policy=x["acceptance_policy"],
        )
    raw = complete_order()
    raw.update(
        id="gid://shopify/Order/2004", name="#2004", updatedAt="2026-11-09T14:00:00Z"
    )
    raw["lineItems"]["nodes"][0]["id"] = "gid://shopify/LineItem/42"
    recapture_selected(session, x, raw)
    with mcp_principal_context(x["principal"]):
        second = prepared(session, x)
        assert second["eligible_for_exact_authorization"] is True
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": second["proposal_id"],
                    "review_digest": second["review_digest"],
                    "approval_proof": acceptance_proof(
                        x,
                        second,
                        kind="standing",
                        mandate_id=mandate.id,
                        mandate_revision=1,
                    ),
                },
                policy=x["acceptance_policy"],
            )
    assert business_counts(session) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


def test_unsupported_commercial_source_keeps_final_prices_unknown_and_cannot_apply(
    session, acceptance_selected
):
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    raw = complete_order()
    raw["updatedAt"] = "2026-11-09T14:00:00Z"
    raw["totalDiscountsSet"]["shopMoney"]["amount"] = "1.00"
    recapture_selected(session, x, raw)
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        assert review["eligible_for_exact_authorization"] is False
        line = review["review_projection"]["effects"][0]["arguments"]["lines"][0]
        assert line["unit_price"] is line["gross_amount"] is None
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": review["proposal_id"],
                    "review_digest": review["review_digest"],
                    "approval_proof": acceptance_proof(x, review),
                },
                policy=x["acceptance_policy"],
            )
    assert not any(business_counts(session).values())


def test_foreign_successor_is_non_disclosing(session, acceptance_selected):
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation, create_tenant
    from reality.services.shopify_order_acceptance import (
        order_acceptance_status,
        review_order_acceptance,
    )

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
    other = create_tenant(session, "Owned foreign synthetic company")
    with mcp_principal_context(x["principal"]):
        for service in [review_order_acceptance, order_acceptance_status]:
            with pytest.raises(InvalidOperation) as error:
                service(session, other.id, {"proposal_id": review["proposal_id"]})
            assert x["source"].id not in str(error.value)
    assert not any(business_counts(session).values())


def test_generic_confirmed_execute_cannot_accept_successor(
    session, acceptance_selected
):
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation
    from reality.tools.application import approve_and_execute_proposal

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
    with pytest.raises(InvalidOperation):
        approve_and_execute_proposal(
            session, x["policy"].tenant_id, review["proposal_id"], confirmed=True
        )
    assert not any(business_counts(session).values())


def test_private_policy_file_and_revocation_after_canonical_wait_roll_back(
    session, acceptance_selected, tmp_path, monkeypatch
):
    from reality.mcp.principal import mcp_principal_context
    from reality.services import intake
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import (
        accept_order,
        prepare_order_acceptance,
    )

    x = acceptance_selected
    path = tmp_path / "owned-issuer-policy.json"
    path.write_text(x["acceptance_policy"].model_dump_json())
    path.chmod(0o600)
    monkeypatch.setenv("REALITY_SHOPIFY_ORDER_ACCEPTANCE_POLICY_FILE", str(path))
    original = intake._apply_effects

    def revoke_after_effects(*args, **kwargs):
        result = original(*args, **kwargs)
        path.write_text(
            x["acceptance_policy"]
            .model_copy(update={"allowed_token_ids": ["different-token"]})
            .model_dump_json()
        )
        return result

    with mcp_principal_context(x["principal"]):
        review = prepare_order_acceptance(session, x["policy"].tenant_id, x["request"])
        monkeypatch.setattr(intake, "_apply_effects", revoke_after_effects)
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": review["proposal_id"],
                    "review_digest": review["review_digest"],
                    "approval_proof": acceptance_proof(x, review),
                },
            )
    assert not any(business_counts(session).values())


@pytest.mark.parametrize("same_proposal", [False, True])
def test_two_actual_sessions_serialize_duplicate_order_and_lost_response_replay(
    postgres_database, request, same_proposal
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace
    from uuid import uuid4

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.db.core import Base
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import (
        InvalidOperation,
        create_item,
        create_location,
        create_party,
        create_tenant,
    )
    from reality.services.shopify_order_acceptance import accept_order

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    request.addfinalizer(engine.dispose)
    setup = Session(engine, expire_on_commit=False)
    request.addfinalizer(setup.close)
    tenant = create_tenant(setup, "Owned external acceptance contention")
    business = SimpleNamespace(
        tenant=tenant,
        company=create_party(setup, tenant.id, "Company", "company"),
        customer=create_party(setup, tenant.id, "Buyer", "customer"),
        item=create_item(setup, tenant.id, "BIKE-LIGHT", "Light"),
        location=create_location(setup, tenant.id, "Location"),
    )
    x = globals()["acceptance_selected"].__wrapped__(setup, business)
    with mcp_principal_context(x["principal"]):
        first = prepared(setup, x)
        x["request"] = {**x["request"], "request_id": str(uuid4())}
        second = first if same_proposal else prepared(setup, x)
    setup.commit()
    proofs = [acceptance_proof(x, first), acceptance_proof(x, second)]
    if same_proposal:
        proofs[1] = proofs[0]
    barrier = Barrier(2)

    def run(index):
        with Session(engine) as worker, mcp_principal_context(x["principal"]):
            barrier.wait(timeout=5)
            review = [first, second][index]
            try:
                return accept_order(
                    worker,
                    tenant.id,
                    {
                        "proposal_id": review["proposal_id"],
                        "review_digest": review["review_digest"],
                        "approval_proof": proofs[index],
                    },
                    policy=x["acceptance_policy"],
                )
            except InvalidOperation:
                return "refused"

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(run, 0)
        b = pool.submit(run, 1)
        results = [a.result(timeout=15), b.result(timeout=15)]
    receipts = [result for result in results if isinstance(result, dict)]
    assert len(receipts) == (2 if same_proposal else 1)
    if same_proposal:
        assert receipts[0] == receipts[1]
    else:
        assert "refused" in results
    assert business_counts(setup) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


@pytest.mark.parametrize("kind", ["missing", "writable", "symlink", "other_purpose"])
def test_private_policy_invalid_or_other_purpose_never_prepares(
    session, acceptance_selected, tmp_path, monkeypatch, kind
):
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import prepare_order_acceptance

    x = acceptance_selected
    path = tmp_path / "policy.json"
    if kind != "missing":
        path.write_text(x["acceptance_policy"].model_dump_json())
        path.chmod(0o600)
    if kind == "writable":
        path.chmod(0o666)
    if kind == "symlink":
        link = tmp_path / "policy-link.json"
        link.symlink_to(path)
        path = link
    if kind == "other_purpose":
        path.write_text(
            path.read_text().replace(
                "shopify_source_order_acceptance/1",
                "shopify_source_buyer_mapping_only/1",
            )
        )
    monkeypatch.setenv("REALITY_SHOPIFY_ORDER_ACCEPTANCE_POLICY_FILE", str(path))
    with mcp_principal_context(x["principal"]), pytest.raises(InvalidOperation):
        prepare_order_acceptance(session, x["policy"].tenant_id, x["request"])
    assert not any(business_counts(session).values())


def test_normal_narrow_mcp_routes_and_scopes_cannot_create_generic_authority(
    session, acceptance_selected, monkeypatch
):
    from reality.mcp.auth import create_mcp_access_token
    from reality.mcp.catalog import dispatch_mcp_tool
    from reality.mcp.principal import MCPPrincipal

    x = acceptance_selected
    allowed = [
        "shopify_source_order_acceptance_" + suffix
        for suffix in ["prepare", "review", "accept", "status"]
    ]
    token, _ = create_mcp_access_token(
        session, x["policy"].tenant_id, "Owned exact narrow acceptance token", allowed
    )
    principal = MCPPrincipal(
        authentication_kind="manual",
        credential_id=token.id,
        grant_id=None,
        user_id=None,
        tenant_id=x["policy"].tenant_id,
        client_id="narrow-392",
        scopes=frozenset(),
        allowed_tools=frozenset(allowed),
    )
    trusted = x["acceptance_policy"].model_copy(
        update={"allowed_token_ids": [token.id]}
    )
    import reality.services.shopify_order_acceptance as service

    original = service._policy
    monkeypatch.setattr(
        service,
        "_policy",
        lambda tenant_id, supplied=None, **kwargs: original(
            tenant_id, supplied or trusted, **kwargs
        ),
    )
    review = dispatch_mcp_tool(session, principal, allowed[0], x["request"])
    assert (
        dispatch_mcp_tool(
            session, principal, allowed[1], {"proposal_id": review["proposal_id"]}
        )
        == review
    )
    with pytest.raises(PermissionError):
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {"proposal_id": review["proposal_id"]},
        )
    receipt = dispatch_mcp_tool(
        session,
        principal,
        allowed[2],
        {
            "proposal_id": review["proposal_id"],
            "review_digest": review["review_digest"],
            "approval_proof": acceptance_proof(x, review),
        },
    )
    assert receipt["verification"] == "applied"
    assert (
        dispatch_mcp_tool(
            session, principal, allowed[3], {"proposal_id": review["proposal_id"]}
        )["receipt"]
        == receipt
    )


def test_new_current_debt_after_review_is_not_hidden_behind_old_as_of(
    session, acceptance_selected
):
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import (
        InvalidOperation,
        create_manual_document_with_lines,
    )
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
    create_manual_document_with_lines(
        session,
        x["policy"].tenant_id,
        "sales_order",
        "Owned new debt after review",
        x["business"].customer.id,
        [
            {
                "item_id": x["business"].item.id,
                "sku": "BIKE-LIGHT",
                "description": "Owned new debt",
                "quantity": "1",
                "unit_price": "1000.00",
                "gross_amount": "1000.00",
                "unit": x["business"].item.unit,
            }
        ],
        "1000.00",
        currency="EUR",
    )
    before = business_counts(session)
    with mcp_principal_context(x["principal"]), pytest.raises(InvalidOperation):
        accept_order(
            session,
            x["policy"].tenant_id,
            {
                "proposal_id": review["proposal_id"],
                "review_digest": review["review_digest"],
                "approval_proof": acceptance_proof(x, review),
            },
            policy=x["acceptance_policy"],
        )
    assert business_counts(session) == before


@pytest.mark.parametrize(
    "change", ["zero_credit", "foreign_currency", "missing_calendar"]
)
def test_explicit_calendar_and_positive_complete_credit_are_required(
    session, acceptance_selected, change
):
    from sqlalchemy import delete

    from reality.db.core import CompanyTimeZone
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    if change == "zero_credit":
        x["business"].customer.credit_limit = 0
    if change == "foreign_currency":
        x["business"].customer.default_currency = "USD"
    if change == "missing_calendar":
        session.execute(
            delete(CompanyTimeZone).where(
                CompanyTimeZone.tenant_id == x["policy"].tenant_id
            )
        )
    session.commit()
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        assert review["eligible_for_exact_authorization"] is False
        assert review["holds"]
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": review["proposal_id"],
                    "review_digest": review["review_digest"],
                    "approval_proof": acceptance_proof(x, review),
                },
                policy=x["acceptance_policy"],
            )
    assert not any(business_counts(session).values())


def test_lost_response_after_database_commit_reconciles_original_receipt_without_resend(
    session, acceptance_selected, monkeypatch
):
    from reality.mcp.principal import mcp_principal_context
    from reality.services import shopify_order_acceptance as service

    x = acceptance_selected
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        args = {
            "proposal_id": review["proposal_id"],
            "review_digest": review["review_digest"],
            "approval_proof": acceptance_proof(x, review),
        }
        original = service._receipt

        def lost_after_commit(*args, **kwargs):
            raise RuntimeError("Owned synthetic response lost after commit")

        monkeypatch.setattr(service, "_receipt", lost_after_commit)
        with pytest.raises(RuntimeError, match="response lost after commit"):
            service.accept_order(
                session, x["policy"].tenant_id, args, policy=x["acceptance_policy"]
            )
        monkeypatch.setattr(service, "_receipt", original)
        receipt = service.order_acceptance_status(
            session, x["policy"].tenant_id, {"proposal_id": review["proposal_id"]}
        )["receipt"]
        assert receipt["verification"] == "applied"
        assert (
            service.accept_order(
                session, x["policy"].tenant_id, args, policy=x["acceptance_policy"]
            )
            == receipt
        )
    assert business_counts(session) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


@pytest.mark.parametrize(
    "processed_at", ["2026-11-09T00:00:00Z", "2026-11-09T01:00:00+02:00"]
)
def test_true_shopify_instant_not_legacy_midnight_day_sentinel(
    session, acceptance_selected, processed_at
):
    from reality.mcp.principal import mcp_principal_context
    from reality.services.company_time_zone import set_company_time_zone

    x = acceptance_selected
    set_company_time_zone(session, x["policy"].tenant_id, "America/New_York")
    raw = complete_order()
    raw.update(processedAt=processed_at, updatedAt="2026-11-09T14:00:00Z")
    recapture_selected(session, x, raw)
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
    assert review["eligible_for_exact_authorization"] is True
    assert (
        review["review_projection"]["effects"][0]["arguments"]["document_date"]
        == "2026-11-08"
    )
    assert review["readiness"]["calendar"]["processed_at"] == processed_at


@pytest.mark.parametrize(
    "created_after", ["2026-11-09T12:00:00Z", "2026-11-09T12:00:01Z"]
)
def test_standing_created_after_is_exclusive_original_creation_bound(
    session, acceptance_selected, created_after
):
    from datetime import UTC, datetime, timedelta

    from reality.domain.shopify_order_acceptance import StandingMandate
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    mandate = StandingMandate(
        id="strict-new-orders",
        revision=1,
        subject="tuesday-person",
        profile="shopify_simple_undiscounted_order/1",
        delivery_terms="not_promised",
        currency="EUR",
        max_order_amount="100.00",
        max_total_amount="100.00",
        max_orders=10,
        max_total_units=100,
        source_created_after=created_after,
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )
    x["acceptance_policy"] = x["acceptance_policy"].model_copy(
        update={"mandates": [mandate]}
    )
    with mcp_principal_context(x["principal"]):
        review = prepared(session, x)
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": review["proposal_id"],
                    "review_digest": review["review_digest"],
                    "approval_proof": acceptance_proof(
                        x,
                        review,
                        kind="standing",
                        mandate_id=mandate.id,
                        mandate_revision=1,
                    ),
                },
                policy=x["acceptance_policy"],
            )
    assert not any(business_counts(session).values())


@pytest.mark.parametrize("protocol", ["2025-03-26", "2025-06-18"])
def test_actual_authenticated_mcp_http_schema_prepare_accept_status_and_denials(
    session, acceptance_selected, tmp_path, monkeypatch, protocol
):
    import json
    import os
    from pathlib import Path

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.mcp import auth as auth_module
    from reality.mcp.app import create_mcp_app
    from reality.mcp.auth import create_mcp_access_token
    from reality.mcp.config import MCPRuntimeSettings

    x = acceptance_selected
    allowed = [
        "shopify_source_order_acceptance_" + suffix
        for suffix in ["prepare", "review", "accept", "status"]
    ]
    token, clear = create_mcp_access_token(
        session, x["policy"].tenant_id, "Owned exact HTTP acceptance grant", allowed
    )
    policy = x["acceptance_policy"].model_copy(update={"allowed_token_ids": [token.id]})
    path = tmp_path / "http-issuer.json"
    path.write_text(policy.model_dump_json())
    path.chmod(0o600)
    monkeypatch.setenv("REALITY_SHOPIFY_ORDER_ACCEPTANCE_POLICY_FILE", str(path))
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    monkeypatch.setattr(auth_module, "Session", factory)
    from reality.mcp import server as server_module

    monkeypatch.setattr(server_module, "Session", factory)
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/", bind_host="127.0.0.1", bind_port=8001
        ),
        session_factory=factory,
    )
    headers = {
        "Authorization": "Bearer " + clear,
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
        "MCP-Protocol-Version": protocol,
    }

    def call(client, index, name, args):
        response = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": index,
                "method": "tools/call",
                "params": {"name": name, "arguments": args},
            },
        )
        assert response.status_code == 200
        result = response.json()["result"]
        assert not result.get("isError"), result
        return json.loads(result["content"][0]["text"])

    with TestClient(runtime) as client:
        initialized = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": protocol,
                    "capabilities": {},
                    "clientInfo": {"name": "owned-392-proof", "version": "1"},
                },
            },
        )
        assert initialized.status_code == 200, initialized.text
        response = client.post(
            "/",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )
        assert response.status_code == 200, response.text
        advertised = [
            item
            for item in response.json()["result"]["tools"]
            if item["name"] in allowed
        ]
        schemas = {
            item["name"]: item["inputSchema"]
            for item in response.json()["result"]["tools"]
            if item["name"] in allowed
        }
        assert set(schemas) == set(allowed)
        denied = client.post(
            "/",
            headers={
                key: value for key, value in headers.items() if key != "Authorization"
            },
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert denied.status_code == 401
        denied = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "proposal_approve_and_execute",
                    "arguments": {"proposal_id": "never-apply"},
                },
            },
        )
        assert denied.status_code == 200 and denied.json()["result"].get("isError")
        review = call(client, 4, allowed[0], x["request"])
        assert review["eligible_for_exact_authorization"] is True
        assert (
            call(client, 5, allowed[1], {"proposal_id": review["proposal_id"]})
            == review
        )
        receipt = call(
            client,
            6,
            allowed[2],
            {
                "proposal_id": review["proposal_id"],
                "review_digest": review["review_digest"],
                "approval_proof": acceptance_proof(x, review),
            },
        )
        assert receipt["verification"] == "applied"
        status = call(client, 7, allowed[3], {"proposal_id": review["proposal_id"]})
        assert status["receipt"] == receipt and status["dispatch_performed"] is False
    if os.environ.get("REALITY_392_TEST_ARTIFACT_DIR"):
        folder = Path(os.environ["REALITY_392_TEST_ARTIFACT_DIR"]) / protocol
        folder.mkdir(parents=True, exist_ok=True)
        folder.chmod(0o700)
        for name, value in [
            ("actual-asgi-input-schemas", schemas),
            ("synthetic-review", review),
            ("synthetic-receipt", receipt),
            ("synthetic-prepare-input", x["request"]),
            ("synthetic-status", status),
            (
                "actual-initialize",
                {
                    "request": {
                        "protocolVersion": protocol,
                        "capabilities": {},
                        "clientInfo": {"name": "owned-392-proof", "version": "1"},
                    },
                    "response": initialized.json(),
                },
            ),
            ("actual-tools-advertisement", advertised),
        ]:
            output = folder / (name + ".json")
            output.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
            output.chmod(0o600)
    assert business_counts(session) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


def test_status_with_different_reader_token_waits_original_acceptance_transaction(
    postgres_database, request, monkeypatch
):
    import time
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from types import SimpleNamespace

    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import Session

    from reality.db.core import Base
    from reality.mcp.auth import create_mcp_access_token
    from reality.mcp.principal import MCPPrincipal, mcp_principal_context
    from reality.services import intake
    from reality.services import shopify_order_acceptance as service
    from reality.services.core import (
        create_item,
        create_location,
        create_party,
        create_tenant,
    )

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    request.addfinalizer(engine.dispose)
    setup = Session(engine, expire_on_commit=False)
    request.addfinalizer(setup.close)
    tenant = create_tenant(setup, "Owned status reconciliation contention")
    business = SimpleNamespace(
        tenant=tenant,
        company=create_party(setup, tenant.id, "Company", "company"),
        customer=create_party(setup, tenant.id, "Buyer", "customer"),
        item=create_item(setup, tenant.id, "BIKE-LIGHT", "Light"),
        location=create_location(setup, tenant.id, "Location"),
    )
    x = globals()["acceptance_selected"].__wrapped__(setup, business)
    reader_token, _ = create_mcp_access_token(
        setup,
        tenant.id,
        "Owned receipt reader",
        ["shopify_source_order_acceptance_status"],
    )
    reader = MCPPrincipal(
        authentication_kind="manual",
        credential_id=reader_token.id,
        grant_id=None,
        user_id=None,
        tenant_id=tenant.id,
        client_id="owned-reader",
        scopes=frozenset(),
        allowed_tools=frozenset({"shopify_source_order_acceptance_status"}),
    )
    with mcp_principal_context(x["principal"]):
        review = prepared(setup, x)
    setup.commit()
    entered, released, reader_started = Event(), Event(), Event()
    original = intake._apply_effects

    def wait_after_effects(*args, **kwargs):
        result = original(*args, **kwargs)
        entered.set()
        assert released.wait(5)
        return result

    monkeypatch.setattr(intake, "_apply_effects", wait_after_effects)
    signed = acceptance_proof(x, review)
    pids = []

    def apply():
        with Session(engine) as worker, mcp_principal_context(x["principal"]):
            return service.accept_order(
                worker,
                tenant.id,
                {
                    "proposal_id": review["proposal_id"],
                    "review_digest": review["review_digest"],
                    "approval_proof": signed,
                },
                policy=x["acceptance_policy"],
            )

    def read():
        with Session(engine) as worker, mcp_principal_context(reader):
            pids.append(worker.scalar(select(func.pg_backend_pid())))
            reader_started.set()
            return service.order_acceptance_status(
                worker, tenant.id, {"proposal_id": review["proposal_id"]}
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        applying = pool.submit(apply)
        assert entered.wait(5)
        reading = pool.submit(read)
        assert reader_started.wait(5)
        try:
            deadline = time.monotonic() + 3
            blocked = False
            while time.monotonic() < deadline and not reading.done():
                with Session(engine) as observer:
                    blocked = bool(
                        observer.scalar(select(func.pg_blocking_pids(pids[0])))
                    )
                if blocked:
                    break
                time.sleep(0.01)
            assert blocked, (
                "Read-only status escaped while original acceptance could still commit"
            )
        finally:
            released.set()
        receipt = applying.result(timeout=10)
        status = reading.result(timeout=10)
    assert status["receipt"] == receipt
    assert business_counts(setup) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


def test_standing_revision_cannot_mix_prior_receipt_currency_or_reset_exposure(
    session, acceptance_selected
):
    from datetime import UTC, datetime, timedelta

    from reality.domain.shopify_order_acceptance import StandingMandate
    from reality.mcp.principal import mcp_principal_context
    from reality.services.core import InvalidOperation, create_party
    from reality.services.shopify_order_acceptance import accept_order

    x = acceptance_selected
    mandate = StandingMandate(
        id="same-finite-id-across-revision",
        revision=1,
        subject="tuesday-person",
        profile="shopify_simple_undiscounted_order/1",
        delivery_terms="not_promised",
        currency="EUR",
        max_order_amount="100.00",
        max_total_amount="1000.00",
        max_orders=100,
        max_total_units=100,
        source_created_after="2026-11-09T00:00:00Z",
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )
    x["acceptance_policy"] = x["acceptance_policy"].model_copy(
        update={"mandates": [mandate]}
    )
    with mcp_principal_context(x["principal"]):
        first = prepared(session, x)
        accept_order(
            session,
            x["policy"].tenant_id,
            {
                "proposal_id": first["proposal_id"],
                "review_digest": first["review_digest"],
                "approval_proof": acceptance_proof(
                    x, first, kind="standing", mandate_id=mandate.id, mandate_revision=1
                ),
            },
            policy=x["acceptance_policy"],
        )
    buyer = create_party(session, x["policy"].tenant_id, "Owned USD buyer", "customer")
    buyer.default_currency = "USD"
    buyer.credit_limit = 1000
    session.commit()
    x["business"].customer = buyer
    raw = complete_order()
    raw.update(
        id="gid://shopify/Order/2004",
        name="#2004",
        updatedAt="2026-11-09T14:00:00Z",
        currencyCode="USD",
    )
    for field in [*TOTAL_FIELDS, *ZERO_FIELDS, "totalPriceSet"]:
        raw[field]["shopMoney"]["currencyCode"] = "USD"
    line = raw["lineItems"]["nodes"][0]
    line["id"] = "gid://shopify/LineItem/42"
    for field in ["originalUnitPriceSet", "originalTotalSet"]:
        line[field]["shopMoney"]["currencyCode"] = "USD"
    recapture_selected(session, x, raw)
    revised = mandate.model_copy(update={"revision": 2, "currency": "USD"})
    x["acceptance_policy"] = x["acceptance_policy"].model_copy(
        update={"currency": "USD", "mandates": [revised]}
    )
    with mcp_principal_context(x["principal"]):
        second = prepared(session, x)
        assert second["eligible_for_exact_authorization"] is True
        with pytest.raises(InvalidOperation):
            accept_order(
                session,
                x["policy"].tenant_id,
                {
                    "proposal_id": second["proposal_id"],
                    "review_digest": second["review_digest"],
                    "approval_proof": acceptance_proof(
                        x,
                        second,
                        kind="standing",
                        mandate_id=mandate.id,
                        mandate_revision=2,
                    ),
                },
                policy=x["acceptance_policy"],
            )
    assert business_counts(session) == {
        "Document": 1,
        "Commitment": 1,
        "Movement": 0,
        "LedgerEntry": 0,
    }


def test_richer_selection_at_unchanged_upstream_version_remains_conflict_not_fake_update(
    session, business
):
    import test_shopify_buyer_mapping as support
    from sqlalchemy import select

    from reality.db.core import SourceStream
    from reality.services.shopify_graphql import capture_shopify_graphql_source

    x = support.bound.__wrapped__(session, business)
    richer = complete_order()
    richer["updatedAt"] = x["raw"]["updatedAt"]
    source, job = capture_shopify_graphql_source(
        session,
        business.tenant.id,
        order=richer,
        acquisition={
            "shop": x["policy"].shop,
            "api_version": "2026-07",
            "query_digest": "b" * 64,
            "observed_at": "2026-11-09T14:00:00Z",
            "coverage": "complete-selected-order",
        },
    )
    stream = session.scalar(
        select(SourceStream).where(
            SourceStream.tenant_id == business.tenant.id,
            SourceStream.source_system == "shopify",
            SourceStream.source_type == "order_graphql",
            SourceStream.external_id == "1004",
        )
    )
    assert (
        source.id != x["source"].id
        and stream.current_source_record_id == x["source"].id
    )
    assert job.status == "failed"
    assert not any(business_counts(session).values())
