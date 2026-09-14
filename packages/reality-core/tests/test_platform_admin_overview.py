"""Platform administration overview: authorization, content and disclosure limits."""

from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    AppUser,
    BusinessEvent,
    CompanyInvitation,
    TenantMembership,
    UserSession,
    now,
    uid,
)
from reality.services import platform as platform_service
from reality.services.core import create_tenant
from reality.services.platform import platform_overview
from reality.web import api as api_module
from reality.web import app as web_module
from reality.web import auth as auth_module


def add_user(session, email: str, *, status: str = "active", admin: bool = False):
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash=auth_module.password_hasher.hash("a-long-account-password"),
        status=status,
        is_platform_admin=admin,
        email_verified_at=now() if status == "active" else None,
    )
    session.add(user)
    session.commit()
    return user


def signed_in_client(session, monkeypatch, email: str):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    browser = TestClient(web_module.app)
    login = browser.post(
        "/api/auth/login",
        json={"email": email, "password": "a-long-account-password"},
    )
    assert login.status_code == 200
    return browser


def test_overview_is_refused_without_platform_administration(session, monkeypatch):
    add_user(session, "member@example.com")
    browser = signed_in_client(session, monkeypatch, "member@example.com")
    try:
        refused = browser.get("/api/admin/overview")
        assert refused.status_code == 403
    finally:
        browser.close()


def test_overview_reports_people_companies_and_operations(session, monkeypatch):
    admin = add_user(session, "owner@example.com", admin=True)
    member = add_user(session, "operator@example.com")
    add_user(session, "waiting@example.com", status="pending_approval")
    tenant = create_tenant(session, "Acme Bikes GmbH")
    session.add_all(
        [
            TenantMembership(
                id=uid("mem"), tenant_id=tenant.id, user_id=member.id, role="owner"
            ),
            CompanyInvitation(
                id=uid("inv"),
                tenant_id=tenant.id,
                normalized_email="invited@example.com",
                status="pending",
                expires_at=now() + timedelta(days=7),
                invited_by_user_id=member.id,
            ),
            BusinessEvent(
                id=uid("evt"),
                tenant_id=tenant.id,
                sequence=1,
                event_type="commitment.recorded",
                subject_type="commitment",
                subject_id="cmt_example",
            ),
            UserSession(
                id=uid("ses"),
                user_id=member.id,
                token_hash=auth_module.digest("an-active-session-token"),
                expires_at=now() + timedelta(days=1),
            ),
        ]
    )
    auth_module.audit(session, "access.approved", member.id, admin.id)
    session.commit()

    overview = platform_overview(session)

    people = overview["people"]
    assert people["total"] == 3
    assert people["by_status"]["active"] == 2
    assert people["by_status"]["pending_approval"] == 1
    listed = {row["email"]: row for row in people["users"]}
    assert listed["operator@example.com"]["active_sessions"] == 1
    assert listed["operator@example.com"]["companies"] == [
        {"id": tenant.id, "name": "Acme Bikes GmbH", "role": "owner"}
    ]
    assert listed["owner@example.com"]["is_platform_admin"] is True

    companies = overview["companies"]
    assert companies["total"] == 1
    assert companies["archived"] == 0
    company = companies["rows"][0]
    assert company["name"] == "Acme Bikes GmbH"
    assert company["owners"] == 1
    assert company["members"] == 0
    assert company["open_invitations"] == 1
    assert company["business_events"] == 1
    assert company["last_event_at"]

    assert overview["operations"]["projections_failed"] == 0
    assert overview["operations"]["active_agent_tokens"] == 0
    assert overview["security"][0]["event_type"] == "access.approved"
    assert overview["security"][0]["actor"] == "owner@example.com"
    assert overview["security"][0]["subject"] == "operator@example.com"


