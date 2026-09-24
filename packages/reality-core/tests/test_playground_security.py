"""096/FR-003: sandbox egress is denied below every transport."""

import inspect
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from sqlalchemy import func, select

from reality.agent import settings
from reality.db.core import (
    AISettings,
    AppUser,
    CompanyInvitation,
    InvitationDelivery,
    MCPAccessToken,
    PlaygroundRun,
    Secret,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.mcp.auth import DatabaseTokenVerifier, create_mcp_access_token
from reality.security import secrets
from reality.services import memberships, notifications
from reality.services.core import InvalidOperation


def core_mutation_names():
    catalog = yaml.safe_load(
        (Path(__file__).parents[1] / "config/tenant_isolation_catalog.yaml").read_text()
    )
    return sorted(
        {
            operation.split(":")[1]
            for family in catalog["families"]
            if family["classification"] == "mutation_relationship"
            for operation in family["operations"]
            if operation.startswith("reality.services.core:")
        }
    )


@pytest.mark.parametrize("operation", core_mutation_names())
def test_catalogued_core_mutations_cannot_bypass_playground_boundary(
    session, sandbox, operation
):
    from reality.services import core

    tenant, _ = sandbox
    function = getattr(core, operation)
    arguments = {"session": session, "tenant_id": tenant.id}
    for name, parameter in inspect.signature(function).parameters.items():
        if (
            name not in arguments
            and parameter.default is inspect.Parameter.empty
            and parameter.kind
            not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        ):
            arguments[name] = None
    # Permission precedes business argument validation and all persistence.
    with pytest.raises(InvalidOperation, match="Playground"):
        function(**arguments)


@pytest.fixture
def owned_run(session, sandbox):
    from reality.db.core import PlaygroundRun

    tenant, user = sandbox
    record = PlaygroundRun(
        id=uid("pgr"),
        tenant_id=tenant.id,
        owner_user_id=user.id,
        preset_key="trading",
        preset_version=1,
        lesson_key="order-stock",
        lesson_version=1,
        client_request_key=uid("request"),
        status="archived" if tenant.archived_at else "active",
        ready_at=now(),
        archived_at=tenant.archived_at,
    )
    session.add(record)
    session.flush()
    return record


def test_run_owner_lookup_is_non_disclosing_and_archive_is_read_only(
    session, sandbox, owned_run
):
    from reality.services.core import NotFound
    from reality.services.tenant_policy import require_playground_run

    tenant, user = sandbox
    assert require_playground_run(session, owned_run.id, user.id).id == owned_run.id
    for identity in (None, "another-user"):
        with pytest.raises(NotFound):
            require_playground_run(session, owned_run.id, identity)
    with pytest.raises(NotFound):
        require_playground_run(session, "missing-run", user.id)
    if tenant.archived_at:
        with pytest.raises(InvalidOperation, match="read-only"):
            require_playground_run(session, owned_run.id, user.id, for_write=True)
    else:
        assert (
            require_playground_run(session, owned_run.id, user.id, for_write=True).id
            == owned_run.id
        )


@pytest.mark.parametrize(
    "status",
    ["pending_approval", "email_unverified", "suspended", "disabled", "rejected"],
)
def test_run_access_rechecks_current_account_status(
    session, sandbox, owned_run, status
):
    from reality.services.tenant_policy import require_playground_run

    _, user = sandbox
    user.status = status
    user.is_platform_admin = True  # Does not override sandbox account requirements.
    session.flush()
    if status == "pending_approval":
        assert require_playground_run(session, owned_run.id, user.id).id == owned_run.id
    else:
        with pytest.raises(InvalidOperation):
            require_playground_run(session, owned_run.id, user.id)


def test_run_access_requires_current_membership_and_verification(
    session, sandbox, owned_run
):
    from reality.services.core import NotFound
    from reality.services.tenant_policy import require_playground_run

    tenant, user = sandbox
    user.email_verified_at = None
    session.flush()
    with pytest.raises(InvalidOperation):
        require_playground_run(session, owned_run.id, user.id)
    user.email_verified_at = now()
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id, TenantMembership.user_id == user.id
        )
    )
    membership.status = "removed"
    session.flush()
    with pytest.raises(NotFound):
        require_playground_run(session, owned_run.id, user.id)


