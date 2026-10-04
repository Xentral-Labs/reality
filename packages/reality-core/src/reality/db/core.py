from __future__ import annotations

import hashlib
import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

from alembic import command
from alembic.config import Config
from sqlalchemy import (
    DDL,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    FetchedValue,
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
        PrimaryKeyConstraint("tenant_id", "id"),
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
    id: Mapped[str] = mapped_column(String)
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
        PrimaryKeyConstraint("tenant_id", "id"),
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
    id: Mapped[str] = mapped_column(String)
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
        PrimaryKeyConstraint("tenant_id", "id"),
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
    id: Mapped[str] = mapped_column(String)
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
    __table_args__ = (
        CheckConstraint(
            "authentication_method IN ('email', 'local_os')",
            name="ck_app_user_authentication_method",
        ),
    )
    authentication_method: Mapped[str] = mapped_column(
        String, default="email", server_default="email"
    )
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


class JourneyProposal(Base):
    """Account-scoped product feedback, never tenant business state."""

    __tablename__ = "journey_proposal"
    __table_args__ = (
        CheckConstraint(
            "status IN ('proposed', 'under_review', 'planned', 'in_progress', "
            "'available', 'declined', 'out_of_scope')",
            name="ck_journey_proposal_status",
        ),
        CheckConstraint(
            "process_area IN ('orders', 'availability', 'payments', 'shipping', "
            "'invoicing', 'returns', 'purchasing', 'receiving', 'payables', "
            "'warehouse', 'products', 'commerce', 'b2b', 'finance', "
            "'master_data', 'sources', 'time', 'combined')",
            name="ck_journey_proposal_process_area",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    creator_account_id: Mapped[str] = mapped_column(
        ForeignKey("app_user.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    business_question: Mapped[str] = mapped_column(String(1000))
    expected_outcome: Mapped[str] = mapped_column(String(2000))
    process_area: Mapped[str] = mapped_column(String(32), index=True)
    business_context: Mapped[str] = mapped_column(String(1000), default="")
    normalized_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(
        String(24), default="proposed", server_default="proposed", index=True
    )
    public_rationale: Mapped[str] = mapped_column(String(2000), default="")
    available_journey_id: Mapped[str | None] = mapped_column(String(3), default=None)
    reviewed_by_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class JourneyProposalVote(Base):
    __tablename__ = "journey_proposal_vote"
    __table_args__ = (
        UniqueConstraint(
            "proposal_id", "account_id", name="uq_journey_proposal_vote_account"
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("journey_proposal.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
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
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "user_id"),
        CheckConstraint(
            "role IN ('owner', 'member')", name="ck_tenant_membership_role"
        ),
        CheckConstraint(
            "status IN ('active', 'removed')", name="ck_tenant_membership_status"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    role: Mapped[str] = mapped_column(String, default="owner")
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SecurityAuditEvent(Base):
    __tablename__ = "security_audit_event"
    # Not keyed by company, unlike every other table that carries a `tenant_id`
    # (spec 181 FR-005). A signup, an admission and a failed login happen before
    # there is a company, and this is where they are written down, so the column
    # is nullable and cannot be part of a key. It is therefore the one
    # company-bearing table that stays unpartitionable by company — which is
    # right, because it is not a company's table.
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
        PrimaryKeyConstraint("tenant_id", "id"),
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
    id: Mapped[str] = mapped_column(String)
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
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "invitation_id"],
            ["company_invitation.tenant_id", "company_invitation.id"],
        ),
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
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    invitation_id: Mapped[str] = mapped_column()
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
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "payment_term_id"],
            ["payment_term.tenant_id", "payment_term.id"],
        ),
        UniqueConstraint("tenant_id", "id", name="uq_party_tenant_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    accounting_code: Mapped[str] = mapped_column(String, default="")
    payment_term_id: Mapped[str | None] = mapped_column(default=None)
    default_currency: Mapped[str] = mapped_column(String, default="EUR")
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    tax_identifier: Mapped[str] = mapped_column(String, default="")


class PartyRole(Base):
    __tablename__ = "party_role"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "default_location_id"],
            ["location.tenant_id", "location.id"],
        ),
        UniqueConstraint("tenant_id", "party_id", "role"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column(String)
    default_location_id: Mapped[str | None] = mapped_column(default=None)


class PartyEmailAddress(Base):
    __tablename__ = "party_email_address"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "party_id",
            "normalized_email",
            name="uq_party_email_address_party_email",
        ),
        CheckConstraint("length(label) <= 80", name="ck_party_email_address_label"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String(320))
    normalized_email: Mapped[str] = mapped_column(String(320), index=True)
    label: Mapped[str] = mapped_column(String(80), default="")


class PartyHold(Base):
    __tablename__ = "party_hold"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column()
    hold_type: Mapped[str] = mapped_column(String)
    reason_code: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String, default="human")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class Item(Base):
    __tablename__ = "item"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "default_location_id"],
            ["location.tenant_id", "location.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    sku: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String, default="pcs")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    item_type: Mapped[str] = mapped_column(String, default="stocked")
    tracking_type: Mapped[str] = mapped_column(String, default="none")
    default_location_id: Mapped[str | None] = mapped_column(default=None)
    purchase_unit: Mapped[str] = mapped_column(String, default="pcs")
    conversion_factor: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)


class Location(Base):
    __tablename__ = "location"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "parent_location_id"],
            ["location.tenant_id", "location.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String, default="warehouse")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_location_id: Mapped[str | None] = mapped_column(default=None)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    allows_stock: Mapped[bool] = mapped_column(Boolean, default=True)


class DeliveryRule(Base):
    """How a customer or one order wants to be delivered (spec 306).

    partial_allowed, ship_complete or no_backorders, as a person stated it with
    a reason. An order's rule wins over its customer's; without either, partial
    deliveries are allowed. Each statement is a version of one source stream per
    subject (spec 320 pattern); the row names the one in force. Whether an order
    is complete is read from its promises, stock and reservations, never stored.
    """

    __tablename__ = "delivery_rule"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        CheckConstraint(
            "(party_id IS NULL) <> (document_id IS NULL)",
            name="ck_delivery_rule_one_subject",
        ),
        CheckConstraint(
            "rule IN ('partial_allowed', 'ship_complete', 'no_backorders')",
            name="ck_delivery_rule_rule",
        ),
        CheckConstraint("btrim(reason) <> ''", name="ck_delivery_rule_reason"),
        Index(
            "uq_delivery_rule_party",
            "tenant_id",
            "party_id",
            unique=True,
            postgresql_where=text("party_id IS NOT NULL"),
        ),
        Index(
            "uq_delivery_rule_document",
            "tenant_id",
            "document_id",
            unique=True,
            postgresql_where=text("document_id IS NOT NULL"),
        ),
        Index("ix_delivery_rule_source_record_id", "tenant_id", "source_record_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str | None] = mapped_column(default=None)
    document_id: Mapped[str | None] = mapped_column(default=None)
    rule: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class StockCount(Base):
    """A count of one location (spec 307): what a person counted, as stated.

    The count is kept as one version of its source stream; its lines carry what
    was counted and when. The book quantity at the counting time is read from
    the movements, never stored; the adjustments that posted the differences
    are linked from the lines.
    """

    __tablename__ = "stock_count"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["location.tenant_id", "location.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        Index("ix_stock_count_location_id", "tenant_id", "location_id"),
        Index("uq_stock_count_source", "tenant_id", "source_record_id", unique=True),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    location_id: Mapped[str] = mapped_column()
    note: Mapped[str] = mapped_column(Text, default="")
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class StockCountLine(Base):
    """One counted item, and its lot where tracked, with when it was counted."""

    __tablename__ = "stock_count_line"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "stock_count_id"],
            ["stock_count.tenant_id", "stock_count.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "lot_id"],
            ["lot.tenant_id", "lot.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "movement_id"],
            ["movement.tenant_id", "movement.id"],
        ),
        CheckConstraint(
            "counted_quantity >= 0", name="ck_stock_count_line_counted_quantity"
        ),
        Index(
            "uq_stock_count_line_item_lot",
            "tenant_id",
            "stock_count_id",
            "item_id",
            text("coalesce(lot_id, '')"),
            unique=True,
        ),
        Index("ix_stock_count_line_movement_id", "tenant_id", "movement_id"),
        Index("ix_stock_count_line_item_id", "tenant_id", "item_id"),
        Index("ix_stock_count_line_lot_id", "tenant_id", "lot_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    stock_count_id: Mapped[str] = mapped_column()
    item_id: Mapped[str] = mapped_column()
    lot_id: Mapped[str | None] = mapped_column(default=None)
    counted_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    counted_at: Mapped[datetime] = mapped_column(UTCDateTime)
    movement_id: Mapped[str | None] = mapped_column(default=None)


class ExternalStockStatement(Base):
    """Stock someone outside states for an item at a location, as stated (spec 344).

    A 3PL's report or a shop's stock level. It never moves stock: the latest
    statement per item and location is compared, when read, with what Reality's
    movements hold there at the stated time, and a difference is a finding.
    """

    __tablename__ = "external_stock_statement"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id", "item_id"], ["item.tenant_id", "item.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["location.tenant_id", "location.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reporter_party_id"], ["party.tenant_id", "party.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        CheckConstraint("quantity >= 0", name="ck_external_stock_statement_quantity"),
        Index(
            "ix_external_stock_statement_item_location",
            "tenant_id",
            "item_id",
            "location_id",
            "stated_at",
        ),
        Index("ix_external_stock_statement_location_id", "tenant_id", "location_id"),
        Index(
            "ix_external_stock_statement_reporter_party_id",
            "tenant_id",
            "reporter_party_id",
        ),
        Index(
            "ix_external_stock_statement_source_record_id",
            "tenant_id",
            "source_record_id",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    item_id: Mapped[str] = mapped_column()
    location_id: Mapped[str] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    stated_at: Mapped[datetime] = mapped_column(UTCDateTime)
    reporter_party_id: Mapped[str | None] = mapped_column(default=None)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CustomerItemNumber(Base):
    """A customer's own number, and name, for one of our items (spec 308).

    Per customer one number names one item; an item may have several numbers
    there. Lines are matched on the normalized key, ignoring case and spaces.
    Each statement is a version of one source stream per customer and number
    (spec 320 pattern); the row names the one in force.
    """

    __tablename__ = "customer_item_number"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id", "party_id", "match_key", name="uq_customer_item_number_key"
        ),
        CheckConstraint(
            "btrim(customer_item_number) <> ''", name="ck_customer_item_number_number"
        ),
        Index("ix_customer_item_number_item_id", "tenant_id", "item_id"),
        Index(
            "ix_customer_item_number_source_record_id", "tenant_id", "source_record_id"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column()
    item_id: Mapped[str] = mapped_column()
    customer_item_number: Mapped[str] = mapped_column(String)
    match_key: Mapped[str] = mapped_column(String)
    customer_item_name: Mapped[str] = mapped_column(String, default="")
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SupplierItemNumber(Base):
    """A supplier's own number, and name, for one of our items (spec 345).

    Per supplier one number names one item; an item may have several numbers
    there, and each supplier has its own. Lines are matched on the normalized
    key, ignoring case and spaces. Each statement is a version of one source
    stream per supplier and number (spec 320 pattern); the row names the one in
    force.
    """

    __tablename__ = "supplier_item_number"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id", "party_id", "match_key", name="uq_supplier_item_number_key"
        ),
        CheckConstraint(
            "btrim(supplier_item_number) <> ''", name="ck_supplier_item_number_number"
        ),
        Index("ix_supplier_item_number_item_id", "tenant_id", "item_id"),
        Index(
            "ix_supplier_item_number_source_record_id", "tenant_id", "source_record_id"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column()
    item_id: Mapped[str] = mapped_column()
    supplier_item_number: Mapped[str] = mapped_column(String)
    match_key: Mapped[str] = mapped_column(String)
    supplier_item_name: Mapped[str] = mapped_column(String, default="")
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ItemReorderPoint(Base):
    """The stock level at which a company reorders an item at a location (spec 302).

    A company statement, kept as stated in the item's stock unit. Whether it is
    reached is read from stock, reservations and supplier promises each time;
    nothing about it is stored. Each statement is a version of one source
    stream per item and location (spec 320); the row names the one in force.
    """

    __tablename__ = "item_reorder_point"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["location.tenant_id", "location.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "item_id",
            "location_id",
            name="uq_item_reorder_point_item_location",
        ),
        CheckConstraint(
            "reorder_point >= 0 AND reorder_quantity > 0",
            name="ck_item_reorder_point_values",
        ),
        Index("ix_item_reorder_point_location_id", "tenant_id", "location_id"),
        Index(
            "ix_item_reorder_point_source_record_id", "tenant_id", "source_record_id"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    item_id: Mapped[str] = mapped_column()
    location_id: Mapped[str] = mapped_column()
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    source_record_id: Mapped[str] = mapped_column(String)


class PartyMerge(Base):
    """One business partner stated to be a duplicate of another (spec 339).

    Append-only: the duplicate's documents, promises and ledger entries keep
    naming it, and reads that answer for the survivor add them at read time.
    A duplicate is merged once and never becomes a survivor itself.
    """

    __tablename__ = "party_merge"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "duplicate_party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "surviving_party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id", "duplicate_party_id", name="uq_party_merge_duplicate"
        ),
        CheckConstraint(
            "duplicate_party_id <> surviving_party_id",
            name="ck_party_merge_distinct",
        ),
        Index("ix_party_merge_surviving_party_id", "tenant_id", "surviving_party_id"),
        Index("ix_party_merge_source_record_id", "tenant_id", "source_record_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    duplicate_party_id: Mapped[str] = mapped_column()
    surviving_party_id: Mapped[str] = mapped_column()
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    source_record_id: Mapped[str] = mapped_column()


class KitComponent(Base):
    """One component of a kit and how many of it one kit takes (spec 333).

    A kit is a stocked item whose units come only from an assembly of its
    components. The components are stated once, in the component's stock unit,
    with an optional share of the kit's price; what a location can build and
    how a kit line splits are read from these rows each time, never stored.
    """

    __tablename__ = "kit_component"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "kit_item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "component_item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "kit_item_id",
            "component_item_id",
            name="uq_kit_component_kit_component",
        ),
        CheckConstraint(
            "quantity > 0 AND (share IS NULL OR (share >= 0 AND share <= 1))"
            " AND kit_item_id <> component_item_id",
            name="ck_kit_component_values",
        ),
        Index("ix_kit_component_component_item_id", "tenant_id", "component_item_id"),
        Index("ix_kit_component_source_record_id", "tenant_id", "source_record_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    kit_item_id: Mapped[str] = mapped_column()
    component_item_id: Mapped[str] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    share: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), default=None)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    source_record_id: Mapped[str] = mapped_column(String)


class SourceSystem(Base):
    __tablename__ = "source_system"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id", name="uq_source_system_tenant_id"),
    )
    id: Mapped[str] = mapped_column(String)
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
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_system_id"],
            ["source_system.tenant_id", "source_system.id"],
        ),
        UniqueConstraint("tenant_id", "source_system_id", "source_type"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_system_id: Mapped[str] = mapped_column()
    source_type: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SourceStream(Base):
    __tablename__ = "source_stream"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "current_source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "source_type",
            "external_id",
            name="uq_source_stream_identity",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_system: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    current_source_record_id: Mapped[str | None] = mapped_column(default=None)


class SourceArtifact(Base):
    __tablename__ = "source_artifact"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "sha256", name="uq_source_artifact_content"),
    )
    id: Mapped[str] = mapped_column(String)
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
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_artifact_id"],
            ["source_artifact.tenant_id", "source_artifact.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "supersedes_source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
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
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_system: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    payload: Mapped[str] = mapped_column(Text)
    payload_hash: Mapped[str] = mapped_column(String(64))
    source_artifact_id: Mapped[str | None] = mapped_column(default=None)
    version: Mapped[int] = mapped_column(Integer)
    source_version_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, default=None
    )
    supersedes_source_record_id: Mapped[str | None] = mapped_column(default=None)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ImportJob(Base):
    __tablename__ = "import_job"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_import_job_source_record"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_record_id: Mapped[str] = mapped_column()
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
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "import_job_id"],
            ["import_job.tenant_id", "import_job.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "import_job_id",
            "attempt",
            name="uq_interpretation_outcome_attempt",
        ),
        CheckConstraint("attempt >= 0", name="ck_interpretation_outcome_attempt"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_record_id: Mapped[str] = mapped_column()
    import_job_id: Mapped[str] = mapped_column()
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
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "outcome_id"],
            ["interpretation_outcome.tenant_id", "interpretation_outcome.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "outcome_id",
            "record_type",
            "record_id",
            name="uq_interpretation_record_reference",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    outcome_id: Mapped[str] = mapped_column()
    record_type: Mapped[str] = mapped_column(String)
    record_id: Mapped[str] = mapped_column(String)


class PaymentTerm(Base):
    __tablename__ = "payment_term"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "code"),
    )
    id: Mapped[str] = mapped_column(String)
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
    requires_prepayment: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(default=None)


