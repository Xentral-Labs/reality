"""Spec 360 FR-008/009/011: actual authenticated HTTP agent review transport."""

import base64
import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from test_intake_admission import prepare
from test_intake_agent_review import owner_mandate

from reality.db.core import ChangeProposal, Document
from reality.mcp import auth as auth_module
from reality.mcp import server as server_module
from reality.mcp.app import create_mcp_app
from reality.mcp.auth import create_mcp_access_token, revoke_mcp_access_token
from reality.mcp.config import MCPRuntimeSettings


def test_http_named_agent_exact_review_quota_replay_and_token_revocation(
    session, business, scheduled_owner, monkeypatch
):
    import test_intake_agent_review as support

    issued = []
    allowed = (
        "intake_agent_review_material",
        "intake_agent_review_source_page",
        "intake_agent_review_and_execute",
    )

    def issue(db, tenant, name, **kwargs):
        record, clear = create_mcp_access_token(
            db, tenant, name, allowed_tools=allowed, **kwargs
        )
        issued.append(clear)
        return record, clear

    monkeypatch.setattr(support, "create_mcp_access_token", issue)
    mandate_id, token = owner_mandate(session, business, scheduled_owner, daily_units=1)
    source, _, proposal = prepare(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(server_module, "Session", factory)
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/", bind_host="127.0.0.1", bind_port=8001
        ),
        session_factory=factory,
    )
    headers = {
        "Authorization": f"Bearer {issued[0]}",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
    }

    with TestClient(runtime) as client:

        def call(name, arguments):
            response = client.post(
                "/",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                },
            )
            assert response.status_code == 200
            return response.json()["result"]

        def data(result):
            assert not result.get("isError"), result
            return result.get("structuredContent") or json.loads(
                result["content"][0]["text"]
            )

        try:
            args = {"mandate_id": mandate_id, "proposal_id": proposal.id}
            material = data(call("intake_agent_review_material", args))
            original = data(call("intake_agent_review_source_page", args))
            assert base64.b64decode(original["content"]) == source.payload.encode(
                "utf-8"
            )
            evidence = {
                **material["evidence_template"],
                "verdict": "approve",
                "reasons": ["source_matches_prepared_meaning"],
            }
            assert call(
                "intake_agent_review_and_execute", {**evidence, "digest": "0" * 64}
            )["isError"]
            session.expire_all()
            assert session.scalar(select(func.count()).select_from(Document)) == 0
            data(call("intake_agent_review_and_execute", evidence))
            data(call("intake_agent_review_and_execute", evidence))
            session.expire_all()
            accepted = session.get(ChangeProposal, (business.tenant.id, proposal.id))
            assert accepted.status == "executed"
            assert (
                accepted.decided_via_token_id == token.id
                and accepted.decided_by_user_id is None
            )
            assert session.scalar(select(func.count()).select_from(Document)) == 1
            assert json.loads(accepted.output)["source_record_id"] == source.id
            # A second distinct source cannot exceed the finite owner decision.
            from reality.services import core

            payload = json.loads(source.payload)
            payload["id"] = "second-http-source"
            _, job = core.enqueue_shopify_order(
                session,
                business.tenant.id,
                payload,
                business.company.id,
                business.customer.id,
                business.location.id,
            )
            from reality.services.intake import prepare_intake

            second = prepare_intake(session, business.tenant.id, job.id)
            second_args = {"mandate_id": mandate_id, "proposal_id": second.id}
            material = data(call("intake_agent_review_material", second_args))
            evidence = {
                **material["evidence_template"],
                "verdict": "approve",
                "reasons": ["source_matches_prepared_meaning"],
            }
            assert call("intake_agent_review_and_execute", evidence)["isError"]
            session.expire_all()
            assert session.scalar(select(func.count()).select_from(Document)) == 1
        finally:
            revoke_mcp_access_token(session, business.tenant.id, token.id)
        response = client.post(
            "/",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert response.status_code == 401
