"""Spec 192: platform administration removes an applicant and everything only they hold."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from reality.db.core import (
    AccessApplication,
    AppUser,
    Base,
    EmailVerificationCode,
    PlaygroundRun,
    SecurityAuditEvent,
    Tenant,
    TenantMembership,
    UserSession,
    now,
    uid,
)
from reality.services.account_deletion import (
    account_deletion_preview,
    application_account_id,
    delete_account,
)
from reality.services.core import InvalidOperation, NotFound, create_party


def make_user(session, email, *, platform_admin=False):
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash="x",
        status="active",
        is_platform_admin=platform_admin,
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    return user


def make_application(session, user, status="approved"):
    application = AccessApplication(
        id=uid("app"), user_id=user.id, status=status, requested_at=now()
    )
    session.add(application)
    session.flush()
    return application


def make_company(session, name, owner, *, purpose="business", role="owner"):
    tenant = Tenant(id=uid("ten"), name=name, purpose=purpose)
    session.add(tenant)
    session.flush()
    join(session, tenant, owner, role=role)
    return tenant


def join(session, tenant, user, *, role="member", status="active"):
    session.add(
        TenantMembership(
            id=uid("mem"),
            tenant_id=tenant.id,
            user_id=user.id,
            role=role,
            status=status,
        )
    )
    session.flush()


def make_sandbox(session, name, owner):
    tenant = make_company(session, name, owner, purpose="playground")
    session.add(
        PlaygroundRun(
            id=uid("run"),
            tenant_id=tenant.id,
            owner_user_id=owner.id,
            preset_key="starter",
            preset_version=1,
            lesson_key="intro",
            lesson_version=1,
            client_request_key=uid("req"),
            status="initializing",
        )
    )
    session.flush()
    return tenant


def exists(session, model, row_id):
    """Ask the database, not the identity map: the sweep deletes through Tables."""
    return (
        session.scalar(
            select(func.count()).select_from(model).where(model.id == row_id)
        )
        or 0
    ) > 0


def user_references(session, user_id):
    """Count every row still pointing at this account, straight from the schema."""
    total = 0
    for table in Base.metadata.sorted_tables:
        if table.name == AppUser.__tablename__:
            continue
        for column in table.columns:
            if any(
                foreign_key.column.table.name == AppUser.__tablename__
                for foreign_key in column.foreign_keys
            ):
                total += (
                    session.scalar(
                        select(func.count()).select_from(table).where(column == user_id)
                    )
                    or 0
                )
    return total


@pytest.fixture
def admin(session):
    return make_user(session, "owner@reality.local", platform_admin=True)


def test_preview_names_owned_and_shared_companies(session, admin):
    applicant = make_user(session, "free5@example.com")
    make_application(session, applicant)
    owned = make_company(session, "Own Company", applicant)
    create_party(session, owned.id, "Customer", "customer")
    shared = make_company(session, "Shared Company", applicant)
    join(session, shared, admin, role="owner")
    make_sandbox(session, "Sandbox", applicant)

    preview = account_deletion_preview(session, applicant.id)

    assert preview["email"] == "free5@example.com"
    assert {entry["name"] for entry in preview["deleted_companies"]} == {
        "Own Company",
        "Sandbox",
    }
    assert [entry["name"] for entry in preview["kept_companies"]] == ["Shared Company"]
    assert preview["sandbox_count"] == 1
    # The membership row alone already makes a company non-empty.
    assert preview["record_count"] >= 3


def test_deletes_account_with_its_sole_owned_companies(session, admin):
    applicant = make_user(session, "free4@example.com")
    application = make_application(session, applicant)
    company = make_company(session, "Test GmbH", applicant)
    create_party(session, company.id, "Customer", "customer")
    sandbox = make_sandbox(session, "Practice", applicant)
    session.add(
        UserSession(
            id=uid("ses"),
            user_id=applicant.id,
            token_hash="hash",
            expires_at=now(),
        )
    )
    session.add(
        EmailVerificationCode(
            id=uid("evc"),
            user_id=applicant.id,
            code_hash="hash",
            expires_at=now(),
        )
    )
    session.flush()
    # Read the identifiers before the sweep: afterwards these instances are
    # expired and touching an attribute would refresh a row that is gone.
    applicant_id, application_id = applicant.id, application.id
    company_id, sandbox_id = company.id, sandbox.id

    summary = delete_account(
        session,
        applicant_id,
        confirmation_email="free4@example.com",
        confirmation_word="DELETE",
        actor_user_id=admin.id,
    )

    assert len(summary["deleted_companies"]) == 2
    assert not exists(session, AppUser, applicant_id)
    assert not exists(session, AccessApplication, application_id)
    # A practice company is a playground tenant; the business policy refuses to
    # touch one, which is exactly why platform administration owns this path.
    assert not exists(session, Tenant, company_id)
    assert not exists(session, Tenant, sandbox_id)
    assert user_references(session, applicant_id) == 0


def test_deletion_is_accepted_for_a_differently_cased_address(session, admin):
    applicant = make_user(session, "free3@example.com")
    make_application(session, applicant)
    applicant_id = applicant.id

    delete_account(
        session,
        applicant_id,
        confirmation_email="  Free3@Example.COM ",
        confirmation_word="DELETE",
        actor_user_id=admin.id,
    )

    assert not exists(session, AppUser, applicant_id)


def test_shared_company_survives_its_deleted_owner(session, admin):
    applicant = make_user(session, "shared@example.com")
    make_application(session, applicant)
    shared = make_company(session, "Two Owners", applicant)
    join(session, shared, admin, role="owner")
    party = create_party(session, shared.id, "Customer", "customer")
    joined = make_company(session, "Someone Else", admin)
    join(session, joined, applicant, role="member")
    applicant_id, shared_id, joined_id, party_id = (
        applicant.id,
        shared.id,
        joined.id,
        party.id,
    )

    delete_account(
        session,
        applicant_id,
        confirmation_email="shared@example.com",
        confirmation_word="DELETE",
        actor_user_id=admin.id,
    )

    assert exists(session, Tenant, shared_id)
    assert exists(session, Tenant, joined_id)
    assert exists(session, type(party), party_id)
    assert user_references(session, applicant_id) == 0
    remaining = session.scalar(
        select(func.count(TenantMembership.id)).where(
            TenantMembership.tenant_id == shared_id
        )
    )
    assert remaining == 1


def test_refuses_self_and_platform_administrators(session, admin):
    colleague = make_user(session, "second-admin@example.com", platform_admin=True)
    make_application(session, colleague)
    make_application(session, admin)

    with pytest.raises(InvalidOperation, match="own account"):
        delete_account(
            session,
            admin.id,
            confirmation_email=admin.email,
            confirmation_word="DELETE",
            actor_user_id=admin.id,
        )
    with pytest.raises(InvalidOperation, match="platform administrator"):
        delete_account(
            session,
            colleague.id,
            confirmation_email=colleague.email,
            confirmation_word="DELETE",
            actor_user_id=admin.id,
        )
    assert exists(session, AppUser, colleague.id)


@pytest.mark.parametrize(
    "email,word",
    [
        ("wrong@example.com", "DELETE"),
        ("confirm@example.com", "delete"),
        ("confirm@example.com", "LÖSCHEN"),
        ("", ""),
    ],
)
def test_confirmations_must_match_exactly(session, admin, email, word):
    applicant = make_user(session, "confirm@example.com")
    make_application(session, applicant)

    with pytest.raises(InvalidOperation, match="must match exactly"):
        delete_account(
            session,
            applicant.id,
            confirmation_email=email,
            confirmation_word=word,
            actor_user_id=admin.id,
        )
    assert exists(session, AppUser, applicant.id)


def test_refusal_leaves_every_row_in_place(session, admin):
    applicant = make_user(session, "intact@example.com")
    make_application(session, applicant)
    company = make_company(session, "Still Here", applicant)
    create_party(session, company.id, "Customer", "customer")
    before = user_references(session, applicant.id)

    with pytest.raises(InvalidOperation):
        delete_account(
            session,
            applicant.id,
            confirmation_email="intact@example.com",
            confirmation_word="nope",
            actor_user_id=admin.id,
        )

    assert exists(session, Tenant, company.id)
    assert user_references(session, applicant.id) == before


def test_writes_a_tombstone_without_a_user_reference(session, admin):
    applicant = make_user(session, "tombstone@example.com")
    make_application(session, applicant)
    make_company(session, "Gone", applicant)

    delete_account(
        session,
        applicant.id,
        confirmation_email="tombstone@example.com",
        confirmation_word="DELETE",
        actor_user_id=admin.id,
    )

    event = session.scalar(
        select(SecurityAuditEvent).where(
            SecurityAuditEvent.event_type == "access.deleted"
        )
    )
    assert event is not None
    assert event.user_id is None
    assert event.actor_user_id == admin.id
    detail = json.loads(event.detail)
    assert detail["email"] == "tombstone@example.com"
    assert detail["company_count"] == 1


def test_unknown_application_and_account_are_not_found(session, admin):
    with pytest.raises(NotFound):
        application_account_id(session, "app_missing")
    with pytest.raises(NotFound):
        account_deletion_preview(session, "usr_missing")
