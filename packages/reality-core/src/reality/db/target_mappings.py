"""Finance-only target catalogs and immutable reviewed mapping decisions."""

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


class AccountingTarget(Base):
    __tablename__ = "accounting_target"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "namespace"),
        CheckConstraint(
            "state IN ('active','blocked') AND revision > 0 AND length(trim(namespace)) > 0 AND length(trim(name)) > 0",
            name="ck_accounting_target_values",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    namespace: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String)
    revision: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class AccountingTargetReference(Base):
    __tablename__ = "accounting_target_reference"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "target_id"],
            ["accounting_target.tenant_id", "accounting_target.id"],
        ),
        UniqueConstraint("tenant_id", "target_id", "kind", "code"),
        UniqueConstraint("tenant_id", "target_id", "id", "kind"),
        CheckConstraint(
            "kind IN ('account','tax_code') AND state IN ('active','blocked') AND revision > 0 AND length(trim(code)) > 0 AND length(trim(name)) > 0",
            name="ck_accounting_reference_values",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    target_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String)
    revision: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class TargetMapping(Base):
    __tablename__ = "finance_target_mapping_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "target_id"],
            ["accounting_target.tenant_id", "accounting_target.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replaces_id"],
            [
                "finance_target_mapping_revision.tenant_id",
                "finance_target_mapping_revision.id",
            ],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "local_account_id"],
            ["subledger_account.tenant_id", "subledger_account.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "case_reference_id", "case_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "group_reference_id", "group_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_id", "external_account_id", "account_kind"],
            [
                "accounting_target_reference.tenant_id",
                "accounting_target_reference.target_id",
                "accounting_target_reference.id",
                "accounting_target_reference.kind",
            ],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_id", "external_tax_code_id", "tax_kind"],
            [
                "accounting_target_reference.tenant_id",
                "accounting_target_reference.target_id",
                "accounting_target_reference.id",
                "accounting_target_reference.kind",
            ],
        ),
        CheckConstraint(
            "case_kind = 'case_code' AND group_kind = 'coding_group' AND account_kind = 'account' AND tax_kind = 'tax_code'",
            name="ck_target_mapping_reference_kinds",
        ),
        CheckConstraint(
            "state IN ('active','blocked') AND revision > 0 AND length(trim(reason)) > 0",
            name="ck_target_mapping_values",
        ),
        CheckConstraint(
            "(mapping_kind = 'local_account' AND local_account_id IS NOT NULL AND transaction_kind IS NULL AND case_reference_id IS NULL AND group_mode IS NULL AND group_reference_id IS NULL AND external_tax_code_id IS NULL) OR (mapping_kind = 'case_routing' AND local_account_id IS NULL AND transaction_kind IS NOT NULL AND transaction_kind IN ('sales_invoice','supplier_invoice','credit_note','supplier_credit_note') AND case_reference_id IS NOT NULL AND group_mode IS NOT NULL AND ((group_mode = 'none' AND group_reference_id IS NULL) OR (group_mode = 'exact' AND group_reference_id IS NOT NULL)))",
            name="ck_target_mapping_shape",
        ),
        *[
            Index(
                "uq_target_mapping_" + name + suffix,
                "tenant_id",
                "target_id",
                *keys,
                *(["revision"] if suffix == "_revision" else []),
                unique=True,
                postgresql_where=text(
                    condition + (" AND is_current" if suffix == "_current" else "")
                ),
            )
            for name, keys, condition in (
                ("account", ["local_account_id"], "mapping_kind = 'local_account'"),
                (
                    "case",
                    ["transaction_kind", "case_reference_id"],
                    "mapping_kind = 'case_routing' AND group_mode = 'none'",
                ),
                (
                    "group",
                    ["transaction_kind", "case_reference_id", "group_reference_id"],
                    "mapping_kind = 'case_routing' AND group_mode = 'exact'",
                ),
            )
            for suffix in ("_revision", "_current")
        ],
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    target_id: Mapped[str] = mapped_column(String)
    mapping_kind: Mapped[str] = mapped_column(String)
    local_account_id: Mapped[str | None] = mapped_column(String)
    transaction_kind: Mapped[str | None] = mapped_column(String)
    case_reference_id: Mapped[str | None] = mapped_column(String)
    group_mode: Mapped[str | None] = mapped_column(String)
    group_reference_id: Mapped[str | None] = mapped_column(String)
    external_account_id: Mapped[str] = mapped_column(String)
    external_tax_code_id: Mapped[str | None] = mapped_column(String)
    case_kind: Mapped[str] = mapped_column(String, default="case_code")
    group_kind: Mapped[str] = mapped_column(String, default="coding_group")
    account_kind: Mapped[str] = mapped_column(String, default="account")
    tax_kind: Mapped[str] = mapped_column(String, default="tax_code")
    revision: Mapped[int]
    replaces_id: Mapped[str | None] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    configuration_snapshot: Mapped[dict] = mapped_column(JSONB)
    reason: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[str | None] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(ForeignKey("action.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
