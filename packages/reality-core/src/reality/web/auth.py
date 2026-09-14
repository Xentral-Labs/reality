from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import smtplib
from datetime import timedelta
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from reality.db.core import (
    AccessAdmissionCounter,
    AccessApplication,
    AppUser,
    EmailVerificationCode,
    SecurityAuditEvent,
    Session,
    Tenant,
    UserSession,
    now,
    uid,
)
from reality.services.access_admission import (
    automatic_access_limit,
    claim_automatic_access_slot,
)
from reality.services.account_deletion import (
    account_deletion_preview,
    application_account_id,
    delete_account,
)
from reality.services.core import InvalidOperation, NotFound, RealityError
from reality.services.memberships import (
    accept_invitation,
    inspect_invitation,
    validate_invitation_recipient,
)
from reality.services.platform import platform_overview
from reality.web.email import (
    send_access_decision_email,
    send_access_request_notification,
    send_verification_email,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])
admin_router = APIRouter(prefix="/api/admin", tags=["platform-admin"])
password_hasher = PasswordHasher()
COOKIE_NAME = "reality_session"
SESSION_DAYS = 30


def database_session():
    with Session() as session:
        yield session


DatabaseSession = Annotated[OrmSession, Depends(database_session)]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def normalize_email(value: str) -> str:
    return value.strip().casefold()


def require_public_signup() -> None:
    """Reject account creation when a hosted environment uses prepared accounts."""
    if os.environ.get("REALITY_PUBLIC_SIGNUP_ENABLED", "true").lower() != "true":
        raise HTTPException(status_code=403, detail="Public signup is disabled.")


def audit(
    session: OrmSession,
    event_type: str,
    user_id: str | None,
    actor_id: str | None = None,
    **detail,
) -> None:
    session.add(
        SecurityAuditEvent(
            id=uid("sec"),
            user_id=user_id,
            actor_user_id=actor_id,
            event_type=event_type,
            detail=json.dumps(detail),
        )
    )


def issue_code(session: OrmSession, user: AppUser) -> str:
    recent = session.scalar(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.user_id == user.id)
        .order_by(EmailVerificationCode.created_at.desc())
    )
    if recent and (now() - recent.created_at).total_seconds() < 60:
        raise HTTPException(
            status_code=429, detail="Please wait before requesting another code."
        )
    code = f"{secrets.randbelow(1_000_000):06d}"
    session.add(
        EmailVerificationCode(
            id=uid("evc"),
            user_id=user.id,
            code_hash=digest(code),
            expires_at=now() + timedelta(minutes=10),
        )
    )
    send_verification_email(user.email, code)
    return code


