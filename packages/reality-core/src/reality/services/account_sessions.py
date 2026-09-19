"""Transport-independent issuance and revocation of existing account sessions."""

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import AppUser, UserSession, now, uid
from reality.services.account_policy import session_identity_allowed
from reality.services.core import InvalidOperation

SESSION_DAYS = 30


def issue_session(session: Session, user: AppUser) -> str:
    if not session_identity_allowed(session, user):
        raise InvalidOperation("This identity is not admitted by this installation.")
    token = secrets.token_urlsafe(48)
    session.add(
        UserSession(
            id=uid("ses"),
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=now() + timedelta(days=SESSION_DAYS),
        )
    )
    user.last_login_at = now()
    return token


def revoke_session(session: Session, token: str) -> None:
    record = session.scalar(
        select(UserSession).where(
            UserSession.token_hash == hashlib.sha256(token.encode()).hexdigest()
        )
    )
    if record:
        record.revoked_at = now()