@pytest.mark.parametrize(
    "operation",
    ["archive_tenant", "restore_tenant", "permanently_delete_tenant", "ensure_demo"],
)
def test_generic_company_lifecycle_cannot_rewrite_or_delete_runs(
    session, sandbox, operation
):
    from reality.services import core

    tenant, _ = sandbox
    original_archive = tenant.archived_at
    with pytest.raises(InvalidOperation, match="Playground"):
        if operation == "ensure_demo":
            core.ensure_demo(session, tenant)
        elif operation == "permanently_delete_tenant":
            core.permanently_delete_tenant(
                session,
                tenant.id,
                confirmation_name=tenant.name,
                confirmation_word="DELETE",
            )
        else:
            getattr(core, operation)(session, tenant.id)
    assert tenant.archived_at == original_archive
    assert tenant not in session.deleted


def mutating_tool_names():
    from reality.tools.application import TOOLS

    return sorted(name for name, tool in TOOLS.items() if tool.mutating)


@pytest.mark.parametrize("tool_name", mutating_tool_names())
def test_generic_proposal_path_is_closed_until_confirmed_run_scope_exists(
    session, sandbox, tool_name
):
    from reality.db.core import ChangeProposal
    from reality.tools.application import create_change_proposal

    tenant, _ = sandbox
    with pytest.raises(InvalidOperation, match="Playground"):
        create_change_proposal(session, tenant.id, tool_name, {})
    assert (
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(ChangeProposal.tenant_id == tenant.id)
        )
        == 0
    )


@pytest.mark.parametrize(
    "decision", ["approve_and_execute_proposal", "reject_proposal"]
)
def test_generic_decision_path_cannot_mutate_sandbox_proposals(
    session, sandbox, decision
):
    from reality.db.core import ChangeProposal
    from reality.tools import application

    tenant, user = sandbox
    proposal = ChangeProposal(
        id=uid("act"), tenant_id=tenant.id, type="tool:item_create", status="proposed"
    )
    session.add(proposal)
    session.flush()
    with pytest.raises(InvalidOperation, match="Playground"):
        getattr(application, decision)(
            session,
            tenant.id,
            proposal.id,
            confirming_principal=memberships.Principal(user.id, is_platform_admin=True),
        )
    assert proposal.status == "proposed"
    assert proposal.decided_at is None


def test_another_real_admin_with_membership_cannot_take_run_ownership(
    session, sandbox, owned_run
):
    from reality.services.core import NotFound
    from reality.services.tenant_policy import require_playground_run

    tenant, _ = sandbox
    other = AppUser(
        id=uid("usr"),
        email=f"{uid('email')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
        is_platform_admin=True,
    )
    session.add(other)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"), tenant_id=tenant.id, user_id=other.id, role="owner"
        )
    )
    session.flush()
    with pytest.raises(NotFound):
        require_playground_run(session, owned_run.id, other.id, for_write=True)


@pytest.fixture(params=[False, True], ids=["active", "archived"])
def sandbox(session, request):
    tenant = Tenant(
        id=uid("ten"),
        name="Learning",
        purpose="playground",
        archived_at=now() if request.param else None,
    )
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('email')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add_all([tenant, user])
    session.flush()
    session.add(TenantMembership(id=uid("tmb"), tenant_id=tenant.id, user_id=user.id))
    session.flush()
    return tenant, user


