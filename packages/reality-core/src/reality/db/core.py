from __future__ import annotations

import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import (
    DDL,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

ROOT = Path(
    os.environ.get("REALITY_ROOT", Path(__file__).resolve().parents[3])
).resolve()
UTCDateTime = DateTime(timezone=True)


def resolve_database_url(environ: Mapping[str, str] = os.environ) -> str:
    """Return the required shared PostgreSQL database URL."""
    database_url = environ.get("REALITY_DATABASE_URL")
    if not database_url:
        raise RuntimeError("REALITY_DATABASE_URL must be configured.")
    if make_url(database_url).get_backend_name() != "postgresql":
        raise ValueError("REALITY_DATABASE_URL must use PostgreSQL.")
    return database_url


@dataclass(frozen=True)
class DatabasePoolSettings:
    pool_size: int = 5
    max_overflow: int = 5
    pool_timeout: int = 30


def _bounded_integer(
    environ: Mapping[str, str], name: str, default: int, minimum: int, maximum: int
) -> int:
    raw = environ.get(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be an integer.") from error
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def resolve_database_pool_settings(
    environ: Mapping[str, str] = os.environ,
) -> DatabasePoolSettings:
    """Return bounded per-process PostgreSQL pool settings."""
    return DatabasePoolSettings(
        pool_size=_bounded_integer(environ, "REALITY_DB_POOL_SIZE", 5, 1, 100),
        max_overflow=_bounded_integer(environ, "REALITY_DB_MAX_OVERFLOW", 5, 0, 100),
        pool_timeout=_bounded_integer(environ, "REALITY_DB_POOL_TIMEOUT", 30, 1, 300),
    )


def build_engine(
    database_url: str,
    *,
    pool_settings: DatabasePoolSettings | None = None,
) -> Engine:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError("Reality requires PostgreSQL.")
    settings = pool_settings or resolve_database_pool_settings()
    return create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
    )


DATABASE_URL = resolve_database_url()
engine = build_engine(DATABASE_URL)
Session = sessionmaker(engine, expire_on_commit=False)


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenant"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('business', 'playground')", name="ck_tenant_purpose"
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    purpose: Mapped[str] = mapped_column(
        String, default="business", server_default="business"
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


# Also protect SQL/bulk writes: changing purpose would bypass the sandbox boundary.
event.listen(
    Tenant.__table__,
    "after_create",
    DDL("""
CREATE OR REPLACE FUNCTION reality_tenant_purpose_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN
    IF NEW.purpose IS DISTINCT FROM OLD.purpose THEN
        RAISE EXCEPTION 'Tenant purpose is immutable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER tenant_purpose_immutable BEFORE UPDATE OF purpose ON tenant
FOR EACH ROW EXECUTE FUNCTION reality_tenant_purpose_immutable();
""").execute_if(dialect="postgresql"),
)


class PlaygroundRun(Base):
    """Owner-bound orchestration metadata, never a second business ledger."""

    __tablename__ = "playground_run"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_playground_run_tenant"),
        CheckConstraint(
            "sandbox_kind IN ('temporary', 'practice')", name="ck_playground_run_kind"
        ),
        UniqueConstraint("tenant_id", "id", name="uq_playground_run_tenant_id"),
        CheckConstraint(
            "jsonb_typeof(initialization_progress) = 'object' AND octet_length(initialization_progress::text) <= 65536",
            name="ck_playground_run_progress",
        ),
        UniqueConstraint(
            "owner_user_id", "client_request_key", name="uq_playground_run_request"
        ),
        CheckConstraint(
            "status IN ('initializing', 'active', 'initialization_failed', 'archived')",
            name="ck_playground_run_status",
        ),
        CheckConstraint(
            "preset_version > 0 AND lesson_version > 0",
            name="ck_playground_run_versions",
        ),
        CheckConstraint(
            "status != 'active' OR ready_at IS NOT NULL", name="ck_playground_run_ready"
        ),
        CheckConstraint(
            "status != 'archived' OR archived_at IS NOT NULL",
            name="ck_playground_run_archived",
        ),
        Index(
            "uq_playground_run_active_owner",
            "owner_user_id",
            unique=True,
            postgresql_where=text("status = 'active' AND sandbox_kind = 'temporary'"),
        ),
        # Storyline mode (spec 182): one active run per storyline per person, so
        # opening Storyline resumes instead of creating.
        CheckConstraint(
            "(storyline_key IS NULL) = (storyline_version IS NULL) "
            "AND (storyline_version IS NULL OR storyline_version > 0)",
            name="ck_playground_run_storyline",
        ),
        CheckConstraint(
            "jsonb_typeof(storyline_state) = 'object' AND octet_length(storyline_state::text) <= 8192",
            name="ck_playground_run_storyline_state",
        ),
        Index(
            "uq_playground_run_active_storyline",
            "owner_user_id",
            "storyline_key",
            unique=True,
            postgresql_where=text("status = 'active' AND storyline_key IS NOT NULL"),
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    preset_key: Mapped[str] = mapped_column(String(80))
    sandbox_kind: Mapped[str] = mapped_column(
        String(16), default="temporary", server_default="temporary"
    )
    preset_version: Mapped[int] = mapped_column(Integer)
    lesson_key: Mapped[str] = mapped_column(String(80))
    lesson_version: Mapped[int] = mapped_column(Integer)
    client_request_key: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(
        String, default="initializing", server_default="initializing"
    )
    initialization_progress: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    initialization_error_code: Mapped[str | None] = mapped_column(
        String(80), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    ready_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    storyline_key: Mapped[str | None] = mapped_column(String(80), default=None)
    storyline_version: Mapped[int | None] = mapped_column(Integer, default=None)
    # Chosen branches only ({"branches": {"<chapter>": "<branch>"}}); the current
    # chapter is derived from the steps, never stored.
    storyline_state: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )


class PlaygroundStep(Base):
    """A proposal link and historical observations, not another execution status."""

    __tablename__ = "playground_step"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["playground_run.tenant_id", "playground_run.id"],
            name="fk_playground_step_run",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "proposal_id"],
            ["action.tenant_id", "action.id"],
            name="fk_playground_step_proposal",
        ),
        UniqueConstraint("proposal_id", name="uq_playground_step_proposal"),
        UniqueConstraint("tenant_id", "id", name="uq_playground_step_tenant_id"),
        UniqueConstraint("run_id", "sequence", name="uq_playground_step_sequence"),
        UniqueConstraint("run_id", "request_key", name="uq_playground_step_request"),
        CheckConstraint("sequence > 0", name="ck_playground_step_sequence"),
        CheckConstraint(
            "before_observation IS NULL OR (jsonb_typeof(before_observation) = 'object' AND octet_length(before_observation::text) <= 65536)",
            name="ck_playground_step_before",
        ),
        CheckConstraint(
            "receipt_observation IS NULL OR (jsonb_typeof(receipt_observation) = 'object' AND octet_length(receipt_observation::text) <= 65536)",
            name="ck_playground_step_receipt",
        ),
        # A Storyline read chapter is a step without a proposal (spec 182); it is
        # still owned by its chapter key.
        CheckConstraint(
            "proposal_id IS NOT NULL OR lesson_step_key IS NOT NULL",
            name="ck_playground_step_owner",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    run_id: Mapped[str] = mapped_column(String)
    sequence: Mapped[int] = mapped_column(Integer)
    request_key: Mapped[str] = mapped_column(String(128))
    proposal_id: Mapped[str | None] = mapped_column(String, default=None)
    lesson_step_key: Mapped[str | None] = mapped_column(String(80), default=None)
    # Storyline marker (spec 182, FR-005): the delta of a chapter is everything
    # recorded after these two values, captured before its first mutating call.
    marker_sequence: Mapped[int | None] = mapped_column(BigInteger, default=None)
    marker_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    before_observation: Mapped[dict | None] = mapped_column(
        JSONB(none_as_null=True), default=None
    )
    receipt_observation: Mapped[dict | None] = mapped_column(
        JSONB(none_as_null=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    observed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class StorylineTraceEntry(Base):
    """One recorded call in a Storyline run (spec 182, FR-004).

    An explanation aid, never a business record: bounded per entry and per run,
    dropped on downgrade, never joined by business reads.
    """

    __tablename__ = "storyline_trace_entry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["playground_run.tenant_id", "playground_run.id"],
            name="fk_storyline_trace_run",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "step_id"],
            ["playground_step.tenant_id", "playground_step.id"],
            name="fk_storyline_trace_step",
        ),
        UniqueConstraint("run_id", "ordinal", name="uq_storyline_trace_ordinal"),
        CheckConstraint(
            "kind IN ('view', 'read', 'propose', 'confirm', 'reject', 'error')",
            name="ck_storyline_trace_kind",
        ),
        CheckConstraint(
            "access IN ('read', 'propose', 'confirm')",
            name="ck_storyline_trace_access",
        ),
        CheckConstraint(
            "input IS NULL OR octet_length(input::text) <= 16384",
            name="ck_storyline_trace_input",
        ),
        CheckConstraint(
            "result IS NULL OR octet_length(result::text) <= 16384",
            name="ck_storyline_trace_result",
        ),
        CheckConstraint(
            "before_exceptions IS NULL OR octet_length(before_exceptions::text) <= 16384",
            name="ck_storyline_trace_before",
        ),
        Index("ix_storyline_trace_run_ordinal", "tenant_id", "run_id", "ordinal"),
        Index("ix_storyline_trace_step", "tenant_id", "step_id"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    run_id: Mapped[str] = mapped_column(String)
    step_id: Mapped[str | None] = mapped_column(String, default=None)
    ordinal: Mapped[int] = mapped_column(BigInteger)
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(120))
    access: Mapped[str] = mapped_column(String(8))
    actor: Mapped[str] = mapped_column(String(16))
    proposal_id: Mapped[str | None] = mapped_column(String, default=None)
    marker_sequence: Mapped[int | None] = mapped_column(BigInteger, default=None)
    marker_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    before_exceptions: Mapped[list | None] = mapped_column(
        JSONB(none_as_null=True), default=None
    )
    input: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), default=None)
    result: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), default=None)
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    recorded_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=now, server_default=text("now()")
    )