def test_overview_reports_secret_presence_without_disclosing_values(
    session, monkeypatch
):
    monkeypatch.setenv("REALITY_MASTER_KEY", "a-real-fernet-key-value")
    monkeypatch.setenv("RESEND_API_KEY", "re_a_real_provider_secret")
    monkeypatch.setenv("REALITY_EMAIL_FROM", "Reality <reality@example.com>")
    monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", "25")

    deployment = platform_overview(session)["deployment"]

    assert deployment["master_key_configured"] is True
    assert deployment["email_credential_configured"] is True
    assert deployment["email_sender_configured"] is True
    assert deployment["automatic_access_limit"] == 25
    serialized = repr(deployment)
    assert "a-real-fernet-key-value" not in serialized
    assert "re_a_real_provider_secret" not in serialized


def test_overview_reports_the_running_version_and_commit(session, monkeypatch):
    monkeypatch.setenv("REALITY_VERSION", "0.1.0")
    monkeypatch.setenv("REALITY_COMMIT", "a204c14")

    deployment = platform_overview(session)["deployment"]

    assert deployment["version"] == "0.1.0"
    assert deployment["commit"] == "a204c14"


def test_overview_version_defaults_to_dev_outside_a_published_image(
    session, monkeypatch
):
    monkeypatch.delenv("REALITY_VERSION", raising=False)
    monkeypatch.delenv("REALITY_COMMIT", raising=False)

    deployment = platform_overview(session)["deployment"]

    assert deployment["version"] == "dev"
    assert deployment["commit"] == ""


def test_overview_flags_a_database_behind_the_shipped_migration_head(session):
    deployment = platform_overview(session)["deployment"]

    # The suite builds the schema from ORM metadata, so no revision is stamped.
    assert deployment["database_revision"] is None
    assert deployment["expected_revision"]
    assert deployment["migrations_current"] is False


def test_packaged_migration_layout_resolves_the_same_head(tmp_path, monkeypatch):
    source_versions = (
        Path(platform_service.__file__).resolve().parents[3] / "migrations" / "versions"
    )
    packaged_versions = (
        tmp_path / "site-packages" / "reality" / "migrations" / "versions"
    )
    packaged_versions.mkdir(parents=True)
    for script in source_versions.glob("*.py"):
        (packaged_versions / script.name).write_bytes(script.read_bytes())

    source_head = platform_service._migration_head(source_versions)
    monkeypatch.setattr(platform_service, "MIGRATION_DIRECTORIES", (packaged_versions,))

    assert source_head
    assert platform_service._expected_revision() == source_head


def test_migration_head_recognizes_a_merge_without_executing_scripts(tmp_path):
    (tmp_path / "one.py").write_text('revision = "one"\ndown_revision = None\n')
    (tmp_path / "two.py").write_text('revision = "two"\ndown_revision = None\n')
    (tmp_path / "merge.py").write_text(
        'revision = "joined"\ndown_revision = (\n "one",\n "two",\n)\n'
        'raise RuntimeError("Migration files must not execute during inspection")\n'
    )
    assert platform_service._migration_head(tmp_path) == "joined"


def test_missing_or_ambiguous_migration_heads_remain_unknown(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setattr(platform_service, "MIGRATION_DIRECTORIES", (missing,))
    assert platform_service._expected_revision() is None

    ambiguous = tmp_path / "ambiguous"
    ambiguous.mkdir()
    (ambiguous / "one.py").write_text(
        'revision = "one"\ndown_revision = None\n', encoding="utf-8"
    )
    (ambiguous / "two.py").write_text(
        'revision = "two"\ndown_revision = None\n', encoding="utf-8"
    )
    monkeypatch.setattr(platform_service, "MIGRATION_DIRECTORIES", (ambiguous,))
    assert platform_service._expected_revision() is None


def test_overview_is_served_to_the_environment_configured_administrator(
    session, monkeypatch
):
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_EMAIL", "platform@example.com")
    monkeypatch.setenv("REALITY_PLATFORM_ADMIN_PASSWORD", "a-long-account-password")
    auth_module.bootstrap_platform_admin(session)
    session.commit()

    browser = signed_in_client(session, monkeypatch, "platform@example.com")
    try:
        served = browser.get("/api/admin/overview")
        assert served.status_code == 200
        payload = served.json()
        assert set(payload) == {
            "generated_at",
            "deployment",
            "people",
            "companies",
            "operations",
            "security",
        }
        assert payload["people"]["users"][0]["email"] == "platform@example.com"
    finally:
        browser.close()