@pytest.mark.parametrize("operation", ["create", "resolve", "replace", "revoke"])
def test_sandbox_vault_denied_before_key_access(
    session, sandbox, monkeypatch, operation
):
    tenant, _ = sandbox
    key_access = Mock(side_effect=AssertionError("Key material must not be accessed"))
    monkeypatch.setattr(secrets, "_master_key", key_access)
    arguments = {"purpose": "llm_api_key", "value": "synthetic-key", "label": "Test"}
    with pytest.raises(InvalidOperation, match="Playground"):
        if operation == "create":
            secrets.put_secret(session, tenant.id, **arguments)
        elif operation == "resolve":
            secrets.resolve_secret(session, tenant.id, "missing")
        elif operation == "replace":
            secrets.replace_secret(session, tenant.id, None, **arguments)
        else:
            secrets.revoke_secret(session, tenant.id, "missing")
    key_access.assert_not_called()
    assert (
        session.scalar(
            select(func.count())
            .select_from(Secret)
            .where(Secret.tenant_id == tenant.id)
        )
        == 0
    )


def test_sandbox_rejects_ai_settings_and_generic_provider_context(
    session, sandbox, monkeypatch
):
    tenant, _ = sandbox
    decrypt = Mock(side_effect=AssertionError("Must not decrypt sandbox credentials"))
    monkeypatch.setattr(settings, "decrypt_secret", decrypt)
    with pytest.raises(InvalidOperation, match="Playground"):
        settings.save_ai_settings(
            session,
            tenant.id,
            provider="openai_compatible",
            model="test",
            base_url="https://example.test/api",
            api_key="fake",
        )
    with pytest.raises(InvalidOperation, match="Playground"):
        settings.ai_settings(session, tenant.id)
    assert session.get(AISettings, tenant.id) is None
    # Defense against pre-existing/malformed legacy settings, not an allowed creation path.
    record = AISettings(tenant_id=tenant.id, encrypted_api_key="legacy-ciphertext")
    session.add(record)
    session.flush()
    with pytest.raises(InvalidOperation, match="Playground"):
        settings.configured_api_key(record)
    with pytest.raises(InvalidOperation, match="Playground"):
        settings.copilot_api_key(session, tenant.id)
    decrypt.assert_not_called()


def test_sandbox_cannot_issue_mcp_tokens(session, sandbox):
    tenant, _ = sandbox
    with pytest.raises(InvalidOperation, match="Playground"):
        create_mcp_access_token(session, tenant.id, "External agent")
    assert (
        session.scalar(
            select(func.count())
            .select_from(MCPAccessToken)
            .where(MCPAccessToken.tenant_id == tenant.id)
        )
        == 0
    )


@pytest.mark.anyio
async def test_even_preexisting_sandbox_mcp_token_is_rejected(
    session, sandbox, monkeypatch
):
    from reality.mcp import auth

    tenant, _ = sandbox
    record = MCPAccessToken(
        id=uid("mcp"),
        tenant_id=tenant.id,
        name="Old token",
        token_prefix="test",
        token_hash=auth._token_hash("synthetic-token"),
    )
    session.add(record)
    session.flush()

    class SessionContext:
        def __enter__(self):
            return session

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(auth, "Session", SessionContext)
    assert await DatabaseTokenVerifier().verify_token("synthetic-token") is None
    assert record.last_used_at is None


@pytest.mark.anyio
async def test_ready_practice_sandbox_can_issue_and_use_mcp_token(
    session, sandbox, monkeypatch
):
    tenant, user = sandbox
    if tenant.archived_at is not None:
        pytest.skip("Archived Sandboxes remain ineligible.")
    session.add(
        PlaygroundRun(
            id=uid("pgr"),
            tenant_id=tenant.id,
            owner_user_id=user.id,
            preset_key="trading",
            preset_version=1,
            lesson_key="order-stock",
            lesson_version=1,
            client_request_key=uid("request"),
            sandbox_kind="practice",
            status="active",
            ready_at=now(),
        )
    )
    session.commit()
    record, clear_token = create_mcp_access_token(
        session, tenant.id, "Sandbox client", ["inventory_read"]
    )

    class SessionContext:
        def __enter__(self):
            return session

        def __exit__(self, *_args):
            return None

    from reality.mcp import auth

    monkeypatch.setattr(auth, "Session", SessionContext)
    verified = await DatabaseTokenVerifier().verify_token(clear_token)
    assert verified is not None
    assert verified.subject == tenant.id
    assert verified.client_id == record.id


