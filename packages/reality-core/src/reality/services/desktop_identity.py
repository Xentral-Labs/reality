"""Bootstrap an OS-owned identity only from a trusted installation session."""

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from reality.db.core import AppUser, SecurityAuditEvent, uid
from reality.services.core import InvalidOperation


def bootstrap_owner(session: Session, installation_id: str) -> AppUser:
    try:
        if str(UUID(installation_id)) != installation_id:
            raise ValueError()
    except (ValueError, TypeError, AttributeError) as error:
        raise InvalidOperation("Invalid desktop installation identity.") from error
    if session.info.get("desktop_installation_id") != installation_id:
        raise InvalidOperation("Trusted desktop installation context required.")
    label = f"{installation_id}@desktop.invalid"
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:identity, 0))"),
        {"identity": label},
    )
    user = session.scalar(select(AppUser).where(AppUser.email == label))
    bound = session.info.get("desktop_owner_id")
    if user is not None:
        if (
            user.authentication_method != "local_os"
            or user.status != "active"
            or user.is_platform_admin
            or user.email_verified_at is not None
            or (bound and bound != user.id)
        ):
            raise InvalidOperation("Desktop owner binding is invalid.")
        return user
    if bound:
        raise InvalidOperation("Bound desktop owner is missing.")
    user = AppUser(
        id=uid("usr"),
        email=label,
        password_hash="!local_os",
        display_name="Local owner",
        status="active",
        authentication_method="local_os",
        is_platform_admin=False,
    )
    session.add(user)
    session.flush()
    session.add(
        SecurityAuditEvent(
            id=uid("aud"),
            user_id=user.id,
            event_type="desktop.owner_created",
            detail="{}",
        )
    )
    return user