class StorylinePackageRecord(Base):
    """An imported storyline package, owned by an account (spec 182, FR-018).

    Account-scoped by design: practice companies are personal and a storyline
    outlives the company it was last played in. Never joined by business reads.
    """

    __tablename__ = "storyline_package"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_storyline_package_version"),
        CheckConstraint(
            "jsonb_typeof(document) = 'object' AND octet_length(document::text) <= 200000",
            name="ck_storyline_package_document",
        ),
        Index(
            "uq_storyline_package_owner_key_version",
            "owner_user_id",
            "key",
            "version",
            unique=True,
            postgresql_where=text("replaced_at IS NULL"),
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    key: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str | None] = mapped_column(String(200), default=None)
    checksum: Mapped[str] = mapped_column(String(64))
    document: Mapped[dict] = mapped_column(JSONB)
    validation: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    imported_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=now, server_default=text("now()")
    )
    replaced_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class AppUser(Base):
    """A human identity. Business access is granted separately by membership."""

    __tablename__ = "app_user"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="email_unverified", index=True)
    language: Mapped[str] = mapped_column(String, default="en")
    locale: Mapped[str] = mapped_column(String, default="en-GB")
    timezone: Mapped[str] = mapped_column(String, default="UTC")
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, default=None
    )
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class EmailVerificationCode(Base):
    __tablename__ = "email_verification_code"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class UserSession(Base):
    __tablename__ = "user_session"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class AccessApplication(Base):
    __tablename__ = "access_application"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("app_user.id"), unique=True, index=True
    )
    company_name: Mapped[str] = mapped_column(String, default="")
    company_website: Mapped[str] = mapped_column(String, default="")
    orders_per_day: Mapped[str] = mapped_column(String, default="")
    role_title: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    review_note: Mapped[str] = mapped_column(Text, default="")
    requested_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None
    )


