"""Immutable received component normalization and internal assignment revisions."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class FinancialComponent(Base):
    __tablename__ = "financial_component"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "id", name="uq_financial_component_tenant"),
        UniqueConstraint(
            "tenant_id", "document_id", name="uq_financial_component_document"
        ),
        UniqueConstraint(
            "tenant_id", "document_line_id", name="uq_financial_component_line"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
            name="fk_component_document",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "document_line_id"],
            ["document_line.tenant_id", "document_line.id"],
            name="fk_component_line",
        ),
        CheckConstraint(
            "(document_id IS NULL) <> (document_line_id IS NULL)",
            name="ck_component_owner",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(String)
    document_line_id: Mapped[str | None] = mapped_column(String)
    stated_net: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    stated_tax: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    stated_gross: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    stated_base: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String)


class ComponentAssignment(Base):
    __tablename__ = "component_assignment_revision"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "id", name="uq_component_assignment_tenant"),
        UniqueConstraint(
            "tenant_id",
            "component_id",
            "revision",
            name="uq_component_assignment_revision",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "component_id"],
            ["financial_component.tenant_id", "financial_component.id"],
            name="fk_assignment_component",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "action_id"],
            ["action.tenant_id", "action.id"],
            name="fk_assignment_action",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "case_reference_id", "case_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_assignment_case",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "group_reference_id", "group_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_assignment_group",
        ),
        CheckConstraint(
            "case_kind='case_code' AND group_kind='coding_group'",
            name="ck_assignment_kinds",
        ),
        CheckConstraint(
            "basis IN ('net','gross','base') AND revision>0",
            name="ck_assignment_basis_revision",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    component_id: Mapped[str] = mapped_column(String, index=True)
    revision: Mapped[int]
    basis: Mapped[str] = mapped_column(String)
    case_reference_id: Mapped[str | None] = mapped_column(String)
    case_kind: Mapped[str] = mapped_column(String, default="case_code")
    group_reference_id: Mapped[str | None] = mapped_column(String)
    group_kind: Mapped[str] = mapped_column(String, default="coding_group")
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("app_user.id"))
    action_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    reference_snapshot: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ComponentAssignmentPart(Base):
    __tablename__ = "component_assignment_part"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id",
            "assignment_revision_id",
            "cost_center_reference_id",
            name="uq_assignment_center",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assignment_revision_id"],
            [
                "component_assignment_revision.tenant_id",
                "component_assignment_revision.id",
            ],
            name="fk_assignment_part_revision",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "cost_center_reference_id", "reference_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_assignment_part_center",
        ),
        CheckConstraint(
            "reference_kind='cost_center' AND amount>0",
            name="ck_assignment_part_amount_kind",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    assignment_revision_id: Mapped[str] = mapped_column(String, index=True)
    cost_center_reference_id: Mapped[str] = mapped_column(String)
    reference_kind: Mapped[str] = mapped_column(String, default="cost_center")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