def create_session(session: OrmSession, user: AppUser, response: Response) -> None:
    clear_token = secrets.token_urlsafe(48)
    session.add(
        UserSession(
            id=uid("ses"),
            user_id=user.id,
            token_hash=digest(clear_token),
            expires_at=now() + timedelta(days=SESSION_DAYS),
        )
    )
    user.last_login_at = now()
    response.set_cookie(
        COOKIE_NAME,
        clear_token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        secure=os.environ.get("REALITY_COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
    )


def user_from_request(request: Request, session: OrmSession) -> AppUser | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    auth_session = session.scalar(
        select(UserSession).where(
            UserSession.token_hash == digest(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now(),
        )
    )
    if not auth_session:
        return None
    return session.get(AppUser, auth_session.user_id)


def current_user(request: Request, session: DatabaseSession) -> AppUser:
    user = user_from_request(request, session)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


CurrentUser = Annotated[AppUser, Depends(current_user)]


def platform_admin(user: CurrentUser) -> AppUser:
    if not user.is_platform_admin:
        raise HTTPException(
            status_code=403, detail="Platform administrator access required."
        )
    return user


PlatformAdmin = Annotated[AppUser, Depends(platform_admin)]


def user_payload(user: AppUser, application: AccessApplication | None = None) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status,
        "language": user.language,
        "locale": user.locale,
        "timezone": user.timezone,
        "is_platform_admin": user.is_platform_admin,
        "application": None
        if not application
        else {
            "id": application.id,
            "company_name": application.company_name,
            "company_website": application.company_website,
            "orders_per_day": application.orders_per_day,
            "role_title": application.role_title,
            "status": application.status,
            "requested_at": application.requested_at,
            "reviewed_at": application.reviewed_at,
        },
    }


# One display locale belongs to each supported language. Signup pairs them itself so a
# client can state what the browser knows without choosing what an account may hold.
SUPPORTED_LOCALES = {"en": "en-GB", "de": "de-DE", "nl": "nl-NL", "es": "es-ES"}


def known_timezone(timezone: str) -> bool:
    """A malformed key is unknown, not an error the caller has to handle."""
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def presentation_defaults(
    language: str | None, timezone: str | None
) -> tuple[str, str, str]:
    """Resolve the initial presentation preference from the browser's own hint.

    The hint is unverified presentation, never identity: an absent, unsupported or
    unresolvable value falls back instead of failing a registration.
    """
    accepted = language if language in SUPPORTED_LOCALES else "en"
    zone = "UTC"
    if timezone and known_timezone(timezone):
        zone = timezone
    return accepted, SUPPORTED_LOCALES[accepted], zone


class SignupBody(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=256)
    accepted_terms: bool
    playground: bool = False
    # What the browser already knows about its reader, not an answered question.
    language: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = normalize_email(value)
        if (
            "@" not in value
            or value.startswith("@")
            or value.endswith("@")
            or "." not in value.rsplit("@", 1)[1]
        ):
            raise ValueError("Enter a valid email address.")
        return value


class VerifyBody(BaseModel):
    email: str
    code: str = Field(pattern=r"^\d{6}$")
    invitation_token: str | None = None


class InvitationTokenBody(BaseModel):
    token: str = Field(min_length=32, max_length=512)


class InvitationSignupBody(SignupBody):
    token: str = Field(min_length=32, max_length=512)


class LoginBody(BaseModel):
    email: str
    password: str


class ApplicationBody(BaseModel):
    display_name: str = Field(default="", max_length=150)
    company_name: str = Field(default="", max_length=200)
    company_website: str = Field(default="", max_length=500)
    orders_per_day: str = Field(default="", max_length=100)
    role_title: str = Field(default="", max_length=150)
    language: str = "en"
    locale: str = "en-GB"
    timezone: str = "UTC"


class ProfileBody(BaseModel):
    display_name: str = Field(max_length=150)
    language: str
    locale: str
    timezone: str


class ReviewBody(BaseModel):
    decision: str = Field(pattern=r"^(approve|reject)$")
    note: str = Field(default="", max_length=1000)


class AccountDeleteBody(BaseModel):
    confirmation_email: str = Field(max_length=320)
    confirmation_word: str = Field(max_length=32)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignupBody, session: DatabaseSession):
    require_public_signup()
    if not body.accepted_terms:
        raise HTTPException(
            status_code=422, detail="Terms and privacy policy must be accepted."
        )
    email = normalize_email(str(body.email))
    existing = session.scalar(select(AppUser).where(AppUser.email == email))
    if existing:
        raise HTTPException(
            status_code=409, detail="An account already exists for this email."
        )
    language, locale, timezone = presentation_defaults(body.language, body.timezone)
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash=password_hasher.hash(body.password),
        language=language,
        locale=locale,
        timezone=timezone,
    )
    session.add(user)
    session.flush()
    code = issue_code(session, user)
    audit(session, "user.signed_up", user.id)
    # Trial allowance is account policy, independent of optional demo creation consent.
    audit(session, "account.trial_started", user.id)
    if body.playground:
        from reality.services.free_playground import request_entry

        request_entry(session, user.id)
    session.commit()
    result = {"email": email, "next": "verify_email"}
    if os.environ.get("REALITY_AUTH_EXPOSE_CODES", "false").lower() == "true":
        result["verification_code"] = code
    return result


@router.post("/invitations/inspect")
def invitation_inspect(body: InvitationTokenBody, session: DatabaseSession):
    return inspect_invitation(session, body.token)


@router.post("/invitations/signup", status_code=status.HTTP_201_CREATED)
def invitation_signup(body: InvitationSignupBody, session: DatabaseSession):
    if not body.accepted_terms:
        raise HTTPException(
            status_code=422, detail="Terms and privacy policy must be accepted."
        )
    try:
        validate_invitation_recipient(session, body.token, body.email)
    except RealityError as error:
        raise HTTPException(
            status_code=400, detail="Invitation is unavailable."
        ) from error
    email = normalize_email(body.email)
    existing = session.scalar(select(AppUser).where(AppUser.email == email))
    if existing:
        return {"email": email, "next": "sign_in"}
    language, locale, timezone = presentation_defaults(body.language, body.timezone)
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash=password_hasher.hash(body.password),
        language=language,
        locale=locale,
        timezone=timezone,
    )
    session.add(user)
    session.flush()
    code = issue_code(session, user)
    audit(session, "user.signed_up_by_invitation", user.id)
    session.commit()
    result = {"email": email, "next": "verify_email"}
    if os.environ.get("REALITY_AUTH_EXPOSE_CODES", "false").lower() == "true":
        result["verification_code"] = code
    return result


