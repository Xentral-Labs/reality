"""Spec 389: an existing buyer choice is a human-reviewed source mapping only."""

import base64
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Commitment, Document, Movement
from reality.domain.shopify_buyer_mapping import AUDIENCE, PURPOSE, BuyerMappingPolicy
from reality.services import shopify_buyer_mapping as mapping
from reality.services.core import (
    InterpretationNeedsReview,
    InvalidOperation,
    create_party,
)
from reality.services.intake import prepare_intake
from reality.services.shopify_graphql import capture_shopify_graphql_source


def b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


@pytest.fixture
def bound(session, business):
    raw = {
        "id": "gid://shopify/Order/1004",
        "name": "#1004",
        "createdAt": "2026-11-09T12:00:00Z",
        "updatedAt": "2026-11-09T12:00:00Z",
        "cancelledAt": None,
        "displayFulfillmentStatus": "UNFULFILLED",
        "currencyCode": "EUR",
        "totalPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "EUR"}},
        "lineItems": {
            "nodes": [
                {
                    "id": "gid://shopify/LineItem/41",
                    "name": "Light",
                    "sku": "BIKE-LIGHT",
                    "quantity": 2,
                    "currentQuantity": 2,
                    "requiresShipping": True,
                    "originalUnitPriceSet": {
                        "shopMoney": {"amount": "5.00", "currencyCode": "EUR"}
                    },
                }
            ],
            "pageInfo": {"hasNextPage": False},
        },
    }
    acquisition = {
        "shop": "pilot.myshopify.com",
        "api_version": "2026-07",
        "query_digest": "a" * 64,
        "observed_at": "2026-11-09T12:00:00Z",
        "coverage": "complete-selected-order",
    }
    source, job = capture_shopify_graphql_source(
        session, business.tenant.id, order=raw, acquisition=acquisition
    )
    with pytest.raises(InterpretationNeedsReview):
        prepare_intake(session, business.tenant.id, job.id)
    key = Ed25519PrivateKey.generate()
    policy = BuyerMappingPolicy(
        tenant_id=business.tenant.id,
        source_record_id=source.id,
        import_job_id=job.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        order_id=raw["id"],
        shop=acquisition["shop"],
        query_digest=acquisition["query_digest"],
        issuer="urn:tuesday:test-installation",
        key_id="test-key",
        public_key=b64(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)),
        allowed_subjects=["tuesday-person"],
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )
    return {
        "business": business,
        "source": source,
        "job": job,
        "key": key,
        "policy": policy,
        "raw": raw,
        "job_input": job.input,
    }


def candidates(session, x):
    return mapping.buyer_candidates(
        session,
        x["business"].tenant.id,
        {
            "source_record_id": x["source"].id,
            "import_job_id": x["job"].id,
            "query": "",
            "limit": 20,
        },
        policy=x["policy"],
    )


def prepare(session, x, customer=None, request=None):
    row = customer or next(
        v
        for v in candidates(session, x)["items"]
        if v["party_id"] == x["business"].customer.id
    )
    return mapping.prepare_buyer_mapping(
        session,
        x["business"].tenant.id,
        {
            "request_id": request or str(uuid4()),
            "source_record_id": x["source"].id,
            "import_job_id": x["job"].id,
            "source_hash": x["source"].payload_hash,
            "source_version": x["source"].version,
            "customer_party_id": row["party_id"],
            "customer_digest": row["digest"],
        },
        policy=x["policy"],
    )


def proof(x, review, **overrides):
    now = int(datetime.now(UTC).timestamp())
    claims = {
        "iss": x["policy"].issuer,
        "aud": AUDIENCE,
        "sub": "tuesday-person",
        "iat": now,
        "exp": now + 300,
        "jti": str(uuid4()),
        "tenant_id": x["policy"].tenant_id,
        "review_id": review["review_id"],
        "review_digest": review["review_digest"],
        "purpose": PURPOSE,
        **overrides,
    }
    header = b64(
        json.dumps(
            {
                "alg": "EdDSA",
                "typ": "tuesday-buyer-mapping+jwt",
                "kid": x["policy"].key_id,
            },
            separators=(",", ":"),
        ).encode()
    )
    body = b64(json.dumps(claims, separators=(",", ":")).encode())
    signing = f"{header}.{body}"
    return f"{signing}.{b64(x['key'].sign(signing.encode()))}"


