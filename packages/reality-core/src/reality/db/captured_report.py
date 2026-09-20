"""Disposable typed reports of immutable captured review selections."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime
from reality.db.costing import CostRecord, _link


class CostGeneration(CostRecord, Base):
    __tablename__ = "cost_generation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_key", "id"),
        UniqueConstraint("tenant_id", "captured_basis_id", "algorithm_version"),
        _link("captured_basis_id", "cost_captured_basis"),
        CheckConstraint(
            "kind='captured_review_selection_v1' AND algorithm_version='captured-report-v1' AND length(scope_key)=64 AND length(output_hash)=64",
            name="ck_cost_generation_version",
        ),
        CheckConstraint(
            "state IN ('building','sealed') AND ((state='sealed') = (completed_at IS NOT NULL))",
            name="ck_cost_generation_state",
        ),
        CheckConstraint(
            "inventory_count>=0 AND contribution_count>=0 AND inventory_count+contribution_count<=10",
            name="ck_cost_generation_counts",
        ),
    )
    captured_basis_id: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String)
    algorithm_version: Mapped[str] = mapped_column(String)
    scope_key: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    inventory_count: Mapped[int]
    contribution_count: Mapped[int]
    output_hash: Mapped[str] = mapped_column(String(64))


class CostInventoryRow(CostRecord, Base):
    __tablename__ = "cost_inventory_row"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "generation_id", "inventory_basis_member_id"),
        _link("generation_id", "cost_generation"),
        _link("inventory_basis_member_id", "cost_captured_inventory_basis"),
        _link("owner_party_id", "party"),
        Index(
            "ix_cost_inventory_group",
            "tenant_id",
            "generation_id",
            "currency",
            "base_unit",
            "method",
            "owner_party_id",
        ),
        CheckConstraint(
            "(state='available_at_capture' AND currency IS NOT NULL AND base_unit IS NOT NULL AND method IS NOT NULL AND owner_party_id IS NOT NULL AND remaining_quantity IS NOT NULL AND acquisition_value IS NOT NULL) OR (state='unknown_at_capture' AND currency IS NULL AND base_unit IS NULL AND method IS NULL AND owner_party_id IS NULL AND remaining_quantity IS NULL AND acquisition_value IS NULL AND carrying_value IS NULL)",
            name="ck_cost_inventory_row_shape",
        ),
        CheckConstraint(
            "remaining_quantity>=0 AND acquisition_value>=0 AND carrying_value>=0 AND carrying_value<=acquisition_value",
            name="ck_cost_inventory_row_amounts",
        ),
    )
    generation_id: Mapped[str] = mapped_column(String, index=True)
    inventory_basis_member_id: Mapped[str] = mapped_column(String, index=True)
    state: Mapped[str] = mapped_column(String)
    currency: Mapped[str | None] = mapped_column(String)
    base_unit: Mapped[str | None] = mapped_column(String)
    method: Mapped[str | None] = mapped_column(String)
    owner_party_id: Mapped[str | None] = mapped_column(String, index=True)
    remaining_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    acquisition_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    carrying_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))


class CostContributionRow(CostRecord, Base):
    __tablename__ = "cost_contribution_row"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "generation_id", "contribution_basis_member_id"),
        _link("generation_id", "cost_generation"),
        _link("contribution_basis_member_id", "cost_captured_contribution_basis"),
        Index(
            "ix_cost_contribution_group",
            "tenant_id",
            "generation_id",
            "currency",
            "base_unit",
        ),
        CheckConstraint(
            "(state='available_at_capture' AND currency IS NOT NULL AND base_unit IS NOT NULL AND revenue IS NOT NULL AND goods_cost IS NOT NULL) OR (state='unknown_at_capture' AND currency IS NULL AND base_unit IS NULL AND revenue IS NULL AND goods_cost IS NULL AND direct_selling_cost IS NULL AND allocated_selling_cost IS NULL)",
            name="ck_cost_contribution_row_shape",
        ),
        CheckConstraint("goods_cost>=0", name="ck_cost_contribution_row_goods"),
    )
    generation_id: Mapped[str] = mapped_column(String, index=True)
    contribution_basis_member_id: Mapped[str] = mapped_column(String, index=True)
    state: Mapped[str] = mapped_column(String)
    currency: Mapped[str | None] = mapped_column(String)
    base_unit: Mapped[str | None] = mapped_column(String)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    goods_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    direct_selling_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    allocated_selling_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))


class CostPublication(CostRecord, Base):
    __tablename__ = "cost_publication"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_key"),
        ForeignKeyConstraint(
            ["tenant_id", "scope_key", "generation_id"],
            [
                "cost_generation.tenant_id",
                "cost_generation.scope_key",
                "cost_generation.id",
            ],
        ),
    )
    scope_key: Mapped[str] = mapped_column(String(64))
    generation_id: Mapped[str] = mapped_column(String, index=True)
