"""Local ownership must never become a hosted email verification bypass."""

import uuid

import pytest
from reality.db.core import AccessApplication, AppUser, now
from reality.services import account_policy, company_setup, desktop_identity
from reality.services.core import InvalidOperation
from reality.services.tenant_policy import PlaygroundOperationDenied
from sqlalchemy import func, select


def local_owner(session):
    installation_id = str(uuid.uuid4())
    session.info["desktop_installation_id"] = installation_id
    user = desktop_identity.bootstrap_owner(session, installation_id)
    session.info["desktop_owner_id"] = user.id
    return user


def test_bootstrap_replays_without_verification_or_admission(session):
    owner = local_owner(session)
    again = desktop_identity.bootstrap_owner(
        session, session.info["desktop_installation_id"]
    )
    assert again.id == owner.id
    assert owner.authentication_method == "local_os"
    assert owner.email_verified_at is None
    assert owner.is_platform_admin is False
    assert session.scalar(select(func.count()).select_from(AccessApplication)) == 0


def test_untrusted_bootstrap_and_wrong_binding_fail_closed(session):
    with pytest.raises(InvalidOperation):
        desktop_identity.bootstrap_owner(session, str(uuid.uuid4()))
    owner = local_owner(session)
    session.info["desktop_owner_id"] = "different-owner"
    with pytest.raises(InvalidOperation):
        desktop_identity.bootstrap_owner(
            session, session.info["desktop_installation_id"]
        )
    assert not account_policy.account_eligible(session, owner)


def test_local_company_uses_shared_confirmation_and_replay(session):
    owner = local_owner(session)
    arguments = (
        session,
        owner.id,
        "first-company",
        "Local company",
        "business",
        "empty",
    )
    with pytest.raises(InvalidOperation):
        company_setup.create_company(*arguments)
    result = company_setup.create_company(*arguments, confirmed=True)
    assert result["status"] == "ready"
    assert (
        company_setup.create_company(*arguments, confirmed=True)["tenant_id"]
        == result["tenant_id"]
    )
    session.info.clear()
    with pytest.raises(PlaygroundOperationDenied):
        company_setup.options(session, owner.id)


@pytest.mark.parametrize("status", ["active", "pending_approval", "suspended"])
@pytest.mark.parametrize("method", ["email", "local_os"])
@pytest.mark.parametrize("bound", [False, True])
def test_python_sql_account_policy_agree(session, status, method, bound):
    owner = local_owner(session)
    owner.status = status
    owner.authentication_method = method
    owner.email_verified_at = now() if method == "email" else None
    if not bound:
        session.info.clear()
    session.flush()
    expected = account_policy.account_eligible(session, owner, allow_pending=True)
    selected = session.scalar(
        select(AppUser.id).where(
            AppUser.id == owner.id,
            account_policy.account_eligible_clause(session, allow_pending=True),
        )
    )
    assert bool(selected) is expected
    assert expected == (
        status in {"active", "pending_approval"}
        if method == "email"
        else bound and status == "active"
    )


def test_hosted_session_rejects_local_owner_even_with_valid_token(session):
    from datetime import timedelta

    from reality.db.core import UserSession, uid
    from reality.web import auth
    from starlette.requests import Request

    owner = local_owner(session)
    session.add(
        UserSession(
            id=uid("ses"),
            user_id=owner.id,
            token_hash=auth.digest("probe-token"),
            expires_at=now() + timedelta(hours=1),
        )
    )
    session.flush()
    request = Request(
        {"type": "http", "headers": [(b"cookie", b"reality_session=probe-token")]}
    )
    assert auth.user_from_request(request, session).id == owner.id
    session.info.clear()
    assert auth.user_from_request(request, session) is None


def test_local_owner_cannot_use_email_login_or_verification(session):
    from fastapi import HTTPException, Response
    from reality.web import auth

    owner = local_owner(session)
    # Bypass email syntax validation to exercise the service boundary directly.
    login = auth.LoginBody.model_construct(email=owner.email, password="irrelevant")
    verify = auth.VerifyBody.model_construct(email=owner.email, code="123456")
    with pytest.raises(HTTPException) as failure:
        auth.login(login, Response(), session)
    assert failure.value.status_code == 401
    with pytest.raises(HTTPException):
        auth.verify_email(verify, Response(), session)
    with pytest.raises(InvalidOperation):
        auth.issue_code(session, owner)


def test_session_issuance_and_revocation_share_owner_policy(session):
    from reality.services.account_sessions import issue_session, revoke_session
    from reality.web import auth
    from starlette.requests import Request

    owner = local_owner(session)
    token = issue_session(session, owner)
    session.flush()
    request = Request(
        {"type": "http", "headers": [(b"cookie", f"reality_session={token}".encode())]}
    )
    assert auth.user_from_request(request, session).id == owner.id
    revoke_session(session, token)
    session.flush()
    assert auth.user_from_request(request, session) is None
    session.info.clear()
    with pytest.raises(InvalidOperation):
        issue_session(session, owner)