def commit(session, x, review, signed):
    return mapping.commit_buyer_mapping(
        session,
        x["policy"].tenant_id,
        {
            "review_id": review["review_id"],
            "review_digest": review["review_digest"],
            "approval_proof": signed,
        },
        policy=x["policy"],
    )


def test_candidates_only_existing_active_customers_and_minimal_fields(session, bound):
    supplier = create_party(
        session, bound["policy"].tenant_id, "Not a buyer", "supplier"
    )
    result = candidates(session, bound)
    assert result["items"] == [
        {
            "party_id": bound["business"].customer.id,
            "label": bound["business"].customer.name,
            "digest": result["items"][0]["digest"],
        }
    ]
    assert supplier.id not in json.dumps(result)
    assert "email" not in json.dumps(result)
    assert result["source_binding"]["source_version"] == bound["source"].version


def test_frozen_prepare_and_verified_mapping_are_not_an_accepted_order(session, bound):
    nonce = str(uuid4())
    review = prepare(session, bound, request=nonce)
    assert prepare(session, bound, request=nonce) == review
    signed = proof(bound, review)
    result = commit(session, bound, review, signed)
    assert result["state"] == "mapping_recorded"
    assert result["customer"]["party_id"] == bound["business"].customer.id
    assert result["approval_source_record_id"]
    assert result["approval"]["proof_digest"] == mapping.proof_digest(signed)
    assert result["business_effects_accepted"] is False
    verified = mapping.get_verified_buyer_mapping(
        session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
    )
    assert verified["customer"]["party_id"] == result["customer"]["party_id"]
    assert verified["approval_source_record_id"] == result["approval_source_record_id"]
    assert verified["mapping_state"] == "applied_to_source"
    session.refresh(bound["source"])
    session.refresh(bound["job"])
    assert json.loads(bound["source"].payload) == bound["raw"]
    assert bound["job"].input == bound["job_input"]
    assert bound["job"].status == "review_required"
    assert (
        json.loads(bound["job"].error)["reason_code"]
        == "buyer_mapping_recorded_intake_pending"
    )
    for model in (Document, Commitment, Movement):
        assert session.scalar(select(func.count()).select_from(model)) == 0
    action = session.scalar(
        select(ChangeProposal).where(ChangeProposal.id == review["review_id"])
    )
    assert action.decided_by_user_id is None


@pytest.mark.parametrize(
    "override",
    [
        {"aud": "other"},
        {"sub": "other"},
        {"tenant_id": "foreign"},
        {"review_digest": "b" * 64},
        {"purpose": "accept_order"},
        {"exp": 1},
    ],
)
def test_wrong_human_proof_never_records_mapping(session, bound, override):
    review = prepare(session, bound)
    with pytest.raises(InvalidOperation):
        commit(session, bound, review, proof(bound, review, **override))
    assert (
        mapping.get_verified_buyer_mapping(
            session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
        )
        is None
    )


def test_exact_proof_replay_is_original_receipt_even_after_expiry(
    session, bound, monkeypatch
):
    review = prepare(session, bound)
    signed = proof(bound, review)
    first = commit(session, bound, review, signed)
    monkeypatch.setattr(
        mapping, "_now", lambda: datetime.now(UTC) + timedelta(minutes=30)
    )
    assert commit(session, bound, review, signed) == first
    assert (
        mapping.buyer_mapping_status(
            session,
            bound["policy"].tenant_id,
            {"review_id": review["review_id"]},
            policy=bound["policy"],
        )
        == first
    )
    with pytest.raises(InvalidOperation):
        commit(session, bound, review, proof(bound, review))


def test_changed_customer_and_stale_source_cannot_commit(session, bound):
    review = prepare(session, bound)
    signed = proof(bound, review)
    bound["business"].customer.is_active = False
    session.flush()
    with pytest.raises(InvalidOperation):
        commit(session, bound, review, signed)
    assert (
        mapping.get_verified_buyer_mapping(
            session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
        )
        is None
    )


def test_second_mapping_never_replaces_first_source_buyer(session, bound):
    other = create_party(
        session, bound["policy"].tenant_id, "Second customer", "customer"
    )
    choices = candidates(session, bound)["items"]
    second = next(v for v in choices if v["party_id"] == other.id)
    first = prepare(session, bound)
    later = prepare(session, bound, customer=second)
    commit(session, bound, first, proof(bound, first))
    with pytest.raises(InvalidOperation):
        commit(session, bound, later, proof(bound, later))
    assert (
        mapping.get_verified_buyer_mapping(
            session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
        )["customer"]["party_id"]
        == bound["business"].customer.id
    )


