"""Disposable, atomically published observations of retained cost reviews."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime
from reality.db.costing import CostRecord, _link


class CostInventoryGeneration(CostRecord, Base):
    __tablename__ = "cost_inventory_generation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "review_id", "id"),
        UniqueConstraint(
            "tenant_id",
            "review_id",
            "assessment_revision_id",
            "algorithm_version",
            postgresql_nulls_not_distinct=True,
        ),
        _link("review_id", "cost_inventory_review"),
        _link("assessment_revision_id", "cost_valuation_assessment_revision"),
        CheckConstraint(
            "algorithm_version='inventory-v1' AND length(output_hash)=64",
            name="ck_inventory_generation_version",
        ),
    )
    review_id: Mapped[str] = mapped_column(String)
    assessment_revision_id: Mapped[str | None] = mapped_column(String)
    algorithm_version: Mapped[str] = mapped_column(String)
    completed_at: Mapped[datetime] = mapped_column(UTCDateTime)
    output_hash: Mapped[str] = mapped_column(String(64))


class CostInventorySnapshot(CostRecord, Base):
    __tablename__ = "cost_inventory_snapshot"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "generation_id"),
        _link("generation_id", "cost_inventory_generation"),
        CheckConstraint(
            "remaining_quantity>=0 AND acquisition_value>=0 AND (carrying_value IS NULL OR (carrying_value>=0 AND carrying_value<=acquisition_value))",
            name="ck_inventory_snapshot_amounts",
        ),
    )
    generation_id: Mapped[str] = mapped_column(String)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    acquisition_value: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    carrying_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))


class CostInventoryPublication(CostRecord, Base):
    __tablename__ = "cost_inventory_publication"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "review_id"),
        _link("review_id", "cost_inventory_review"),
        ForeignKeyConstraint(
            ["tenant_id", "review_id", "generation_id"],
            [
                "cost_inventory_generation.tenant_id",
                "cost_inventory_generation.review_id",
                "cost_inventory_generation.id",
            ],
        ),
    )
    review_id: Mapped[str] = mapped_column(String)
    generation_id: Mapped[str] = mapped_column(String)


class CostContributionGeneration(CostRecord, Base):
    __tablename__ = "cost_contribution_generation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "action_id", "algorithm_version"),
        _link("action_id", "action"),
        CheckConstraint(
            "algorithm_version='commercial-v1' AND length(output_hash)=64",
            name="ck_contribution_generation_version",
        ),
    )
    action_id: Mapped[str] = mapped_column(String)
    algorithm_version: Mapped[str] = mapped_column(String)
    completed_at: Mapped[datetime] = mapped_column(UTCDateTime)
    output_hash: Mapped[str] = mapped_column(String(64))


class CostContributionSnapshot(CostRecord, Base):
    __tablename__ = "cost_contribution_snapshot"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "generation_id", "review_id"),
        _link("generation_id", "cost_contribution_generation"),
        _link("review_id", "cost_contribution_review"),
        CheckConstraint("goods_cost>=0", name="ck_contribution_snapshot_goods"),
        CheckConstraint(
            "(known_direct_selling_cost IS NULL) = (known_allocated_selling_cost IS NULL) AND (NOT selling_complete OR known_direct_selling_cost IS NOT NULL)",
            name="ck_contribution_snapshot_selling",
        ),
    )
    generation_id: Mapped[str] = mapped_column(String)
    review_id: Mapped[str] = mapped_column(String)
    goods_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    known_direct_selling_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    known_allocated_selling_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    selling_complete: Mapped[bool]