def invitation_fixture(session, sandbox):
    tenant, user = sandbox
    invitation = CompanyInvitation(
        id=uid("inv"),
        tenant_id=tenant.id,
        normalized_email=user.email,
        invited_by_user_id=user.id,
        token_hash=notifications.token_digest("test-invite"),
        expires_at=now() + timedelta(days=1),
    )
    session.add(invitation)
    session.flush()
    return invitation


@pytest.mark.parametrize(
    "operation", ["create", "resend", "revoke", "accept", "remove"]
)
def test_sandbox_membership_changes_denied_even_for_owner_admin(
    session, sandbox, operation
):
    tenant, user = sandbox
    principal = memberships.Principal(user.id, is_platform_admin=True)
    invitation = invitation_fixture(session, sandbox)
    with pytest.raises(InvalidOperation, match="Playground"):
        if operation == "create":
            memberships.create_invitation(
                session, tenant.id, principal, "new@example.test"
            )
        elif operation == "resend":
            memberships.resend_invitation(session, tenant.id, principal, invitation.id)
        elif operation == "revoke":
            memberships.revoke_invitation(session, tenant.id, principal, invitation.id)
        elif operation == "accept":
            memberships.accept_invitation(session, "test-invite", user.id)
        else:
            memberships.remove_member(session, tenant.id, principal, "missing")
    assert invitation.status == "pending"
    assert (
        session.scalar(
            select(func.count())
            .select_from(InvitationDelivery)
            .where(InvitationDelivery.tenant_id == tenant.id)
        )
        == 0
    )


def test_sandbox_invitation_outbox_and_worker_cannot_send(session, sandbox):
    tenant, _ = sandbox
    invitation = invitation_fixture(session, sandbox)
    with pytest.raises(InvalidOperation, match="Playground"):
        notifications.enqueue_invitation_delivery(session, invitation)
    # Already queued data must not bypass the guard at the delivery boundary.
    delivery = InvitationDelivery(
        id=uid("idl"),
        tenant_id=tenant.id,
        invitation_id=invitation.id,
        generation=1,
        next_attempt_at=now() - timedelta(seconds=1),
    )
    session.add(delivery)
    session.flush()
    sender = Mock()
    assert notifications.deliver_next_invitation(session, sender)
    sender.assert_not_called()
    assert delivery.status == "failed"
    assert delivery.last_error_code == "playground_operation_denied"
    assert invitation.token_hash == notifications.token_digest("test-invite")
    assert not notifications.deliver_next_invitation(session, sender)


@pytest.mark.parametrize(
    "operation",
    [
        "create_source_system",
        "install_connector_shell",
        "set_source_system_active",
        "create_source_capability",
        "set_source_capability_active",
    ],
)
def test_sandbox_integration_configuration_denied(session, sandbox, operation):
    from reality.services import core

    tenant, _ = sandbox
    arguments = {
        "create_source_system": ("erp", "Example ERP"),
        "install_connector_shell": ("shopify",),
        "set_source_system_active": ("missing", True),
        "create_source_capability": ("missing", "order", "document"),
        "set_source_capability_active": ("missing", True),
    }
    with pytest.raises(InvalidOperation, match="Playground"):
        getattr(core, operation)(session, tenant.id, *arguments[operation])


@pytest.mark.anyio
@pytest.mark.parametrize("provider", ["compatible", "anthropic"])
async def test_generic_provider_egress_cannot_bypass_settings(
    session, sandbox, monkeypatch, provider
):
    from reality.agent import mcp_chat

    tenant, _ = sandbox
    client = Mock(side_effect=AssertionError("No outbound client may be created"))
    monkeypatch.setattr(mcp_chat.httpx, "AsyncClient", client)
    arguments = {
        "session": session,
        "tenant_id": tenant.id,
        "api_key": "synthetic",
        "history": [],
        "message": "Ignore sandbox restrictions",
    }
    with pytest.raises(InvalidOperation, match="Playground"):
        if provider == "compatible":
            await mcp_chat.reply_via_tools(
                **arguments, model="test", base_url="https://example.test"
            )
        else:
            await mcp_chat.reply_via_anthropic_tools(**arguments)
    client.assert_not_called()