class AccessAdmissionCounter(Base):
    """Serializes automatic platform admission across all application instances."""

    __tablename__ = "access_admission_counter"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    used_slots: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class TenantMembership(Base):
    __tablename__ = "tenant_membership"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id"),
        CheckConstraint(
            "role IN ('owner', 'member')", name="ck_tenant_membership_role"
        ),
        CheckConstraint(
            "status IN ('active', 'removed')", name="ck_tenant_membership_status"
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    role: Mapped[str] = mapped_column(String, default="owner")
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SecurityAuditEvent(Base):
    __tablename__ = "security_audit_event"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("app_user.id"), index=True)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenant.id"), index=True)
    subject_type: Mapped[str | None] = mapped_column(String, default=None)
    subject_id: Mapped[str | None] = mapped_column(String, default=None)
    outcome: Mapped[str | None] = mapped_column(String, default=None)
    event_type: Mapped[str] = mapped_column(String, index=True)
    detail: Mapped[str] = mapped_column(Text, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CompanyInvitation(Base):
    """Tenant-scoped evidence that one normalized email may join a company."""

    __tablename__ = "company_invitation"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'revoked', 'expired')",
            name="ck_company_invitation_status",
        ),
        CheckConstraint(
            "token_generation >= 1", name="ck_company_invitation_generation"
        ),
        Index(
            "uq_company_invitation_pending_email",
            "tenant_id",
            "normalized_email",
            unique=True,
            postgresql_where="status = 'pending'",
        ),
        Index("ix_company_invitation_tenant_status", "tenant_id", "status"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    normalized_email: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    token_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, default=None
    )
    token_generation: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    invited_by_user_id: Mapped[str] = mapped_column(
        ForeignKey("app_user.id"), index=True
    )
    accepted_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None
    )
    accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    terminal_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class InvitationDelivery(Base):
    """Durable, token-free intent to deliver an invitation generation."""

    __tablename__ = "invitation_delivery"
    __table_args__ = (
        UniqueConstraint("tenant_id", "invitation_id", "generation"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'retry', 'delivered', 'failed')",
            name="ck_invitation_delivery_status",
        ),
        CheckConstraint("attempt_count >= 0", name="ck_invitation_delivery_attempts"),
        Index(
            "ix_invitation_delivery_due",
            "status",
            "next_attempt_at",
            "claimed_at",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    invitation_id: Mapped[str] = mapped_column(
        ForeignKey("company_invitation.id"), index=True
    )
    generation: Mapped[int] = mapped_column(Integer)
    template_key: Mapped[str] = mapped_column(String, default="company_invitation")
    locale: Mapped[str] = mapped_column(String, default="en")
    status: Mapped[str] = mapped_column(String, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    claimed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    attempted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    provider_message_id: Mapped[str | None] = mapped_column(String, default=None)
    last_error_code: Mapped[str | None] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Party(Base):
    __tablename__ = "party"
    __table_args__ = (UniqueConstraint("tenant_id", "id", name="uq_party_tenant_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    accounting_code: Mapped[str] = mapped_column(String, default="")
    payment_term_id: Mapped[str | None] = mapped_column(
        ForeignKey("payment_term.id"), default=None
    )
    default_currency: Mapped[str] = mapped_column(String, default="EUR")
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    tax_identifier: Mapped[str] = mapped_column(String, default="")


class PartyRole(Base):
    __tablename__ = "party_role"
    __table_args__ = (UniqueConstraint("tenant_id", "party_id", "role"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column(ForeignKey("party.id"), index=True)
    role: Mapped[str] = mapped_column(String)
    default_location_id: Mapped[str | None] = mapped_column(
        ForeignKey("location.id"), default=None
    )


class PartyHold(Base):
    __tablename__ = "party_hold"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column(ForeignKey("party.id"), index=True)
    hold_type: Mapped[str] = mapped_column(String)
    reason_code: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String, default="human")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class Item(Base):
    __tablename__ = "item"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    sku: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String, default="pcs")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    item_type: Mapped[str] = mapped_column(String, default="stocked")
    tracking_type: Mapped[str] = mapped_column(String, default="none")
    default_location_id: Mapped[str | None] = mapped_column(
        ForeignKey("location.id"), default=None
    )
    purchase_unit: Mapped[str] = mapped_column(String, default="pcs")
    conversion_factor: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)


class Location(Base):
    __tablename__ = "location"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String, default="warehouse")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_location_id: Mapped[str | None] = mapped_column(
        ForeignKey("location.id"), default=None
    )
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    allows_stock: Mapped[bool] = mapped_column(Boolean, default=True)


class SourceSystem(Base):
    __tablename__ = "source_system"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id", name="uq_source_system_tenant_id"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    # The external system's own interface for this instance, so a record can be
    # opened where it is owned. Configuration only: never a credential, never called.
    base_url: Mapped[str | None] = mapped_column(Text, default=None)
    # The catalog connector this instance was installed from. It is the only
    # association between an instance and a connector; null means none is known,
    # which is the state a hand-created system has.
    connector_code: Mapped[str | None] = mapped_column(String, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SourceCapability(Base):
    __tablename__ = "source_capability"
    __table_args__ = (UniqueConstraint("tenant_id", "source_system_id", "source_type"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_system_id: Mapped[str] = mapped_column(
        ForeignKey("source_system.id"), index=True
    )
    source_type: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SourceStream(Base):
    __tablename__ = "source_stream"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "source_type",
            "external_id",
            name="uq_source_stream_identity",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_system: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    current_source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )


class SourceArtifact(Base):
    __tablename__ = "source_artifact"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sha256", name="uq_source_artifact_content"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    filename: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(
        String, default="application/octet-stream"
    )
    byte_size: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="staged", index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    attached_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class SourceRecord(Base):
    __tablename__ = "source_record"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "source_type",
            "external_id",
            "payload_hash",
            name="uq_source_record_identity_payload",
        ),
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "source_type",
            "external_id",
            "version",
            name="uq_source_record_identity_version",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_system: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    payload: Mapped[str] = mapped_column(Text)
    payload_hash: Mapped[str] = mapped_column(String(64))
    source_artifact_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_artifact.id"), default=None
    )
    version: Mapped[int] = mapped_column(Integer)
    source_version_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, default=None
    )
    supersedes_source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ImportJob(Base):
    __tablename__ = "import_job"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_import_job_source_record"
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_record_id: Mapped[str] = mapped_column(
        ForeignKey("source_record.id"), index=True
    )
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    input: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str] = mapped_column(Text, default="")
    next_attempt_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class InterpretationOutcome(Base):
    """Immutable terminal result of one source interpretation attempt."""

    __tablename__ = "interpretation_outcome"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "import_job_id",
            "attempt",
            name="uq_interpretation_outcome_attempt",
        ),
        CheckConstraint("attempt >= 0", name="ck_interpretation_outcome_attempt"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_record_id: Mapped[str] = mapped_column(
        ForeignKey("source_record.id"), index=True
    )
    import_job_id: Mapped[str] = mapped_column(ForeignKey("import_job.id"), index=True)
    attempt: Mapped[int] = mapped_column(Integer)
    classification: Mapped[str] = mapped_column(String, index=True)
    interpreter_name: Mapped[str] = mapped_column(String, default="")
    interpreter_version: Mapped[str] = mapped_column(String, default="1")
    reason_code: Mapped[str] = mapped_column(String, default="")
    summary: Mapped[str] = mapped_column(String, default="")
    completed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class InterpretationRecordReference(Base):
    """Opaque identity of one record produced by an interpretation outcome."""

    __tablename__ = "interpretation_record_reference"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "outcome_id",
            "record_type",
            "record_id",
            name="uq_interpretation_record_reference",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    outcome_id: Mapped[str] = mapped_column(
        ForeignKey("interpretation_outcome.id", ondelete="CASCADE"), index=True
    )
    record_type: Mapped[str] = mapped_column(String)
    record_id: Mapped[str] = mapped_column(String)


class PaymentTerm(Base):
    __tablename__ = "payment_term"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    due_days: Mapped[int] = mapped_column(Integer)
    # An early-payment discount is a rate and a window, and null in both is the
    # statement that this term grants none. A zero rate would say "nothing off",
    # which is a different thing from "no such offer".
    discount_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 3), default=None
    )
    discount_days: Mapped[int | None] = mapped_column(Integer, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )


