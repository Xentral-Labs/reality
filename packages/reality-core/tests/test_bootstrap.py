from sqlalchemy import func, select

from reality.db.core import Party, Tenant
from reality.services.bootstrap import bootstrap_empty_database


def test_configured_bootstrap_creates_demo_once(session, monkeypatch):
    monkeypatch.setenv("REALITY_BOOTSTRAP_TENANT_NAME", "Acme Bikes GmbH")

    tenant = bootstrap_empty_database(session)
    repeated = bootstrap_empty_database(session)

    assert tenant is not None
    assert tenant.name == "Acme Bikes GmbH"
    assert repeated is None
    assert session.scalar(select(func.count(Tenant.id))) == 1
    assert session.scalar(select(func.count(Party.id))) == 3


def test_bootstrap_is_disabled_without_configuration(session, monkeypatch):
    monkeypatch.delenv("REALITY_BOOTSTRAP_TENANT_NAME", raising=False)

    assert bootstrap_empty_database(session) is None
    assert session.scalar(select(func.count(Tenant.id))) == 0