@router.post("/resend-code")
def resend_code(body: dict, session: DatabaseSession):
    require_public_signup()
    email = normalize_email(str(body.get("email", "")))
    user = session.scalar(select(AppUser).where(AppUser.email == email))
    if user and not user.email_verified_at:
        issue_code(session, user)
        session.commit()
    return {"ok": True}


@router.post("/verify-email")
def verify_email(body: VerifyBody, response: Response, session: DatabaseSession):
    user = session.scalar(
        select(AppUser).where(AppUser.email == normalize_email(str(body.email)))
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification code."
        )
    challenge = session.scalar(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.consumed_at.is_(None),
        )
        .order_by(EmailVerificationCode.created_at.desc())
    )
    if not challenge or challenge.expires_at <= now() or challenge.attempts >= 5:
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification code."
        )
    challenge.attempts += 1
    if not secrets.compare_digest(challenge.code_hash, digest(body.code)):
        session.commit()
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification code."
        )
    challenge.consumed_at = now()
    user.email_verified_at = now()
    invited = False
    if body.invitation_token:
        try:
            validate_invitation_recipient(session, body.invitation_token, user.email)
            invited = True
        except RealityError as error:
            raise HTTPException(
                status_code=400, detail="Invitation is unavailable."
            ) from error
    automatically_approved = False if invited else claim_automatic_access_slot(session)
    user.status = (
        "pending_approval"
        if invited
        else ("active" if automatically_approved else "pending_approval")
    )
    application = None
    if not invited:
        application = AccessApplication(
            id=uid("apl"),
            user_id=user.id,
            status="approved" if automatically_approved else "pending",
            review_note="Automatically approved by the deployment admission policy."
            if automatically_approved
            else "",
            reviewed_at=now() if automatically_approved else None,
        )
        session.add(application)
    create_session(session, user, response)
    audit(session, "user.email_verified", user.id)
    session.commit()
    try:
        if invited:
            pass
        elif automatically_approved:
            send_access_decision_email(user.email, True)
        else:
            send_access_request_notification(user.email)
    except (OSError, RuntimeError, smtplib.SMTPException, httpx.HTTPError):
        log.exception(
            "Could not send Reality access request notification for %s", user.email
        )
    return user_payload(user, application)


@router.post("/invitations/accept")
def invitation_accept(
    body: InvitationTokenBody,
    user: CurrentUser,
    session: DatabaseSession,
):
    try:
        membership = accept_invitation(session, body.token, user.id)
    except RealityError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    tenant = session.get(Tenant, membership.tenant_id)
    session.commit()
    return {
        "status": "accepted",
        "company": {"id": tenant.id, "name": tenant.name},
    }


@router.post("/login")
def login(body: LoginBody, response: Response, session: DatabaseSession):
    user = session.scalar(
        select(AppUser).where(AppUser.email == normalize_email(str(body.email)))
    )
    try:
        valid = bool(user) and password_hasher.verify(user.password_hash, body.password)
    except VerifyMismatchError:
        valid = False
    if not valid or not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user.status in {"rejected", "suspended"}:
        raise HTTPException(status_code=403, detail="This account is not active.")
    create_session(session, user, response)
    audit(session, "user.logged_in", user.id)
    session.commit()
    application = session.scalar(
        select(AccessApplication).where(AccessApplication.user_id == user.id)
    )
    return user_payload(user, application)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, session: DatabaseSession):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        auth_session = session.scalar(
            select(UserSession).where(UserSession.token_hash == digest(token))
        )
        if auth_session:
            auth_session.revoked_at = now()
            session.commit()
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me")
def me(user: CurrentUser, session: DatabaseSession):
    application = session.scalar(
        select(AccessApplication).where(AccessApplication.user_id == user.id)
    )
    return user_payload(user, application)


def validate_preferences(language: str, locale: str, timezone: str) -> None:
    if language not in SUPPORTED_LOCALES:
        raise HTTPException(status_code=422, detail="Unsupported language.")
    if locale not in SUPPORTED_LOCALES.values():
        raise HTTPException(status_code=422, detail="Unsupported locale.")
    if not known_timezone(timezone):
        raise HTTPException(status_code=422, detail="Unknown timezone.")


