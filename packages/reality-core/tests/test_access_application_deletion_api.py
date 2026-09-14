"""Spec 192 FR-011: the deletion preview and delete routes and their authorization."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    AccessApplication,
    AppUser,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.web import api as api_module
from reality.web import app as web_module
from reality.web import auth as auth_module

PASSWORD = "a-long-account-password"


def add_user(session, email, *, admin=False):
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash=auth_module.password_hasher.hash(PASSWORD),
        status="active",
        is_platform_admin=admin,
        email_verified_at=now(),
    )
    session.add(user)
    session.commit()
    return user


def add_application(session, user):
    application = AccessApplication(
        id=uid("app"), user_id=user.id, status="approved", requested_at=now()
    )
    session.add(application)
    session.commit()
    return application


def add_company(session, name, owner):
    tenant = Tenant(id=uid("ten"), name=name, purpose="playground")
    session.add(tenant)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("mem"),
            tenant_id=tenant.id,
            user_id=owner.id,
            role="owner",
            status="active",
        )
    )
    session.commit()
    return tenant


def signed_in_client(session, monkeypatch, email):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    browser = TestClient(web_module.app)
    login = browser.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    return browser


def rows(session, model, row_id):
    return (
        session.scalar(
            select(func.count()).select_from(model).where(model.id == row_id)
        )
        or 0
    )


def test_preview_and_delete_remove_the_applicant_and_their_company(
    session, monkeypatch
):
    add_user(session, "owner@reality.local", admin=True)
    applicant = add_user(session, "free5@example.com")
    application = add_application(session, applicant)
    company = add_company(session, "Sandbox", applicant)
    applicant_id, application_id, company_id = (
        applicant.id,
        application.id,
        company.id,
    )
    browser = signed_in_client(session, monkeypatch, "owner@reality.local")
    try:
        preview = browser.get(
            f"/api/admin/access-applications/{application_id}/deletion-preview"
        )
        assert preview.status_code == 200
        assert preview.json()["email"] == "free5@example.com"
        assert [entry["name"] for entry in preview.json()["deleted_companies"]] == [
            "Sandbox"
        ]

        removed = browser.post(
            f"/api/admin/access-applications/{application_id}/delete",
            json={
                "confirmation_email": "free5@example.com",
                "confirmation_word": "DELETE",
            },
        )
        assert removed.status_code == 200
        assert removed.json()["record_count"] >= 1
    finally:
        web_module.app.dependency_overrides.clear()

    session.expire_all()
    assert rows(session, AppUser, applicant_id) == 0
    assert rows(session, AccessApplication, application_id) == 0
    assert rows(session, Tenant, company_id) == 0


def test_delete_refuses_a_wrong_confirmation_without_removing_anything(
    session, monkeypatch
):
    add_user(session, "owner@reality.local", admin=True)
    applicant = add_user(session, "intact@example.com")
    application = add_application(session, applicant)
    applicant_id, application_id = applicant.id, application.id
    browser = signed_in_client(session, monkeypatch, "owner@reality.local")
    try:
        refused = browser.post(
            f"/api/admin/access-applications/{application_id}/delete",
            json={
                "confirmation_email": "intact@example.com",
                "confirmation_word": "delete",
            },
        )
        assert refused.status_code == 400
        assert "match exactly" in refused.json()["detail"]
    finally:
        web_module.app.dependency_overrides.clear()

    session.expire_all()
    assert rows(session, AppUser, applicant_id) == 1


def test_deletion_routes_require_platform_administration(session, monkeypatch):
    member = add_user(session, "member@example.com")
    application = add_application(session, member)
    browser = signed_in_client(session, monkeypatch, "member@example.com")
    try:
        assert (
            browser.get(
                f"/api/admin/access-applications/{application.id}/deletion-preview"
            ).status_code
            == 403
        )
        assert (
            browser.post(
                f"/api/admin/access-applications/{application.id}/delete",
                json={
                    "confirmation_email": "member@example.com",
                    "confirmation_word": "DELETE",
                },
            ).status_code
            == 403
        )
    finally:
        web_module.app.dependency_overrides.clear()


def test_unknown_application_is_not_found(session, monkeypatch):
    add_user(session, "owner@reality.local", admin=True)
    browser = signed_in_client(session, monkeypatch, "owner@reality.local")
    try:
        assert (
            browser.get(
                "/api/admin/access-applications/app_missing/deletion-preview"
            ).status_code
            == 404
        )
    finally:
        web_module.app.dependency_overrides.clear()