class PriceList(Base):
    __tablename__ = "price_list"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    direction: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )


class PriceListEntry(Base):
    __tablename__ = "price_list_entry"
    __table_args__ = (
        UniqueConstraint("tenant_id", "price_list_id", "item_id", "min_quantity"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    price_list_id: Mapped[str] = mapped_column(ForeignKey("price_list.id"), index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("item.id"), index=True)
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    unit: Mapped[str] = mapped_column(String)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )


class PartyPriceList(Base):
    __tablename__ = "party_price_list"
    __table_args__ = (UniqueConstraint("tenant_id", "party_id", "price_list_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column(ForeignKey("party.id"), index=True)
    price_list_id: Mapped[str] = mapped_column(ForeignKey("price_list.id"), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class PartyGroup(Base):
    __tablename__ = "party_group"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    group_type: Mapped[str] = mapped_column(String, default="pricing")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )


class PartyGroupMember(Base):
    __tablename__ = "party_group_member"
    __table_args__ = (UniqueConstraint("tenant_id", "party_group_id", "party_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_group_id: Mapped[str] = mapped_column(
        ForeignKey("party_group.id"), index=True
    )
    party_id: Mapped[str] = mapped_column(ForeignKey("party.id"), index=True)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class PartyGroupPriceList(Base):
    __tablename__ = "party_group_price_list"
    __table_args__ = (UniqueConstraint("tenant_id", "party_group_id", "price_list_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_group_id: Mapped[str] = mapped_column(
        ForeignKey("party_group.id"), index=True
    )
    price_list_id: Mapped[str] = mapped_column(ForeignKey("price_list.id"), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class Document(Base):
    __tablename__ = "document"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_document_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "source_record_id",
            "type",
            name="uq_document_source_type",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_record.id"))
    type: Mapped[str] = mapped_column(String)
    number: Mapped[str] = mapped_column(String)
    party_id: Mapped[str | None] = mapped_column(ForeignKey("party.id"))
    currency: Mapped[str] = mapped_column(String, default="EUR")
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str] = mapped_column(String, default="open")
    document_date: Mapped[str] = mapped_column(String, default="")
    ordered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    requested_delivery_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, default=None
    )
    customer_reference: Mapped[str] = mapped_column(String, default="")
    sales_channel: Mapped[str] = mapped_column(String, default="")
    payment_term_id: Mapped[str | None] = mapped_column(
        ForeignKey("payment_term.id"), default=None
    )
    ship_to_party_id: Mapped[str | None] = mapped_column(
        ForeignKey("party.id"), default=None
    )


class DocumentLine(Base):
    __tablename__ = "document_line"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_document_line_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "document_id",
            "source_line_id",
            name="uq_document_line_source_line",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("document.id"))
    source_line_id: Mapped[str | None] = mapped_column(String)
    item_id: Mapped[str | None] = mapped_column(ForeignKey("item.id"))
    sku: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default="")
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    promised_at: Mapped[str] = mapped_column(String, default="")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    unit: Mapped[str] = mapped_column(String, default="pcs")
    requested_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    line_type: Mapped[str] = mapped_column(String, default="item")
    price_list_entry_id: Mapped[str | None] = mapped_column(
        ForeignKey("price_list_entry.id"), default=None
    )
    # Which agreed line this billed line settles. Null is a statement: the line
    # bills nothing an order promised, such as freight or a one-off service.
    billed_document_line_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_line.id"), default=None
    )


class Commitment(Base):
    __tablename__ = "commitment"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "document_line_id",
            "type",
            name="uq_commitment_document_line_type",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    from_party_id: Mapped[str | None] = mapped_column(ForeignKey("party.id"))
    to_party_id: Mapped[str | None] = mapped_column(ForeignKey("party.id"))
    item_id: Mapped[str | None] = mapped_column(ForeignKey("item.id"))
    location_id: Mapped[str | None] = mapped_column(ForeignKey("location.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    status: Mapped[str] = mapped_column(String, default="open")
    document_id: Mapped[str | None] = mapped_column(ForeignKey("document.id"))
    document_line_id: Mapped[str | None] = mapped_column(ForeignKey("document_line.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    priority: Mapped[str] = mapped_column(String, default="normal")


class CommitmentRevision(Base):
    """One statement by a counterparty restating a promise.

    Append-only, and a table rather than a column on the promise for one
    reason: a date somebody stated is a received value, and a column would let
    the second statement overwrite the first. The promise keeps the date it was
    made with, which is what makes "originally due" answerable.
    """

    __tablename__ = "commitment_revision"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    commitment_id: Mapped[str] = mapped_column(ForeignKey("commitment.id"), index=True)
    # Both nullable and at least one required: a statement restates the date,
    # the quantity, or both. "Eighty pieces, two weeks later" is one sentence
    # and belongs in one record with one `stated_at`.
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=None)
    stated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    note: Mapped[str] = mapped_column(Text, default="")
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CommitmentHold(Base):
    __tablename__ = "commitment_hold"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    commitment_id: Mapped[str] = mapped_column(ForeignKey("commitment.id"), index=True)
    reason_code: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String, default="human")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class Reservation(Base):
    __tablename__ = "reservation"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    commitment_id: Mapped[str] = mapped_column(ForeignKey("commitment.id"))
    item_id: Mapped[str] = mapped_column(ForeignKey("item.id"))
    location_id: Mapped[str] = mapped_column(ForeignKey("location.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(String, default="active")
    reserved_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    handling_unit_id: Mapped[str | None] = mapped_column(
        ForeignKey("handling_unit.id"), default=None
    )
    lot_id: Mapped[str | None] = mapped_column(ForeignKey("lot.id"), default=None)
    serial_unit_id: Mapped[str | None] = mapped_column(
        ForeignKey("serial_unit.id"), default=None
    )


class HandlingUnit(Base):
    __tablename__ = "handling_unit"
    __table_args__ = (UniqueConstraint("tenant_id", "nve"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    nve: Mapped[str | None] = mapped_column(String, default=None)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Lot(Base):
    __tablename__ = "lot"
    __table_args__ = (UniqueConstraint("tenant_id", "item_id", "lot_number"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("item.id"), index=True)
    lot_number: Mapped[str] = mapped_column(String)
    # The best-before date somebody read off the goods, never computed from a
    # shelf life. A calendar day rather than an instant, because a best-before
    # has no time of day and inventing one would be inventing precision.
    #
    # Absent says nothing in either direction: an item with no shelf life and a
    # label nobody read are indistinguishable here, and pretending otherwise
    # would be worse than the silence.
    expires_at: Mapped[date | None] = mapped_column(Date, default=None)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SerialUnit(Base):
    __tablename__ = "serial_unit"
    __table_args__ = (UniqueConstraint("tenant_id", "item_id", "serial_number"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("item.id"), index=True)
    serial_number: Mapped[str] = mapped_column(String)
    lot_id: Mapped[str | None] = mapped_column(ForeignKey("lot.id"), default=None)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Shipment(Base):
    __tablename__ = "shipment"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('inbound', 'outbound')", name="ck_shipment_direction"
        ),
        CheckConstraint(
            "purpose IN ('customer_delivery', 'supplier_delivery', 'customer_return', 'supplier_return')",
            name="ck_shipment_purpose",
        ),
        Index(
            "ix_shipment_tenant_direction_created",
            "tenant_id",
            "direction",
            "created_at",
        ),
        Index(
            "ix_shipment_tenant_purpose_created", "tenant_id", "purpose", "created_at"
        ),
        Index("ix_shipment_tenant_counterparty", "tenant_id", "counterparty_id"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    direction: Mapped[str] = mapped_column(String)
    purpose: Mapped[str] = mapped_column(String)
    counterparty_id: Mapped[str] = mapped_column(ForeignKey("party.id"))
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ShipmentPackage(Base):
    __tablename__ = "shipment_package"
    __table_args__ = (
        Index("ix_shipment_package_tenant_shipment", "tenant_id", "shipment_id"),
        Index(
            "ix_shipment_package_tenant_carrier_tracking",
            "tenant_id",
            "carrier",
            "tracking_number",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipment.id"))
    carrier: Mapped[str | None] = mapped_column(String, default=None)
    tracking_number: Mapped[str | None] = mapped_column(String, default=None)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ShipmentEvent(Base):
    __tablename__ = "shipment_event"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('announced', 'handed_over', 'in_transit', 'delivered', 'delivery_exception', 'received')",
            name="ck_shipment_event_type",
        ),
        CheckConstraint(
            "reporter_type IN ('company', 'counterparty', 'carrier', 'integration')",
            name="ck_shipment_event_reporter",
        ),
        Index(
            "ix_shipment_event_tenant_shipment",
            "tenant_id",
            "shipment_id",
            "recorded_at",
        ),
        Index(
            "ix_shipment_event_tenant_package",
            "tenant_id",
            "shipment_package_id",
            "recorded_at",
        ),
        Index("ix_shipment_event_tenant_external", "tenant_id", "external_event_id"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipment.id"))
    shipment_package_id: Mapped[str | None] = mapped_column(
        ForeignKey("shipment_package.id"), default=None
    )
    event_type: Mapped[str] = mapped_column(String)
    reporter_type: Mapped[str] = mapped_column(String)
    occurred_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    location_text: Mapped[str | None] = mapped_column(String, default=None)
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    external_event_id: Mapped[str | None] = mapped_column(String, default=None)


class ShipmentEventSupersession(Base):
    __tablename__ = "shipment_event_supersession"
    __table_args__ = (UniqueConstraint("tenant_id", "superseded_event_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    superseded_event_id: Mapped[str] = mapped_column(ForeignKey("shipment_event.id"))
    replacement_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("shipment_event.id"), default=None
    )
    reason: Mapped[str] = mapped_column(Text)
    actor_context: Mapped[str] = mapped_column(Text, default="{}")
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Movement(Base):
    __tablename__ = "movement"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    item_id: Mapped[str] = mapped_column(ForeignKey("item.id"))
    from_location_id: Mapped[str | None] = mapped_column(ForeignKey("location.id"))
    to_location_id: Mapped[str | None] = mapped_column(ForeignKey("location.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    commitment_id: Mapped[str | None] = mapped_column(ForeignKey("commitment.id"))
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_record.id"))
    handling_unit_id: Mapped[str | None] = mapped_column(
        ForeignKey("handling_unit.id"), default=None
    )
    lot_id: Mapped[str | None] = mapped_column(ForeignKey("lot.id"), default=None)
    serial_unit_id: Mapped[str | None] = mapped_column(
        ForeignKey("serial_unit.id"), default=None
    )
    shipment_package_id: Mapped[str | None] = mapped_column(
        ForeignKey("shipment_package.id"), default=None, index=True
    )
    # Which return this movement settles. Null is a statement: almost every
    # movement settles none, and what happened to returned goods is what the
    # settling movement is — a transfer back to stock, a write-off, a shipment
    # to the supplier — never a separate label that could disagree.
    resolves_movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("movement.id"), default=None
    )
    # Which announced return these goods fulfil. Null is a statement in the same
    # way: almost every movement fulfils none, and a return that arrives without
    # having been announced is ordinary rather than incomplete.
    return_announcement_id: Mapped[str | None] = mapped_column(
        ForeignKey("return_announcement.id"), default=None
    )


class ReturnAnnouncement(Base):
    """What a customer said they would send back, before it has left them.

    Reality rather than Evidence: it is not the message the customer sent, it is
    the promise the company holds as a result. So it is fulfilled or withdrawn
    and never corrected, and the quantity, reference and reason are exactly what
    somebody stated — nothing here is generated, the reference least of all,
    because a number this product invented would be a number somebody has to
    tell the customer.

    A record of its own rather than a third `Commitment.type`, which is the
    semantically obvious home. `customer_delivery` is read in thirty-two places
    across eight modules, seventeen of them a two-way branch whose `else` means
    *supplier delivery*; a third type would make all seventeen wrong and most
    would keep passing their tests.
    """

    __tablename__ = "return_announcement"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    # The customer delivery the goods went out on. It gives the item, the party
    # and the order line for free, and it is what bounds how much may come back.
    commitment_id: Mapped[str] = mapped_column(ForeignKey("commitment.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    # The number the parcel will carry, as the customer or the company stated it.
    reference: Mapped[str] = mapped_column(String, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    announced_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    # The day the customer said the goods would go, where they said one. Absent
    # is not "soon": it is the customer not having said, and the queue judges
    # those two differently.
    expected_by: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    # The same three words a Commitment uses, because it is the same shape of
    # thing: open, fulfilled, withdrawn.
    status: Mapped[str] = mapped_column(String, default="open")
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    note: Mapped[str] = mapped_column(Text, default="")
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class MovementCorrection(Base):
    __tablename__ = "movement_correction"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_fingerprint"),
        UniqueConstraint("original_movement_id"),
        UniqueConstraint("compensating_movement_id"),
        UniqueConstraint("replacement_movement_id"),
        CheckConstraint(
            "original_movement_id <> compensating_movement_id",
            name="ck_movement_correction_original_compensation_distinct",
        ),
        CheckConstraint(
            "replacement_movement_id IS NULL OR "
            "replacement_movement_id <> original_movement_id",
            name="ck_movement_correction_original_replacement_distinct",
        ),
        CheckConstraint(
            "replacement_movement_id IS NULL OR "
            "replacement_movement_id <> compensating_movement_id",
            name="ck_movement_correction_compensation_replacement_distinct",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    original_movement_id: Mapped[str] = mapped_column(
        ForeignKey("movement.id"), index=True
    )
    compensating_movement_id: Mapped[str] = mapped_column(
        ForeignKey("movement.id"), index=True
    )
    replacement_movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("movement.id"), index=True, default=None
    )
    reason: Mapped[str] = mapped_column(Text)
    corrected_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    actor_context: Mapped[str] = mapped_column(Text, default="{}")
    request_fingerprint: Mapped[str] = mapped_column(String)


class SubledgerAccount(Base):
    __tablename__ = "subledger_account"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "code"),
        CheckConstraint("state IN ('active', 'blocked')"),
        CheckConstraint(
            "role IN ('accounts_receivable','accounts_payable','cash','sales_revenue','inventory','customer_reduction','supplier_reduction','opening_counterpart')",
            name="ck_subledger_account_role",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, default="active")
    revision: Mapped[int] = mapped_column(Integer, default=1)


class FinanceRoleDestination(Base):
    __tablename__ = "finance_role_destination"
    __table_args__ = (
        UniqueConstraint("tenant_id", "role"),
        ForeignKeyConstraint(
            ["tenant_id", "account_id"],
            ["subledger_account.tenant_id", "subledger_account.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    role: Mapped[str] = mapped_column(String)
    account_id: Mapped[str] = mapped_column(String)


class FinanceState(Base):
    __tablename__ = "finance_state"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), unique=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)


class LedgerEntry(Base):
    __tablename__ = "ledger_entry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "account_id"],
            ["subledger_account.tenant_id", "subledger_account.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    posting_group_id: Mapped[str] = mapped_column(String, index=True, default="")
    account_id: Mapped[str] = mapped_column(String, index=True)
    account_record: Mapped[SubledgerAccount] = relationship(
        lazy="joined", innerjoin=True, viewonly=True
    )

    @hybrid_property
    def account(self) -> str:
        """Operational role derived from the account, never a second stored code."""
        return self.account_record.role

    @account.inplace.expression
    @classmethod
    def _account_expression(cls):
        return (
            select(SubledgerAccount.role)
            .where(
                SubledgerAccount.id == cls.account_id,
                SubledgerAccount.tenant_id == cls.tenant_id,
            )
            .scalar_subquery()
        )

    party_id: Mapped[str | None] = mapped_column(ForeignKey("party.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String, default="EUR")
    debit_credit: Mapped[str] = mapped_column(String)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("document.id"))
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_record.id"))


class LedgerReversal(Base):
    """Durable correction evidence linking one posting group to its exact inverse."""

    __tablename__ = "ledger_reversal"
    __table_args__ = (
        UniqueConstraint("original_posting_group_id"),
        UniqueConstraint("reversing_posting_group_id"),
        UniqueConstraint("tenant_id", "request_fingerprint"),
        CheckConstraint(
            "original_posting_group_id <> reversing_posting_group_id",
            name="ck_ledger_reversal_groups_distinct",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    original_posting_group_id: Mapped[str] = mapped_column(String, index=True)
    reversing_posting_group_id: Mapped[str] = mapped_column(String, index=True)
    reason: Mapped[str] = mapped_column(Text)
    reversed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    actor_context: Mapped[str] = mapped_column(Text, default="{}")
    request_fingerprint: Mapped[str] = mapped_column(String)


class SettlementAllocation(Base):
    __tablename__ = "settlement_allocation"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    payment_ledger_entry_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_entry.id"), index=True
    )
    invoice_ledger_entry_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_entry.id"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String, default="EUR")
    allocated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Fact(Base):
    __tablename__ = "fact"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_fingerprint"),
        Index("ix_fact_tenant_recorded", "tenant_id", "recorded_at"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    subject_type: Mapped[str] = mapped_column(String)
    subject_id: Mapped[str] = mapped_column(String)
    predicate: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    # When Reality wrote the Fact down, as opposed to when it was true. A Storyline
    # chapter reads "Facts recorded after its marker" (spec 182, FR-005); business
    # time cannot answer that because Facts are routinely backdated.
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_record.id"))
    request_fingerprint: Mapped[str | None] = mapped_column(String, default=None)
    interpretation_rule_id: Mapped[str | None] = mapped_column(
        ForeignKey("interpretation_rule.id"), default=None, index=True
    )


class RealityGap(Base):
    __tablename__ = "reality_gap"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_fingerprint"),
        CheckConstraint("revision >= 1", name="ck_reality_gap_revision"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    intended_use: Mapped[str] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String, index=True)
    origin_reference: Mapped[str | None] = mapped_column(String, default=None)
    status: Mapped[str] = mapped_column(String, default="open", index=True)
    destination: Mapped[str | None] = mapped_column(String, default=None, index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    request_fingerprint: Mapped[str] = mapped_column(String)
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class RealityGapEntry(Base):
    __tablename__ = "reality_gap_entry"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    gap_id: Mapped[str] = mapped_column(ForeignKey("reality_gap.id"), index=True)
    entry_type: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    actor_type: Mapped[str] = mapped_column(String, default="human")
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class InterpretationRule(Base):
    __tablename__ = "interpretation_rule"
    __table_args__ = (
        UniqueConstraint("tenant_id", "logical_name", "version"),
        CheckConstraint("version >= 1", name="ck_interpretation_rule_version"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    gap_id: Mapped[str] = mapped_column(ForeignKey("reality_gap.id"), index=True)
    logical_name: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="draft", index=True)
    source_system: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    value_path: Mapped[str] = mapped_column(String)
    conditions_mode: Mapped[str] = mapped_column(String, default="all")
    conditions: Mapped[str] = mapped_column(Text, default="[]")
    iteration_path: Mapped[str | None] = mapped_column(String, default=None)
    source_line_id_path: Mapped[str | None] = mapped_column(String, default=None)
    output_mode: Mapped[str] = mapped_column(String, default="source_path")
    output_path: Mapped[str | None] = mapped_column(String, default=None)
    output_scope: Mapped[str] = mapped_column(String, default="source")
    constant_value: Mapped[str | None] = mapped_column(Text, default=None)
    predicate: Mapped[str] = mapped_column(String)
    subject_type: Mapped[str] = mapped_column(String, default="commitment")
    subject_resolver: Mapped[str] = mapped_column(
        String, default="source_document_commitments"
    )
    value_type: Mapped[str] = mapped_column(String, default="string")
    allowed_values: Mapped[str] = mapped_column(Text, default="[]")
    value_mapping: Mapped[str] = mapped_column(Text, default="{}")
    normalization: Mapped[str] = mapped_column(Text, default="[]")
    observed_at_mode: Mapped[str] = mapped_column(String, default="source_received_at")
    observed_at_path: Mapped[str | None] = mapped_column(String, default=None)
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    activated_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    disabled_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class RuleInterpretationOutcome(Base):
    __tablename__ = "rule_interpretation_outcome"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "rule_id",
            "source_record_id",
            "element_key",
            name="uq_rule_outcome_source_element",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    rule_id: Mapped[str] = mapped_column(
        ForeignKey("interpretation_rule.id"), index=True
    )
    source_record_id: Mapped[str] = mapped_column(
        ForeignKey("source_record.id"), index=True
    )
    element_key: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, index=True)
    fact_id: Mapped[str | None] = mapped_column(ForeignKey("fact.id"), default=None)
    detail: Mapped[str] = mapped_column(Text, default="{}")
    evaluated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ChangeProposal(Base):
    """Auditable mutation proposed for approval before execution.

    The physical table name remains stable so existing tenant databases do not
    lose their audit trail during the terminology correction.
    """

    __tablename__ = "action"
    __table_args__ = (UniqueConstraint("tenant_id", "id", name="uq_action_tenant_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    actor_type: Mapped[str] = mapped_column(String, default="human")
    status: Mapped[str] = mapped_column(String, default="executed")
    input: Mapped[str] = mapped_column(Text, default="{}")
    output: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    # An approval boundary exists to record who crossed it. Both stay nullable:
    # decisions settled before this existed cannot be reconstructed, and a
    # decision taken without a signed-in principal has no user to name.
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    decided_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), index=True, default=None
    )


# Transitional import alias for older adapters. New domain code uses
# ChangeProposal; this can be removed after downstream integrations migrate.
Action = ChangeProposal


class BusinessEvent(Base):
    __tablename__ = "business_event"
    __table_args__ = (UniqueConstraint("tenant_id", "sequence"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    sequence: Mapped[int] = mapped_column(BigInteger)
    event_type: Mapped[str] = mapped_column(String, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    subject_type: Mapped[str] = mapped_column(String)
    subject_id: Mapped[str] = mapped_column(String, index=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    source_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_record.id"), default=None
    )
    action_id: Mapped[str | None] = mapped_column(ForeignKey("action.id"), default=None)
    causation_id: Mapped[str | None] = mapped_column(
        ForeignKey("business_event.id"), default=None
    )
    correlation_id: Mapped[str | None] = mapped_column(String, default=None)


class ProjectionRow(Base):
    __tablename__ = "projection_row"
    __table_args__ = (UniqueConstraint("tenant_id", "projection_name", "record_key"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    projection_name: Mapped[str] = mapped_column(String, index=True)
    projection_version: Mapped[int] = mapped_column(Integer, default=1)
    record_key: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[str] = mapped_column(Text)
    source_event_sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ProjectionCheckpoint(Base):
    __tablename__ = "projection_checkpoint"
    __table_args__ = (UniqueConstraint("tenant_id", "projection_name"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    projection_name: Mapped[str] = mapped_column(String, index=True)
    projection_version: Mapped[int] = mapped_column(Integer, default=1)
    last_event_sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String, default="ready")
    error: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ChatSession(Base):
    __tablename__ = "chat_session"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class AISettings(Base):
    __tablename__ = "ai_settings"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String, default="local")
    model: Mapped[str] = mapped_column(String, default="")
    base_url: Mapped[str] = mapped_column(String, default="https://api.openai.com/v1")
    api_key_secret_id: Mapped[str | None] = mapped_column(
        ForeignKey("secret.id"), default=None
    )
    # Kept temporarily so installations can lazily move an existing key into the
    # generic vault without exposing or manually re-entering it.
    encrypted_api_key: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Secret(Base):
    """Tenant-scoped encrypted material; consumers retain only this opaque ID."""

    __tablename__ = "secret"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    purpose: Mapped[str] = mapped_column(String, index=True)
    provider: Mapped[str] = mapped_column(String, default="")
    label: Mapped[str] = mapped_column(String)
    ciphertext: Mapped[str] = mapped_column(Text)
    nonce: Mapped[str] = mapped_column(Text)
    encrypted_data_key: Mapped[str] = mapped_column(Text)
    key_version: Mapped[int] = mapped_column(Integer, default=1)
    fingerprint: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    rotated_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class SecretAuditEvent(Base):
    """Metadata-only audit trail. Secret values are never written here."""

    __tablename__ = "secret_audit_event"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    secret_id: Mapped[str] = mapped_column(ForeignKey("secret.id"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class MCPAccessToken(Base):
    __tablename__ = "mcp_access_token"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    token_prefix: Mapped[str] = mapped_column(String, index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    allowed_tools: Mapped[str] = mapped_column(Text, default='["*"]')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class ChatMessage(Base):
    __tablename__ = "chat_message"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_session.id"))
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


def init_db() -> None:
    """Bring the configured database to the current Alembic revision."""
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))
    command.upgrade(config, "head")


# Register infrastructure metadata even when callers import only Base.
# Register private analytics configuration with the shared metadata.
from reality.db import analytics as _analytics_models  # noqa: F401
from reality.db import company_setup as _company_setup  # noqa: F401
from reality.db import components as _components  # noqa: F401
from reality.db import demo_data as _demo_data  # noqa: F401
from reality.db import finance_references as _finance_references  # noqa: F401
from reality.db import opening as _opening  # noqa: F401
from reality.db import scheduled_jobs as _scheduled_jobs  # noqa: F401
from reality.db import source_mappings as _source_mappings  # noqa: F401
from reality.db import target_mappings as _target_mappings  # noqa: F401


def index_foreign_keys(metadata: MetaData) -> list[Index]:
    """Give the first column of every foreign key an index unless one already leads with it.

    Spec 181: a read or a delete of a referenced row must not scan its referrers. Without
    this, matching one payment walked every ledger entry of the company for its document
    (197 ms per payment at 10,000 orders), and removing a company took half an hour in
    foreign-key checks (`business_event.causation_id`, every `source_record_id`). The rule
    is applied once, here, after every model module has registered its tables, so the
    test schema and the migrations describe the same indexes. Migration 0059 creates
    them with the same names for existing databases.
    """
    created: list[Index] = []
    for table in metadata.sorted_tables:
        covered = {next(iter(index.columns)).name for index in table.indexes}
        for constraint in table.constraints:
            columns = list(getattr(constraint, "columns", []))
            if columns and isinstance(
                constraint, (PrimaryKeyConstraint, UniqueConstraint)
            ):
                covered.add(columns[0].name)
        for foreign_key in table.foreign_key_constraints:
            column = next(iter(foreign_key.columns))
            if column.name in covered or column.index:
                continue
            covered.add(column.name)
            created.append(Index(f"ix_{table.name}_{column.name}", column))
    return created


FOREIGN_KEY_INDEXES = index_foreign_keys(Base.metadata)
