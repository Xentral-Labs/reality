"""Exact source classification revisions; no monetary or tax determination."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class SourceClassificationMapping(Base):
    __tablename__ = "source_classification_mapping_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_source_mapping_tenant"),
        UniqueConstraint(
            "tenant_id",
            "source_system_id",
            "namespace",
            "field_kind",
            "source_code",
            "revision",
            name="uq_source_mapping_revision",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_system_id"],
            ["source_system.tenant_id", "source_system.id"],
            name="fk_source_mapping_system",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reference_id", "field_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_source_mapping_reference",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replaces_id"],
            [
                "source_classification_mapping_revision.tenant_id",
                "source_classification_mapping_revision.id",
            ],
            name="fk_source_mapping_predecessor",
        ),
        CheckConstraint(
            "field_kind IN ('case_code','coding_group')", name="ck_source_mapping_kind"
        ),
        CheckConstraint(
            "state IN ('active','blocked')", name="ck_source_mapping_state"
        ),
        CheckConstraint(
            "revision > 0 AND length(trim(namespace)) > 0 AND length(trim(source_code)) > 0 AND length(trim(reason)) > 0",
            name="ck_source_mapping_values",
        ),
        Index(
            "uq_source_mapping_current",
            "tenant_id",
            "source_system_id",
            "namespace",
            "field_kind",
            "source_code",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_system_id: Mapped[str] = mapped_column(String)
    namespace: Mapped[str] = mapped_column(String(200))
    field_kind: Mapped[str] = mapped_column(String)
    source_code: Mapped[str] = mapped_column(String(200))
    reference_id: Mapped[str] = mapped_column(String)
    revision: Mapped[int]
    replaces_id: Mapped[str | None] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    reference_snapshot: Mapped[dict] = mapped_column(JSONB)
    reason: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[str | None] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(ForeignKey("action.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