class PriceList(Base):
    __tablename__ = "price_list"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "code"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    direction: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(default=None)


class PriceListEntry(Base):
    __tablename__ = "price_list_entry"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "price_list_id"],
            ["price_list.tenant_id", "price_list.id"],
        ),
        UniqueConstraint("tenant_id", "price_list_id", "item_id", "min_quantity"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    price_list_id: Mapped[str] = mapped_column()
    item_id: Mapped[str] = mapped_column()
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    unit: Mapped[str] = mapped_column(String)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    source_record_id: Mapped[str | None] = mapped_column(default=None)


class PartyPriceList(Base):
    __tablename__ = "party_price_list"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "price_list_id"],
            ["price_list.tenant_id", "price_list.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        UniqueConstraint("tenant_id", "party_id", "price_list_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column()
    price_list_id: Mapped[str] = mapped_column()
    priority: Mapped[int] = mapped_column(Integer, default=100)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class PartyGroup(Base):
    __tablename__ = "party_group"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "code"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    group_type: Mapped[str] = mapped_column(String, default="pricing")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_record_id: Mapped[str | None] = mapped_column(default=None)


class PartyGroupMember(Base):
    __tablename__ = "party_group_member"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "party_group_id"],
            ["party_group.tenant_id", "party_group.id"],
        ),
        UniqueConstraint("tenant_id", "party_group_id", "party_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_group_id: Mapped[str] = mapped_column()
    party_id: Mapped[str] = mapped_column()
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class PartyGroupPriceList(Base):
    __tablename__ = "party_group_price_list"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_group_id"],
            ["party_group.tenant_id", "party_group.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "price_list_id"],
            ["price_list.tenant_id", "price_list.id"],
        ),
        UniqueConstraint("tenant_id", "party_group_id", "price_list_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_group_id: Mapped[str] = mapped_column()
    price_list_id: Mapped[str] = mapped_column()
    priority: Mapped[int] = mapped_column(Integer, default=100)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class Document(Base):
    __tablename__ = "document"
    # The order link's server default is not fetched back (see order_document_id).
    __mapper_args__: ClassVar[dict[str, Any]] = {"eager_defaults": False}
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "ship_to_party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "payment_term_id"],
            ["payment_term.tenant_id", "payment_term.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "order_document_id"],
            ["document.tenant_id", "document.id"],
            name="fk_document_order_document",
        ),
        Index("ix_document_order_document_id", "tenant_id", "order_document_id"),
        UniqueConstraint("tenant_id", "id", name="uq_document_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "source_record_id",
            "type",
            name="uq_document_source_type",
        ),
        # Sixteen analysis objects read this one table and tell themselves apart by
        # `type`, so every one of them paid for the rows belonging to the other
        # fifteen. The day is the third column because the questions that select a
        # type almost always bound or group by it as well.
        Index("ix_document_tenant_type_date", "tenant_id", "type", "document_date"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_record_id: Mapped[str | None] = mapped_column()
    type: Mapped[str] = mapped_column(String)
    number: Mapped[str] = mapped_column(String)
    party_id: Mapped[str | None] = mapped_column()
    currency: Mapped[str] = mapped_column(String, default="EUR")
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str] = mapped_column(String, default="open")
    # A day, stored as a day: the register orders and filters on it, analysis groups
    # by it, and an impossible date cannot reach the column at all. Callers and every
    # transport still speak ISO text; `reality.domain.calendar` is the one crossing.
    document_date: Mapped[date | None] = mapped_column(Date, default=None)
    ordered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    requested_delivery_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, default=None
    )
    customer_reference: Mapped[str] = mapped_column(String, default="")
    sales_channel: Mapped[str] = mapped_column(String, default="")
    payment_term_id: Mapped[str | None] = mapped_column(default=None)
    ship_to_party_id: Mapped[str | None] = mapped_column(default=None)
    # The sales order a down-payment or pro-forma invoice is for (spec 299): the
    # document is for the order, not for any of its lines, so no line bills one.
    # Deferred, and left out of an INSERT that does not set it, so documents on
    # a schema from before 0105 (the historical migration tests) still load and
    # insert; readers that need the link select the column itself.
    order_document_id: Mapped[str | None] = mapped_column(
        server_default=FetchedValue(), deferred=True
    )


class DownPaymentOffset(Base):
    """A down payment a final invoice states it deducts (spec 299)."""

    __tablename__ = "down_payment_offset"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "final_invoice_document_id"],
            ["document.tenant_id", "document.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "down_payment_document_id"],
            ["document.tenant_id", "document.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        CheckConstraint("amount > 0", name="ck_down_payment_offset_amount"),
        Index(
            "ix_down_payment_offset_final_invoice_document_id",
            "tenant_id",
            "final_invoice_document_id",
        ),
        Index(
            "ix_down_payment_offset_down_payment_document_id",
            "tenant_id",
            "down_payment_document_id",
        ),
        Index(
            "ix_down_payment_offset_source_record_id", "tenant_id", "source_record_id"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    final_invoice_document_id: Mapped[str] = mapped_column()
    down_payment_document_id: Mapped[str] = mapped_column()
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    source_record_id: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class DocumentLine(Base):
    __tablename__ = "document_line"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "price_list_entry_id"],
            ["price_list_entry.tenant_id", "price_list_entry.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "billed_document_line_id"],
            ["document_line.tenant_id", "document_line.id"],
        ),
        UniqueConstraint("tenant_id", "id", name="uq_document_line_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "document_id",
            "source_line_id",
            name="uq_document_line_source_line",
        ),
        # Eight line objects are told apart by the type of their document, which the
        # compiler checks with an EXISTS back to the parent. That lookup, and every
        # line-of-document join, starts here.
        Index("ix_document_line_tenant_document", "tenant_id", "document_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    document_id: Mapped[str] = mapped_column()
    source_line_id: Mapped[str | None] = mapped_column(String)
    item_id: Mapped[str | None] = mapped_column()
    sku: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default="")
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    # Null states that the source gave no price (spec 314); nothing is invented.
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    promised_at: Mapped[str] = mapped_column(String, default="")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    unit: Mapped[str] = mapped_column(String, default="pcs")
    requested_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    line_type: Mapped[str] = mapped_column(String, default="item")
    price_list_entry_id: Mapped[str | None] = mapped_column(default=None)
    # Which agreed line this billed line settles. Null is a statement: the line
    # bills nothing an order promised, such as freight or a one-off service.
    billed_document_line_id: Mapped[str | None] = mapped_column(default=None)


class DunningNotice(Base):
    """One immutable, stated reminder of one customer's overdue invoices."""

    __tablename__ = "dunning_notice"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"], ["document.tenant_id", "document.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"], ["party.tenant_id", "party.id"]
        ),
        UniqueConstraint("tenant_id", "document_id"),
        CheckConstraint("level BETWEEN 1 AND 3", name="ck_dunning_notice_level"),
        CheckConstraint("fee_amount >= 0", name="ck_dunning_notice_fee_nonnegative"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    document_id: Mapped[str] = mapped_column(String)
    source_record_id: Mapped[str | None] = mapped_column(String, default=None)
    party_id: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    notice_date: Mapped[date] = mapped_column(Date)
    level: Mapped[int] = mapped_column(Integer)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class DunningNoticeInvoice(Base):
    """Shortest opaque link from one reminder to one reminded invoice."""

    __tablename__ = "dunning_notice_invoice"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "notice_id"],
            ["dunning_notice.tenant_id", "dunning_notice.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["document.tenant_id", "document.id"]
        ),
        UniqueConstraint("tenant_id", "notice_id", "invoice_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    notice_id: Mapped[str] = mapped_column(String)
    invoice_id: Mapped[str] = mapped_column(String)


class DunningScheduleLevel(Base):
    """The company's stated waiting period and fixed fee for one dunning level.

    Configuration, not Reality: every dunning run reads it to decide an item's
    next level and a notice's fee. A notice keeps the fee it was recorded with,
    so changing the schedule never rewrites history.
    """

    __tablename__ = "dunning_schedule_level"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "level", name="uq_dunning_schedule_level_level"),
        CheckConstraint("level BETWEEN 1 AND 3", name="ck_dunning_schedule_level_level"),
        CheckConstraint("wait_days >= 0", name="ck_dunning_schedule_level_wait_days"),
        CheckConstraint("fee_amount >= 0", name="ck_dunning_schedule_level_fee"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    level: Mapped[int] = mapped_column(Integer)
    # Level 1: days overdue; levels 2 and 3: days since the item's last notice.
    wait_days: Mapped[int] = mapped_column(Integer)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    source_record_id: Mapped[str] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CollectionHandover(Base):
    """A confirmed decision to hand a customer's dunned items to collection.

    Reality, append-only. Whether an item is in collection is read from its
    link below; the invoice carries no field for it.
    """

    __tablename__ = "collection_handover"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"], ["party.tenant_id", "party.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_collection_handover_source"
        ),
        CheckConstraint("btrim(reason) <> ''", name="ck_collection_handover_reason"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column(String)
    handover_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(Text)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CollectionHandoverInvoice(Base):
    """Shortest opaque link from one handover to one invoice; an invoice goes once."""

    __tablename__ = "collection_handover_invoice"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "handover_id"],
            ["collection_handover.tenant_id", "collection_handover.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["document.tenant_id", "document.id"]
        ),
        UniqueConstraint(
            "tenant_id", "invoice_id", name="uq_collection_handover_invoice_invoice"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    handover_id: Mapped[str] = mapped_column(String)
    invoice_id: Mapped[str] = mapped_column(String)


class PaymentReturn(Base):
    """A customer payment that came back: a returned direct debit or a chargeback.

    Reality, append-only. It keeps what the bank or provider stated. What it
    caused points back to it, never the other way (spec 322): the ledger
    reversal is the one of the payment's posting group, the fee documents carry
    this return's source record, and which invoices reopened is read from the
    payment's allocations.
    """

    __tablename__ = "payment_return"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "payment_document_id"], ["document.tenant_id", "document.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id", "payment_document_id", name="uq_payment_return_payment"
        ),
        CheckConstraint(
            "kind IN ('direct_debit_return', 'chargeback')", name="ck_payment_return_kind"
        ),
        CheckConstraint("fee_amount >= 0", name="ck_payment_return_fee"),
        CheckConstraint(
            "(fee_amount = 0 AND fee_bearer = 'none') OR "
            "(fee_amount > 0 AND fee_bearer IN ('customer', 'company'))",
            name="ck_payment_return_fee_bearer",
        ),
        CheckConstraint("btrim(reason) <> ''", name="ck_payment_return_reason"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    payment_document_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    reference: Mapped[str] = mapped_column(String, default="")
    returned_on: Mapped[date] = mapped_column(Date)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    fee_bearer: Mapped[str] = mapped_column(String, default="none")
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class PaymentAuthorization(Base):
    """An amount a card or wallet provider authorized for one sales order (spec 336).

    Reality, append-only: what the provider stated, with its expiry. Captures
    against it are their own records; what is left is derived.
    """

    __tablename__ = "payment_authorization"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "order_document_id"], ["document.tenant_id", "document.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "order_document_id",
            "reference",
            name="uq_payment_authorization_reference",
        ),
        CheckConstraint("amount > 0", name="ck_payment_authorization_amount"),
        CheckConstraint(
            "expires_at > authorized_at", name="ck_payment_authorization_expiry"
        ),
        CheckConstraint(
            "btrim(reference) <> ''", name="ck_payment_authorization_reference"
        ),
        Index(
            "ix_payment_authorization_order_document_id",
            "tenant_id",
            "order_document_id",
        ),
        Index(
            "ix_payment_authorization_source_record_id",
            "tenant_id",
            "source_record_id",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    order_document_id: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String(3))
    authorized_at: Mapped[datetime] = mapped_column(UTCDateTime)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    reference: Mapped[str] = mapped_column(String)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class PaymentCapture(Base):
    """An amount captured against an authorization (spec 336); never more than is left."""

    __tablename__ = "payment_capture"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "authorization_id"],
            ["payment_authorization.tenant_id", "payment_authorization.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        CheckConstraint("amount > 0", name="ck_payment_capture_amount"),
        Index(
            "ix_payment_capture_authorization_id", "tenant_id", "authorization_id"
        ),
        Index("ix_payment_capture_source_record_id", "tenant_id", "source_record_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    authorization_id: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    captured_at: Mapped[datetime] = mapped_column(UTCDateTime)
    reference: Mapped[str] = mapped_column(String, default="")
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Commitment(Base):
    __tablename__ = "commitment"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "from_party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "to_party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["location.tenant_id", "location.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "document_line_id"],
            ["document_line.tenant_id", "document_line.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "document_line_id",
            "type",
            name="uq_commitment_document_line_type",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    from_party_id: Mapped[str | None] = mapped_column()
    to_party_id: Mapped[str | None] = mapped_column()
    item_id: Mapped[str | None] = mapped_column()
    location_id: Mapped[str | None] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    status: Mapped[str] = mapped_column(String, default="open")
    document_id: Mapped[str | None] = mapped_column()
    document_line_id: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    priority: Mapped[str] = mapped_column(String, default="normal")
    # Spec 301: the unit the quantity is held in, recorded on purchase promises
    # made since then. None means the line's unit, or the item's without a line.
    unit: Mapped[str | None] = mapped_column(
        String, server_default=FetchedValue(), deferred=True
    )
    __mapper_args__: ClassVar[dict[str, Any]] = {"eager_defaults": False}


class CommitmentRevision(Base):
    """One statement by a counterparty restating a promise.

    Append-only, and a table rather than a column on the promise for one
    reason: a date somebody stated is a received value, and a column would let
    the second statement overwrite the first. The promise keeps the date it was
    made with, which is what makes "originally due" answerable.
    """

    __tablename__ = "commitment_revision"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        CheckConstraint(
            "unit_price IS NULL OR unit_price >= 0",
            name="ck_commitment_revision_unit_price",
        ),
    )
    # The spec 310 price is left out of an INSERT that does not set it, so
    # schemas from before it keep working in the historical migration tests.
    __mapper_args__: ClassVar[dict[str, Any]] = {"eager_defaults": False}
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    commitment_id: Mapped[str] = mapped_column()
    # Both nullable and at least one required: a statement restates the date,
    # the quantity, or both. "Eighty pieces, two weeks later" is one sentence
    # and belongs in one record with one `stated_at`.
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=None)
    stated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    note: Mapped[str] = mapped_column(Text, default="")
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    # Spec 310: the unit price the supplier confirmed, in the order line's unit.
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), server_default=FetchedValue(), deferred=True
    )


