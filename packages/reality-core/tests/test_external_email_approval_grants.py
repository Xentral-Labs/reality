"""Spec 354: exact external approval and independently permissioned execution."""

import base64
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_agent_email_handoffs import claim, proposal, report

from reality.db.core import ChangeProposal, EmailDispatch, SourceRecord, now
from reality.services.core import InvalidOperation, NotFound, create_tenant
from reality.services.decision_attribution import decision_attributions
from reality.services.email_approval_grants import accept_grant
from reality.services.emails import email_history


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def signed(key, claims, **headers):
    header = {
        "alg": "EdDSA",
        "typ": "reality-email-approval+jwt",
        "kid": "key-1",
        **headers,
    }
    data = ".".join(b64(json.dumps(v).encode()) for v in (header, claims))
    return data + "." + b64(key.sign(data.encode()))


@pytest.fixture
def approval(session, business, monkeypatch):
    key = Ed25519PrivateKey.generate()
    issuer = "https://approval.example.test"
    registry = {
        issuer: {
            "keys": {"key-1": b64(key.public_key().public_bytes_raw())},
            "tenants": {
                business.tenant.id: {
                    "subjects": {"person-42": "Anna Buyer"},
                    "revoked_grant_ids": [],
                    "revoked_before": 0,
                }
            },
        }
    }
    monkeypatch.setenv("REALITY_EMAIL_APPROVAL_TRUST_JSON", json.dumps(registry))
    proposed = proposal(
        session,
        business.tenant.id,
        business_references=[{"kind": "party", "id": business.supplier.id}],
    )
    claims = {
        "version": 1,
        "iss": issuer,
        "sub": "person-42",
        "aud": "reality:email_dispatch",
        "jti": "approval-1",
        "tenant_id": business.tenant.id,
        "proposal_id": proposed.id,
        "approval_digest": json.loads(proposed.output)["approval_digest"],
        "decision": "approve",
        "human_approved": True,
        "iat": int(now().timestamp()),
        "exp": int(now().timestamp()) + 300,
    }
    return key, registry, proposed, claims


def submit(session, company_id, approval, **updates):
    return accept_grant(
        session,
        company_id,
        {
            "proposal_id": approval[2].id,
            "grant": signed(approval[0], {**approval[3], **updates}),
        },
    )


def counts(session, tenant_id):
    return tuple(
        session.scalar(
            select(func.count()).select_from(m).where(m.tenant_id == tenant_id)
        )
        for m in (SourceRecord, EmailDispatch, ChangeProposal)
    )


def test_supplier_single_external_approval_full_evidence_chain(
    session, business, approval
):
    tenant = business.tenant.id
    result = submit(session, tenant, approval)
    assert result["state"] == "dispatch_authorized"
    assert submit(session, tenant, approval) == result
    assert counts(session, tenant)[1:] == (1, 1)
    evidence = email_history(session, tenant, {"proposal_id": approval[2].id})
    decider = evidence["decision"]["decider"]
    assert decider["kind"] == "external_grant"
    assert decider["name"] == "Anna Buyer"
    assert decider["subject"] == "person-42"
    assert decider["issuer"] == approval[3]["iss"]
    assert decider["grant_source_id"] == result["grant_source_id"]
    original = session.get(
        SourceRecord, {"tenant_id": tenant, "id": result["grant_source_id"]}
    )
    assert json.loads(original.payload)["grant"] == signed(approval[0], approval[3])
    assert json.loads(original.payload)["verification"]["public_key"] == b64(
        approval[0].public_key().public_bytes_raw()
    )
    held = claim(session, tenant, approval[2])
    report(
        session,
        tenant,
        held,
        outcome="accepted",
        actual_message=held["message"],
        provider_evidence={"smtp": "250"},
    )
    history = email_history(session, tenant, {"proposal_id": approval[2].id})
    assert history["decision"]["decider"] == decider
    assert history["reports"]
    assert history["business_references"][0]["id"] == business.supplier.id


@pytest.mark.parametrize(
    "update",
    [
        {"iss": "untrusted"},
        {"sub": "not-authorized"},
        {"tenant_id": "foreign"},
        {"proposal_id": "other"},
        {"aud": "other"},
        {"approval_digest": "0" * 64},
        {"decision": "reject"},
        {"human_approved": False},
        {"version": 2},
        {"iat": 0, "exp": 1},
        {"exp": 9999999999},
        {"iat": 9999999999},
        {"iat": True},
        {"extra": "unchecked"},
    ],
)
def test_invalid_claims_have_no_effects(session, business, approval, update):
    before = counts(session, business.tenant.id)
    with pytest.raises(InvalidOperation):
        submit(session, business.tenant.id, approval, **update)
    assert counts(session, business.tenant.id) == before
    session.refresh(approval[2])
    assert approval[2].status == "proposed"