@router.put("/application")
def update_application(
    body: ApplicationBody, user: CurrentUser, session: DatabaseSession
):
    validate_preferences(body.language, body.locale, body.timezone)
    application = session.scalar(
        select(AccessApplication).where(AccessApplication.user_id == user.id)
    )
    if not application:
        raise HTTPException(status_code=404, detail="Access application not found.")
    user.display_name, user.language, user.locale, user.timezone = (
        body.display_name.strip(),
        body.language,
        body.locale,
        body.timezone,
    )
    (
        application.company_name,
        application.company_website,
        application.orders_per_day,
        application.role_title,
    ) = (
        body.company_name.strip(),
        body.company_website.strip(),
        body.orders_per_day.strip(),
        body.role_title.strip(),
    )
    user.updated_at = now()
    session.commit()
    return user_payload(user, application)


@router.put("/profile")
def update_profile(body: ProfileBody, user: CurrentUser, session: DatabaseSession):
    validate_preferences(body.language, body.locale, body.timezone)
    user.display_name, user.language, user.locale, user.timezone, user.updated_at = (
        body.display_name.strip(),
        body.language,
        body.locale,
        body.timezone,
        now(),
    )
    session.commit()
    return user_payload(user)


@admin_router.get("/access-applications")
def applications(_: PlatformAdmin, session: DatabaseSession):
    rows = session.execute(
        select(AccessApplication, AppUser)
        .join(AppUser, AppUser.id == AccessApplication.user_id)
        .order_by(AccessApplication.requested_at.desc())
    ).all()
    return [
        {
            **user_payload(user, application),
            "requested_at": application.requested_at,
            "reviewed_at": application.reviewed_at,
        }
        for application, user in rows
    ]


@admin_router.get("/access-capacity")
def access_capacity(_: PlatformAdmin, session: DatabaseSession):
    counter = session.get(AccessAdmissionCounter, "automatic")
    return {
        "used": counter.used_slots if counter else 0,
        "limit": automatic_access_limit(),
    }


@admin_router.post("/access-applications/{application_id}/review")
def review_application(
    application_id: str,
    body: ReviewBody,
    admin: PlatformAdmin,
    session: DatabaseSession,
):
    application = session.get(AccessApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    user = session.get(AppUser, application.user_id)
    application.status = "approved" if body.decision == "approve" else "rejected"
    (
        application.review_note,
        application.reviewed_at,
        application.reviewed_by_user_id,
    ) = body.note.strip(), now(), admin.id
    user.status = "active" if body.decision == "approve" else "rejected"
    audit(session, f"access.{application.status}", user.id, admin.id)
    session.commit()
    try:
        send_access_decision_email(user.email, body.decision == "approve")
    except (OSError, RuntimeError, smtplib.SMTPException, httpx.HTTPError):
        log.exception("Could not send Reality access decision to %s", user.email)
    return user_payload(user, application)


@admin_router.get("/access-applications/{application_id}/deletion-preview")
def deletion_preview(
    application_id: str, _: PlatformAdmin, session: DatabaseSession
):
    """Name what deleting this applicant would remove, before anything is removed."""
    try:
        return account_deletion_preview(
            session, application_account_id(session, application_id)
        )
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@admin_router.post("/access-applications/{application_id}/delete")
def delete_application_account(
    application_id: str,
    body: AccountDeleteBody,
    admin: PlatformAdmin,
    session: DatabaseSession,
):
    """Remove the applicant, their sole-owned companies and every reference to them."""
    try:
        return delete_account(
            session,
            application_account_id(session, application_id),
            confirmation_email=body.confirmation_email,
            confirmation_word=body.confirmation_word,
            actor_user_id=admin.id,
        )
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidOperation as error:
        # Every guard runs before the first write, so the refused request has
        # nothing to undo; the request-scoped session is discarded either way.
        raise HTTPException(status_code=400, detail=str(error)) from error


@admin_router.get("/overview")
def overview(_: PlatformAdmin, session: DatabaseSession):
    """Return platform operation metadata; tenant business content stays scoped."""
    return platform_overview(session)


def bootstrap_platform_admin(session: OrmSession) -> None:
    email = normalize_email(os.environ.get("REALITY_PLATFORM_ADMIN_EMAIL", ""))
    password = os.environ.get("REALITY_PLATFORM_ADMIN_PASSWORD", "")
    if not email or not password:
        return
    user = session.scalar(select(AppUser).where(AppUser.email == email))
    if not user:
        user = AppUser(
            id=uid("usr"),
            email=email,
            password_hash=password_hasher.hash(password),
            status="active",
            is_platform_admin=True,
            email_verified_at=now(),
        )
        session.add(user)
    else:
        user.status, user.is_platform_admin = "active", True
    session.commit()