class SupplierItemTerms(Base):
    """A supplier's minimum order quantity and order multiple for an item (spec 310).

    Both in the item's purchase unit. Each statement is a version of one source
    stream per supplier and item (spec 320 pattern); the row names the one in
    force. Order review names a quantity that falls short of them.
    """

    __tablename__ = "supplier_item_terms"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id", "party_id"], ["party.tenant_id", "party.id"]),
        ForeignKeyConstraint(["tenant_id", "item_id"], ["item.tenant_id", "item.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id", "party_id", "item_id", name="uq_supplier_item_terms_item"
        ),
        CheckConstraint(
            "minimum_quantity IS NOT NULL OR order_multiple IS NOT NULL",
            name="ck_supplier_item_terms_stated",
        ),
        CheckConstraint(
            "(minimum_quantity IS NULL OR minimum_quantity > 0) "
            "AND (order_multiple IS NULL OR order_multiple > 0)",
            name="ck_supplier_item_terms_positive",
        ),
        Index("ix_supplier_item_terms_item_id", "tenant_id", "item_id"),
        Index("ix_supplier_item_terms_source_record_id", "tenant_id", "source_record_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    party_id: Mapped[str] = mapped_column()
    item_id: Mapped[str] = mapped_column()
    minimum_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    order_multiple: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SupplyAssignment(Base):
    """One append-only statement of what supplier supply is intended to serve."""

    __tablename__ = "supply_assignment"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "supplier_commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "customer_commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reverses_assignment_id"],
            ["supply_assignment.tenant_id", "supply_assignment.id"],
        ),
        CheckConstraint(
            "purpose IN ('customer_demand', 'stock_replenishment')",
            name="ck_supply_assignment_purpose",
        ),
        CheckConstraint("quantity > 0", name="ck_supply_assignment_quantity_positive"),
        CheckConstraint(
            "(purpose = 'customer_demand' AND customer_commitment_id IS NOT NULL) "
            "OR (purpose = 'stock_replenishment' AND customer_commitment_id IS NULL)",
            name="ck_supply_assignment_customer_purpose",
        ),
        CheckConstraint(
            "reverses_assignment_id IS NULL OR reverses_assignment_id <> id",
            name="ck_supply_assignment_not_self_reversal",
        ),
        Index(
            "ix_supply_assignment_tenant_supplier",
            "tenant_id",
            "supplier_commitment_id",
        ),
        Index(
            "ix_supply_assignment_tenant_customer",
            "tenant_id",
            "customer_commitment_id",
        ),
        UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_supply_assignment_source"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    supplier_commitment_id: Mapped[str] = mapped_column(String)
    customer_commitment_id: Mapped[str | None] = mapped_column(String, default=None)
    purpose: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    source_record_id: Mapped[str] = mapped_column(String)
    reverses_assignment_id: Mapped[str | None] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CommitmentHold(Base):
    __tablename__ = "commitment_hold"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    commitment_id: Mapped[str] = mapped_column()
    reason_code: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String, default="human")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class Reservation(Base):
    __tablename__ = "reservation"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "handling_unit_id"],
            ["handling_unit.tenant_id", "handling_unit.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "lot_id"],
            ["lot.tenant_id", "lot.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["location.tenant_id", "location.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "serial_unit_id"],
            ["serial_unit.tenant_id", "serial_unit.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    commitment_id: Mapped[str] = mapped_column()
    item_id: Mapped[str] = mapped_column()
    location_id: Mapped[str] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(String, default="active")
    reserved_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    handling_unit_id: Mapped[str | None] = mapped_column(default=None)
    lot_id: Mapped[str | None] = mapped_column(default=None)
    serial_unit_id: Mapped[str | None] = mapped_column(default=None)


class HandlingUnit(Base):
    __tablename__ = "handling_unit"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "nve"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    nve: Mapped[str | None] = mapped_column(String, default=None)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Lot(Base):
    __tablename__ = "lot"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "item_id", "lot_number"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    item_id: Mapped[str] = mapped_column()
    lot_number: Mapped[str] = mapped_column(String)
    # The best-before date somebody read off the goods, never computed from a
    # shelf life. A calendar day rather than an instant, because a best-before
    # has no time of day and inventing one would be inventing precision.
    #
    # Absent says nothing in either direction: an item with no shelf life and a
    # label nobody read are indistinguishable here, and pretending otherwise
    # would be worse than the silence.
    expires_at: Mapped[date | None] = mapped_column(Date, default=None)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class SerialUnit(Base):
    __tablename__ = "serial_unit"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "lot_id"],
            ["lot.tenant_id", "lot.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        UniqueConstraint("tenant_id", "item_id", "serial_number"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    item_id: Mapped[str] = mapped_column()
    serial_number: Mapped[str] = mapped_column(String)
    lot_id: Mapped[str | None] = mapped_column(default=None)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Shipment(Base):
    __tablename__ = "shipment"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "counterparty_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
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
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    direction: Mapped[str] = mapped_column(String)
    purpose: Mapped[str] = mapped_column(String)
    counterparty_id: Mapped[str] = mapped_column()
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ShipmentPackage(Base):
    __tablename__ = "shipment_package"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "shipment_id"],
            ["shipment.tenant_id", "shipment.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        Index("ix_shipment_package_tenant_shipment", "tenant_id", "shipment_id"),
        Index(
            "ix_shipment_package_tenant_carrier_tracking",
            "tenant_id",
            "carrier",
            "tracking_number",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    shipment_id: Mapped[str] = mapped_column()
    carrier: Mapped[str | None] = mapped_column(String, default=None)
    tracking_number: Mapped[str | None] = mapped_column(String, default=None)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ShipmentEvent(Base):
    __tablename__ = "shipment_event"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shipment_package_id"],
            ["shipment_package.tenant_id", "shipment_package.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shipment_id"],
            ["shipment.tenant_id", "shipment.id"],
        ),
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
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    shipment_id: Mapped[str] = mapped_column()
    shipment_package_id: Mapped[str | None] = mapped_column(default=None)
    event_type: Mapped[str] = mapped_column(String)
    reporter_type: Mapped[str] = mapped_column(String)
    occurred_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    location_text: Mapped[str | None] = mapped_column(String, default=None)
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    external_event_id: Mapped[str | None] = mapped_column(String, default=None)


class ShipmentEventSupersession(Base):
    __tablename__ = "shipment_event_supersession"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "superseded_event_id"],
            ["shipment_event.tenant_id", "shipment_event.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replacement_event_id"],
            ["shipment_event.tenant_id", "shipment_event.id"],
        ),
        UniqueConstraint("tenant_id", "superseded_event_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    superseded_event_id: Mapped[str] = mapped_column()
    replacement_event_id: Mapped[str | None] = mapped_column(default=None)
    reason: Mapped[str] = mapped_column(Text)
    actor_context: Mapped[str] = mapped_column(Text, default="{}")
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class DeliveryFailure(Base):
    """A customer shipment that did not reach the customer (spec 335).

    Reality, append-only, at most one per shipment. It keeps what was stated:
    the parcel came back undeliverable, was refused, or was lost, why, and
    when. What it caused points back to it, never the other way (spec 322):
    the corrections are those of the shipment's movements, and a carrier claim
    is the document that carries this failure's source record.
    """

    __tablename__ = "delivery_failure"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "shipment_id"], ["shipment.tenant_id", "shipment.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "shipment_id", name="uq_delivery_failure_shipment"),
        CheckConstraint(
            "kind IN ('undeliverable', 'refused', 'lost')",
            name="ck_delivery_failure_kind",
        ),
        CheckConstraint("btrim(reason) <> ''", name="ck_delivery_failure_reason"),
        Index("ix_delivery_failure_source_record", "tenant_id", "source_record_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Misdelivery(Base):
    """A movement of another item than the line it was meant for (spec 338).

    The movement moves what it carries, so stock is true; it names no
    commitment, so the line it was meant for stays open. This row is the one
    link from the movement to that line. What is still out the wrong way is
    read from these rows and their movements each time, never stored.
    """

    __tablename__ = "misdelivery"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "movement_id"], ["movement.tenant_id", "movement.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"], ["commitment.tenant_id", "commitment.id"]
        ),
        UniqueConstraint("tenant_id", "movement_id", name="uq_misdelivery_movement"),
        Index("ix_misdelivery_commitment_id", "tenant_id", "commitment_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    movement_id: Mapped[str] = mapped_column(String)
    commitment_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CommitmentSubstitute(Base):
    """An item accepted in place of what a purchase line ordered (spec 338).

    The line keeps the item it ordered; receipts of the substitute name the
    line and fulfil it. The decision is a stated source record.
    """

    __tablename__ = "commitment_substitute"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"], ["commitment.tenant_id", "commitment.id"]
        ),
        ForeignKeyConstraint(["tenant_id", "item_id"], ["item.tenant_id", "item.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "commitment_id",
            "item_id",
            name="uq_commitment_substitute_commitment_item",
        ),
        CheckConstraint("btrim(reason) <> ''", name="ck_commitment_substitute_reason"),
        Index("ix_commitment_substitute_item_id", "tenant_id", "item_id"),
        Index(
            "ix_commitment_substitute_source_record_id", "tenant_id", "source_record_id"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    commitment_id: Mapped[str] = mapped_column(String)
    item_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ShipmentAdviceLine(Base):
    """How much an inbound notice advises for one purchase promise (spec 338).

    Stated with the notice and never changed. Advised against received, and
    what is still in transit, are read from these rows and the receipts
    recorded into the same shipment.
    """

    __tablename__ = "shipment_advice_line"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "shipment_id"], ["shipment.tenant_id", "shipment.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"], ["commitment.tenant_id", "commitment.id"]
        ),
        UniqueConstraint(
            "tenant_id",
            "shipment_id",
            "commitment_id",
            name="uq_shipment_advice_line_shipment_commitment",
        ),
        CheckConstraint("quantity > 0", name="ck_shipment_advice_line_quantity"),
        Index("ix_shipment_advice_line_commitment_id", "tenant_id", "commitment_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(String)
    commitment_id: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Movement(Base):
    __tablename__ = "movement"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "to_location_id"],
            ["location.tenant_id", "location.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["item.tenant_id", "item.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "resolves_movement_id"],
            ["movement.tenant_id", "movement.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "serial_unit_id"],
            ["serial_unit.tenant_id", "serial_unit.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "handling_unit_id"],
            ["handling_unit.tenant_id", "handling_unit.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "return_announcement_id"],
            ["return_announcement.tenant_id", "return_announcement.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shipment_package_id"],
            ["shipment_package.tenant_id", "shipment_package.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "lot_id"],
            ["lot.tenant_id", "lot.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "from_location_id"],
            ["location.tenant_id", "location.id"],
        ),
        CheckConstraint(
            "(stated_quantity IS NULL) = (stated_unit IS NULL)",
            name="ck_movement_stated_unit",
        ),
    )
    # The stated pair is not fetched back on insert (see stated_quantity).
    __mapper_args__: ClassVar[dict[str, Any]] = {"eager_defaults": False}
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    item_id: Mapped[str] = mapped_column()
    from_location_id: Mapped[str | None] = mapped_column()
    to_location_id: Mapped[str | None] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    commitment_id: Mapped[str | None] = mapped_column()
    source_record_id: Mapped[str | None] = mapped_column()
    handling_unit_id: Mapped[str | None] = mapped_column(default=None)
    lot_id: Mapped[str | None] = mapped_column(default=None)
    serial_unit_id: Mapped[str | None] = mapped_column(default=None)
    shipment_package_id: Mapped[str | None] = mapped_column(default=None)
    # Which return this movement settles. Null is a statement: almost every
    # movement settles none, and what happened to returned goods is what the
    # settling movement is — a transfer back to stock, a write-off, a shipment
    # to the supplier — never a separate label that could disagree.
    resolves_movement_id: Mapped[str | None] = mapped_column(default=None)
    # Which announced return these goods fulfil. Null is a statement in the same
    # way: almost every movement fulfils none, and a return that arrives without
    # having been announced is ordinary rather than incomplete.
    return_announcement_id: Mapped[str | None] = mapped_column(default=None)
    # Spec 301: what a receipt stated when it was not in the stock unit, kept
    # beside `quantity`, which is always in the item's stock unit. Deferred and
    # left out of an INSERT that does not set them, so movements on a schema from
    # before 0106 (the historical migration tests) still load and insert.
    stated_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), server_default=FetchedValue(), deferred=True
    )
    stated_unit: Mapped[str | None] = mapped_column(
        String, server_default=FetchedValue(), deferred=True
    )


class OutboundDelivery(Base):
    """A planned outbound delivery of one customer's promises (spec 334).

    It is a reviewed statement, kept as versions of one internal source stream;
    the current statement holds the stated address and the booked slot. It has
    no status: planned, picked and shipped are read from its lines, the pick
    movements and the shipment that executed it.
    """

    __tablename__ = "outbound_delivery"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"], ["party.tenant_id", "party.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "recipient_party_id"], ["party.tenant_id", "party.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "staging_location_id"],
            ["location.tenant_id", "location.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shipment_id"], ["shipment.tenant_id", "shipment.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        Index("ix_outbound_delivery_customer_id", "tenant_id", "customer_id"),
        Index(
            "ix_outbound_delivery_recipient_party_id", "tenant_id", "recipient_party_id"
        ),
        Index(
            "ix_outbound_delivery_staging_location_id",
            "tenant_id",
            "staging_location_id",
        ),
        Index("ix_outbound_delivery_source_record_id", "tenant_id", "source_record_id"),
        Index("uq_outbound_delivery_shipment", "tenant_id", "shipment_id", unique=True),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    customer_id: Mapped[str] = mapped_column()
    recipient_party_id: Mapped[str | None] = mapped_column(default=None)
    staging_location_id: Mapped[str | None] = mapped_column(default=None)
    shipment_id: Mapped[str | None] = mapped_column(default=None)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class OutboundDeliveryLine(Base):
    """One promise on a planned delivery, with the quantity planned for it."""

    __tablename__ = "outbound_delivery_line"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "outbound_delivery_id"],
            ["outbound_delivery.tenant_id", "outbound_delivery.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        CheckConstraint("quantity > 0", name="ck_outbound_delivery_line_quantity"),
        Index(
            "uq_outbound_delivery_line_commitment",
            "tenant_id",
            "outbound_delivery_id",
            "commitment_id",
            unique=True,
        ),
        Index("ix_outbound_delivery_line_commitment_id", "tenant_id", "commitment_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    outbound_delivery_id: Mapped[str] = mapped_column()
    commitment_id: Mapped[str] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))


class OutboundDeliveryPick(Base):
    """A transfer that picked goods into staging for a line, or put them back."""

    __tablename__ = "outbound_delivery_pick"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "outbound_delivery_line_id"],
            ["outbound_delivery_line.tenant_id", "outbound_delivery_line.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "movement_id"], ["movement.tenant_id", "movement.id"]
        ),
        CheckConstraint(
            "kind IN ('pick', 'put_back')", name="ck_outbound_delivery_pick_kind"
        ),
        Index(
            "ix_outbound_delivery_pick_line_id",
            "tenant_id",
            "outbound_delivery_line_id",
        ),
        Index(
            "uq_outbound_delivery_pick_movement", "tenant_id", "movement_id", unique=True
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    outbound_delivery_line_id: Mapped[str] = mapped_column()
    movement_id: Mapped[str] = mapped_column()
    kind: Mapped[str] = mapped_column(String)


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
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    # The customer delivery the goods went out on. It gives the item, the party
    # and the order line for free, and it is what bounds how much may come back.
    commitment_id: Mapped[str] = mapped_column()
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
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CustomerExchange(Base):
    """A replacement that settles part of a customer return instead of a credit.

    Reality, append-only: a confirmed statement that this promise answers that
    return. It links the shortest true pair, the return (goods back, or goods
    announced) and the replacement promise; party, item and order line follow
    from them. Nothing here says whether the exchange is settled: that is read
    from the movements and from whether the replacement was cancelled.
    """

    __tablename__ = "customer_exchange"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "return_movement_id"],
            ["movement.tenant_id", "movement.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "return_announcement_id"],
            ["return_announcement.tenant_id", "return_announcement.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replacement_commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        CheckConstraint(
            "(return_movement_id IS NULL) <> (return_announcement_id IS NULL)",
            name="ck_customer_exchange_one_return",
        ),
        CheckConstraint("quantity > 0", name="ck_customer_exchange_quantity_positive"),
        UniqueConstraint(
            "tenant_id",
            "replacement_commitment_id",
            name="uq_customer_exchange_replacement",
        ),
        UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_customer_exchange_source"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    return_movement_id: Mapped[str | None] = mapped_column(String, default=None)
    return_announcement_id: Mapped[str | None] = mapped_column(String, default=None)
    replacement_commitment_id: Mapped[str] = mapped_column(String)
    # The exchanged quantity of the returned item; the replacement states its own.
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    reason: Mapped[str] = mapped_column(Text)
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class StockBlock(Base):
    """Stock held back where it lies: not available, reserved, shipped or moved (spec 304).

    A person's statement about goods the company holds, with its reason. The
    goods stay where they are and no movement is recorded. The row stays as
    stated (spec 316): each release or scrap is its own `StockBlockResolution`,
    and what is still blocked is the stated quantity less those, read at read
    time (`core._open_stock_blocks`).
    """

    __tablename__ = "stock_block"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id", "item_id"], ["item.tenant_id", "item.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["location.tenant_id", "location.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "handling_unit_id"],
            ["handling_unit.tenant_id", "handling_unit.id"],
        ),
        ForeignKeyConstraint(["tenant_id", "lot_id"], ["lot.tenant_id", "lot.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "serial_unit_id"],
            ["serial_unit.tenant_id", "serial_unit.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "receipt_movement_id"], ["movement.tenant_id", "movement.id"]
        ),
        CheckConstraint("quantity > 0", name="ck_stock_block_quantity"),
        CheckConstraint(
            "reason_code IN ('quality','damage','expiry','inspection')",
            name="ck_stock_block_reason",
        ),
        Index("ix_stock_block_item_location", "tenant_id", "item_id", "location_id"),
        Index("ix_stock_block_location_id", "tenant_id", "location_id"),
        Index("ix_stock_block_handling_unit_id", "tenant_id", "handling_unit_id"),
        Index("ix_stock_block_lot_id", "tenant_id", "lot_id"),
        Index("ix_stock_block_serial_unit_id", "tenant_id", "serial_unit_id"),
        Index("ix_stock_block_receipt_movement_id", "tenant_id", "receipt_movement_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    item_id: Mapped[str] = mapped_column()
    location_id: Mapped[str] = mapped_column()
    handling_unit_id: Mapped[str | None] = mapped_column(default=None)
    lot_id: Mapped[str | None] = mapped_column(default=None)
    serial_unit_id: Mapped[str | None] = mapped_column(default=None)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    reason_code: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    created_by: Mapped[str] = mapped_column(String, default="human")
    # The receipt that stated the block (spec 304 H08/H15), never a scrap.
    receipt_movement_id: Mapped[str | None] = mapped_column(default=None)


class StockBlockResolution(Base):
    """One release or scrap of part or all of a stock block (spec 316).

    Appended, never changed. A scrap names the adjustment it recorded; the
    movement key is deferred because the resolution must stand before that
    adjustment runs, or the adjustment would take stock still held back.
    """

    __tablename__ = "stock_block_resolution"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "block_id"], ["stock_block.tenant_id", "stock_block.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "movement_id"],
            ["movement.tenant_id", "movement.id"],
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("quantity > 0", name="ck_stock_block_resolution_quantity"),
        CheckConstraint(
            "kind IN ('release','scrap')", name="ck_stock_block_resolution_kind"
        ),
        CheckConstraint("btrim(reason) <> ''", name="ck_stock_block_resolution_reason"),
        CheckConstraint(
            "(kind = 'scrap') = (movement_id IS NOT NULL)",
            name="ck_stock_block_resolution_movement",
        ),
        UniqueConstraint(
            "tenant_id", "movement_id", name="uq_stock_block_resolution_movement"
        ),
        Index("ix_stock_block_resolution_block_id", "tenant_id", "block_id"),
        Index("ix_stock_block_resolution_movement_id", "tenant_id", "movement_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    block_id: Mapped[str] = mapped_column()
    kind: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    reason: Mapped[str] = mapped_column(Text)
    resolved_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    resolved_by: Mapped[str] = mapped_column(String, default="human")
    movement_id: Mapped[str | None] = mapped_column(default=None)


class PrepaymentRelease(Base):
    """An owner's decision to ship a prepayment order before it is paid (spec 347).

    Appended, never changed. It covers the order's stated gross amount as it
    stood when the owner decided; an order raised past that amount asks again.
    The unpaid remainder stays an ordinary open receivable. The person comes
    from the decision that confirmed it; the reason is stated here.
    """

    __tablename__ = "prepayment_release"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"], ["document.tenant_id", "document.id"]
        ),
        CheckConstraint(
            "covered_amount >= 0", name="ck_prepayment_release_covered_amount"
        ),
        CheckConstraint("btrim(reason) <> ''", name="ck_prepayment_release_reason"),
        Index("ix_prepayment_release_document_id", "tenant_id", "document_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    document_id: Mapped[str] = mapped_column()
    covered_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String(3))
    reason: Mapped[str] = mapped_column(Text)
    action_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class MovementCorrection(Base):
    __tablename__ = "movement_correction"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "original_movement_id"],
            ["movement.tenant_id", "movement.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replacement_movement_id"],
            ["movement.tenant_id", "movement.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "compensating_movement_id"],
            ["movement.tenant_id", "movement.id"],
        ),
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
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    original_movement_id: Mapped[str] = mapped_column()
    compensating_movement_id: Mapped[str] = mapped_column()
    replacement_movement_id: Mapped[str | None] = mapped_column(default=None)
    reason: Mapped[str] = mapped_column(Text)
    corrected_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    actor_context: Mapped[str] = mapped_column(Text, default="{}")
    request_fingerprint: Mapped[str] = mapped_column(String)


class SubledgerAccount(Base):
    __tablename__ = "subledger_account"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint(
            "tenant_id", "default_destination_id", name="uq_account_default_destination"
        ),
        Index(
            "uq_account_default_role",
            "tenant_id",
            "role",
            unique=True,
            postgresql_where=text("default_destination_id IS NOT NULL"),
        ),
        CheckConstraint("state IN ('active', 'blocked')"),
        CheckConstraint(
            "role IN ('accounts_receivable','accounts_payable','cash','sales_revenue','inventory','customer_reduction','supplier_reduction','bad_debt_expense','dunning_fee_revenue','payment_fee_expense','customer_down_payments','exchange_difference','carrier_claim_income','opening_counterpart')",
            name="ck_subledger_account_role",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, default="active")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    # The retained opaque selection identity; NULL means not the role's default.
    default_destination_id: Mapped[str | None] = mapped_column(
        String, server_default=FetchedValue(), deferred=True
    )


class FinanceRoleDestination(Base):
    __tablename__ = "finance_role_destination"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "role"),
        ForeignKeyConstraint(
            ["tenant_id", "account_id"],
            ["subledger_account.tenant_id", "subledger_account.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    role: Mapped[str] = mapped_column(String)
    account_id: Mapped[str] = mapped_column(String)


# DISTINCT deliberately refuses all legacy writes: account_id must never become
# an alternate write path to the selected account's primary key.
FinanceRoleDestination.__table__.info["compatibility_view_sql"] = (
    "CREATE VIEW finance_role_destination AS SELECT DISTINCT "
    "default_destination_id AS id, tenant_id, role, id AS account_id "
    "FROM subledger_account WHERE default_destination_id IS NOT NULL"
)
FinanceRoleDestination.__table__.add_is_dependent_on(SubledgerAccount.__table__)


class FinanceState(Base):
    __tablename__ = "finance_state"
    __table_args__ = (PrimaryKeyConstraint("tenant_id", "id"),)
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), unique=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)


class LedgerEntry(Base):
    __tablename__ = "ledger_entry"
    # The spec 309 columns are left out of an INSERT that does not set them, so
    # schemas from before them keep working in the historical migration tests.
    __mapper_args__: ClassVar[dict[str, Any]] = {"eager_defaults": False}
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "account_id"],
            ["subledger_account.tenant_id", "subledger_account.id"],
        ),
        CheckConstraint(
            "company_amount IS NULL OR company_amount >= 0",
            name="ck_ledger_entry_company_amount",
        ),
        CheckConstraint(
            "exchange_rate IS NULL OR exchange_rate > 0",
            name="ck_ledger_entry_exchange_rate",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    posting_group_id: Mapped[str] = mapped_column(String, index=True, default="")
    account_id: Mapped[str] = mapped_column(String)
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

    party_id: Mapped[str | None] = mapped_column()
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String, default="EUR")
    debit_credit: Mapped[str] = mapped_column(String)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    document_id: Mapped[str | None] = mapped_column()
    source_record_id: Mapped[str | None] = mapped_column()
    # Spec 309: the amount in the company currency and the rate used; null for a
    # foreign entry posted before the company currency existed (unconverted).
    company_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), server_default=FetchedValue(), deferred=True
    )
    exchange_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8), server_default=FetchedValue(), deferred=True
    )


