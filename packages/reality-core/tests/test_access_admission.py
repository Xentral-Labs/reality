"""Admission defaults and cumulative capacity across mode changes."""

import pytest

from reality.db.core import AccessAdmissionCounter
from reality.web import auth


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, None),
        ("", None),
        ("  ", None),
        ("0", 0),
        ("2", 2),
        (" 2 ", 2),
        ("-1", 0),
        ("invalid", 0),
        ("1.5", 0),
    ],
)
def test_admission_setting(raw, expected, monkeypatch):
    if raw is None:
        monkeypatch.delenv("REALITY_AUTO_APPROVE_LIMIT", raising=False)
    else:
        monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", raw)
    assert auth.automatic_access_limit() == expected


def test_open_admissions_count_toward_later_finite_limit(session, monkeypatch):
    session.add(AccessAdmissionCounter(id="automatic", used_slots=0))
    session.flush()
    monkeypatch.delenv("REALITY_AUTO_APPROVE_LIMIT", raising=False)
    assert auth.claim_automatic_access_slot(session)
    assert auth.claim_automatic_access_slot(session)
    monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", "3")
    assert auth.claim_automatic_access_slot(session)
    assert not auth.claim_automatic_access_slot(session)
    monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", "0")
    assert not auth.claim_automatic_access_slot(session)
    session.expire_all()
    assert session.get(AccessAdmissionCounter, "automatic").used_slots == 3


def test_concurrent_admission_cannot_exceed_finite_capacity(
    postgres_database, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine(postgres_database)
    try:
        AccessAdmissionCounter.__table__.create(engine)
        with Session(engine) as session:
            session.add(AccessAdmissionCounter(id="automatic", used_slots=0))
            session.commit()
        monkeypatch.setenv("REALITY_AUTO_APPROVE_LIMIT", "3")

        def admit(_):
            with Session(engine) as session:
                admitted = auth.claim_automatic_access_slot(session)
                session.commit()
                return admitted

        with ThreadPoolExecutor(max_workers=8) as pool:
            assert sum(pool.map(admit, range(12))) == 3
        with Session(engine) as session:
            assert session.get(AccessAdmissionCounter, "automatic").used_slots == 3
    finally:
        engine.dispose()


def test_generic_installation_defaults_do_not_restrict_admission():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    # compose.dev.yml only ever carried this through the marketing-site dev
    # service, which is provider content and not built here; the api service it
    # overlays takes the variable from compose.yml.
    for name in ("compose.yml", "installer/compose.yml"):
        lines = [
            line
            for line in (root / name).read_text().splitlines()
            if "REALITY_AUTO_APPROVE_LIMIT:" in line
        ]
        assert lines
        assert all("${REALITY_AUTO_APPROVE_LIMIT:-}" in line for line in lines)
    for name in (".env.example", "installer/install.sh"):
        assert "\nREALITY_AUTO_APPROVE_LIMIT=\n" in (root / name).read_text()
    assert 'autoApproveLimit: ""' in (root / "helm/reality/values.yaml").read_text()
