from pathlib import Path

import yaml

from reality.db.core import (
    CompanyInvitation,
    InvitationDelivery,
    SecurityAuditEvent,
    TenantMembership,
)

ROOT = Path(__file__).resolve().parents[3]


def test_membership_invitation_models_keep_shortest_tenant_scoped_links() -> None:
    invitation_columns = set(CompanyInvitation.__table__.columns.keys())
    delivery_columns = set(InvitationDelivery.__table__.columns.keys())

    assert {"tenant_id", "normalized_email", "terminal_at"} <= invitation_columns
    assert "user_id" not in invitation_columns
    assert {"tenant_id", "invitation_id", "generation"} <= delivery_columns
    assert "membership_id" not in invitation_columns | delivery_columns
    assert "invitation_id" not in TenantMembership.__table__.columns


def test_access_model_catalog_matches_sqlalchemy_models() -> None:
    catalog = yaml.safe_load(
        (ROOT / "packages/reality-core/config/data_model.yaml").read_text(
            encoding="utf-8"
        )
    )
    access_tables = next(
        section["tables"]
        for section in catalog["sections"]
        if section["name"] == "Accounts and Access"
    )

    assert "company_invitation" in access_tables
    assert "invitation_delivery" in access_tables
    assert {"tenant_id", "subject_type", "subject_id", "outcome"} <= set(
        SecurityAuditEvent.__table__.columns.keys()
    )