class CompanyCurrency(Base):
    """The currency the company keeps its books in (spec 309); absent means EUR."""

    __tablename__ = "company_currency"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_company_currency_code"),
        Index("ix_company_currency_source_record_id", "tenant_id", "source_record_id"),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    currency: Mapped[str] = mapped_column(String(3))
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CompanyTimeZone(Base):
    """The time zone the company's business days are counted in (spec 349); absent means UTC."""

    __tablename__ = "company_time_zone"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        Index("ix_company_time_zone_source_record_id", "tenant_id", "source_record_id"),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    time_zone: Mapped[str] = mapped_column(String(64))
    source_record_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class LedgerReversal(Base):
    """Durable correction evidence linking one posting group to its exact inverse."""

    __tablename__ = "ledger_reversal"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("original_posting_group_id"),
        UniqueConstraint("reversing_posting_group_id"),
        UniqueConstraint("tenant_id", "request_fingerprint"),
        CheckConstraint(
            "original_posting_group_id <> reversing_posting_group_id",
            name="ck_ledger_reversal_groups_distinct",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    original_posting_group_id: Mapped[str] = mapped_column(String, index=True)
    reversing_posting_group_id: Mapped[str] = mapped_column(String, index=True)
    reason: Mapped[str] = mapped_column(Text)
    reversed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    actor_context: Mapped[str] = mapped_column(Text, default="{}")
    request_fingerprint: Mapped[str] = mapped_column(String)


class SettlementAllocation(Base):
    __tablename__ = "settlement_allocation"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "payment_ledger_entry_id"],
            ["ledger_entry.tenant_id", "ledger_entry.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_ledger_entry_id"],
            ["ledger_entry.tenant_id", "ledger_entry.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    payment_ledger_entry_id: Mapped[str] = mapped_column()
    invoice_ledger_entry_id: Mapped[str] = mapped_column()
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String, default="EUR")
    allocated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Fact(Base):
    __tablename__ = "fact"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "interpretation_rule_id"],
            ["interpretation_rule.tenant_id", "interpretation_rule.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        UniqueConstraint("tenant_id", "request_fingerprint"),
        Index("ix_fact_tenant_recorded", "tenant_id", "recorded_at"),
    )
    id: Mapped[str] = mapped_column(String)
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
    source_record_id: Mapped[str | None] = mapped_column()
    request_fingerprint: Mapped[str | None] = mapped_column(String, default=None)
    interpretation_rule_id: Mapped[str | None] = mapped_column(default=None)


