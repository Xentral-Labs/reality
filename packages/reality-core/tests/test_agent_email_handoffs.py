"""Spec 351: lossless evidence and exact, externally executed email decisions."""

import base64
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import EmailDispatch, SourceRecord
from reality.services.artifacts import materialize_artifact, stage_artifact
from reality.services.core import InvalidOperation, NotFound, create_tenant
from reality.services.emails import (
    capture_email,
    claim_dispatch,
    complete_email_file,
    email_history,
    email_workflow,
    report_dispatch,
    stage_email_chunk,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def message(**overrides):
    return {
        "account": "support@example.test",
        "sender": "customer@example.test",
        "to": ["support@example.test"],
        "subject": "Delivery question",
        "text": "Please confirm delivery. Grüße!",
        "html": "<p>Please confirm delivery.</p>",
        "external_payload": {"x-vendor": [1, {"unchanged": True}]},
        **overrides,
    }


@pytest.fixture
def files(monkeypatch, tmp_path):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path))


def capture(session, tenant_id, **overrides):
    return capture_email(
        session,
        tenant_id,
        {
            "origin": "mail_agent",
            "retry_key": "inbound-1",
            "direction": "inbound",
            "message": message(),
            **overrides,
        },
    )


def proposal(session, tenant_id, **overrides):
    return create_change_proposal(
        session,
        tenant_id,
        "email_dispatch_authorize",
        {
            "message": message(
                sender="support@example.test", to=["customer@example.test"]
            ),
            "rationale": "Answer the received question",
            "supporting_source_ids": [],
            **overrides,
        },
    )


def claim(session, tenant_id, proposed, **overrides):
    return claim_dispatch(
        session,
        tenant_id,
        {
            "proposal_id": proposed.id,
            "fingerprint": json.loads(proposed.input)["fingerprint"],
            "retry_key": "send-1",
            **overrides,
        },
        executor="local:test",
    )


def report(session, tenant_id, execution, **overrides):
    return report_dispatch(
        session,
        tenant_id,
        {
            "execution_id": execution["execution_id"],
            "retry_key": "receipt-1",
            "outcome": "accepted",
            "observed_at": "2026-10-03T10:00:00Z",
            "actual_message": execution["message"],
            "provider_evidence": {"message_id": "provider-1", "accepted": True},
            **overrides,
        },
        executor="local:test",
    )


def test_capture_preserves_versions_and_file_occurrence_metadata(
    session, business, files
):
    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        BytesIO(b"invoice bytes"),
        filename="old-name.txt",
        content_type="text/plain",
    )
    msg = message(
        attachments=[
            {
                "part_id": "part-1",
                "filename": "Rechnung ä.txt",
                "content_type": "text/plain",
                "artifact_id": artifact.id,
                "sha256": artifact.sha256,
                "inline": True,
                "content_id": "image-1",
            }
        ]
    )
    first = capture(session, business.tenant.id, message=msg)
    replay = capture(session, business.tenant.id, message=msg)
    assert replay["source_id"] == first["source_id"]
    history = email_history(
        session, business.tenant.id, {"source_id": first["source_id"]}
    )
    assert history["source"]["payload"]["message"] == msg
    assert history["attachments"][0]["payload"]["filename"] == "Rechnung ä.txt"
    with materialize_artifact(artifact) as path:
        assert path.read_bytes() == b"invoice bytes"
    second = capture(session, business.tenant.id, message=message(text="Changed"))
    assert second["source_id"] != first["source_id"]
    assert second["version"] == 2
    assert history["source"]["payload"]["message"]["text"] == msg["text"]


def test_missing_files_are_explicit_and_foreign_files_refused(session, business, files):
    result = capture(
        session,
        business.tenant.id,
        message=message(
            attachments=[
                {
                    "part_id": "p1",
                    "filename": "missing.pdf",
                    "missing_reason": "not supplied",
                }
            ]
        ),
    )
    assert result["state"] == "evidence_incomplete"
    assert result["missing_parts"] == ["p1", "original_message"]
    foreign = create_tenant(session, "Other")
    art, _ = stage_artifact(
        session, foreign.id, BytesIO(b"secret"), filename="s", content_type="text/plain"
    )
    with pytest.raises(NotFound):
        capture(
            session,
            business.tenant.id,
            message=message(
                attachments=[
                    {"part_id": "p1", "filename": "secret", "artifact_id": art.id}
                ]
            ),
        )


