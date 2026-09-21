"""Defined internal classifications, without financial values or inferred meaning."""

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base


class FinanceReference(Base):
    __tablename__ = "finance_reference"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "kind", "code", name="uq_finance_reference_code"),
        UniqueConstraint(
            "tenant_id", "id", "kind", name="uq_finance_reference_kind_id"
        ),
        CheckConstraint(
            "kind IN ('cost_center','case_code','coding_group')",
            name="ck_finance_reference_kind",
        ),
        CheckConstraint(
            "state IN ('active','blocked')", name="ck_finance_reference_state"
        ),
        CheckConstraint("revision > 0", name="ck_finance_reference_revision"),
        CheckConstraint(
            "length(trim(code)) > 0 AND length(trim(name)) > 0",
            name="ck_finance_reference_labels",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    kind: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String)
    revision: Mapped[int]
