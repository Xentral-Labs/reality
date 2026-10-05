"""Coordination authority; business completion remains in Reality records."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class OperationalCase(Base):
    __tablename__ = "operational_case"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "order_document_id"], ["document.tenant_id", "document.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "return_announcement_id"],
            ["return_announcement.tenant_id", "return_announcement.id"],
        ),
        UniqueConstraint("tenant_id", "order_document_id"),
        UniqueConstraint("tenant_id", "return_announcement_id"),
        CheckConstraint(
            "(kind = 'order_fulfillment' AND order_document_id IS NOT NULL AND return_announcement_id IS NULL) OR (kind = 'customer_return' AND order_document_id IS NULL AND return_announcement_id IS NOT NULL)",
            name="ck_case_anchor",
        ),
        CheckConstraint(
            "control_mode IN ('automation', 'human')", name="ck_case_control"
        ),
        CheckConstraint(
            "control_revision >= 1 AND policy_version = 1", name="ck_case_revision"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    kind: Mapped[str] = mapped_column(String)
    order_document_id: Mapped[str | None] = mapped_column(String, default=None)
    return_announcement_id: Mapped[str | None] = mapped_column(String, default=None)
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    control_mode: Mapped[str] = mapped_column(String, default="automation")
    control_revision: Mapped[int] = mapped_column(Integer, default=1)
    takeover_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CaseCommitmentLink(Base):
    __tablename__ = "case_commitment_link"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "case_id", "commitment_id"),
        ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["operational_case.tenant_id", "operational_case.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "commitment_id"], ["commitment.tenant_id", "commitment.id"]
        ),
    )
    tenant_id: Mapped[str] = mapped_column(String)
    case_id: Mapped[str] = mapped_column(String)
    commitment_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CaseProposalLink(Base):
    __tablename__ = "case_proposal_link"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "case_id", "proposal_id"),
        ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["operational_case.tenant_id", "operational_case.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "proposal_id"], ["action.tenant_id", "action.id"]
        ),
        CheckConstraint("bound_control_revision >= 1", name="ck_case_binding_revision"),
    )
    tenant_id: Mapped[str] = mapped_column(String)
    case_id: Mapped[str] = mapped_column(String)
    proposal_id: Mapped[str] = mapped_column(String)
    bound_control_revision: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CaseAdoption(Base):
    __tablename__ = "case_adoption"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "decision_id"], ["action.tenant_id", "action.id"]
        ),
        CheckConstraint(
            "capture_sequence >= 0 AND policy_version = 1",
            name="ck_case_adoption_boundary",
        ),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    decision_id: Mapped[str] = mapped_column(String)
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    capture_sequence: Mapped[int] = mapped_column(BigInteger)
    selected_order_ids: Mapped[list] = mapped_column(JSONB, default=list)
    selected_return_ids: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class CaseConsumerCheckpoint(Base):
    __tablename__ = "case_consumer_checkpoint"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "policy_version"),
        CheckConstraint(
            "incorporated_sequence >= 0 AND policy_version = 1",
            name="ck_case_checkpoint",
        ),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    incorporated_sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