def test_file_chunks_round_trip_integrity_and_limits(session, business, files):
    content = b"first chunk" + b"second chunk"
    ids = [
        stage_email_chunk(
            session,
            business.tenant.id,
            {"content_base64": base64.b64encode(chunk).decode()},
        )["artifact_id"]
        for chunk in (b"first chunk", b"second chunk")
    ]
    args = {
        "part_artifact_ids": ids,
        "filename": "original.bin",
        "content_type": "application/octet-stream",
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    result = complete_email_file(session, business.tenant.id, args)
    assert result["byte_size"] == len(content)
    assert (
        complete_email_file(session, business.tenant.id, args)["artifact_id"]
        == result["artifact_id"]
    )
    with pytest.raises(InvalidOperation):
        complete_email_file(session, business.tenant.id, {**args, "sha256": "0" * 64})
    with pytest.raises(InvalidOperation):
        stage_email_chunk(session, business.tenant.id, {"content_base64": "invalid!"})
    assert email_workflow()["chunk_bytes"] <= 1024 * 1024


def test_only_exact_approved_snapshot_can_be_claimed(session, business):
    p = proposal(session, business.tenant.id)
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, p)
    approve_and_execute_proposal(session, business.tenant.id, p.id, confirmed=True)
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, p, fingerprint="0" * 64)
    instruction = claim(session, business.tenant.id, p)
    assert instruction["state"] == "dispatch_claimed"
    assert instruction["message"] == json.loads(p.input)["message"]
    assert (
        claim(session, business.tenant.id, p)["execution_id"]
        == instruction["execution_id"]
    )
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, p, retry_key="another-send")
    changed = proposal(
        session, business.tenant.id, message=message(text="Changed reply")
    )
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, changed)
    assert p.status == "executed"
    assert "accepted" not in json.loads(p.output)


def test_result_acceptance_replay_deviation_and_conflict(session, business):
    incoming = capture(session, business.tenant.id)
    p = proposal(
        session, business.tenant.id, supporting_source_ids=[incoming["source_id"]]
    )
    approve_and_execute_proposal(session, business.tenant.id, p.id, confirmed=True)
    execution = claim(session, business.tenant.id, p)
    result = report(session, business.tenant.id, execution)
    assert result["state"] == "provider_accepted"
    assert (
        report(session, business.tenant.id, execution)["source_id"]
        == result["source_id"]
    )
    history = email_history(
        session, business.tenant.id, {"execution_id": execution["execution_id"]}
    )
    assert history["supporting_sources"][0]["id"] == incoming["source_id"]
    assert history["decision"]["proposal_id"] == p.id
    assert history["reports"][0]["payload"]["actual_message"] == execution["message"]
    assert (
        report(
            session,
            business.tenant.id,
            execution,
            retry_key="bad",
            outcome="failed",
            actual_message=None,
        )["state"]
        == "conflicting_evidence"
    )


def test_uncertainty_never_releases_claim_and_deviation_preserves_actual(
    session, business
):
    p = proposal(session, business.tenant.id)
    approve_and_execute_proposal(session, business.tenant.id, p.id, confirmed=True)
    execution = claim(session, business.tenant.id, p)
    assert (
        report(
            session,
            business.tenant.id,
            execution,
            outcome="unknown",
            actual_message=None,
        )["state"]
        == "execution_uncertain"
    )
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, p, retry_key="retry-timeout")
    result = report(
        session,
        business.tenant.id,
        execution,
        retry_key="reconciled",
        actual_message={**execution["message"], "text": "Unapproved edit"},
    )
    assert result["state"] == "approval_deviation"
    assert (
        json.loads(
            session.get(
                SourceRecord,
                {"tenant_id": business.tenant.id, "id": result["source_id"]},
            ).payload
        )["actual_message"]["text"]
        == "Unapproved edit"
    )


def test_history_and_executor_are_tenant_scoped(session, business):
    p = proposal(session, business.tenant.id)
    approve_and_execute_proposal(session, business.tenant.id, p.id, confirmed=True)
    execution = claim(session, business.tenant.id, p)
    foreign = create_tenant(session, "Other")
    with pytest.raises(NotFound):
        email_history(session, foreign.id, {"execution_id": execution["execution_id"]})
    with pytest.raises(InvalidOperation):
        report_dispatch(
            session,
            business.tenant.id,
            {
                "execution_id": execution["execution_id"],
                "retry_key": "x",
                "outcome": "unknown",
                "observed_at": "2026-10-03T10:00:00Z",
                "provider_evidence": {},
            },
            executor="another-agent",
        )