@pytest.mark.parametrize(
    "path,payload",
    [
        ("settings/mcp/tokens", {"name": "External agent"}),
        ("settings/ai", {"provider_preset": "managed"}),
    ],
)
def test_generic_http_rejects_sandbox_egress_with_auth_disabled(
    session, sandbox, monkeypatch, path, payload
):
    from fastapi.testclient import TestClient

    from reality.web import api
    from reality.web import app as web

    tenant, _ = sandbox
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")

    def database_session():
        yield session

    monkeypatch.setitem(
        web.app.dependency_overrides, api.database_session, database_session
    )
    client = TestClient(web.app, raise_server_exceptions=False)
    method = client.put if path == "settings/ai" else client.post
    response = method(f"/api/tenants/{tenant.id}/{path}", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_business_only_policy_is_fail_closed_without_flushing(session, sandbox):
    from reality.services.tenant_policy import require_business_operation

    tenant, _ = sandbox
    pending = AISettings(tenant_id=tenant.id)
    session.add(pending)
    with pytest.raises(InvalidOperation, match="Playground"):
        require_business_operation(session, tenant.id, "unknown_future_egress")
    assert pending in session.new


def test_cli_cannot_create_items_in_sandbox(session, sandbox, monkeypatch):
    from sqlalchemy.orm import sessionmaker
    from typer.testing import CliRunner

    from reality.cli import app as cli
    from reality.db.core import Item

    tenant, _ = sandbox
    monkeypatch.setattr(
        cli, "Session", sessionmaker(session.bind, expire_on_commit=False)
    )
    monkeypatch.setattr(cli, "init_db", lambda: None)
    result = CliRunner().invoke(
        cli.app, ["item", "create", "TEST", "Test item", "--tenant", tenant.id]
    )
    assert result.exit_code != 0
    assert "Playground" in result.output or "Playground" in str(result.exception), (
        result.output
    )
    assert (
        session.scalar(
            select(func.count()).select_from(Item).where(Item.tenant_id == tenant.id)
        )
        == 0
    )


def test_mcp_dispatch_cannot_propose_sandbox_writes(session, sandbox):
    from reality.db.core import ChangeProposal
    from reality.mcp.catalog import dispatch_tool

    tenant, _ = sandbox
    with pytest.raises(InvalidOperation, match="Playground"):
        dispatch_tool(
            session,
            tenant.id,
            "item_create_propose",
            {"sku": "TEST", "name": "Test item"},
        )
    assert (
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(ChangeProposal.tenant_id == tenant.id)
        )
        == 0
    )


@pytest.mark.parametrize(
    "operation",
    [
        "capture_gap",
        "add_gap_entry",
        "recommend_gap",
        "decide_gap",
        "prepare_implementation",
        "activate_rule",
        "disable_rule",
        "replay_rule",
        "evaluate_active_rules",
    ],
)
def test_rule_workflow_mutations_cannot_bypass_policy(session, sandbox, operation):
    from reality.services import reality_gaps

    tenant, _ = sandbox
    function = getattr(reality_gaps, operation)
    arguments = {"session": session, "tenant_id": tenant.id}
    for name, parameter in inspect.signature(function).parameters.items():
        if name not in arguments and parameter.default is inspect.Parameter.empty:
            arguments[name] = None
    with pytest.raises(InvalidOperation, match="Playground"):
        function(**arguments)


def test_sandbox_upload_is_denied_before_touching_filesystem(
    session, sandbox, monkeypatch
):
    from reality.services import artifacts

    tenant, _ = sandbox
    root = Mock(side_effect=AssertionError("No upload storage may be accessed"))
    monkeypatch.setattr(artifacts, "artifact_root", root)
    with pytest.raises(InvalidOperation, match="Playground"):
        artifacts.stage_artifact(
            session, tenant.id, Mock(), filename="example.csv", content_type="text/csv"
        )
    root.assert_not_called()