@pytest.mark.parametrize(
    "headers",
    [
        {"alg": "none"},
        {"alg": "HS256"},
        {"kid": "unknown"},
        {"typ": "JWT"},
        {"jku": "https://attacker.test"},
    ],
)
def test_bad_headers_refused(session, business, approval, headers):
    before = counts(session, business.tenant.id)
    with pytest.raises(InvalidOperation):
        accept_grant(
            session,
            business.tenant.id,
            {
                "proposal_id": approval[2].id,
                "grant": signed(approval[0], approval[3], **headers),
            },
        )
    assert counts(session, business.tenant.id) == before


def test_invalid_signature_and_malformed_proof(session, business, approval):
    for proof in [
        "not-a-proof",
        signed(Ed25519PrivateKey.generate(), approval[3]),
        signed(approval[0], approval[3]) + "=",
    ]:
        with pytest.raises(InvalidOperation):
            accept_grant(
                session,
                business.tenant.id,
                {"proposal_id": approval[2].id, "grant": proof},
            )


@pytest.mark.parametrize("field", ["text", "bcc", "business_references", "rationale"])
def test_changed_proposal_invalidates_grant(session, business, approval, field):
    data = json.loads(approval[2].input)
    if field in {"text", "bcc"}:
        data["message"][field] = (
            ["hidden@example.test"] if field == "bcc" else "Changed"
        )
    else:
        data[field] = (
            [{"kind": "item", "id": business.item.id}]
            if field == "business_references"
            else "Changed rationale"
        )
    approval[2].input = json.dumps(data)
    session.commit()
    with pytest.raises(InvalidOperation):
        submit(session, business.tenant.id, approval)


@pytest.mark.parametrize("revoke", ["key", "subject", "company", "grant", "cutoff"])
def test_revocation_blocks_claim_preserves_historical_decider(
    session, business, approval, monkeypatch, revoke
):
    submit(session, business.tenant.id, approval)
    tenant_id = business.tenant.id
    before = decision_attributions(session, tenant_id, [approval[2].id])
    registry = approval[1]
    issuer = registry[approval[3]["iss"]]
    mandate = issuer["tenants"][tenant_id]
    if revoke == "key":
        issuer["keys"].clear()
    elif revoke == "subject":
        mandate["subjects"].clear()
    elif revoke == "company":
        issuer["tenants"].clear()
    elif revoke == "grant":
        mandate["revoked_grant_ids"] = [approval[3]["jti"]]
    else:
        mandate["revoked_before"] = approval[3]["iat"]
    monkeypatch.setenv("REALITY_EMAIL_APPROVAL_TRUST_JSON", json.dumps(registry))
    with pytest.raises(InvalidOperation):
        claim(session, tenant_id, approval[2])
    assert decision_attributions(session, tenant_id, [approval[2].id]) == before
    assert (
        session.scalar(
            select(EmailDispatch).where(EmailDispatch.tenant_id == tenant_id)
        ).executor
        is None
    )


def test_foreign_proposal_no_disclosure(session, business, approval):
    other = create_tenant(session, "Foreign")
    with pytest.raises(NotFound):
        submit(session, other.id, approval)


def test_issuer_grant_id_cannot_rebind_second_proposal(session, business, approval):
    submit(session, business.tenant.id, approval)
    second = proposal(session, business.tenant.id)
    claims = {
        **approval[3],
        "proposal_id": second.id,
        "approval_digest": json.loads(second.output)["approval_digest"],
    }
    with pytest.raises(InvalidOperation):
        accept_grant(
            session,
            business.tenant.id,
            {"proposal_id": second.id, "grant": signed(approval[0], claims)},
        )
    assert counts(session, business.tenant.id)[1] == 1


def test_concurrent_identical_acceptance_one_decision(postgres_database, monkeypatch):
    from sqlalchemy import create_engine

    from reality.db.core import Base

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    key = Ed25519PrivateKey.generate()
    with Session(engine) as db:
        tenant = create_tenant(db, "Concurrent")
        proposed = proposal(db, tenant.id)
        tenant_id = tenant.id
        claims = {
            "version": 1,
            "iss": "issuer",
            "sub": "person",
            "aud": "reality:email_dispatch",
            "jti": "one",
            "tenant_id": tenant_id,
            "proposal_id": proposed.id,
            "approval_digest": json.loads(proposed.output)["approval_digest"],
            "decision": "approve",
            "human_approved": True,
            "iat": int(now().timestamp()),
            "exp": int(now().timestamp()) + 300,
        }
        registry = {
            "issuer": {
                "keys": {"key-1": b64(key.public_key().public_bytes_raw())},
                "tenants": {tenant_id: {"subjects": {"person": "Anna"}}},
            }
        }
        monkeypatch.setenv("REALITY_EMAIL_APPROVAL_TRUST_JSON", json.dumps(registry))
        args = {"proposal_id": proposed.id, "grant": signed(key, claims)}

    def run(_):
        with Session(engine) as concurrent:
            return accept_grant(concurrent, tenant_id, args)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, range(2)))
        assert results[0] == results[1]
        with Session(engine) as db:
            assert counts(db, tenant_id)[1] == 1
    finally:
        engine.dispose()