def test_concurrent_claims_have_one_winner(postgres_database):
    from sqlalchemy import create_engine

    from reality.db.core import Base

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        tenant = create_tenant(db, "Concurrent")
        p = proposal(db, tenant.id)
        approve_and_execute_proposal(db, tenant.id, p.id, confirmed=True)
        args = {"proposal_id": p.id, "fingerprint": json.loads(p.input)["fingerprint"]}
        tenant_id = tenant.id

    def attempt(key):
        with Session(engine) as db:
            try:
                return claim_dispatch(
                    db, tenant_id, {**args, "retry_key": key}, executor="local:test"
                )
            except InvalidOperation:
                return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, ["a", "b"]))
        assert sum(item is not None for item in results) == 1
        with Session(engine) as db:
            assert len(list(db.scalars(select(EmailDispatch)))) == 1
    finally:
        engine.dispose()


def test_mcp_permissions_and_server_derived_executor(session, business):
    from reality.mcp.catalog import dispatch_mcp_tool, dispatch_tool
    from reality.mcp.principal import MCPPrincipal

    tid = business.tenant.id
    tools = frozenset(
        {
            "email_capture",
            "email_history",
            "email_workflow",
            "email_dispatch_claim",
            "email_dispatch_propose",
        }
    )
    principal = MCPPrincipal(
        "manual", "token-a", None, None, tid, "client", frozenset(), tools
    )
    incoming = dispatch_mcp_tool(
        session,
        principal,
        "email_capture",
        {
            "origin": "mail_agent",
            "retry_key": "incoming",
            "direction": "inbound",
            "message": message(),
        },
    )
    assert (
        dispatch_mcp_tool(
            session, principal, "email_history", {"source_id": incoming["source_id"]}
        )["source"]["payload"]["message"]
        == message()
    )
    proposed = dispatch_mcp_tool(
        session,
        principal,
        "email_dispatch_propose",
        {
            "message": message(),
            "rationale": "Reply",
            "supporting_source_ids": [incoming["source_id"]],
        },
    )
    assert proposed["requires_confirmation"] is True
    with pytest.raises(PermissionError):
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {"proposal_id": proposed["proposal_id"], "confirmed": True},
        )
    with pytest.raises(PermissionError):
        dispatch_tool(
            session, tid, "email_capture", {}, allowed_access=("read", "propose")
        )
    approve_and_execute_proposal(session, tid, proposed["proposal_id"], confirmed=True)
    instruction = dispatch_mcp_tool(
        session,
        principal,
        "email_dispatch_claim",
        {
            "proposal_id": proposed["proposal_id"],
            "fingerprint": proposed["preview"]["fingerprint"],
            "retry_key": "send",
        },
    )
    assert (
        session.get(
            EmailDispatch, {"tenant_id": tid, "id": instruction["execution_id"]}
        ).executor
        == "mcp:token-a"
    )


def test_api_evidence_review_and_file_round_trip(session, business, files):
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
                "origin": "mail_agent",
                "retry_key": "api-in",
                "direction": "inbound",
                "message": message(),
            }
            incoming = client.post(base + "/email/capture", json=args)
            assert incoming.status_code == 200, incoming.text
            original = client.get(
                base + "/email/history",
                params={"source_id": incoming.json()["source_id"]},
            )
            assert original.json()["source"]["payload"]["message"] == args["message"]
            proposed = client.post(
                base + "/email/dispatch-proposals",
                json={
                    "message": message(bcc=["audit@example.test"]),
                    "rationale": "Answer",
                    "supporting_source_ids": [incoming.json()["source_id"]],
                },
            )
            assert proposed.status_code == 200, proposed.text
            review = client.get(
                base + "/change-proposals/" + proposed.json()["proposal_id"] + "/review"
            )
            assert review.json()["input"]["message"]["bcc"] == ["audit@example.test"]
            assert (
                review.json()["next_step"]["decision_policy"]["approval"]["authority"]
                == "company_member"
            )
            content = b"original email attachment"
            chunk = client.post(
                base + "/email/files/chunks",
                json={"content_base64": base64.b64encode(content).decode()},
            ).json()
            completed = client.post(
                base + "/email/files/complete",
                json={
                    "part_artifact_ids": [chunk["artifact_id"]],
                    "filename": "Original.txt",
                    "content_type": "text/plain",
                    "sha256": hashlib.sha256(content).hexdigest(),
                },
            )
            assert completed.status_code == 200, completed.text
            download = client.get(completed.json()["download_url"])
            assert download.content == content
            assert download.headers["x-content-type-options"] == "nosniff"
            assert download.headers["content-disposition"].startswith("attachment;")
    finally:
        app.dependency_overrides.clear()