def test_mapping_is_read_by_candidates_and_intake_stays_explicitly_held(session, bound):
    from reality.services.shopify_graphql import (
        ShopifyBuyerMappingRecorded,
        prepare_graphql_order,
    )

    review = prepare(session, bound)
    receipt = commit(session, bound, review, proof(bound, review))
    assert receipt["approval"]["jti"]
    assert (
        candidates(session, bound)["existing_mapping"]["mapping_state"]
        == "applied_to_source"
    )
    with pytest.raises(ShopifyBuyerMappingRecorded):
        prepare_graphql_order(
            session, bound["policy"].tenant_id, bound["source"], bound["job"]
        )
    assert bound["job"].input == bound["job_input"]
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_latest_source_change_invalidates_pending_review(session, bound):
    review = prepare(session, bound)
    signed = proof(bound, review)
    raw = {**bound["raw"], "updatedAt": "2026-11-09T12:01:00Z", "name": "#1004 amended"}
    capture_shopify_graphql_source(
        session,
        bound["policy"].tenant_id,
        order=raw,
        acquisition=json.loads(bound["job_input"])["acquisition"],
    )
    with pytest.raises(InvalidOperation):
        mapping.buyer_mapping_status(
            session,
            bound["policy"].tenant_id,
            {"review_id": review["review_id"]},
            policy=bound["policy"],
        )
    with pytest.raises(InvalidOperation):
        commit(session, bound, review, signed)


def test_changed_label_and_nonce_cannot_silently_refresh(session, bound):
    request = str(uuid4())
    review = prepare(session, bound, request=request)
    bound["business"].customer.name = "New legal label"
    session.flush()
    with pytest.raises(InvalidOperation):
        commit(session, bound, review, proof(bound, review))
    with pytest.raises(InvalidOperation):
        prepare(session, bound, request=request)


def test_historical_receipt_preserves_proof_but_reports_inactive_customer(
    session, bound
):
    review = prepare(session, bound)
    receipt = commit(session, bound, review, proof(bound, review))
    bound["business"].customer.is_active = False
    session.flush()
    status = mapping.buyer_mapping_status(
        session,
        bound["policy"].tenant_id,
        {"review_id": review["review_id"]},
        policy=bound["policy"],
    )
    assert status["approval"] == receipt["approval"]
    assert status["current_basis"] == {
        "source_current": True,
        "customer_current": False,
    }


@pytest.mark.parametrize(
    "mutation", ["signature", "extra_header", "duplicate", "wrong_key"]
)
def test_malformed_or_other_signature_never_records(session, bound, mutation):
    review = prepare(session, bound)
    header, body, signature = proof(bound, review).split(".")
    if mutation == "signature":
        signature = b64(bytes(64))
    elif mutation == "extra_header":
        header = b64(
            json.dumps(
                {
                    "alg": "EdDSA",
                    "typ": "tuesday-buyer-mapping+jwt",
                    "kid": bound["policy"].key_id,
                    "jwk": {},
                }
            ).encode()
        )
        signature = b64(bound["key"].sign(f"{header}.{body}".encode()))
    elif mutation == "duplicate":
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode()
        body = b64((raw[:-1] + ',"sub":"tuesday-person"}').encode())
        signature = b64(bound["key"].sign(f"{header}.{body}".encode()))
    else:
        signature = b64(Ed25519PrivateKey.generate().sign(f"{header}.{body}".encode()))
    with pytest.raises(InvalidOperation):
        commit(session, bound, review, f"{header}.{body}.{signature}")
    assert (
        mapping.get_verified_buyer_mapping(
            session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
        )
        is None
    )