def test_acceptance_failure_rolls_back_source_and_authorization(
    session, business, approval, monkeypatch
):
    from reality.services import email_approval_grants

    before = counts(session, business.tenant.id)

    original_authorize = email_approval_grants.authorize_dispatch

    def fail(*args, **kwargs):
        original_authorize(*args, **kwargs)
        raise RuntimeError("Injected authorization failure")

    monkeypatch.setattr(email_approval_grants, "authorize_dispatch", fail)
    with pytest.raises(RuntimeError):
        submit(session, business.tenant.id, approval)
    assert counts(session, business.tenant.id) == before
    session.refresh(approval[2])
    assert approval[2].status == "proposed"


def test_manual_mcp_submission_requires_own_permission_and_not_person_identity(
    session, business, approval, monkeypatch
):
    from reality.mcp.catalog import dispatch_mcp_tool
    from reality.mcp.principal import MCPPrincipal

    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    tenant_id = business.tenant.id
    args = {"proposal_id": approval[2].id, "grant": signed(approval[0], approval[3])}
    token = MCPPrincipal(
        "manual",
        "executor-token",
        None,
        None,
        tenant_id,
        "client",
        frozenset(),
        frozenset({"email_dispatch_claim"}),
    )
    with pytest.raises(PermissionError):
        dispatch_mcp_tool(session, token, "email_dispatch_accept_grant", args)
    authorized = MCPPrincipal(
        "manual",
        "submit-token",
        None,
        None,
        tenant_id,
        "client",
        frozenset(),
        frozenset({"email_dispatch_accept_grant"}),
    )
    result = dispatch_mcp_tool(session, authorized, "email_dispatch_accept_grant", args)
    assert result["grant_source_id"]
    attribution = decision_attributions(session, tenant_id, [approval[2].id])[
        approval[2].id
    ]
    assert attribution["decider"]["kind"] == "external_grant"
    assert approval[2].decided_by_user_id is None
    assert approval[2].decided_via_token_id is None


def test_expired_proof_blocks_claim_replay(session, business, approval, monkeypatch):
    from datetime import timedelta

    from reality.services import email_approval_grants

    submit(session, business.tenant.id, approval)
    claim(session, business.tenant.id, approval[2])
    later = now() + timedelta(seconds=601)
    monkeypatch.setattr(email_approval_grants, "now", lambda: later)
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, approval[2])


def test_duplicate_json_members_refused_even_with_valid_signature(
    session, business, approval
):
    header = b64(
        b'{"alg":"EdDSA","typ":"reality-email-approval+jwt","kid":"key-1","kid":"key-1"}'
    )
    content = header + "." + b64(json.dumps(approval[3]).encode())
    proof = content + "." + b64(approval[0].sign(content.encode()))
    with pytest.raises(InvalidOperation):
        accept_grant(
            session, business.tenant.id, {"proposal_id": approval[2].id, "grant": proof}
        )


def test_external_grant_cannot_approve_uncertain_retry_risk(
    session, business, approval
):
    from reality.tools.application import approve_and_execute_proposal

    old = proposal(session, business.tenant.id)
    approve_and_execute_proposal(session, business.tenant.id, old.id, confirmed=True)
    execution = claim(session, business.tenant.id, old)
    # Exact current no-report snapshot remains uncertain; signing risk is insufficient.
    retry = proposal(
        session,
        business.tenant.id,
        retry_acknowledgements=[
            {
                "execution_id": execution["execution_id"],
                "report_source_ids": [],
                "reason": "Explicit risk",
                "accept_duplicate_send_risk": True,
            }
        ],
    )
    claims = {
        **approval[3],
        "proposal_id": retry.id,
        "approval_digest": json.loads(retry.output)["approval_digest"],
    }
    with pytest.raises(InvalidOperation):
        accept_grant(
            session,
            business.tenant.id,
            {"proposal_id": retry.id, "grant": signed(approval[0], claims)},
        )
    session.refresh(retry)
    assert retry.status == "proposed"


def test_api_grant_acceptance_and_original_source_navigation(
    session, business, approval
):
    from fastapi.testclient import TestClient

    from reality.web.api import database_session
    from reality.web.app import app

    def database():
        yield session

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            args = {
                "proposal_id": approval[2].id,
                "grant": signed(approval[0], approval[3]),
            }
            refused = client.post(
                base + "/email/dispatch-grants", json={**args, "grant": "unsigned"}
            )
            assert refused.status_code == 400
            accepted = client.post(base + "/email/dispatch-grants", json=args)
            assert accepted.status_code == 200, accepted.text
            history = client.get(
                base + "/email/history", params={"proposal_id": approval[2].id}
            ).json()
            assert history["decision"]["decider"]["kind"] == "external_grant"
            original = client.get(
                base + "/inspector/source_record/" + accepted.json()["grant_source_id"]
            )
            assert original.status_code == 200, original.text
            assert args["grant"] in original.text
    finally:
        app.dependency_overrides.clear()
