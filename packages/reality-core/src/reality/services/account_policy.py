"""Equivalent account admission rules for object checks and scoped SQL readers."""

from sqlalchemy import and_, false, or_
from sqlalchemy.orm import Session

from reality.db.core import AppUser


def local_owner_id(session: Session) -> str | None:
    installation = session.info.get("desktop_installation_id")
    owner = session.info.get("desktop_owner_id")
    return (
        owner
        if isinstance(installation, str)
        and installation
        and isinstance(owner, str)
        and owner
        else None
    )


def account_eligible(
    session: Session, user: AppUser, *, allow_pending: bool = False
) -> bool:
    if user.authentication_method == "local_os":
        return user.status == "active" and user.id == local_owner_id(session)
    return (
        user.authentication_method == "email"
        and user.email_verified_at is not None
        and user.status
        in ({"active", "pending_approval"} if allow_pending else {"active"})
    )


def account_eligible_clause(session: Session, *, allow_pending: bool = False):
    owner = local_owner_id(session)
    email = and_(
        AppUser.authentication_method == "email",
        AppUser.email_verified_at.is_not(None),
        AppUser.status.in_(
            ["active", "pending_approval"] if allow_pending else ["active"]
        ),
    )
    local = (
        and_(
            AppUser.authentication_method == "local_os",
            AppUser.status == "active",
            AppUser.id == owner,
        )
        if owner
        else false()
    )
    return or_(email, local)


def session_identity_allowed(session: Session, user: AppUser) -> bool:
    """Preserve hosted pre-admission sessions; never admit local identities there."""
    return user.authentication_method == "email" or (
        user.authentication_method == "local_os" and account_eligible(session, user)
    )