def test_default_deny_private_policy_and_exact_tenant(
    session, bound, tmp_path, monkeypatch
):
    arguments = {
        "source_record_id": bound["source"].id,
        "import_job_id": bound["job"].id,
    }
    monkeypatch.delenv(
        "REALITY_SHOPIFY_SOURCE_BUYER_MAPPING_POLICY_FILE", raising=False
    )
    with pytest.raises(InvalidOperation):
        mapping.buyer_candidates(session, bound["policy"].tenant_id, arguments)
    file = tmp_path / "policy.json"
    file.write_text(bound["policy"].model_dump_json())
    file.chmod(0o644)
    monkeypatch.setenv("REALITY_SHOPIFY_SOURCE_BUYER_MAPPING_POLICY_FILE", str(file))
    with pytest.raises(InvalidOperation):
        mapping.buyer_candidates(session, bound["policy"].tenant_id, arguments)
    file.chmod(0o600)
    assert mapping.buyer_candidates(session, bound["policy"].tenant_id, arguments)[
        "items"
    ]
    with pytest.raises(InvalidOperation):
        mapping.buyer_candidates(session, "foreign", arguments)
    link = tmp_path / "link.json"
    link.symlink_to(file)
    monkeypatch.setenv("REALITY_SHOPIFY_SOURCE_BUYER_MAPPING_POLICY_FILE", str(link))
    with pytest.raises(InvalidOperation):
        mapping.buyer_candidates(session, bound["policy"].tenant_id, arguments)


def test_generic_approval_cannot_execute_mapping_action(session, bound):
    from reality.tools.application import approve_and_execute_proposal

    review = prepare(session, bound)
    with pytest.raises((InvalidOperation, ValueError)):
        approve_and_execute_proposal(
            session, bound["policy"].tenant_id, review["review_id"], confirmed=True
        )
    assert (
        mapping.get_verified_buyer_mapping(
            session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
        )
        is None
    )


def test_mcp_live_token_scope_revoke_and_truthful_attribution(
    session, bound, monkeypatch
):
    from reality.domain.shopify_buyer_mapping import canonical
    from reality.mcp.auth import create_mcp_access_token
    from reality.mcp.catalog import dispatch_mcp_tool
    from reality.mcp.principal import MCPPrincipal

    tools = [
        "shopify_source_buyer_candidates",
        "shopify_source_buyer_mapping_prepare",
        "shopify_source_buyer_mapping_commit",
        "shopify_source_buyer_mapping_status",
    ]
    token, _ = create_mcp_access_token(
        session, bound["policy"].tenant_id, "Synthetic mapping bridge", tools
    )
    principal = MCPPrincipal(
        authentication_kind="manual",
        credential_id=token.id,
        grant_id=None,
        user_id=None,
        tenant_id=bound["policy"].tenant_id,
        client_id="test",
        scopes=frozenset(),
        allowed_tools=frozenset(tools),
    )
    # MCP schema has no host-policy field. Trusted file only.
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as folder:
        file = Path(folder) / "policy.json"
        file.write_text(canonical(bound["policy"].model_dump()))
        file.chmod(0o600)
        monkeypatch.setenv(
            "REALITY_SHOPIFY_SOURCE_BUYER_MAPPING_POLICY_FILE", str(file)
        )
        choices = dispatch_mcp_tool(
            session,
            principal,
            tools[0],
            {"source_record_id": bound["source"].id, "import_job_id": bound["job"].id},
        )
        customer = next(
            row
            for row in choices["items"]
            if row["party_id"] == bound["business"].customer.id
        )
        review = dispatch_mcp_tool(
            session,
            principal,
            tools[1],
            {
                "request_id": str(uuid4()),
                "source_record_id": bound["source"].id,
                "import_job_id": bound["job"].id,
                "source_hash": bound["source"].payload_hash,
                "source_version": bound["source"].version,
                "customer_party_id": customer["party_id"],
                "customer_digest": customer["digest"],
            },
        )
        signed = proof(bound, review)
        from reality.db.core import now

        token.revoked_at = now()
        session.commit()
        args = {
            "review_id": review["review_id"],
            "review_digest": review["review_digest"],
            "approval_proof": signed,
        }
        with pytest.raises(InvalidOperation):
            dispatch_mcp_tool(session, principal, tools[2], args)
        token.revoked_at = None
        session.commit()
        result = dispatch_mcp_tool(session, principal, tools[2], args)
        assert result["approval"]["subject"] == "tuesday-person"
        action = session.scalar(
            select(ChangeProposal).where(ChangeProposal.id == review["review_id"])
        )
        assert action.decided_via_token_id == token.id
        assert action.decided_by_user_id is None
        assert action.decided_via_channel is None
        with pytest.raises(PermissionError):
            dispatch_mcp_tool(
                session,
                principal,
                "proposal_approve_and_execute",
                {"proposal_id": review["review_id"]},
            )