def test_rejection_and_foreign_support_are_refused(session, business):
    from reality.tools.application import reject_proposal

    p = proposal(session, business.tenant.id)
    reject_proposal(session, business.tenant.id, p.id)
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, p)
    other = create_tenant(session, "Foreign evidence")
    incoming = capture(session, other.id)
    with pytest.raises(NotFound):
        proposal(
            session, business.tenant.id, supporting_source_ids=[incoming["source_id"]]
        )


def test_approval_rechecks_current_membership(session, business, scheduled_owner):
    from reality.db.core import TenantMembership
    from reality.services.memberships import Principal

    p = proposal(session, business.tenant.id)
    membership = session.scalar(
        select(TenantMembership).where(TenantMembership.user_id == scheduled_owner.id)
    )
    membership.status = "removed"
    session.commit()
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            p.id,
            confirmed=True,
            confirming_principal=Principal(scheduled_owner.id),
        )


def test_provider_added_transport_headers_are_not_content_deviations(session, business):
    p = proposal(session, business.tenant.id)
    approve_and_execute_proposal(session, business.tenant.id, p.id, confirmed=True)
    execution = claim(session, business.tenant.id, p)
    actual = {
        **execution["message"],
        "headers": {"Received": "provider-hop"},
        "message_id": "generated-id",
    }
    assert (
        report(session, business.tenant.id, execution, actual_message=actual)["state"]
        == "provider_accepted"
    )


def test_unknown_send_cannot_be_reproposed_as_a_duplicate(session, business):
    first = proposal(session, business.tenant.id)
    second = proposal(session, business.tenant.id)
    approve_and_execute_proposal(session, business.tenant.id, first.id, confirmed=True)
    approve_and_execute_proposal(session, business.tenant.id, second.id, confirmed=True)
    execution = claim(session, business.tenant.id, first)
    with pytest.raises(InvalidOperation):
        claim(session, business.tenant.id, second)
    report(
        session, business.tenant.id, execution, outcome="unknown", actual_message=None
    )
    with pytest.raises(InvalidOperation):
        proposal(session, business.tenant.id)
    report(
        session,
        business.tenant.id,
        execution,
        retry_key="resolved",
        outcome="failed",
        actual_message=None,
    )
    assert proposal(session, business.tenant.id).status == "proposed"


def test_arbitrary_imported_receipt_cannot_close_a_dispatch(session, business):
    from reality.services.core import enqueue_source

    p = proposal(session, business.tenant.id)
    approve_and_execute_proposal(session, business.tenant.id, p.id, confirmed=True)
    execution = claim(session, business.tenant.id, p)
    enqueue_source(
        session,
        business.tenant.id,
        "reality_email_execution",
        "email_send_result",
        execution["execution_id"] + ":forged",
        {
            "outcome": "accepted",
            "deviation": False,
            "provider_evidence": {"id": "fake"},
        },
    )
    history = email_history(
        session, business.tenant.id, {"execution_id": execution["execution_id"]}
    )
    assert history["state"] == "dispatch_claimed"
    assert history["reports"] == []


def test_unbound_receipt_labels_are_only_original_evidence(session, business):
    from reality.services.core import enqueue_source

    source, _ = enqueue_source(
        session,
        business.tenant.id,
        "reality_email_execution",
        "email_send_result",
        "unbound",
        {"outcome": "accepted"},
    )
    history = email_history(session, business.tenant.id, {"source_id": source.id})
    assert history["source"]["payload"] == {"outcome": "accepted"}
    assert history["decision"] is None


def test_original_mime_file_is_retained_losslessly(session, business, files):
    content = (
        b"From: sender@example.test\r\nSubject: Original\r\n\r\nRaw MIME bytes\r\n"
    )
    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        BytesIO(content),
        filename="message.eml",
        content_type="message/rfc822",
    )
    stored = capture(
        session,
        business.tenant.id,
        message=message(
            original_artifact_id=artifact.id, original_filename="original.eml"
        ),
    )
    assert stored["state"] == "evidence_stored"
    assert stored["missing_parts"] == []
    source = session.get(
        SourceRecord, {"tenant_id": business.tenant.id, "id": stored["source_id"]}
    )
    assert source.source_artifact_id == artifact.id
    with materialize_artifact(artifact) as path:
        assert path.read_bytes() == content