class RealityGap(Base):
    __tablename__ = "reality_gap"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "request_fingerprint"),
        CheckConstraint("revision >= 1", name="ck_reality_gap_revision"),
    )
    id: Mapped[str] = mapped_column(String)
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
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "gap_id"],
            ["reality_gap.tenant_id", "reality_gap.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    gap_id: Mapped[str] = mapped_column()
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
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "gap_id"],
            ["reality_gap.tenant_id", "reality_gap.id"],
        ),
        UniqueConstraint("tenant_id", "logical_name", "version"),
        CheckConstraint("version >= 1", name="ck_interpretation_rule_version"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    gap_id: Mapped[str] = mapped_column()
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
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "fact_id"],
            ["fact.tenant_id", "fact.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rule_id"],
            ["interpretation_rule.tenant_id", "interpretation_rule.id"],
        ),
        UniqueConstraint(
            "tenant_id",
            "rule_id",
            "source_record_id",
            "element_key",
            name="uq_rule_outcome_source_element",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    rule_id: Mapped[str] = mapped_column()
    source_record_id: Mapped[str] = mapped_column()
    element_key: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, index=True)
    fact_id: Mapped[str | None] = mapped_column(default=None)
    detail: Mapped[str] = mapped_column(Text, default="{}")
    evaluated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ChangeProposal(Base):
    """Auditable mutation proposed for approval before execution.

    The physical table name remains stable so existing tenant databases do not
    lose their audit trail during the terminology correction.
    """

    __tablename__ = "action"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "id", name="uq_action_tenant_id"),
        CheckConstraint(
            "decided_via_channel IS NULL OR decided_via_channel IN ('chat', 'external_grant')",
            name="ck_action_decided_via_channel",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "decided_via_token_id"],
            ["mcp_access_token.tenant_id", "mcp_access_token.id"],
            name="fk_action_decided_via_token",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "chat_session_id"],
            ["chat_session.tenant_id", "chat_session.id"],
            name="fk_action_chat_session",
        ),
        Index("ix_action_tenant_chat_session", "tenant_id", "chat_session_id"),
    )
    # Historical-schema tests insert proposals on revisions without
    # `chat_session_id`; no RETURNING for the server-side fetched column.
    __mapper_args__: ClassVar[dict[str, Any]] = {"eager_defaults": False}
    id: Mapped[str] = mapped_column(String)
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
    # A decision settled through MCP names the access token that sent it (spec 263).
    # It is never copied into `decided_by_user_id`: Reality sees the token, not the
    # person at the agent client, and the record must not claim more than that.
    decided_via_token_id: Mapped[str | None] = mapped_column(String, default=None)
    # A built-in Chat confirmation observes an agent channel, not a human identity.
    decided_via_channel: Mapped[str | None] = mapped_column(String(16), default=None)
    # The conversation whose turn made this proposal (spec 328). Set once, inside a
    # chat turn only; null for MCP, CLI, services and everything made before.
    chat_session_id: Mapped[str | None] = mapped_column(
        String, server_default=FetchedValue(), deferred=True
    )