def test_foreign_mapping_reads_and_writes_never_expose_or_change_receipt(
    session, bound
):
    from reality.services.core import create_tenant

    other = create_tenant(session, "Foreign mapping test")
    review = prepare(session, bound)
    with pytest.raises(InvalidOperation):
        mapping.buyer_candidates(
            session,
            other.id,
            {"source_record_id": bound["source"].id, "import_job_id": bound["job"].id},
            policy=bound["policy"],
        )
    with pytest.raises(InvalidOperation):
        mapping.buyer_mapping_status(
            session,
            other.id,
            {"review_id": review["review_id"]},
            policy=bound["policy"],
        )
    with pytest.raises(InvalidOperation):
        mapping.commit_buyer_mapping(
            session,
            other.id,
            {
                "review_id": review["review_id"],
                "review_digest": review["review_digest"],
                "approval_proof": proof(bound, review),
            },
            policy=bound["policy"],
        )
    assert (
        mapping.get_verified_buyer_mapping(
            session, other.id, bound["source"].id, bound["job"].id
        )
        is None
    )
    assert (
        mapping.get_verified_buyer_mapping(
            session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
        )
        is None
    )


def test_expiry_after_canonical_source_wait_never_accepts_mapping(
    session, bound, monkeypatch
):
    review = prepare(session, bound)
    signed = proof(bound, review)
    original = mapping.core.store_source_record
    instant = mapping._now()

    def delayed(*args, **kwargs):
        value = original(*args, **kwargs)
        monkeypatch.setattr(mapping, "_now", lambda: instant + timedelta(minutes=6))
        return value

    monkeypatch.setattr(mapping.core, "store_source_record", delayed)
    with pytest.raises(InvalidOperation):
        commit(session, bound, review, signed)
    session.rollback()
    action = session.scalar(
        select(ChangeProposal).where(ChangeProposal.id == review["review_id"])
    )
    assert action.status == "proposed"
    assert (
        mapping.get_verified_buyer_mapping(
            session, bound["policy"].tenant_id, bound["source"].id, bound["job"].id
        )
        is None
    )


def test_concurrent_different_reviews_accept_only_one_mapping(
    postgres_database, monkeypatch, request
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic, sleep
    from types import SimpleNamespace

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from reality.db.core import Base
    from reality.services.core import create_tenant

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    request.addfinalizer(engine.dispose)
    request.addfinalizer(session.close)
    tenant = create_tenant(session, "Owned concurrent mapping test")
    business = SimpleNamespace(
        tenant=tenant,
        customer=create_party(session, tenant.id, "Existing buyer", "customer"),
    )
    bound = globals()["bound"].__wrapped__(session, business)
    first = prepare(session, bound)
    second = prepare(session, bound)
    signed_first, signed_second = proof(bound, first), proof(bound, second)
    tenant_id = bound["policy"].tenant_id
    policy = bound["policy"]
    reached, release, second_started = Event(), Event(), Event()
    second_pid = []
    original = mapping.core.store_source_record

    def hold(*args, **kwargs):
        reached.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(mapping.core, "store_source_record", hold)

    def run(review, signed, waiting=False):
        with Session(engine) as connection:
            if waiting:
                second_pid.append(connection.scalar(text("select pg_backend_pid()")))
                second_started.set()
            try:
                return mapping.commit_buyer_mapping(
                    connection,
                    tenant_id,
                    {
                        "review_id": review["review_id"],
                        "review_digest": review["review_digest"],
                        "approval_proof": signed,
                    },
                    policy=policy,
                )["state"]
            except InvalidOperation:
                connection.rollback()
                return "refused"

    session.commit()
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(run, first, signed_first)
        assert reached.wait(5)
        b = pool.submit(run, second, signed_second, True)
        assert second_started.wait(5)
        until = monotonic() + 4
        blocked = False
        try:
            while monotonic() < until:
                with engine.connect() as observer:
                    blocked = bool(
                        observer.scalar(
                            text("select cardinality(pg_blocking_pids(:pid)) > 0"),
                            {"pid": second_pid[0]},
                        )
                    )
                if blocked:
                    break
                sleep(0.01)
            assert blocked
        finally:
            release.set()
        assert a.result(timeout=5) == "mapping_recorded"
        assert b.result(timeout=5) == "refused"
    session.expire_all()
    assert (
        candidates(session, bound)["existing_mapping"]["review_id"]
        == first["review_id"]
    )
