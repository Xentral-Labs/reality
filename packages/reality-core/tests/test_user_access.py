from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    AccessAdmissionCounter,
    AppUser,
    InvitationDelivery,
    TenantMembership,
    UserSession,
    now,
    uid,
)
from reality.services.core import create_tenant
from reality.services.memberships import Principal, create_invitation
from reality.services.notifications import issue_delivery_token
from reality.web import api as api_module
from reality.web import app as web_module
from reality.web import auth as auth_module


def test_current_user_resolution_does_not_write_session_activity(session):
    clear_token = "read-only-session-token"
    user = AppUser(
        id="usr_read_only",
        email="reader@example.com",
        password_hash="unused",
        status="active",
    )
    auth_session = UserSession(
        id="ses_read_only",
        user_id=user.id,
        token_hash=auth_module.digest(clear_token),
        expires_at=now() + timedelta(days=1),
    )
    session.add_all([user, auth_session])
    session.commit()
    session.expunge(user)
    statements: list[str] = []

    def record_statement(_conn, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", record_statement)
    try:
        resolved = auth_module.user_from_request(
            SimpleNamespace(cookies={auth_module.COOKIE_NAME: clear_token}),
            session,
        )
    finally:
        event.remove(session.bind, "before_cursor_execute", record_statement)

    assert resolved.id == user.id
    assert not any(
        statement.lstrip().upper().startswith("UPDATE USER_SESSION")
        for statement in statements
    )


def test_public_signup_can_be_disabled_without_disabling_prepared_login(
    session, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setenv("REALITY_PUBLIC_SIGNUP_ENABLED", "false")
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_EMAIL", "owner@example.com")
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_PASSWORD", "a-very-long-admin-password")
    auth_module.bootstrap_platform_admin(session)

    browser = TestClient(web_module.app)
    try:
        signup = browser.post(
            "/api/auth/signup",
            json={
                "email": "unexpected@example.com",
                "password": "a-long-operator-password",
                "accepted_terms": True,
            },
        )
        assert signup.status_code == 403
        assert signup.json() == {"detail": "Public signup is disabled."}
        assert (
            session.query(AppUser)
            .filter(AppUser.email == "unexpected@example.com")
            .one_or_none()
            is None
        )

        login = browser.post(
            "/api/auth/login",
            json={
                "email": "owner@example.com",
                "password": "a-very-long-admin-password",
            },
        )
        assert login.status_code == 200
    finally:
        browser.close()


def test_invitation_signup_bypasses_public_signup_but_requires_explicit_acceptance(
    session, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setenv("REALITY_PUBLIC_SIGNUP_ENABLED", "false")
    monkeypatch.setenv("REALITY_AUTH_EXPOSE_CODES", "true")
    tenant = create_tenant(session, "Invitation Company")
    owner = AppUser(
        id=uid("usr"),
        email="invitation-owner@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(owner)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=owner.id,
            role="owner",
            status="active",
        )
    )
    session.flush()
    invitation = create_invitation(
        session,
        tenant.id,
        Principal(owner.id),
        "invited-operator@example.com",
    )
    delivery = (
        session.query(InvitationDelivery)
        .filter(InvitationDelivery.invitation_id == invitation.id)
        .one()
    )
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)
    session.commit()

    browser = TestClient(web_module.app)
    try:
        inspected = browser.post("/api/auth/invitations/inspect", json={"token": token})
        assert inspected.status_code == 200
        assert inspected.json()["company_name"] == "Invitation Company"
        signup = browser.post(
            "/api/auth/invitations/signup",
            json={
                "token": token,
                "email": "invited-operator@example.com",
                "password": "a-long-operator-password",
                "accepted_terms": True,
            },
        )
        assert signup.status_code == 201
        verified = browser.post(
            "/api/auth/verify-email",
            json={
                "email": "invited-operator@example.com",
                "code": signup.json()["verification_code"],
                "invitation_token": token,
            },
        )
        assert verified.status_code == 200
        assert verified.json()["status"] == "pending_approval"
        invited_user = (
            session.query(AppUser)
            .filter(AppUser.email == "invited-operator@example.com")
            .one()
        )
        assert (
            session.query(TenantMembership)
            .filter(TenantMembership.user_id == invited_user.id)
            .one_or_none()
            is None
        )

        accepted = browser.post("/api/auth/invitations/accept", json={"token": token})
        assert accepted.status_code == 200
        assert accepted.json()["company"]["id"] == tenant.id
        assert (
            session.query(TenantMembership)
            .filter(TenantMembership.user_id == invited_user.id)
            .one()
            .status
            == "active"
        )
    finally:
        browser.close()


def test_signup_approval_and_company_membership(session, monkeypatch):
    access_notifications: list[str] = []
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_EXPOSE_CODES", "true")
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", "0")
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_EMAIL", "owner@example.com")
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_PASSWORD", "a-very-long-admin-password")
    monkeypatch.setattr(
        auth_module,
        "send_access_request_notification",
        access_notifications.append,
    )
    auth_module.bootstrap_platform_admin(session)

    browser = TestClient(web_module.app)
    try:
        signup = browser.post(
            "/api/auth/signup",
            json={
                "email": "operator@example.com",
                "password": "a-long-operator-password",
                "accepted_terms": True,
            },
        )
        assert signup.status_code == 201
        verified = browser.post(
            "/api/auth/verify-email",
            json={
                "email": "operator@example.com",
                "code": signup.json()["verification_code"],
            },
        )
        assert verified.json()["status"] == "pending_approval"
        assert access_notifications == ["operator@example.com"]
        application_id = verified.json()["application"]["id"]

        assert (
            browser.post(
                "/api/auth/login",
                json={
                    "email": "owner@example.com",
                    "password": "a-very-long-admin-password",
                },
            ).status_code
            == 200
        )
        assert (
            browser.post(
                f"/api/admin/access-applications/{application_id}/review",
                json={"decision": "approve", "note": "Good fit"},
            ).status_code
            == 200
        )

        assert (
            browser.post(
                "/api/auth/login",
                json={
                    "email": "operator@example.com",
                    "password": "a-long-operator-password",
                },
            ).status_code
            == 200
        )

        profile = browser.put(
            "/api/auth/profile",
            json={
                "display_name": "Operations Lead",
                "language": "de",
                "locale": "de-DE",
                "timezone": "Europe/Berlin",
            },
        )
        assert profile.status_code == 200
        assert profile.json()["language"] == "de"
        assert profile.json()["locale"] == "de-DE"
        assert profile.json()["timezone"] == "Europe/Berlin"

        company = browser.post("/api/v1/companies", json={"name": "Operator GmbH"})
        assert company.status_code == 201
        bootstrap = browser.get("/api/v1/bootstrap").json()
        assert bootstrap["tenants"] == [
            {"id": company.json()["id"], "name": "Operator GmbH", "role": "owner"}
        ]

        demo_company = browser.post(
            "/api/v1/companies",
            json={"name": "Operator Demo", "guided_demo": True},
        )
        assert demo_company.status_code == 201
        demo_parties = browser.get(f"/api/tenants/{demo_company.json()['id']}/parties")
        assert demo_parties.status_code == 200
        assert len(demo_parties.json()) == 3

        foreign = create_tenant(session, "Foreign Demo")
        hidden = browser.get(f"/api/tenants/{foreign.id}/parties")
        assert hidden.status_code == 404
        assert hidden.json()["detail"] == "Company not found."
    finally:
        browser.close()


def test_first_verified_accounts_are_automatically_admitted(session, monkeypatch):
    access_notifications: list[str] = []
    approval_notifications: list[tuple[str, bool]] = []
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_EXPOSE_CODES", "true")
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", "2")
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_EMAIL", "owner@example.com")
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_PASSWORD", "a-very-long-admin-password")
    monkeypatch.setattr(
        auth_module,
        "send_access_request_notification",
        access_notifications.append,
    )
    monkeypatch.setattr(
        auth_module,
        "send_access_decision_email",
        lambda email, approved: approval_notifications.append((email, approved)),
    )
    session.add(AccessAdmissionCounter(id="automatic", used_slots=0))
    auth_module.bootstrap_platform_admin(session)
    session.commit()

    browser = TestClient(web_module.app)
    try:
        statuses: list[str] = []
        for index in range(3):
            email = f"operator-{index}@example.com"
            signup = browser.post(
                "/api/auth/signup",
                json={
                    "email": email,
                    "password": "a-long-operator-password",
                    "accepted_terms": True,
                },
            )
            verified = browser.post(
                "/api/auth/verify-email",
                json={"email": email, "code": signup.json()["verification_code"]},
            )
            assert verified.status_code == 200
            statuses.append(verified.json()["status"])

        assert statuses == ["active", "active", "pending_approval"]
        assert approval_notifications == [
            ("operator-0@example.com", True),
            ("operator-1@example.com", True),
        ]
        assert access_notifications == ["operator-2@example.com"]

        browser.post("/api/auth/logout")
        assert (
            browser.post(
                "/api/auth/login",
                json={
                    "email": "owner@example.com",
                    "password": "a-very-long-admin-password",
                },
            ).status_code
            == 200
        )
        assert browser.get("/api/admin/access-capacity").json() == {
            "used": 2,
            "limit": 2,
        }
    finally:
        browser.close()


def test_bootstrap_roles_identical_company_names_removed_access_and_no_company(
    session, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    owner_company = create_tenant(session, "Same Company")
    member_company = create_tenant(session, "Same Company")
    hidden_company = create_tenant(session, "Same Company")
    user = AppUser(
        id=uid("usr"),
        email="multi-company@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    clear_token = "multi-company-session"
    session.add(user)
    session.flush()
    memberships = [
        TenantMembership(
            id=uid("tmb"),
            tenant_id=owner_company.id,
            user_id=user.id,
            role="owner",
            status="active",
        ),
        TenantMembership(
            id=uid("tmb"),
            tenant_id=member_company.id,
            user_id=user.id,
            role="member",
            status="active",
        ),
    ]
    bounded_users = [
        AppUser(
            id=uid("usr"),
            email=f"bounded-member-{index:03d}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        for index in range(500)
    ]
    session.add_all(bounded_users)
    session.flush()
    bounded_memberships = [
        TenantMembership(
            id=uid("tmb"),
            tenant_id=owner_company.id,
            user_id=bounded_user.id,
            role="member",
            status="active",
        )
        for bounded_user in bounded_users
    ]
    session.add_all(
        [
            *memberships,
            *bounded_memberships,
            UserSession(
                id=uid("ses"),
                user_id=user.id,
                token_hash=auth_module.digest(clear_token),
                expires_at=now() + timedelta(days=1),
            ),
        ]
    )
    session.commit()

    browser = TestClient(web_module.app)
    browser.cookies.set(auth_module.COOKIE_NAME, clear_token)
    try:
        bootstrap = browser.get("/api/v1/bootstrap")
        assert bootstrap.status_code == 200
        assert {
            (row["id"], row["name"], row["role"]) for row in bootstrap.json()["tenants"]
        } == {
            (owner_company.id, "Same Company", "owner"),
            (member_company.id, "Same Company", "member"),
        }
        owner_members = browser.get(f"/api/tenants/{owner_company.id}/settings/members")
        assert owner_members.status_code == 200
        assert len(owner_members.json()["members"]) == 500
        assert (
            browser.get(
                f"/api/tenants/{member_company.id}/settings/members"
            ).status_code
            == 400
        )
        hidden = browser.get(f"/api/tenants/{hidden_company.id}/settings/members")
        assert hidden.status_code == 404
        assert hidden.json() == {"detail": "Company not found."}

        for membership in memberships:
            membership.status = "removed"
        session.commit()
        no_company = browser.get("/api/v1/bootstrap")
        assert no_company.status_code == 200
        assert no_company.json() == {"tenants": []}
    finally:
        browser.close()


def test_member_removal_preserves_global_session_and_other_company_access(
    session, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    removed_company = create_tenant(session, "Removed Access Company")
    retained_company = create_tenant(session, "Retained Access Company")
    owner = AppUser(
        id=uid("usr"),
        email="removal-owner@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    member = AppUser(
        id=uid("usr"),
        email="removed-member@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    owner_token = "removal-owner-session"
    member_token = "removal-member-session"
    session.add_all([owner, member])
    session.flush()
    removed_membership = TenantMembership(
        id=uid("tmb"),
        tenant_id=removed_company.id,
        user_id=member.id,
        role="member",
        status="active",
    )
    session.add_all(
        [
            TenantMembership(
                id=uid("tmb"),
                tenant_id=removed_company.id,
                user_id=owner.id,
                role="owner",
                status="active",
            ),
            removed_membership,
            TenantMembership(
                id=uid("tmb"),
                tenant_id=retained_company.id,
                user_id=member.id,
                role="member",
                status="active",
            ),
            UserSession(
                id=uid("ses"),
                user_id=owner.id,
                token_hash=auth_module.digest(owner_token),
                expires_at=now() + timedelta(days=1),
            ),
            UserSession(
                id=uid("ses"),
                user_id=member.id,
                token_hash=auth_module.digest(member_token),
                expires_at=now() + timedelta(days=1),
            ),
        ]
    )
    session.commit()

    browser = TestClient(web_module.app)
    try:
        browser.cookies.set(auth_module.COOKIE_NAME, owner_token)
        removed = browser.post(
            f"/api/tenants/{removed_company.id}/settings/members/{removed_membership.id}/remove"
        )
        assert removed.status_code == 204

        browser.cookies.set(auth_module.COOKIE_NAME, member_token)
        denied = browser.get(f"/api/tenants/{removed_company.id}/parties")
        assert denied.status_code == 404
        bootstrap = browser.get("/api/v1/bootstrap")
        assert bootstrap.status_code == 200
        assert bootstrap.json()["tenants"] == [
            {
                "id": retained_company.id,
                "name": retained_company.name,
                "role": "member",
            }
        ]
        assert (
            session.query(UserSession).filter_by(user_id=member.id).one().revoked_at
            is None
        )
    finally:
        browser.close()


@pytest.mark.parametrize("configured", [None, "", "  "])
def test_default_admission_verification_and_replay(session, monkeypatch, configured):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    for module in (web_module, auth_module, api_module):
        monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_EXPOSE_CODES", "true")
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    if configured is None:
        monkeypatch.delenv("REALITY_AUTO_APPROVE_LIMIT", raising=False)
    else:
        monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", configured)
    notifications = []
    monkeypatch.setattr(
        auth_module,
        "send_access_decision_email",
        lambda *args: notifications.append(args),
    )
    monkeypatch.setattr(
        auth_module,
        "send_access_request_notification",
        lambda *_: pytest.fail("Open signup requested manual approval"),
    )
    session.add(AccessAdmissionCounter(id="automatic", used_slots=1000))
    session.commit()
    with TestClient(web_module.app) as browser:
        for index in range(2):
            email = f"open-{index}@example.com"
            signup = browser.post(
                "/api/auth/signup",
                json={
                    "email": email,
                    "password": "a-long-operator-password",
                    "accepted_terms": True,
                },
            )
            assert signup.status_code == 201
            challenge = {"email": email, "code": signup.json()["verification_code"]}
            verified = browser.post("/api/auth/verify-email", json=challenge)
            assert verified.status_code == 200
            assert verified.json()["status"] == "active"
            assert verified.json()["application"]["status"] == "approved"
            assert (
                browser.post("/api/auth/verify-email", json=challenge).status_code
                == 400
            )
            browser.post("/api/auth/logout")
    session.expire_all()
    assert session.get(AccessAdmissionCounter, "automatic").used_slots == 1002
    assert len(notifications) == 2


def signup_browser(session, monkeypatch) -> TestClient:
    """A client whose signups create accounts in the test transaction."""
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setenv("REALITY_PUBLIC_SIGNUP_ENABLED", "true")
    return TestClient(web_module.app)


def registered(session, email: str) -> AppUser:
    session.expire_all()
    return session.query(AppUser).filter(AppUser.email == email).one()


def test_signup_adopts_the_presentation_defaults_the_browser_states(
    session, monkeypatch
):
    browser = signup_browser(session, monkeypatch)
    try:
        for language, locale, zone in (
            ("de", "de-DE", "Europe/Berlin"),
            ("nl", "nl-NL", "Europe/Amsterdam"),
            ("es", "es-ES", "America/Bogota"),
            ("en", "en-GB", "Australia/Sydney"),
        ):
            email = f"{language}-registrant@example.com"
            created = browser.post(
                "/api/auth/signup",
                json={
                    "email": email,
                    "password": "a-long-operator-password",
                    "accepted_terms": True,
                    "language": language,
                    "timezone": zone,
                },
            )
            assert created.status_code == 201, created.text
            account = registered(session, email)
            assert (account.language, account.locale, account.timezone) == (
                language,
                locale,
                zone,
            )
    finally:
        browser.close()


def test_signup_keeps_the_established_defaults_when_no_hint_is_usable(
    session, monkeypatch
):
    browser = signup_browser(session, monkeypatch)
    unusable = (
        {},
        {"language": None, "timezone": None},
        {"language": "", "timezone": ""},
        {"language": "fr", "timezone": "Mars/Olympus_Mons"},
        {"language": "de-DE", "timezone": "../../etc/passwd"},
        {"language": "EN", "timezone": "UTC+2"},
    )
    try:
        for index, hint in enumerate(unusable):
            email = f"fallback-{index}@example.com"
            created = browser.post(
                "/api/auth/signup",
                json={
                    "email": email,
                    "password": "a-long-operator-password",
                    "accepted_terms": True,
                    **hint,
                },
            )
            assert created.status_code == 201, f"{hint}: {created.text}"
            account = registered(session, email)
            assert (account.language, account.locale, account.timezone) == (
                "en",
                "en-GB",
                "UTC",
            ), hint
    finally:
        browser.close()


def test_signup_pairs_the_locale_itself_and_never_takes_one_from_the_client(
    session, monkeypatch
):
    browser = signup_browser(session, monkeypatch)
    try:
        created = browser.post(
            "/api/auth/signup",
            json={
                "email": "locale-claim@example.com",
                "password": "a-long-operator-password",
                "accepted_terms": True,
                "language": "de",
                "locale": "en-GB",
                "timezone": "Europe/Berlin",
            },
        )
        assert created.status_code == 201, created.text
        account = registered(session, "locale-claim@example.com")
        assert (account.language, account.locale) == ("de", "de-DE")
    finally:
        browser.close()


def test_signup_rejects_an_oversized_hint_before_an_account_exists(
    session, monkeypatch
):
    browser = signup_browser(session, monkeypatch)
    try:
        refused = browser.post(
            "/api/auth/signup",
            json={
                "email": "oversized@example.com",
                "password": "a-long-operator-password",
                "accepted_terms": True,
                "timezone": "Europe/" + "B" * 500,
            },
        )
        assert refused.status_code == 422
        session.expire_all()
        assert (
            session.query(AppUser)
            .filter(AppUser.email == "oversized@example.com")
            .one_or_none()
            is None
        )
    finally:
        browser.close()


def test_invitation_signup_adopts_the_presentation_defaults_too(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setenv("REALITY_PUBLIC_SIGNUP_ENABLED", "false")
    tenant = create_tenant(session, "Invitation Preferences Company")
    owner = AppUser(
        id=uid("usr"),
        email="preferences-owner@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(owner)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=owner.id,
            role="owner",
            status="active",
        )
    )
    session.flush()
    invitation = create_invitation(
        session,
        tenant.id,
        Principal(owner.id),
        "invited-registrant@example.com",
    )
    delivery = (
        session.query(InvitationDelivery)
        .filter(InvitationDelivery.invitation_id == invitation.id)
        .one()
    )
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)
    session.commit()

    browser = TestClient(web_module.app)
    try:
        created = browser.post(
            "/api/auth/invitations/signup",
            json={
                "token": token,
                "email": "invited-registrant@example.com",
                "password": "a-long-operator-password",
                "accepted_terms": True,
                "language": "de",
                "timezone": "Europe/Berlin",
            },
        )
        assert created.status_code == 201, created.text
        account = registered(session, "invited-registrant@example.com")
        assert (account.language, account.locale, account.timezone) == (
            "de",
            "de-DE",
            "Europe/Berlin",
        )
    finally:
        browser.close()


def test_signup_and_profile_decide_preferences_from_one_vocabulary():
    for language, locale in auth_module.SUPPORTED_LOCALES.items():
        # What signup accepts as a default is exactly what a profile update accepts.
        assert auth_module.presentation_defaults(language, "Europe/Berlin") == (
            language,
            locale,
            "Europe/Berlin",
        )
        auth_module.validate_preferences(language, locale, "Europe/Berlin")
    with pytest.raises(HTTPException):
        auth_module.validate_preferences("fr", "fr-FR", "Europe/Paris")
    # A malformed zone is an unknown zone on both paths, never an unhandled error.
    for malformed in ("../../etc/passwd", "Mars/Olympus_Mons", ""):
        with pytest.raises(HTTPException) as refused:
            auth_module.validate_preferences("en", "en-GB", malformed)
        assert refused.value.status_code == 422
    assert auth_module.presentation_defaults("fr", "Europe/Paris") == (
        "en",
        "en-GB",
        "Europe/Paris",
    )