class EmailBusinessLink(Base):
    """Validated explicit object membership; original email evidence is immutable."""

    __tablename__ = "email_business_link"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "source_record_id", "kind", "record_id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        Index(
            "ix_email_business_link_object",
            "tenant_id",
            "kind",
            "record_id",
            "source_record_id",
        ),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    source_record_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    record_id: Mapped[str] = mapped_column(String)


class EmailDispatch(Base):
    """One authorized external execution; a claim is never automatically released."""

    __tablename__ = "email_dispatch"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "proposal_id", name="uq_email_dispatch_proposal"),
        ForeignKeyConstraint(
            ["tenant_id", "proposal_id"], ["action.tenant_id", "action.id"]
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    proposal_id: Mapped[str] = mapped_column(String)
    fingerprint: Mapped[str] = mapped_column(String(64))
    executor: Mapped[str | None] = mapped_column(String, default=None)
    claim_key: Mapped[str | None] = mapped_column(String, default=None)
    claimed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class EmailDispatchReceipt(Base):
    """Bind only executor-reported Sources to dispatch outcome derivation."""

    __tablename__ = "email_dispatch_receipt"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "source_record_id"),
        ForeignKeyConstraint(
            ["tenant_id", "dispatch_id"],
            ["email_dispatch.tenant_id", "email_dispatch.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        Index("ix_email_dispatch_receipt_dispatch", "tenant_id", "dispatch_id"),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    source_record_id: Mapped[str] = mapped_column(String)
    dispatch_id: Mapped[str] = mapped_column(String)


# Transitional import alias for older adapters. New domain code uses
# ChangeProposal; this can be removed after downstream integrations migrate.
Action = ChangeProposal


class BusinessEvent(Base):
    __tablename__ = "business_event"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "causation_id"],
            ["business_event.tenant_id", "business_event.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "action_id"],
            ["action.tenant_id", "action.id"],
        ),
        UniqueConstraint("tenant_id", "sequence"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    sequence: Mapped[int] = mapped_column(BigInteger)
    event_type: Mapped[str] = mapped_column(String, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    subject_type: Mapped[str] = mapped_column(String)
    subject_id: Mapped[str] = mapped_column(String, index=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    source_record_id: Mapped[str | None] = mapped_column(default=None)
    action_id: Mapped[str | None] = mapped_column(default=None)
    causation_id: Mapped[str | None] = mapped_column(default=None)
    correlation_id: Mapped[str | None] = mapped_column(String, default=None)


class ProjectionRow(Base):
    __tablename__ = "projection_row"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "projection_name", "record_key"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    projection_name: Mapped[str] = mapped_column(String, index=True)
    projection_version: Mapped[int] = mapped_column(Integer, default=1)
    record_key: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[str] = mapped_column(Text)
    source_event_sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class TenantEventProgress(Base):
    """How far one company's business events have got, on a row of its own.

    `max(business_event.sequence)` answers this for one company at a time. Spec 181
    FR-004 needs it asked of every company at once — which projections of which
    companies have fallen behind — and that has to be one indexed read rather than ten
    thousand round trips a sweep.

    It is deliberately **not** a column on `tenant`. Every table that references a
    company takes `FOR KEY SHARE` on its row to check the foreign key, so writing that
    row on every business event makes any concurrent REPEATABLE READ transaction that
    inserts anything fail to serialise — which is to say, all of them. Nothing
    references this table, so writing it disturbs nobody.
    """

    __tablename__ = "tenant_event_progress"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    last_event_sequence: Mapped[int] = mapped_column(BigInteger, default=0)


class ProjectionCheckpoint(Base):
    __tablename__ = "projection_checkpoint"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "projection_name"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    projection_name: Mapped[str] = mapped_column(String, index=True)
    projection_version: Mapped[int] = mapped_column(Integer, default=1)
    last_event_sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    #: Where the *company* had got to when this projection was last evaluated, as
    #: opposed to `last_event_sequence`, which is where the events this projection
    #: depends on had got to. The two differ on purpose: a journal that no posting has
    #: touched sits at zero however busy the company is, so comparing it against the
    #: company would say "behind" forever.
    #:
    #: This is the column the fleet-wide selection compares (spec 181 FR-004). It
    #: answers "has anything at all happened here since this projection last looked",
    #: which over-selects — the event may turn out to be irrelevant — and never
    #: under-selects, which is the direction that would leave a projection stale.
    observed_event_sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String, default="ready")
    error: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    #: When this projection could next answer differently with no event at all, for
    #: the one projection whose classes are judged against the moment they are read
    #: (spec 181 FR-004). It replaces asking every sixty seconds whether anything has
    #: aged: a company with nothing dated is looked at once a day, and one with a
    #: promise falling due tonight is looked at tonight. `None` for every projection
    #: that does not read the clock, and for a generation written before this column.
    clock_due_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class ChatSession(Base):
    __tablename__ = "chat_session"
    __table_args__ = (PrimaryKeyConstraint("tenant_id", "id"),)
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class AISettings(Base):
    __tablename__ = "ai_settings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "api_key_secret_id"],
            ["secret.tenant_id", "secret.id"],
        ),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String, default="local")
    model: Mapped[str] = mapped_column(String, default="")
    base_url: Mapped[str] = mapped_column(String, default="https://api.openai.com/v1")
    api_key_secret_id: Mapped[str | None] = mapped_column(default=None)
    # Kept temporarily so installations can lazily move an existing key into the
    # generic vault without exposing or manually re-entering it.
    encrypted_api_key: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class Secret(Base):
    """Tenant-scoped encrypted material; consumers retain only this opaque ID."""

    __tablename__ = "secret"
    __table_args__ = (PrimaryKeyConstraint("tenant_id", "id"),)
    id: Mapped[str] = mapped_column(String)
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
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "secret_id"],
            ["secret.tenant_id", "secret.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    secret_id: Mapped[str] = mapped_column()
    event_type: Mapped[str] = mapped_column(String, index=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class MCPAccessToken(Base):
    __tablename__ = "mcp_access_token"
    __table_args__ = (PrimaryKeyConstraint("tenant_id", "id"),)
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    token_prefix: Mapped[str] = mapped_column(String, index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    allowed_tools: Mapped[str] = mapped_column(Text, default='["*"]')
    # The owner who issued the token, so a decision it settles has someone to answer
    # for it. Tokens issued before spec 263 have none, and none is invented.
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), index=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class ChatMessage(Base):
    __tablename__ = "chat_message"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["chat_session.tenant_id", "chat_session.id"],
        ),
        CheckConstraint(
            "answer_basis IS NULL OR octet_length(answer_basis::text) <= 16384",
            name="ck_chat_message_answer_basis_size",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    session_id: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    answer_basis: Mapped[dict | None] = mapped_column(
        JSONB(none_as_null=True), default=None
    )
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
from reality.db import captured_report as _captured_report  # noqa: F401
from reality.db import company_generations as _company_generations  # noqa: F401
from reality.db import company_setup as _company_setup  # noqa: F401
from reality.db import components as _components  # noqa: F401
from reality.db import contribution as _contribution  # noqa: F401
from reality.db import cost_captured_basis as _cost_captured_basis  # noqa: F401
from reality.db import cost_census as _cost_census  # noqa: F401
from reality.db import cost_generations as _cost_generations  # noqa: F401
from reality.db import costing as _costing  # noqa: F401
from reality.db import demo_data as _demo_data  # noqa: F401
from reality.db import finance_references as _finance_references  # noqa: F401
from reality.db import interactions as _interactions  # noqa: F401
from reality.db import inventory_costing as _inventory_costing  # noqa: F401
from reality.db import mcp_authorization as _mcp_authorization  # noqa: F401
from reality.db import opening as _opening  # noqa: F401
from reality.db import scheduled_jobs as _scheduled_jobs  # noqa: F401
from reality.db import source_mappings as _source_mappings  # noqa: F401
from reality.db import target_mappings as _target_mappings  # noqa: F401

#: PostgreSQL refuses an identifier longer than this, and silently truncating one
#: would let two indexes collide under the same name.
MAXIMUM_IDENTIFIER = 63


def _index_name(table: str, columns: tuple[str, ...]) -> str:
    """What to call an index over these columns, within PostgreSQL's limit.

    Named after what the index is *for* rather than everything it holds: the
    company leads every reference between two company-scoped tables, so spelling
    it out would say nothing and would push the longest names past the limit. An
    index that was `ix_x_parent_id` therefore keeps its name and becomes
    composite underneath, which is also one less rename in the migration.

    Five names are still too long even so, and a plain truncation would have made
    two of them equal. The digest is of the full name, so it is stable across
    runs and machines and says which index this is where the name had to stop.
    """
    name = f"ix_{table}_{'_'.join(columns)}"
    if len(name) <= MAXIMUM_IDENTIFIER:
        return name
    digest = hashlib.sha256(name.encode()).hexdigest()[:8]
    return f"{name[: MAXIMUM_IDENTIFIER - 9]}_{digest}"


def index_foreign_keys(metadata: MetaData) -> list[Index]:
    """Give every foreign key an index over its own columns, unless one already leads.

    Spec 181: a read or a delete of a referenced row must not scan its referrers. Without
    this, matching one payment walked every ledger entry of the company for its document
    (197 ms per payment at 10,000 orders), and removing a company took half an hour in
    foreign-key checks (`business_event.causation_id`, every `source_record_id`). The rule
    is applied once, here, after every model module has registered its tables, so the
    test schema and the migrations describe the same indexes. Migration 0059 creates
    them with the same names for existing databases.

    It indexes the whole key rather than its first column, because a reference between
    two company-scoped tables now names the company first (spec 181 FR-005). Asking only
    about the first column would have found `tenant_id` already indexed and left 73
    references unindexed — `business_event.causation_id` among them, the one that took a
    company deletion from thirty-six minutes to under four seconds. An index over
    `(tenant_id, causation_id)` answers both the foreign key's check and the question a
    reader actually asks, which is always about one company.
    """

    def leading(columns) -> tuple[str, ...]:
        return tuple(column.name for column in columns)

    created: list[Index] = []
    for table in metadata.sorted_tables:
        covered = {leading(index.columns) for index in table.indexes}
        for constraint in table.constraints:
            if isinstance(constraint, (PrimaryKeyConstraint, UniqueConstraint)):
                covered.add(leading(constraint.columns))
        for foreign_key in table.foreign_key_constraints:
            columns = list(foreign_key.columns)
            names = leading(columns)
            # A wider index answers a narrower question: an index on (a, b) already
            # serves a key on (a), so only a key nothing starts with needs one.
            if any(existing[: len(names)] == names for existing in covered):
                continue
            if len(columns) == 1 and columns[0].index:
                continue
            # Named after what it is for, not after every column it holds: the
            # company leads every one of these, so spelling it out would say
            # nothing and would push the longer names past PostgreSQL's 63
            # characters. An index that was `ix_x_parent_id` keeps that name and
            # becomes composite underneath, which is also one less rename in the
            # migration.
            distinguishing = names[1:] if names[0] == "tenant_id" else names
            covered.add(names)
            created.append(Index(_index_name(table.name, distinguishing), *columns))
    return created


from reality.db import cost_census_members as _cost_census_members  # noqa: F401
from reality.db import cost_manifest_members as _cost_manifest_members  # noqa: F401
from reality.db import cost_projections as _cost_projections  # noqa: F401
from reality.db import finance_reference_store as _finance_reference_store  # noqa: F401

FOREIGN_KEY_INDEXES = index_foreign_keys(Base.metadata)
